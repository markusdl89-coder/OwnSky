import math
import time
from typing import Dict, Any, Tuple
import database as db
from economy import calculate_cargo_metrics, calculate_dynamic_price

class GameCore:
    
    @staticmethod
    def update_city_production(city_name: str):
        """
        Проверяет, сколько реального времени прошло с последнего тика фабрик города,
        и доначисляет произведенные ресурсы на склад биржи.
        """
        current_time = int(time.time())
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT last_tick FROM locations WHERE name = %s;", [city_name])
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return

        last_tick = row[0]
        time_passed = current_time - last_tick
        tick_interval = 60 
        accumulated_ticks = time_passed // tick_interval
        
        if accumulated_ticks > 0:
            if city_name == 'Горн':
                production = {"steel": 2 * accumulated_ticks, "tools": 1 * accumulated_ticks, "coal": -1 * accumulated_ticks}
            elif city_name == 'Пар-Сити':
                production = {"fuel": 3 * accumulated_ticks, "steel": -1 * accumulated_ticks}
            else:
                production = {"coal": 2 * accumulated_ticks, "iron_ore": 2 * accumulated_ticks}
                
            for item_id, change_qty in production.items():
                cursor.execute("""
                    SELECT quantity FROM inventories 
                    WHERE owner_type = 'city' AND owner_name = %s AND item_name = %s
                """, (city_name, item_id))
                inv_row = cursor.fetchone()
                
                if inv_row is not None:
                    new_qty = max(0, inv_row[0] + change_qty)
                    cursor.execute("""
                        UPDATE inventories SET quantity = %s 
                        WHERE owner_type = 'city' AND owner_name = %s AND item_name = %s
                    """, (new_qty, city_name, item_id))
            
            new_tick_time = last_tick + (accumulated_ticks * tick_interval)
            cursor.execute("UPDATE locations SET last_tick = %s WHERE name = %s;", [new_tick_time, city_name])
            conn.commit()
            
        cursor.close()
        conn.close()

    @staticmethod
    def check_and_update_flight_status(user_id: int) -> str:
        """Проверяет таймер прибытия и переводит корабль в статус порта."""
        p = db.get_player_data(user_id)
        if not p or p['status'] != 'В полете':
            return "idle"
            
        current_time = int(time.time())
        arrival_timestamp = p.get('arrival_time')
        
        if arrival_timestamp and current_time >= int(arrival_timestamp):
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE players 
                SET x = target_x, 
                    y = target_y, 
                    status = 'В порту', 
                    arrival_time = NULL 
                WHERE user_id = %s;
            """, [user_id])
            conn.commit()
            cursor.close()
            conn.close()
            return "arrived"
            
        return "flying"

    @staticmethod
    def get_ship_report(user_id: int) -> str:
        """Формирует полный текстовый отчет о состоянии дирижабля."""
        GameCore.check_and_update_flight_status(user_id)
        p = db.get_player_data(user_id)
        if not p:
            return "❌ Капитан не найден. Используйте /start для регистрации."
            
        cargo = db.get_player_cargo_dict(user_id)
        current_weight, current_volume = calculate_cargo_metrics(cargo)
        
        current_time = int(time.time())
        if p['status'] == 'В полете':
            arrival = p.get('arrival_time')
            if arrival and current_time < arrival:
                remaining = int(arrival - current_time)
                minutes = remaining // 60
                seconds = remaining % 60
                status_text = f"✈ В полете (Осталось: {minutes}м {seconds}с)"
            else:
                status_text = "✈ Завершает маневр посадки..."
        else:
            status_text = "⚓ В порту"
            
        report = (
            f"🛸 **ДИРИЖАБЛЬ: {p['ship_type']}**\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"💰 Кредиты: `{p['credits']}` 🪙\n"
            f"⛽ Топливо: `{p['fuel']}/{p['max_fuel']}` Брл.\n"
            f"📦 Масса трюма: `{current_weight}/{p['max_cargo']}` кг\n"
            f"📐 Объем трюма: `{current_volume}/{p['max_volume']}` куб.м\n"
            f"📍 Координаты: `[{p['x']}, {p['y']}]` \n"
            f"📊 Статус: **{status_text}**\n"
        )
        return report

    @staticmethod
    def start_flight(user_id: int, target_city_name: str) -> Tuple[bool, str]:
        """Инициализирует перелет реального времени."""
        p = db.get_player_data(user_id)
        if not p: 
            return False, "Вы не зарегистрированы."
        if p['status'] == 'В полете': 
            return False, "❌ Ваш дирижабль уже находится в воздухе!"
            
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT x, y FROM locations WHERE name = %s;", [target_city_name])
        city = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not city:
            return False, "🗺 Такой город не найден на полетных картах."
            
        tx, ty = city[0], city[1]
        distance = math.hypot(tx - p['x'], ty - p['y'])
        if distance == 0:
            return False, "🏙 Вы уже находитесь в этом городе!"
            
        # === НАСТРОЙКА БАЛАНСА ВРЕМЕНИ ПОЛЕТА ===
        # ship_speed = 10 
        # travel_time = int(distance / ship_speed) 
        travel_time = 10  # Временный тест на 10 секунд для проверок
        # =======================================
        
        fuel_cost = 5
        if p['fuel'] < fuel_cost:
            return False, f"⛽ Недостаточно топлива! Для этого перелета нужно {fuel_cost} Брл."
            
        arrival_timestamp = int(time.time()) + travel_time
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE players 
            SET status = 'В полете', 
                target_x = %s, 
                target_y = %s, 
                arrival_time = %s, 
                fuel = fuel - %s 
            WHERE user_id = %s;
        """, [tx, ty, arrival_timestamp, fuel_cost, user_id])
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, f"🚀 Дирижабль отдал швартовы и взял курс на **{target_city_name}**! Время в пути: {travel_time} сек."

    @staticmethod
    def get_market_data(city_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Собирает данные рынка города для инлайн-кнопок.
        Сразу обсчитывает пассивное производство фабрик.
        """
        GameCore.update_city_production(city_name)
        
        from items import ITEMS_REGISTRY
        market_profile = {}
        
        for item_id in ITEMS_REGISTRY.keys():
            stock, base_demand = db.get_city_storage_data(city_name, item_id)
            prices = calculate_dynamic_price(item_id, stock, base_demand)
            
            market_profile[item_id] = {
                "stock": stock,
                "buy_price": prices["buy_price"],
                "sell_price": prices["sell_price"],
                "is_contraband": prices["is_contraband"]
            }
        return market_profile

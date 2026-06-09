import math
import time
from typing import Dict, Any, Tuple
import database as db
from economy import calculate_cargo_metrics

class GameCore:
    
    @staticmethod
    def get_ship_report(user_id: int) -> str:
        """
        Формирует полный текстовый отчет о состоянии дирижабля для Telegram.
        Выводит массу и объем трюма на лету, убирая пустые ресурсы.
        """
        p = db.get_player_data(user_id)
        if not p:
            return "❌ Капитан не найден. Используйте /start для регистрации."
            
        # Запрашиваем из универсальной таблицы текущие грузы игрока
        cargo = db.get_player_cargo_dict(user_id)
        current_weight, current_volume = calculate_cargo_metrics(cargo)
        
        # Считаем статус и время полета
        current_time = int(time.time())
        if p['status'] == 'В полете':
            arrival = p.get('arrival_time')
            if arrival and current_time < arrival:
                remaining = int(arrival - current_time)
                # Красивое отображение минут и секунд без дробей
                minutes = remaining // 60
                seconds = remaining % 60
                status_text = f"✈ В полете (Осталось: {minutes}м {seconds}с)"
            else:
                status_text = "✈ Завершает маневр посадки..."
        else:
            status_text = "⚓ В порту"
            
        # Формируем scannable-интерфейс для экрана смартфона
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
        """
        Инициализирует полет до выбранного города.
        Рассчитывает точную целую секунду прибытия в реальном времени.
        """
        p = db.get_player_data(user_id)
        if not p: 
            return False, "Вы не зарегистрированы."
        if p['status'] == 'В полете': 
            return False, "❌ Ваш дирижабль уже находится в воздухе!"
            
        # Ищем координаты города назначения в базе данных
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT x, y FROM locations WHERE name = %s;", [target_city_name])
        city = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not city:
            return False, "🗺 Такой город не найден на полетных картах."
            
        tx, ty = city
        
        # Расстояние между текущей точкой дирижабля и целью
        distance = math.hypot(tx - p['x'], ty - p['y'])
        if distance == 0:
            return False, "🏙 Вы уже находитесь в этом городе!"
            
        # ====================================================================
        # === НАСТРОЙКА БАЛАНСА: СКОРОСТЬ И ВРЕМЯ ПОЛЕТА (РЕАЛЬНОЕ ВРЕМЯ) ===
        # ====================================================================
        # 1. Твоя будущая базовая скорость корабля (км в час или единиц в секунду):
        ship_speed = 10 
        
        # 2. Формула реального времени: расстояние делим на скорость (в секундах)
        # travel_time = int(distance / ship_speed) 
        
        # 3. ВРЕМЕННЫЙ ТЕСТОВЫЙ РЕЖИМ (сейчас любой полет длится ровно 10 секунд):
        travel_time = 10 
        # ====================================================================
        
        # Расход топлива (строго целое число, например, 5 бочек за перелет)
        fuel_cost = 5
        if p['fuel'] < fuel_cost:
            return False, f"⛽ Недостаточно топлива! Для этого перелета нужно {fuel_cost} Брл."
            
        # Вычисляем точную целую секунду Unix, когда корабль должен прилететь
        arrival_timestamp = int(time.time()) + travel_time
        
        # Записываем параметры полета в Postgres
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
    def check_and_update_flight_status(user_id: int) -> str:
        """
        Проверяет, наступило ли время прилета.
        Если время пришло — мгновенно переносит корабль в координаты города.
        Возвращает: 'arrived' (прилетел), 'flying' (еще летит), 'idle' (был в порту).
        """
        p = db.get_player_data(user_id)
        if not p or p['status'] != 'В полете':
            return "idle"
            
        current_time = int(time.time())
        arrival_timestamp = p.get('arrival_time')
        
        # Проверяем: текущее время компьютера уже больше или равно времени финиша?
        if arrival_timestamp and current_time >= int(arrival_timestamp):
            # Время пришло! Фиксируем прибытие корабля в координаты цели
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

import time
import math
from typing import Dict, Any, Optional
# Мы используем заглушку базы данных, если реальный модуль db не импортирован.
# В реальном коде убедись, что db настроен на работу с Neon.tech
try:
    import db
except ImportError:
    class MockDB:
        @staticmethod
        def get_player_data(user_id: int) -> Optional[Dict[str, Any]]:
            return None
        @staticmethod
        def get_connection():
            return None
    db = MockDB()

# Импортируем функции штурманского плана
from navigation import process_flight_plan_action

class GameCore:
    """Центральный процессор игровых механик OwnSky."""
    
    @staticmethod
    def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
        """Вычисляет гипотенузу (расстояние) между двумя координатами."""
        return math.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def start_flight(user_id: int, target_location_name: str) -> str:
        """
        Инициализирует полет корабля.
        Вычисляет расстояние, списывает топливо, устанавливает статус 'В полете' 
        и рассчитывает arrival_time (время прибытия).
        """
        p = db.get_player_data(user_id)
        if not p:
            return "Игрок не найден."
            
        if p.get('status') == 'В полете':
            return "Корабль уже находится в небе!"

        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Получаем координаты цели
        cursor.execute("SELECT x, y FROM locations WHERE name = %s;", (target_location_name,))
        loc = cursor.fetchone()
        if not loc:
            cursor.close()
            conn.close()
            return f"Локация '{target_location_name}' не найдена на карте."
            
        tx, ty = loc[0], loc[1]
        
        # Считаем дистанцию и расход топлива
        distance = GameCore.calculate_distance(p['x'], p['y'], tx, ty)
        fuel_cost = int(distance * 0.5)  # 1 единица топлива на 2 км пути
        
        if p['fuel'] < fuel_cost:
            cursor.close()
            conn.close()
            return f"Недостаточно топлива для перелета. Требуется: {fuel_cost}, доступно: {p['fuel']}."
            
        # Настройка времени (скорость: 10 км за 1 реальную секунду для тестов)
        speed = 10.0
        flight_duration = max(int(distance / speed), 2)  # Минимум 2 секунды полета
        arrival_time = int(time.time()) + flight_duration
        
        # Запись полета в БД
        cursor.execute("""
            UPDATE players 
            SET status = 'В полете', 
                target_x = %s, target_y = %s, 
                arrival_time = %s, 
                fuel = fuel - %s
            WHERE user_id = %s;
        """, (tx, ty, arrival_time, fuel_cost, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return f"Дирижабль поднялся в воздух и взял курс на {target_location_name}. Время в пути: {flight_duration} сек."

    @staticmethod
    def check_and_update_flight_status(user_id: int) -> str:
        """Проверяет таймер прибытия, выполняет торговый приказ в порту и запускает следующую точку плана."""
        p = db.get_player_data(user_id)
        if not p:
            return "idle"

        # СИТУАЦИЯ А: Корабль стоит на месте, проверяем, нет ли новых приказов в плане
        if p['status'] != 'В полете':
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, target_x, target_y, action 
                FROM flight_plans 
                WHERE user_id = %s AND status = 'pending' 
                ORDER BY queue_order ASC LIMIT 1;
            """, [user_id])
            next_point = cursor.fetchone()
            
            if next_point:
                plan_id, tx, ty, action = next_point
                
                # Ищем имя города по координатам, чтобы скормить его в start_flight
                cursor.execute("SELECT name FROM locations WHERE x = %s AND y = %s;", (tx, ty))
                city_row = cursor.fetchone()
                
                if city_row:
                    city_name = city_row[0]
                    # Переводим точку полетного плана в статус активной
                    cursor.execute("UPDATE flight_plans SET status = 'active' WHERE id = %s;", [plan_id])
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    # Отправляем дирижабль в путь
                    GameCore.start_flight(user_id, city_name)
                    return "flying"
                    
            if 'cursor' in locals() and not cursor.closed:
                cursor.close()
            if 'conn' in locals() and not conn.closed:
                conn.close()
            return "idle"

        # СИТУАЦИЯ Б: Корабль летел, проверяем таймер приземления
        current_time = int(time.time())
        arrival_timestamp = p.get('arrival_time')
        
        if arrival_timestamp and current_time >= int(arrival_timestamp):
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # 1. Достаем текущий активный приказ
            cursor.execute("""
                SELECT id, action FROM flight_plans 
                WHERE user_id = %s AND status = 'active';
            """, [user_id])
            active_row = cursor.fetchone()
            
            report_msg = ""
            if active_row:
                plan_id, action = active_row
                # ВЫПОЛНЯЕМ ТОРГОВЫЙ ПРИКАЗ ПО НАШЕЙ ЭКОНОМИКЕ
                report_msg = process_flight_plan_action(cursor, user_id, action)
                
                # Помечаем эту точку маршрута как выполненную
                cursor.execute("UPDATE flight_plans SET status = 'completed' WHERE id = %s;", [plan_id])
            
            # 2. Обновляем статус игрока: перемещаем его в координаты города
            cursor.execute("""
                UPDATE players
                SET x = target_x, y = target_y, status = 'В порту', arrival_time = NULL
                WHERE user_id = %s;
            """, [user_id])
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Печатаем лог сделки в консоль сервера (позже выведем игроку в телеграм)
            if report_msg:
                print(f"[БОРТОВОЙ ЖУРНАЛ ИГРОКА {user_id}]: {report_msg}")
            
            # 3. Рекурсивно проверяем: возможно в очереди есть следующая точка? Полетели дальше!
            return GameCore.check_and_update_flight_status(user_id)
            
        return "flying"

    @staticmethod
    def get_ship_report(user_id: int) -> Dict[str, Any]:
        """Формирует текущий статус корабля для вывода игроку."""
        GameCore.check_and_update_flight_status(user_id)
        p = db.get_player_data(user_id)
        if not p:
            return {"error": "Корабль пропал с радаров рейнджеров."}
            
        if p['status'] == 'В полете':
            remains = max(0, int(p['arrival_time']) - int(time.time()))
            return {
                "status": "В небе",
                "message": f"Дирижабль идет по приборам. Прибытие через {remains} сек.",
                "fuel": f"{p['fuel']}/{p['max_fuel']}"
            }
        
        return {
            "status": "В порту",
            "message": f"Корабль пришвартован в координатах ({p['x']}, {p['y']}). Экипаж готов к заправке.",
            "fuel": f"{p['fuel']}/{p['max_fuel']}"
        }

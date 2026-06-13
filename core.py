# ====================================================================
# МОДУЛЬ: core.py (Ядро логической системы OwnSky)
# Слой: Логика автоматических рейсов, перемещений и симуляции экономики
# ====================================================================

import math
from typing import List, Dict, Any, Tuple

# Импорты внутренних модулей проекта
from items import ITEMS_REGISTRY  # Физические параметры ресурсов (вес, объем)
from ships import get_ship_blueprint, calculate_current_speed  # Параметры дирижаблей
import config

# ====================================================================
# СЛОЙ 1: СИСТЕМА АВТОМАТИЧЕСКИХ РЕЙСОВ (НОВЫЙ ФУНКЦИОНАЛ)
# ====================================================================

def calculate_route_estimate(user_id: int, points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    [Шаг 1] Калькулятор сметы маршрута.
    Считает суммарное расстояние, динамическую скорость корабля по массе груза,
    необходимое количество топлива и время полета в минутах.
    """
    # Изолированный импорт для предотвращения циклической зависимости (Circular Import)
    from main import get_connection  
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Получаем текущую модель корабля игрока из базы данных Neon
    cursor.execute("SELECT ship_type FROM players WHERE user_id = %s;", (user_id,))
    ship_row = cursor.fetchone()
    ship_type = ship_row[0] if ship_row and ship_row[0] else "scout"
    blueprint = get_ship_blueprint(ship_type)
    
    # 2. Сканируем трюм игрока для вычисления точной массы груза
    cursor.execute("SELECT item_id, quantity FROM inventories WHERE user_id = %s;", (user_id,))
    inventory_rows = cursor.fetchall()
    
    current_weight = 0.0
    current_fuel_in_inventory = 0  # Общий запас топлива на борту
    
    for item_id, quantity in inventory_rows:
        if item_id in ITEMS_REGISTRY:
            current_weight += ITEMS_REGISTRY[item_id].weight * quantity
            if item_id == "fuel":
                current_fuel_in_inventory += quantity
                
    cursor.close()
    conn.close()
    
    # 3. Рассчитываем реальную скорость с учетом утяжеления корабля
    actual_speed = calculate_current_speed(blueprint, current_weight)
    
    # 4. Преобразуем абстрактные точки цепочки в координатную сетку X/Y
    coords_chain: List[Tuple[int, int]] = []
    for pt in points:
        if pt.get("type") == "city":
            city_name = pt.get("name")
            if city_name in config.CITIES:
                coords_chain.append(config.CITIES[city_name])
        elif pt.get("type") == "coords":
            coords_chain.append((pt.get("x"), pt.get("y")))
            
    # Если маршрут пустой или состоит из одной точки — лететь некуда
    if len(coords_chain) < 2:
        return {
            "total_distance": 0.0,
            "current_speed": actual_speed,
            "total_time_min": 0.0,
            "fuel_needed": 0,
            "has_enough_fuel": True
        }
        
    # 5. Вычисляем общее расстояние по всей цепочке (формула Евклида)
    total_distance = 0.0
    for i in range(len(coords_chain) - 1):
        x1, y1 = coords_chain[i]
        x2, y2 = coords_chain[i+1]
        total_distance += math.hypot(x2 - x1, y2 - y1)
        
    # 6. Финальный расчет затрат
    # Расход бензина округляем в большую сторону
    fuel_needed = math.ceil(total_distance * blueprint.fuel_consumption)
    # Время полета в минутах
    total_time_min = round(total_distance / actual_speed, 1) if actual_speed > 0 else 0.0
    # Проверка физического наличия топлива в инвентаре
    has_enough_fuel = current_fuel_in_inventory >= fuel_needed
    
    return {
        "total_distance": round(total_distance, 1),
        "current_speed": round(actual_speed, 1),
        "total_time_min": total_time_min,
        "fuel_needed": fuel_needed,
        "has_enough_fuel": has_enough_fuel
    }


# ====================================================================
# СЛОЙ 2: СТАРАЯ ИГРОВАЯ СИСТЕМА (СОХРАНЕНИЕ СОВМЕСТИМОСТИ ДЛЯ MAIN.PY)
# ====================================================================

class GameCore:
    """
    Класс-заглушка для сохранения обратной совместимости со старыми вызовами.
    Постепенно перенесем всю логику из этого слоя в чистые функции Слоя 1.
    """
    def __init__(self):
        # Оставляем инициализацию пустой, так как база данных теперь работает напрямую через Neon
        pass

    def process_turn(self):
        """Старая заглушка обработки игрового тика."""
        return "Симуляция шага выполнена (Архив)"

    def get_market_prices(self):
        """Старая заглушка для получения цен."""
        return {"coal": 10, "iron_ore": 20, "fuel": 50}

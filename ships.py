# ships.py
# Модуль чертежей и конфигураций дирижаблей проекта OwnSky

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ShipBlueprint:
    id: str                      # Уникальный идентификатор модели (например, "scout")
    name: str                    # Красивое название для вывода игроку
    base_speed: float            # Скорость пустого корабля (координатных единиц в минуту)
    fuel_consumption: float      # Базовый расход топлива (fuel) на 1 единицу расстояния
    max_weight: int              # Предельная грузоподъемность в килограммах (кг)
    max_volume: int              # Физическая вместимость трюма в условных единицах объема
    speed_penalty_factor: float  # Максимальная потеря скорости при 100% загрузке веса (0.3 = 30%)

# Глобальный реестр чертежей кораблей мира OwnSky
SHIP_TEMPLATES: Dict[str, ShipBlueprint] = {
    "scout": ShipBlueprint(
        id="scout",
        name="Ветроход «Скаут»",
        base_speed=12.0,            # Проходит 12 единиц карты за минуту
        fuel_consumption=0.1,       # Тратит 1 бочку топлива на 10 единиц пути
        max_weight=600,             # Подъёмный лимит гелиевых баллонов в кг
        max_volume=30,              # Объём трюма под потолок (помещается 15 бочек топлива или 30 руды)
        speed_penalty_factor=0.3    # Полный вес замедляет дирижабль максимум на 30% (скорость упадет до 8.4)
    )
    # В будущем сюда легко добавятся тяжелые баржи, броненосцы и фрегаты
}

def get_ship_blueprint(ship_id: Optional[str]) -> ShipBlueprint:
    """
    Безопасно возвращает технический паспорт корабля по его ID.
    Если у игрока старый аккаунт или корабль не найден, возвращает базовый 'scout'.
    """
    if not ship_id or ship_id not in SHIP_TEMPLATES:
        return SHIP_TEMPLATES["scout"]
    return SHIP_TEMPLATES[ship_id]

def calculate_current_speed(blueprint: ShipBlueprint, current_weight: float) -> float:
    """
    Рассчитывает динамическую скорость дирижабля на основе веса груза.
    Объем груза на скорость не влияет — только масса, тянущая корабль к земле.
    """
    if current_weight <= 0:
        return blueprint.base_speed
        
    # Если вес превышает максимальный (перегруз), штраф применяется к максимальному лимиту
    weight_ratio = min(current_weight / blueprint.max_weight, 1.0)
    
    # Формула: Скорость = Базовая * (1 - Штраф * Процент_Загрузки_Веса)
    penalty = blueprint.speed_penalty_factor * weight_ratio
    return blueprint.base_speed * (1.0 - penalty)

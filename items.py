from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class Item:
    id: str
    name: str
    description: str
    weight: int  # Только целые числа
    volume: int  # Только целые числа
    base_price: int
    is_contraband: bool = False

# Глобальный реестр игровых ресурсов
ITEMS_REGISTRY: Dict[str, Item] = {
    "coal": Item(
        id="coal",
        name="Уголь",
        description="Горючее ископаемое. Основа тяжелой промышленности.",
        weight=10,
        volume=1,
        base_price=20
    ),
    "iron_ore": Item(
        id="iron_ore",
        name="Железная руда",
        description="Необработанная порода. Требует переплавки.",
        weight=20,
        volume=1,
        base_price=35
    ),
    "steel": Item(
        id="steel",
        name="Сталь",
        description="Прочный сплав для обшивки кораблей и станков.",
        weight=50,
        volume=1,
        base_price=90
    ),
    "tools": Item(
        id="tools",
        name="Инструменты",
        description="Высокоточные наборы для ремонта и сборки модулей.",
        weight=15,
        volume=1,
        base_price=150
    ),
    "fuel": Item(
        id="fuel",
        name="Топливо в бочках",
        description="Тяжелое топливо для маршевых двигателей. Можно заправлять в бак.",
        weight=30,
        volume=2,
        base_price=60
    )
}

def get_item(item_id: str) -> Item | None:
    """Безопасное получение предмета из реестра."""
    return ITEMS_REGISTRY.get(item_id)

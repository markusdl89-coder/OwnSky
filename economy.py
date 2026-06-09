from typing import Dict, Tuple, Any
from items import ITEMS_REGISTRY, get_item

# Константы экономики по ТЗ
MIN_PRICE_MODIFIER = 0.30  # Защита от падения цены (30%)
MAX_PRICE_MODIFIER = 5.00  # Защита от взлета цены (500%)
MARKET_SPREAD = 0.05       # Налог рынка (5%), город покупает дешевле
BLACK_MARKET_MULTIPLIER = 2.5 # Множитель контрабанды

def calculate_cargo_metrics(cargo: Dict[str, int]) -> Tuple[int, int]:
    """
    Вычисляет общий вес и объем текущего трюма.
    Игнорирует предметы с нулевым или отрицательным количеством.
    """
    total_weight = 0
    total_volume = 0
    
    for item_id, quantity in cargo.items():
        if quantity <= 0:
            continue
        item = get_item(item_id)
        if item:
            total_weight += item.weight * quantity
            total_volume += item.volume * quantity
            
    return total_weight, total_volume

def validate_cargo_space(
    current_cargo: Dict[str, int], 
    item_id: str, 
    quantity: int, 
    max_cargo: int, 
    max_volume: int
) -> bool:
    """
    Проверяет, поместится ли указанное количество товара в трюм.
    """
    item = get_item(item_id)
    if not item or quantity <= 0:
        return False
        
    current_weight, current_volume = calculate_cargo_metrics(current_cargo)
    
    added_weight = item.weight * quantity
    added_volume = item.volume * quantity
    
    if (current_weight + added_weight) > max_cargo:
        return False
    if (current_volume + added_volume) > max_volume:
        return False
        
    return True

def calculate_dynamic_price(item_id: str, stock: int, base_demand: int = 100) -> Dict[str, Any]:
    """
    Считает динамическую цену на основе дефицита (stock относительно base_demand).
    Реализует спред, черный рынок и хуки тюрьмы Космических Рейнджеров.
    """
    item = get_item(item_id)
    if not item:
        raise ValueError(f"Предмет {item_id} не найден в реестре.")
        
    # Базовая логика дефицита: чем меньше stock, тем выше цена
    # Защита от ZeroDivisionError: если склад пуст, считаем как stock = 1
    effective_stock = max(1, stock)
    scarcity_ratio = base_demand / effective_stock
    
    # Применение ограничений (30% - 500%)
    modifier = max(MIN_PRICE_MODIFIER, min(scarcity_ratio, MAX_PRICE_MODIFIER))
    calculated_base = item.base_price * modifier
    
    # Инициализация структуры ответа
    result = {
        "is_contraband": item.is_contraband,
        "legal_market_allowed": not item.is_contraband,
        "buy_price": 0,   # Цена, по которой игрок ПОКУПАЕТ у города
        "sell_price": 0,  # Цена, по которой игрок ПРОДАЕТ городу
        "trigger_space_rangers_jail": False
    }
    
    if item.is_contraband:
        # Черный рынок
        black_market_price = int(calculated_base * BLACK_MARKET_MULTIPLIER)
        result["buy_price"] = black_market_price
        result["sell_price"] = int(black_market_price * (1.0 - MARKET_SPREAD))
        result["trigger_space_rangers_jail"] = True
    else:
        # Легальный рынок с учетом налога (спреда) города
        result["buy_price"] = int(calculated_base)
        result["sell_price"] = int(calculated_base * (1.0 - MARKET_SPREAD))
        
    # Финальная защита: цены не должны быть нулевыми, если базовая стоимость > 0
    if result["buy_price"] <= 0 and item.base_price > 0:
        result["buy_price"] = 1
    if result["sell_price"] <= 0 and item.base_price > 0:
        result["sell_price"] = 1
        
    return result

def get_clean_hold_view(cargo: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    """
    Формирует отфильтрованный список грузов для вывода на экран смартфона.
    Исключает строки с нулевым или отрицательным количеством.
    """
    clean_hold = {}
    for item_id, quantity in cargo.items():
        if quantity > 0:
            item = get_item(item_id)
            if item:
                clean_hold[item_id] = {
                    "name": item.name,
                    "quantity": quantity,
                    "total_weight": item.weight * quantity,
                    "total_volume": item.volume * quantity
                }
    return clean_hold

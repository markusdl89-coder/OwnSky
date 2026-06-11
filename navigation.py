import pg8000

from items import get_item
from economy import calculate_dynamic_price

def add_flight_point(db_cursor, user_id: int, tx: int, ty: int, action: str = "none", strategy: str = "retreat") -> None:
    """Добавляет одну точку в конец очереди полетного плана игрока."""
    query_order = """
        SELECT COALESCE(MAX(queue_order), 0) + 1 
        FROM flight_plans 
        WHERE user_id = %s;
    """
    db_cursor.execute(query_order, (user_id,))
    res = db_cursor.fetchone()
    next_order = res[0] if res else 1

    insert_query = """
        INSERT INTO flight_plans (user_id, queue_order, target_x, target_y, action, emergency_strategy)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    db_cursor.execute(insert_query, (user_id, next_order, tx, ty, action, strategy))

def clear_flight_plan(db_cursor, user_id: int) -> None:
    """Полностью сбрасывает текущий полетный план игрока."""
    db_cursor.execute(
        "DELETE FROM flight_plans WHERE user_id = %s;", 
        (user_id,)
    )

def process_flight_plan_action(db_cursor, user_id: int, action_str: str) -> str:
    """Парсит и выполняет реальный экономический приказ из плана полета."""
    if not action_str or action_str == "none":
        return "Приказов для порта нет. Экипаж отдыхает."
        
    parts = action_str.split(":")
    cmd = parts[0]
    
    if cmd in ["buy", "sell"] and len(parts) == 3:
        item_id = parts[1]
        qty = int(parts[2])
        item_obj = get_item(item_id)
        
        if not item_obj:
            return f"Ошибка штурмана: предмет '{item_id}' не найден в реестре игры."
            
        # Запрашиваем динамическую цену из economy.py (stock ставим 50 по умолчанию)
        prices = calculate_dynamic_price(item_id, stock=50)
        
        # ЛОГИКА АВТО-ЗАКУПКИ
        if cmd == "buy":
            total_cost = prices["buy_price"] * qty
            db_cursor.execute("SELECT gold FROM players WHERE user_id = %s;", (user_id,))
            res = db_cursor.fetchone()
            gold = res[0] if res else 0
            
            if gold < total_cost:
                return f"Авто-закупка [{item_obj.name}] сорвана: нужно {total_cost} золота, у вас {gold}."
                
            db_cursor.execute("UPDATE players SET gold = gold - %s WHERE user_id = %s;", (total_cost, user_id))
            db_cursor.execute("""
                INSERT INTO inventories (user_id, item_id, quantity) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, item_id) 
                DO UPDATE SET quantity = inventories.quantity + %s;
            """, (user_id, item_id, qty, qty))
            return f"Экипаж закупил в порту {qty} ед. товара '{item_obj.name}' за {total_cost} X-золота."
            
        # ЛОГИКА АВТО-ПРОДАЖИ
        if cmd == "sell":
            db_cursor.execute("SELECT quantity FROM inventories WHERE user_id = %s AND item_id = %s;", (user_id, item_id))
            res = db_cursor.fetchone()
            player_has_qty = res[0] if res else 0
            
            if player_has_qty < qty:
                return f"Авто-продажа [{item_obj.name}] сорвана: в трюме только {player_has_qty} из {qty} необходимых."
                
            total_income = prices["sell_price"] * qty
            db_cursor.execute("UPDATE inventories SET quantity = quantity - %s WHERE user_id = %s AND item_id = %s;", (qty, user_id, item_id))
            db_cursor.execute("UPDATE players SET gold = gold + %s WHERE user_id = %s;", (total_income, user_id))
            return f"Экипаж успешно продал {qty} ед. товара '{item_obj.name}' за {total_income} X-золота."
            
    return "Неизвестная команда автоматизации."

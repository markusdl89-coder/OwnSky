import psycopg2
from psycopg2 import extensions
def add_flight_point(db_cursor, user_id: int, tx: int, ty: int, strategy: str = "retreat") -> None:
    """Добавляет одну точку в конец очереди полетного плана игрока."""
    query_order = """
        SELECT COALESCE(MAX(queue_order), 0) + 1 
        FROM flight_plans 
        WHERE user_id = %s;
    """
    db_cursor.execute(query_order, (user_id,))
    next_order = db_cursor.fetchone()[0]

    insert_query = """
        INSERT INTO flight_plans (user_id, queue_order, target_x, target_y, emergency_strategy)
        VALUES (%s, %s, %s, %s, %s);
    """
    db_cursor.execute(insert_query, (user_id, next_order, tx, ty, strategy))
def clear_flight_plan(db_cursor, user_id: int) -> None:
    """Полностью сбрасывает текущий полетный план игрока."""
    db_cursor.execute(
        "DELETE FROM flight_plans WHERE user_id = %s;", 
        (user_id,)
    )

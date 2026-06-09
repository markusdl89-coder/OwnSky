import os
import pg8000
from typing import Dict, Any, List, Tuple

# Подключение к Neon PostgreSQL через переменную окружения Render
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/ownsky")

def get_connection():
    """Создает подключение к базе данных через pg8000."""
    return pg8000.connect(dsn=DATABASE_URL)

def init_db():
    """Инициализирует таблицы и наполняет мир стартовыми городами."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Таблица игроков (добавлены max_cargo и max_volume)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            credits INT DEFAULT 5000,
            ship_type TEXT DEFAULT 'Старатель',
            x INT DEFAULT 0,
            y INT DEFAULT 0,
            status TEXT DEFAULT 'В порту',
            target_x INT,
            target_y INT,
            arrival_time REAL,
            fuel INT DEFAULT 100,
            max_fuel INT DEFAULT 100,
            max_cargo INT DEFAULT 500,
            max_volume INT DEFAULT 50
        );
    """)
    
    # 2. Таблица локаций (городов)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            name TEXT PRIMARY KEY,
            x INT,
            y INT,
            description TEXT
        );
    """)
    
    # 3. Твоя универсальная таблица складов (добавлен base_demand для экономики)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventories (
            id SERIAL PRIMARY KEY,
            owner_type TEXT, -- 'player', 'city' или 'camp'
            owner_id BIGINT,  -- user_id для игроков, 0 для городов (связь по имени товара/города)
            owner_name TEXT, -- Имя города или лагеря (для удобства фильтрации)
            item_name TEXT,  -- ID предмета (coal, steel, fuel и т.д.)
            quantity INT DEFAULT 0,
            price INT DEFAULT 0,
            base_demand INT DEFAULT 100, -- Базовый спрос города для расчета дефицита
            UNIQUE(owner_type, owner_id, owner_name, item_name)
        );
    """)
    
    # 4. Журнал Адмирала (Задел под ТЗ для скрытых заметок)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_journals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES players(user_id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        );
    """)
    
    conn.commit()
    
    # Первичное наполнение городов (если таблица пуста)
    cursor.execute("SELECT COUNT(*) FROM locations;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO locations (name, x, y, description) VALUES ('Горн', 0, 0, 'Индустриальное сердце региона.');")
        cursor.execute("INSERT INTO locations (name, x, y, description) VALUES ('Пар-Сити', 400, 500, 'Паровой мегаполис.');")
        cursor.execute("INSERT INTO locations (name, x, y, description) VALUES ('Ветроград', -200, 300, 'Город парящих ветряков.');")
        
        # Заполняем склады городов дефолтными товарами для расчета цен
        from items import ITEMS_REGISTRY
        for city in ['Горн', 'Пар-Сити', 'Ветроград']:
            for item_id in ITEMS_REGISTRY.keys():
                cursor.execute("""
                    INSERT INTO inventories (owner_type, owner_id, owner_name, item_name, quantity, base_demand) 
                    VALUES ('city', 0, %s, %s, 100, 100)
                    ON CONFLICT DO NOTHING;
                """, [city, item_id])
        conn.commit()
        
    cursor.close()
    conn.close()

# --- Функции API для работы с базой данных ---

def get_player_data(user_id: int) -> Dict[str, Any] | None:
    """Получает все данные игрока из базы."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, credits, ship_type, x, y, status, fuel, max_fuel, max_cargo, max_volume FROM players WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "user_id": row[0], "username": row[1], "credits": row[2], "ship_type": row[3],
            "x": row[4], "y": row[5], "status": row[6], "fuel": row[7], "max_fuel": row[8],
            "max_cargo": row[9], "max_volume": row[10]
        }
    return None

def update_inventory(owner_type: str, owner_id: int, owner_name: str, item_name: str, change_quantity: int, set_price: int = None):
    """Универсальное изменение количества предметов на любом складе."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже строка
    cursor.execute("""
        SELECT quantity FROM inventories 
        WHERE owner_type = %s AND owner_id = %s AND owner_name = %s AND item_name = %s
    """, (owner_type, owner_id, owner_name, item_name))
    row = cursor.fetchone()
    
    if row is None:
        # Если строки нет — создаем новую
        qty = max(0, change_quantity)
        price = set_price if set_price is not None else 0
        cursor.execute("""
            INSERT INTO inventories (owner_type, owner_id, owner_name, item_name, quantity, price) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (owner_type, owner_id, owner_name, item_name, qty, price))
    else:
        # Если есть — обновляем
        new_qty = max(0, row[0] + change_quantity)
        if set_price is not None:
            cursor.execute("""
                UPDATE inventories SET quantity = %s, price = %s 
                WHERE owner_type = %s AND owner_id = %s AND owner_name = %s AND item_name = %s
            """, (new_qty, set_price, owner_type, owner_id, owner_name, item_name))
        else:
            cursor.execute("""
                UPDATE inventories SET quantity = %s 
                WHERE owner_type = %s AND owner_id = %s AND owner_name = %s AND item_name = %s
            """, (new_qty, owner_type, owner_id, owner_name, item_name))
            
    conn.commit()
    cursor.close()
    conn.close()

def get_player_cargo_dict(user_id: int) -> Dict[str, int]:
    """Возвращает чистый словарь трюма игрока {item_name: quantity} для калькулятора."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, quantity FROM inventories WHERE owner_type = 'player' AND owner_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_city_storage_data(city_name: str, item_name: str) -> Tuple[int, int]:
    """Возвращает (stock, base_demand) товара в конкретном городе."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT quantity, base_demand FROM inventories 
        WHERE owner_type = 'city' AND owner_name = %s AND item_name = %s
    """, (city_name, item_name))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row[0], row[1]
    return 100, 100 # Дефолт, если не нашли

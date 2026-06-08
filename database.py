import psycopg2
from psycopg2.extras import DictCursor

# Ваш вечный ключ подключения к Neon PostgreSQL
DATABASE_URL = "postgresql://neondb_owner:npg_6mhMOVdk8jLn@ep-fragrant-morning-a2a6oftt.eu-central-1.aws.neon.tech/neondb?sslmode=require"

def get_connection():
    """Создает подключение к базе данных"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Создает универсальные таблицы, которые сами подстроятся под любые ресурсы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Таблица игроков (базовые параметры)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            credits INT DEFAULT 1000,
            ship_type TEXT DEFAULT 'Скаут',
            x INT DEFAULT 0,
            y INT DEFAULT 0,
            status TEXT DEFAULT 'В порту',
            target_x INT,
            target_y INT,
            arrival_time REAL,
            fuel INT DEFAULT 100
        )
    ''')
    
    # 2. Таблица локаций (города на карте и лагеря игроков)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            x INT,
            y INT,
            type TEXT, -- 'city' или 'camp'
            owner_id BIGINT DEFAULT 0 -- 0 для городов, user_id для лагерей
        )
    ''')
    
    # 3. УНИВЕРСАЛЬНАЯ ТАБЛИЦА СКЛАДОВ (Сюда автоматически полезут любые ресурсы!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventories (
            id SERIAL PRIMARY KEY,
            owner_type TEXT,     -- 'player' (трюм), 'location' (город/лагерь)
            owner_id BIGINT,     -- user_id игрока ИЛИ id локации
            item_name TEXT,      -- название ресурса (уголь, сталь, шестеренка...)
            quantity INT DEFAULT 0,
            price INT DEFAULT 0, -- актуально для магазинов в городах
            UNIQUE(owner_type, owner_id, item_name)
        )
    ''')
    
    conn.commit()
    
    # Заполняем стартовые города, если их еще нет
    cursor.execute("SELECT COUNT(*) FROM locations WHERE type = 'city'")
    if cursor.fetchone()[0] == 0:
        starting_cities = [
            ("Нью-Арк", 0, 0, "city", 0),
            ("Железный Пик", 15, -30, "city", 0),
            ("Пароград", -40, 20, "city", 0)
        ]
        cursor.executemany('''
            INSERT INTO locations (name, x, y, type, owner_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', starting_cities)
        conn.commit()
        print("Базовая вселенная успешно создана в облаке!")

    cursor.close()
    conn.close()

def register_player(user_id, username):
    """Регистрация нового игрока"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM players WHERE user_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO players (user_id, username, credits, ship_type, x, y, fuel)
            VALUES (%s, %s, 1000, 'Скаут', 0, 0, 100)
        ''', (user_id, username))
        conn.commit()
    cursor.close()
    conn.close()

def get_player_data(user_id):
    """Получает базовые данные игрока"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM players WHERE user_id = %s", (user_id,))
    player = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(player) if player else None

def get_player_inventory(user_id):
    """АВТОМАТИЧЕСКИ собирает всё, что лежит в трюме игрока"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, quantity FROM inventories WHERE owner_type = 'player' AND owner_id = %s", (user_id,))
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return {item[0]: item[1] for item in items}

def update_inventory(owner_type, owner_id, item_name, change_quantity, set_price=None):
    """
    Универсальная функция: добавляет или отнимает любой ресурс у кого угодно.
    change_quantity может быть как положительным (+5 угля), так и отрицательным (-2 стали).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже такая запись на складе
    cursor.execute('''
        SELECT quantity FROM inventories 
        WHERE owner_type = %s AND owner_id = %s AND item_name = %s
    ''', (owner_type, owner_id, item_name))
    row = cursor.fetchone()
    
    if row is None:
        # Если такого ресурса еще не было на этом складе — создаем строку
        new_qty = max(0, change_quantity)
        price = set_price if set_price is not None else 0
        cursor.execute('''
            INSERT INTO inventories (owner_type, owner_id, item_name, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
        ''', (owner_type, owner_id, item_name, new_qty, price))
    else:
        # Если ресурс уже был — обновляем количество
        new_qty = max(0, row[0] + change_quantity)
        if set_price is not None:
            cursor.execute('''
                UPDATE inventories SET quantity = %s, price = %s 
                WHERE owner_type = %s AND owner_id = %s AND item_name = %s
            ''', (new_qty, set_price, owner_type, owner_id, item_name))
        else:
            cursor.execute('''
                UPDATE inventories SET quantity = %s 
                WHERE owner_type = %s AND owner_id = %s AND item_name = %s
            ''', (new_qty, owner_type, owner_id, item_name))
            
    conn.commit()
    cursor.close()
    conn.close()

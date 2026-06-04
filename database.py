import sqlite3 

def init_db():

    conn = sqlite3.connect('ownsky.db')
    cursor = conn.cursor()
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,   
            credits REAL DEFAULT 1000.0,   
            ship_name TEXT DEFAULT 'Цеппелин-1', 
            cargo_coal REAL DEFAULT 0.0,   
            cargo_ore REAL DEFAULT 0.0,    
            cargo_steel REAL DEFAULT 0.0,  
            fuel REAL DEFAULT 100.0,       
            x REAL DEFAULT 0.0,            
            y REAL DEFAULT 0.0             
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT,                            
            x REAL,                               
            y REAL,                               
            owner_id INTEGER DEFAULT NULL,        
            is_hidden INTEGER DEFAULT 0,          
            stock_coal REAL DEFAULT 0.0,          
            stock_ore REAL DEFAULT 0.0,           
            stock_steel REAL DEFAULT 0.0          
        )
    ''')

    conn.commit()
    
    
    conn.close()

def register_player(user_id):
    """Регистрирует цеппелин нового игрока, если его еще нет в SQLite"""
    conn = sqlite3.connect('ownsky.db')
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже такой пилот в базе
    cursor.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,))
    player = cursor.fetchone()
    
    # Если запись не найдена — создаем её (остальные поля заполнятся дефолтами)
    if not player:
        cursor.execute("INSERT INTO players (user_id) VALUES (?)", (user_id,))
        conn.commit() # Жестко сохраняем изменения в файле
        
    conn.close() # Закрываем соединение

def get_player_status(user_id):
    """Получает все данные игрока для вывода на экран"""
    conn = sqlite3.connect('ownsky.db')
    cursor = conn.cursor()
    
    # Запрашиваем имя корабля, деньги, топливо и ресурсы в трюме
    cursor.execute("SELECT ship_name, credits, fuel, cargo_coal, cargo_ore, cargo_steel FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    conn.close()
    return row # Возвращает данные или None, если игрок не найден

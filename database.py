import sqlite3 # Подключаем встроенную библиотеку для работы с БД SQLite

def init_db():
    # Подключаемся к файлу базы данных (если его нет, он создастся сам)
    conn = sqlite3.connect('ownsky.db')
    cursor = conn.cursor()
    
    # Создаем таблицу игроков и их цеппелинов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,   # Уникальный ID игрока из Telegram
            credits REAL DEFAULT 1000.0,   # Баланс кредитов игрока
            ship_name TEXT DEFAULT 'Цеппелин-1', # Название корабля
            cargo_coal REAL DEFAULT 0.0,   # Сколько угля в трюме
            cargo_ore REAL DEFAULT 0.0,    # Сколько руды в трюме
            cargo_steel REAL DEFAULT 0.0,  # Сколько стали в трюме
            fuel REAL DEFAULT 100.0,       # Текущее топливо в баке
            x REAL DEFAULT 0.0,            # Координата X корабля
            y REAL DEFAULT 0.0             # Координата Y корабля
        )
    ''')
# --- ПОДСКАЗКА: СЛЕДУЮЩИЙ КУСОК ВСТАВЛЯЙ СРАЗУ ПОД ЭТОЙ СТРОКОЙ БЕЗ ЛИШНИХ ПРОБЕЛОВ ---
    # Создаем таблицу локаций (системные города и будущие скрытые базы игроков)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, # Автоматический порядковый номер
            name TEXT,                            # Название (Горн, Пар-Сити, Скрытое убежище)
            x REAL,                               # Координата X на карте
            y REAL,                               # Координата Y на карте
            owner_id INTEGER DEFAULT NULL,        # ID создателя (NULL, если это системный город)
            is_hidden INTEGER DEFAULT 0,          # 1 = скрытая точка интереса, 0 = видна всем
            stock_coal REAL DEFAULT 0.0,          # Запас угля на складе этой локации
            stock_ore REAL DEFAULT 0.0,           # Запас руды на складе этой локации
            stock_steel REAL DEFAULT 0.0          # Запас стали на складе этой локации
        )
    ''')
# --- ПОДСКАЗКА: ПОСЛЕДНИЙ КУСОК ВСТАВЛЯЙ СРАЗУ ПОД ЭТОЙ СТРОКОЙ ---
    # Сохраняем все созданные таблицы в файл базы данных
    conn.commit()
    
    # Закрываем соединение с базой данных, чтобы освободить память
    conn.close()
# --- ПОДСКАЗКА: КОНЕЦ ФАЙЛА DATABASE.PY. СЛЕДУЮЩИЕ СТРОКИ НЕ НУЖНЫ ---

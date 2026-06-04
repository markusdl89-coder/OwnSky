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


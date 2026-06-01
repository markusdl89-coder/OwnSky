FEATURE_TOGGLES = {
    "flight_system": True,
    "crew_simulation": False,
    "doctrinal_logic": True
}

# Координаты и экономика городов (склады, цены)
CITIES = {
    "gorn": {
        "name": "Шахтерский аванпост 'Горн'",
        "x": 100.0,
        "y": 100.0,
        "production_speed": 1.0,
        "stockpile": {"coal": 100, "iron_ore": 50, "steel": 0, "tools": 0},
        "prices": {"coal": 5, "iron_ore": 8, "steel": 0, "tools": 40}  # 0 означает, что товар не продается/не покупается здесь
    },
    "steam_city": {
        "name": "Индустриальный мегаполис 'Пар-Сити'",
        "x": 400.0,
        "y": 500.0,
        "production_speed": 1.0,
        "stockpile": {"coal": 10, "iron_ore": 5, "steel": 0, "tools": 0},
        "prices": {"coal": 25, "iron_ore": 35, "steel": 80, "tools": 0}
    }
}

# Вес каждого ресурса в килограммах за 1 единицу
RESOURCE_WEIGHTS = {
    "coal": 10,       # 1 ящик угля = 10 кг
    "iron_ore": 20,   # 1 ящик руды = 20 кг
    "steel": 50,      # 1 слиток стали = 50 кг
    "tools": 15       # 1 ящик инструментов = 15 кг
}

# Базовая точка появления для новых игроков
START_PORT = CITIES["gorn"]

USER_SHIPS = {}

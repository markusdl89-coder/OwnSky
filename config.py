import os

# Робот сам возьмет токен из настроек сервера
TOKEN = os.environ.get("BOT_TOKEN")

# Переключатели модулей игры
FEATURE_TOGGLES = {
    "core_interface": True,     
    "crew_management": True,    
    "tactical_doctrines": False, 
    "expeditions": False        
}

USER_SHIPS = {}

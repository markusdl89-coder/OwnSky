# bot_instance.py
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Автоматически берем секретный токен из настроек сервера Render
# Если тестируете на ПК, можно временно вместо os.getenv вписать "ВАШ_ТОКЕН"
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА_СЮДА")

# Инициализируем асинхронного бота
bot = Bot(token=BOT_TOKEN)

# Включаем виртуальную память для пошаговых анкет игроков (FSM)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

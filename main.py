# main.py
import os
import importlib
from aiogram import types
from aiogram.utils import executor

# Импортируем вашего бота и реестр кнопок
from bot_instance import dp, bot  
from interface import GAME_BUTTONS, get_game_keyboard
import server  # Запуск вашего веб-сервера для деплоя на Render

def auto_load_modules():
    """Автоматически находит и включает все игровые файлы в репозитории"""
    # Список системных файлов, которые НЕ являются игровыми кнопками
    system_files = {
        'main.py', 'main_old.py', 'bot_instance.py', 
        'config.py', 'database.py', 'server.py', 'interface.py'
    }
    
    # Сканируем корень репозитория
    for filename in os.listdir('.'):
        # Ищем только файлы кода Python, игнорируя системные
        if filename.endswith('.py') and filename not in system_files:
            module_name = filename[:-3] # Отрезаем ".py" от имени файла
            try:
                # Загружаем модуль в память — в этот момент он сам регистрирует свою кнопку
                importlib.import_module(module_name)
                print(f" Модуль успешно подключен: {filename}")
            except Exception as e:
                print(f"❌ Ошибка при авто-подключении {filename}: {e}")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def main_dispatcher(message: types.Message):
    """Главный распределитель: ловит сообщения игрока со смартфона"""
    text = message.text

    # Если текст нажатой кнопки совпадает с зарегистрированным игровым модулем
    if text in GAME_BUTTONS:
        # Передаем управление в этот модуль!
        await GAME_BUTTONS[text](message)
    else:
        # Если команда неизвестна (или старт) — выдаем автоматическое меню кнопок
        await message.answer(
            "Приветствую на мостике корабля, Капитан! Все системы готовы к работе.", 
            reply_markup=get_game_keyboard()
        )

if __name__ == "__main__":
    print("🤖 Запуск Умного Диспетчера...")
    auto_load_modules() # 1. Сами нашли и подключили все файлы игры
    
    print("🌐 Запуск веб-сервера под Render...")
    server.start()       # 2. Держим порт для бесперебойной работы хостинга
    
    print("🚀 Бот успешно запущен в Telegram!")
    executor.start_polling(dp, skip_updates=True) # 3. Включаем прием сообщений

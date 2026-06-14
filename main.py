# main.py
import os
import asyncio
import importlib
from aiogram import types

# Импортируем движок бота и реестр кнопок
from bot_instance import dp, bot  
from interface import GAME_BUTTONS, get_game_keyboard
import server  # Наш веб-сервер для Render

def auto_load_modules():
    """Автоматически находит и включает все игровые файлы в репозитории"""
    system_files = {
        'main.py', 'main_old.py', 'bot_instance.py', 
        'config.py', 'database.py', 'server.py', 'interface.py'
    }
    
    for filename in os.listdir('.'):
        if filename.endswith('.py') and filename not in system_files:
            module_name = filename[:-3]
            try:
                # Втягиваем модуль в память — кнопка сама зарегистрируется в interface
                importlib.import_module(module_name)
                print(f"[System] Модуль успешно подключен: {filename}")
            except Exception as e:
                print(f"[Error] Ошибка при авто-подключении {filename}: {e}")

async def main():
    print("🤖 Запуск асинхронного Умного Диспетчера (Aiogram 3)...")
    
    # 1. Автоматически подключаем все слои игры
    auto_load_modules() 
    
    # 2. Включаем ваш родной сервер для Render (как раз ту самую функцию!)
    print("🌐 Активация хостинга на Render...")
    server.start_hosting() 
    
    # 3. Включаем постоянное слушание Телеграма
    print("🚀 Бот успешно запущен и слушает игроков!")
    await dp.start_polling(bot, skip_updates=True)

# Главный распределитель сообщений
@dp.message(lambda message: message.text)
async def main_dispatcher(message: types.Message):
    text = message.text

    # Если нажатая кнопка совпадает со списком в interface.py
    if text in GAME_BUTTONS:
        # Передаем управление этому слою игры
        await GAME_BUTTONS[text](message)
    else:
        # Если команда /start или неизвестный текст — выдаем автоматическое меню
        await message.answer(
            "Приветствую на мостике корабля, Капитан! Системы готовы к работе.", 
            reply_markup=get_game_keyboard()
        )

if __name__ == "__main__":
    # Запуск асинхронного ядра
    asyncio.run(main())

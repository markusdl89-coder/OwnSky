import asyncio
import logging
import os
import importlib
import pkgutil
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования для Render (вывод в stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_routers(dispatcher: Dispatcher) -> None:
    """
    Автоматически сканирует папку handlers/, динамически импортирует 
    все модули и регистрирует их роутеры в Диспетчере.
    """
    # Определяем абсолютный путь к папке handlers
    handlers_path = os.path.join(os.path.dirname(__file__), "handlers")
    
    if not os.path.exists(handlers_path):
        logger.error(f"Критическая ошибка: Папка '{handlers_path}' не найдена!")
        return

    logger.info("Запуск автоматического сканирования модулей в handlers/...")

    # Рекурсивно обходим пакет handlers
    for _, module_name, is_pkg in pkgutil.walk_packages([handlers_path], prefix="handlers."):
        if is_pkg:
            continue  # Пропускаем папки-пакеты, ищем только файлы модулей
            
        try:
            # Динамически импортируем модуль
            module = importlib.import_module(module_name)
            
            # Проверяем, есть ли внутри модуля переменная router
            if hasattr(module, "router"):
                dispatcher.include_router(module.router)
                logger.info(f" Successfully registered router from: {module_name}")
            else:
                logger.warning(f" Модуль {module_name} загружен, но в нем нет переменной 'router'")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при импорте модуля {module_name}: {e}", exc_info=True)


async def main() -> None:
    """
    Главная точка входа в игру OwnSky.
    Инициализирует окружение, бота и запускает слепой диспетчер.
    """
    # 1. Чтение и валидация переменных окружения
    bot_token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")

    if not bot_token:
        logger.critical("Критическая ошибка: Переменная среды BOT_TOKEN не задана!")
        return
    if not database_url:
        logger.critical("Критическая ошибка: Переменная среды DATABASE_URL не задана!")
        return

    logger.info("OwnSky Core: Переменные окружения успешно валидированы.")

    # 2. Инициализация Bot и Dispatcher с поддержкой FSM в памяти
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 3. Автоматическое подключение всех игровых модулей
    setup_routers(dp)

    # 4. Запуск Long Polling
    logger.info("OwnSky запущен и готов к обработке команд аэронавтов! 🪐")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Сессия бота успешно закрыта. Работа OwnSky Core завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную.")

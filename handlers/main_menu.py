import random
from aiogram import Router, F, types
from aiogram.filters import Command

# Импортируем нашу фабрику экранов из сервиса интерфейсов
from services.interface import (
    get_cabinet_screen,
    get_fleet_list_screen,
    get_ship_status_screen,
    get_ship_control_keyboard
)

router = Router(name="main_menu")

# --- ВРЕМЕННЫЙ СИМУЛЯТОР ДАННЫХ ИЗ NEON DB ---
# Когда мы подключим database.py, эти функции будут заменены на реальные запросы
async def mock_get_player_profile(user_id: int):
    """Имитирует получение профиля Адмирала из базы данных"""
    return {
        "title": "Адмирал",
        "name": "Маркус",
        "surname": "Делакруа"
    }

async def mock_get_ship_data(user_id: int):
    """Имитирует получение данных цеппелина и двухмерного трюма из базы данных"""
    return {
        "ship_name": "Коршун-М",
        "condition": 100,
        "fuel_pct": 45,
        "weight_current": 1.2,
        "weight_max": 5.0,
        "volume_current": 15.0,
        "volume_max": 60.0,
        "cargo_list": [
            "Ящики с авиационными запчастями — 1.0 т | 10 м³",
            "Медикаменты и спирт (спецгруз) — 0.2 т | 5 м³"
        ]
    }


# ==========================================
# 1. ОБРАБОТЧИКИ ВЕРХНЕГО УРОВНЯ (КАБИНЕТ)
# ==========================================

@router.message(Command("menu"))
@router.message(F.text == "🔙 Назад в Кабинет")
async def process_cabinet_screen(message: types.Message):
    """Открывает Главное меню — Рабочий кабинет Адмирала"""
    # Запрашиваем данные игрока (пока из симулятора)
    player = await mock_get_player_profile(message.from_user.id)
    
    # Генерируем текст и клавиатуру через сервис
    text, keyboard = await get_cabinet_screen(
        title=player["title"],
        name=player["name"],
        surname=player["surname"]
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# ==========================================
# 2. ОБРАБОТЧИКИ МОДУЛЯ ФЛОТА
# ==========================================

@router.message(F.text == "🛸 Мой Флот")
@router.message(F.text == "🔙 Назад к списку Флота")
async def process_fleet_list(message: types.Message):
    """Открывает реестр подчиненных судов"""
    text, keyboard = await get_fleet_list_screen()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(F.text == "📋 Борт: «Коршун-М»")
async def process_ship_bridge(message: types.Message):
    """Открывает командный мостик конкретного корабля со сводкой рапортов"""
    ship = await mock_get_ship_data(message.from_user.id)
    
    # Сначала получаем текст детального статуса и трюма
    text = await get_ship_status_screen(
        ship_name=ship["ship_name"],
        condition=ship["condition"],
        fuel_pct=ship["fuel_pct"],
        weight_current=ship["weight_current"],
        weight_max=ship["weight_max"],
        volume_current=ship["volume_current"],
        volume_max=ship["volume_max"],
        cargo_list=ship["cargo_list"]
    )
    # Берем клавиатуру управления кораблем с заглушками (Экипаж, Рейс)
    keyboard = get_ship_control_keyboard()
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# ==========================================
# 3. ЕДИНЫЙ ОБРАБОТЧИК КНОПОК-ЗАГЛУШЕК (РАДИОПОМЕХИ)
# ==========================================

@router.message(F.text.in_({
    "👥 Офицерский Корпус", 
    "🗺 Карта и Проекты", 
    "📡 Сеть Контактов", 
    "🛫 Назначить Рейс", 
    "👥 Экипаж Борта"
}))
async def process_interface_stubs(message: types.Message):
    """
    Перехватывает нажатия всех незавершенных кнопок.
    Выдает атмосферные дизельпанк-ответы с имитацией радиопомех.
    """
    radio_noises = [
        "🛸 *Пш-ш-ш... Кххх...* Эфир перегружен статическим электричеством. Связь с этим сектором временно недоступна.",
        "📡 *Внимание!* Терминал заблокирован. Ожидайте расшифровки пакетных данных от шифровального отдела.",
        "⚙️ *Клик... Скрип шестерен...* Запрошенный отсек диспетчерской обесточен. Подайте питание на вспомогательные генераторы.",
        "📻 *Хррр-пшшш...* Капитан Г. Штольц на связи. Адмирал, этот канал защищен военным шифром, коды будут доступны в следующем обновлении сети."
    ]
    # Выбираем случайную помеху для реализма
    await message.answer(random.choice(radio_noises), parse_mode="Markdown")

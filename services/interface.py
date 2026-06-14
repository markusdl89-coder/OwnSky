from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Генерирует клавиатуру верхнего уровня для Рабочего кабинета Адмирала.
    Сетка кнопок: 2х2 для идеального отображения на экранах смартфонов.
    """
    builder = ReplyKeyboardBuilder()
    
    # Добавляем кнопки в буфер строителя
    builder.add(KeyboardButton(text="🛸 Мой Флот"))
    builder.add(KeyboardButton(text="👥 Офицерский Корпус"))
    builder.add(KeyboardButton(text="🗺 Карта и Проекты"))
    builder.add(KeyboardButton(text="📡 Сеть Контактов"))
    
    # Настраиваем сетку: по 2 кнопки в ряд
    builder.adjust(2)
    
    # Возвращаем готовую клавиатуру с авто-подгонкой размера под экран
    return builder.as_markup(resize_keyboard=True)


def get_ship_control_keyboard() -> ReplyKeyboardMarkup:
    """
    Генерирует клавиатуру управления конкретным цеппелином (Командный мостик).
    Сетка кнопок: 1 вверху (основная боевая) и 2 ниже + кнопка возврата.
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📊 Статус Корабля"))
    builder.add(KeyboardButton(text="🛫 Назначить Рейс"))
    builder.add(KeyboardButton(text="👥 Экипаж Борта"))
    builder.add(KeyboardButton(text="🔙 Назад в Кабинет"))
    
    # Настройка сетки: Статус на всю ширину, Рейс и Экипаж в один ряд, Назад на всю ширину
    builder.adjust(1, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)


async def get_cabinet_screen(title: str, name: str, surname: str) -> tuple[str, ReplyKeyboardMarkup]:
    """
    Формирует текстовый экран и клавиатуру для Рабочего кабинета Адмирала.
    Принимает динамические данные персонажа из базы данных.
    """
    text = (
        f"**[ СТРАТЕГИЧЕСКИЙ ЦЕНТР УПРАВЛЕНИЯ ]**\n"
        f"--------------------------------------------------\n"
        f"🦾 Добро пожаловать в Диспетчерскую Рубку, **{title} {name} {surname}**.\n\n"
        f"На массивном стальном столе горит лампа, освещая разложенные карты воздушных секторов. "
        f"На стене тихо гудит коммутатор связи, ожидая донесений с Ваших бортов.\n\n"
        f"За бронированным стеклом иллюминатора клубится радиоактивный туман постъядерного мира. "
        f"Система готова к работе.\n"
        f"--------------------------------------------------"
    )
    keyboard = get_main_menu_keyboard()
    return text, keyboard


async def get_fleet_list_screen() -> tuple[str, ReplyKeyboardMarkup]:
    """
    Формирует экран реестра подчиненных судов.
    На данном этапе хардкодит стартовый цеппелин, в будущем будет принимать список из БД.
    """
    text = (
        f"**🛸 [ РЕЕСТР ПОДЧИНЕННЫХ СУДОВ ]**\n"
        f"--------------------------------------------------\n"
        f"Адмирал, на Ваш стол легли fresh-рапорты от командиров кораблей. "
        f"В Вашем секторе базирования находится:\n\n"
        f"1. **Грузовой цеппелин «Коршун-М»**\n"
        f"   • Командир: Капитан Г. Штольц.\n"
        f"   • Статус: Ожидает приказов в доке.\n"
        f"--------------------------------------------------"
    )
    
    # Строим быструю клавиатуру для выбора корабля
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📋 Борт: «Коршун-М»"))
    builder.add(KeyboardButton(text="🔙 Назад в Кабинет"))
    builder.adjust(1)
    
    return text, builder.as_markup(resize_keyboard=True)


async def get_ship_status_screen(
    ship_name: str, 
    condition: int, 
    fuel_pct: int, 
    weight_current: float, 
    weight_max: float, 
    volume_current: float, 
    volume_max: float, 
    cargo_list: list[str]
) -> str:
    """
    Формирует детальный рапорт технического состояния и двухмерного трюма.
    Возвращает только текст, так как клавиатура управления кораблем остается неизменной.
    """
    # Собираем красивый текстовый список карго
    if cargo_list:
        cargo_text = "\n".join(f"   {idx+1}. {item}" for idx, item in enumerate(cargo_list))
    else:
        cargo_text = "   [ Грузовые отсеки пусты ]"

    text = (
        f"**📊 [ БОРТОВОЙ ЖУРНАЛ: «{ship_name}» ]**\n"
        f"--------------------------------------------------\n"
        f"**Сводка от старшего механика:**\n"
        f"🛠 Состояние корпуса: {condition}% (Бронепластины в норме).\n"
        f"🔋 Топливные баки: {fuel_pct}% (Запаса хватит на перелет).\n\n"
        f"**Сводка от логиста снабжения (Трюм):**\n"
        f"• ⚖️ Масса груза: {weight_current} т / {weight_max} т (Доступно: {round(weight_max - weight_current, 1)} т)\n"
        f"• 📦 Объем груза: {volume_current} м³ / {volume_max} м³ (Доступно: {round(volume_max - volume_current, 1)} м³)\n\n"
        f"*Размещенный груз:*\n{cargo_text}\n"
        f"--------------------------------------------------"
    )
    return text

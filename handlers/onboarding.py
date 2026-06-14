import re
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Инициализируем роутер модуля. 
# Главный dispatcher (main.py) автоматически найдет его при сканировании.
router = Router()

# Описываем состояния машины (FSM) для процесса создания персонажа
class Onboarding(StatesGroup):
    waiting_for_name = State()
    waiting_for_dynasty_choice = State()
    waiting_for_new_dynasty = State()
    waiting_for_dynasty_code = State()


# =====================================================================
# ШАГ 1: ПЕРВОЕ КАСАНИЕ (/start)
# =====================================================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Тут будет выполняться проверка в Neon DB через ваш пул соединений.
    # ПРИМЕР: user_exists = await db.check_player_exists(message.from_user.id)
    user_exists = False # Временный симулятор: считаем, что игрока нет в базе

    if user_exists:
        # Если игрок есть, onboarding пропускается, вызываем Главное Меню
        await message.answer("Приветствуем на мостике, Адмирал! (Вызов Главного Меню)")
        return

    # Если игрока нет — запускаем процесс создания персонажа
    # Примечание: Для видео-эдита используйте message.answer_video(video="FILE_ID_ИЛИ_URL", caption=...)
    text = (
        "«...Земля мертва с 1980 года. Но небо выжило. Благодаря безопасному гелию "
        "человечество построило новую цивилизацию на цеппелинах. Здесь, среди бесконечных "
        "радиоактивных облаков, одиночка обречен на гибель. Выживают лишь те, у кого есть "
        "верный экипаж и мощный флот.\n\n"
        "Добро пожаловать в OwnSky. Настало время основать твою авиационную флотилию. "
        "Твой первый легкий дирижабль „Старатель“ уже прогревает двигатели в порту „Горн“...»"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Основать флотилию", callback_data="start_onboarding")]
    ])
    
    await message.answer(text=text, reply_markup=kb)


# =====================================================================
# ШАГ 2: ВВОД ЛИЧНОГО ИМЕНИ
# =====================================================================
@router.callback_query(F.data == "start_onboarding")
async def start_onboarding_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    text = "Внимание! Запрос бортового регистра порта „Горн“.\nВведите официальное Имя Адмирала флота (только буквы):"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Взять из Telegram", callback_data="take_tg_name")]
    ])
    
    await callback.message.answer(text=text, reply_markup=kb)
    await state.set_state(Onboarding.waiting_for_name)


@router.callback_query(F.data == "take_tg_name", Onboarding.waiting_for_name)
async def take_tg_name_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Берем имя из профиля Telegram (first_name)
    tg_name = callback.from_user.first_name
    # Очищаем от лишних символов, оставляя только буквы
    clean_name = re.sub(r'[^a-zA-Zа-яА-Я]', '', tg_name)[:15]
    
    if len(clean_name) < 3:
        clean_name = f"Пилот{callback.from_user.id % 1000}"

    await state.update_data(chosen_name=clean_name)
    await proceed_to_dynasty_choice(callback.message, clean_name, state)


@router.message(Onboarding.waiting_for_name)
async def process_manual_name(message: Message, state: FSMContext):
    # Валидация ручного ввода: только русские и английские буквы
    if not re.match(r"^[a-zA-Zа-яА-Я]+$", message.text):
        await message.answer("Ошибка! Разрешены только буквы без цифр и пробелов. Попробуйте снова:")
        return
        
    if len(message.text) < 3 or len(message.text) > 15:
        await message.answer("Длина имени должна быть от 3 до 15 символов. Попробуйте снова:")
        return

    await state.update_data(chosen_name=message.text)
    await proceed_to_dynasty_choice(message, message.text, state)


# Вспомогательная функция перехода к выбору Династии
async def proceed_to_dynasty_choice(message: Message, name: str, state: FSMContext):
    text = (
        f"Капитан {name} внесен в реестр.\n\n"
        f"Теперь определите происхождение вашей Династии. Вы можете заложить "
        f"собственный великий дом или примкнуть к существующему семейству "
        f"по секретному коду усыновления."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Основать новую Династию", callback_data="dynasty_new")],
        [InlineKeyboardButton(text="🤝 Присоединиться к существующей", callback_data="dynasty_join")]
    ])
    
    await message.answer(text=text, reply_markup=kb)
    await state.set_state(Onboarding.waiting_for_dynasty_choice)


# =====================================================================
# ШАГ 3: ВЫБОР СУДЬБЫ РОДА
# =====================================================================
@router.callback_query(F.data == "dynasty_new", Onboarding.waiting_for_dynasty_choice)
async def dynasty_new_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите Фамилию вашей будущей Династии (будет добавлена к вашему позывному):")
    await state.set_state(Onboarding.waiting_for_new_dynasty)


@router.callback_query(F.data == "dynasty_join", Onboarding.waiting_for_dynasty_choice)
async def dynasty_join_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите уникальный Код Усыновления, полученный от членов вашей семьи:")
    await state.set_state(Onboarding.waiting_for_dynasty_code)


# =====================================================================
# ШАГ 4А: ОФОРМЛЕНИЕ НОВОЙ ДИНАСТИИ (Автоматическая работа с Neon DB)
# =====================================================================
@router.message(Onboarding.waiting_for_new_dynasty)
async def process_new_dynasty(message: Message, state: FSMContext):
    if not re.match(r"^[a-zA-Zа-яА-Я]+$", message.text):
        await message.answer("Фамилия должна состоять только из букв. Попробуйте снова:")
        return

    # Тут будет запрос к Neon DB для проверки уникальности фамилии.
    # ПРИМЕР: is_taken = await db.check_dynasty_name_taken(message.text)
    is_taken = False # Временный симулятор: фамилия всегда свободна

    if is_taken:
        await message.answer("Эта фамилия уже внесена в бортовые журналы другого Адмирала. Выберите другую:")
        return

    user_data = await state.get_data()
    full_name = f"{user_data['chosen_name']} {message.text}"

    # Тут выполняется автоматический INSERT всех стартовых параметров в Neon DB
    # ПРИМЕР:
    # await db.create_player(
    #     tg_id=message.from_user.id, 
    #     name=full_name, 
    #     role="Основатель", 
    #     credits=5000, 
    #     location_id=1
    # )

    await state.clear() # Полностью очищаем FSM-состояние
    await message.answer(f"Династия {message.text} основана!\nДобро пожаловать на мостик, Адмирал {full_name}!\n\n[Вызов Главного Меню]")


# =====================================================================
# ШАГ 4Б: ПРИСОЕДИНЕНИЕ (ВРЕМЕННАЯ БЕЗОПАСНАЯ ЗАГЛУШКА)
# =====================================================================
@router.message(Onboarding.waiting_for_dynasty_code)
async def process_dynasty_code_stub(message: Message, state: FSMContext):
    # Временный симулятор-заглушка, чтобы бот не ломался при тестах.
    # Принимает абсолютно любой введенный код, имитируя успех.
    user_data = await state.get_data()
    stub_surname = "Тестовый"
    full_name = f"{user_data['chosen_name']} {stub_surname}"

    # В будущем здесь будет вызов функции из модуля dynasty.py:
    # parent = await dynasty.verify_code(message.text)

    await state.clear() # Полностью очищаем FSM-состояние
    await message.answer(
        f"[ТЕСТОВАЯ ЗАГЛУШКА]: Код '{message.text}' успешно проверен!\n"
        f"Вы приняты в ветку Династии {stub_surname}.\n"
        f"Добро пожаловать на мостик, Адмирал {full_name}!\n\n[Вызов Главного Меню]"
    )

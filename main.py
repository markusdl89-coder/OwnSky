# === СЛОЙ 1: СИСТЕМНЫЕ ИМПОРТЫ И ЗАГЛУШКА ДЛЯ RENDER ===
import http.server
import threading
import time
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорты наших новых модулей экономики и базы данных
import database as db
from core import GameCore
from items import ITEMS_REGISTRY
from economy import calculate_dynamic_price, validate_cargo_space

# Создаем обработчик, который отвечает "ОК" на проверки Render
class RenderHealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and flying!")

    def log_message(self, format, *args):
        return

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, RenderHealthCheckHandler)
    print(f" Навигационный маяк (заглушка) успешно запущен на порту {port}")
    httpd.serve_forever()

# Инициализация бота
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация базы данных
db.init_db()

# Запуск сервера-заглушки
threading.Thread(target=run_fake_server, daemon=True).start()

# === СЛОЙ 2: БАЗОВЫЙ СТАТУС И НАВИГАЦИЯ (ПОЛЁТЫ) ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Регистрация нового капитана в Postgres и выдача стартового пустого трюма."""
    user_id = message.from_user.id
    username = message.from_user.username or "Капитан"
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO players (user_id, username) 
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
    """, [user_id, username])
    conn.commit()
    cursor.close()
    conn.close()
    
    # Инициализируем пустые ячейки для товаров из реестра
    for item_id in ITEMS_REGISTRY.keys():
        db.update_inventory('player', user_id, '', item_id, 0)
        
    welcome_text = (
        "🌅 **OwnSky: Эпоха Дирижаблей приветствует тебя!**\n\n"
        "Ты — капитан грузового судна в мире парящих городов.\n"
        "Используй команду /ship, чтобы проверить трюм и системы.\n"
        "Используй команду /fly, чтобы открыть навигационную карту полетов."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['ship'])
def show_ship(message):
    """Выводит актуальный scannable-отчет о состоянии судна (масса, кубатура, баки)."""
    user_id = message.from_user.id
    report = GameCore.get_ship_report(user_id)
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

@bot.message_handler(commands=['fly'])
def choose_destination(message):
    """Выводит список доступных городов для перелета в реальном времени."""
    user_id = message.from_user.id
    p = db.get_player_data(user_id)
    
    if not p:
        bot.reply_to(message, "❌ Используйте /start для регистрации.")
        return
        
    if p['status'] == 'В полете':
        bot.reply_to(message, "❌ Вы уже находитесь в воздухе!")
        return

    text = "🗺 **НАВИГАЦИОННЫЙ МОСТИК**\nВыберите город назначения для прокладки курса:"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    # Выводим кнопки всех трех доступных городов из ТЗ
    keyboard.add(
        InlineKeyboardButton("🏙 Курс на Горн", callback_data="fly_to_Горн"),
        InlineKeyboardButton("🏙 Курс на Пар-Сити", callback_data="fly_to_Пар-Сити"),
        InlineKeyboardButton("🏙 Курс на Ветроград", callback_data="fly_to_Ветроград")
    )
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("fly_to_"))
def process_flight_start(call):
    """Обработчик нажатия на кнопку города. Запуск полета реального времени."""
    user_id = call.from_user.id
    target_city = call.data.replace("fly_to_", "")
    
    # Вызываем метод запуска полета из core.py
    success, message_text = GameCore.start_flight(user_id, target_city)
    
    if success:
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        # Если не хватило топлива или город тот же — показываем алерт поверх экрана
        bot.answer_callback_query(call.id, message_text, show_alert=True)


# === СЛОЙ 3: ФОНОВЫЙ ИГРОВОЙ ЦИКЛ (СЕРДЦЕ СЕРВЕРА) ===

def game_loop():
    """
    Фоновый движок времени. Раз в 3 секунды обрабатывает состояние экипажа,
    полетные тики и пассивное производство фабрик всех игроков в Postgres.
    """
    while True:
        # Твой оригинальный интервал времени — 3 секунды
        time.sleep(3)
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            # Запрашиваем всех зарегистрированных капитанов
            cursor.execute("SELECT user_id, username, status, fuel, x, y FROM players")
            all_players = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for row in all_players:
                user_id = row[0]
                username = row[1]
                status = row[2]
                fuel = row[3]
                px = row[4]
                py = row[5]
                
                # --- 1. ЛОГИКА ЭКИПАЖА (СОХРАНЯЕМ ТВОЙ МЕНЕДЖЕР) ---
                is_in_flight = (status == "В полете")
                # Твой crew_manager получает точный статус и крутит тики в реальном времени
                crew_manager.update_tick(is_in_flight)
                
                # --- 2. ЛОГИКА ПОЛЕТОВ И КАТАСТРОФ ---
                if is_in_flight:
                    # Проверяем таймер прибытия через ядро
                    flight_status = GameCore.check_and_update_flight_status(user_id)
                    
                    if flight_status == "arrived":
                        # Дирижабль успешно сел. Определяем имя города по целым координатам
                        if px == 400 and py == 500:
                            city_name = "Пар-Сити"
                        elif px == -200 and py == 300:
                            city_name = "Ветроград"
                        else:
                            city_name = "Горн"
                            
                        # Шаг 4: Обновляем фабрики этого города при посадке
                        GameCore.update_city_production(city_name)
                        
                        bot.send_message(user_id, f"🔔 **Бортовой журнал:** Приземлились в порту: {city_name}!")
                        
                    elif fuel <= 0:
                        # Твой оригинальный сценарий крушения дирижабля при нуле топлива
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE players 
                            SET status = 'В порту', x = 0, y = 0, fuel = 10 
                            WHERE user_id = %s
                        """, [user_id])
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        bot.send_message(user_id, "🚨 **КАТАСТРОФА:** Топливо иссякло. Корабль рухнул. Экипаж погиб.")
                        
        except Exception as e:
            print(f"Ошибка в фоновом цикле GameLoop: {e}")

# Запуск фонового движка времени в отдельном системном потоке
threading.Thread(target=game_loop, daemon=True).start()


# === СЛОЙ 4: ИНТЕРФЕЙСНЫЕ РЕПЛИКИ И ОБРАБОТЧИКИ МЕНЮ ===

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Регистрируем игрока в новой базе данных Postgres
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO players (user_id, username) 
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
    """, [user_id, message.from_user.username or "Капитан"])
    conn.commit()
    cursor.close()
    conn.close()
    
    # Твоя оригинальная Reply-клавиатура управления дирижаблем
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = telebot.types.KeyboardButton("📊 Статус")
    btn_crew = telebot.types.KeyboardButton("👥 Экипаж")
    btn_journal = telebot.types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    # === НА БУДУЩЕЕ: ЗДЕСЬ БУДЕТ ВСТАВКА ВИДЕОРОЛИКА-ТРЕЙЛЕРА ЛОРА ИГРЫ ===
    
    # Очищенный от старых слэшей текст, переведенный на кнопки интерфейса
    bot.send_message(
        chat_id, 
        "Приветствую, Адмирал! Ваш стартовый дирижабль пришвартован в Горне.\n\n"
        "📜 **Управление флотом:**\n"
        "• Для проверки трюма и систем нажмите кнопку `📊 Статус`\n"
        "• Для открытия торговой биржи порта нажмите кнопку `📖 Бортовой журнал`\n"
        "• Проложить курс в другие города можно через команду `/fly`", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Перехватываем нажатия твоих Reply-кнопок и связываем их с новым ядром
@bot.message_handler(func=lambda message: message.text in ["📊 Статус", "👥 Экипаж", "📖 Бортовой журнал"])
def handle_menu_buttons(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if message.text == "📊 Статус":
        # Вызываем новый scannable-отчет из Postgres
        report = GameCore.get_ship_report(user_id)
        bot.send_message(chat_id, report, parse_mode="Markdown")
        
    elif message.text == "👥 Экипаж":
        # Задел под твой crew_manager (вывод параметров усталости, еды и т.д.)
        bot.send_message(chat_id, "👥 **УПРАВЛЕНИЕ ЭКИПАЖЕМ:**\nПараметры лояльности, припасов и усталости обсчитываются в реальном времени.")
        
    elif message.text == "📖 Бортовой журнал":
        # Кнопка журнала теперь мгновенно открывает Inline-биржу текущего города
        # Симулируем вызов команды /market для удобства игрока
        class FakeMessage:
            def __init__(self, c_id, u_id):
                self.chat = self
                self.id = c_id
                self.from_user = self
                self.username = "Капитан"
        fake_msg = FakeMessage(chat_id, user_id)
        show_market(fake_msg)

# === СЛОЙ 5: ГЛАВНОЕ МЕНЮ (НИЖНИЕ КНОПКИ КЛАВИАТУРЫ) ===

@bot.message_handler(func=lambda message: message.text == "📊 Статус")
def ship_status(message):
    chat_id = message.chat.id
    data = get_player_status(chat_id)
    
    if not data:
        register_player(chat_id)
        data = get_player_status(chat_id)
        
    ship_name, credits, fuel, coal, ore, steel = data
    current_weight = int((coal * 10) + (ore * 20) + (steel * 50))
    
    status_text = "🛸 **Текущий актив:** " + str(ship_name) + "\n⚙️ **Статус:** В порту ⚓\n📍 **Координаты:** X: 0.0, Y: 0.0\n⛽ **Топливо:** " + f"{fuel:.1f}" + " / 100.0 л.\n💰 **Капитал:** " + f"{credits:.1f}" + " кредитов\n📦 **Трюм (" + str(current_weight) + " / 500 кг):**\n ├ Уголь: " + f"{coal:.0f}" + " ед.\n ├ Железная руда: " + f"{ore:.0f}" + " ед.\n ├ Сталь: " + f"{steel:.0f}" + " ед.\n └ Инструменты: 0 ед.\n"
    bot.send_message(chat_id, status_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📖 Бортовой журнал")
def port_market_info(message):
    chat_id = message.chat.id
    if chat_id not in USER_SHIPS:
        GameCore.init_ship(chat_id)
        
    ship = USER_SHIPS[chat_id]
    if ship["status"] == "in_flight":
        bot.send_message(chat_id, "📖 В воздухе доступ к складам портов закрыт.")
        return

    city_id = ship["current_city_id"]
    city = CITIES[city_id]
    
    market_text = "⚓ **Вы в порту:** " + str(city['name']) + "\n📍 **Координаты:** X: " + str(city['x']) + ", Y: " + str(city['y']) + "\n📈 **Эффективность:** " + f"{city['production_speed'] * 100:.0f}" + "%\n\n🏪 **БИРЖА ГОРОДА (Склады и цены):**\n"
    
    for resource, amount in city["stockpile"].items():
        price = city["prices"].get(resource, 0)
        weight = RESOURCE_WEIGHTS.get(resource, 0)
        
        ru_names = {"coal": "Уголь", "iron_ore": "Железо", "steel": "Сталь", "tools": "Инструменты"}
        res_name = ru_names.get(resource, resource)
        
        price_text = str(price) + " кр." if price > 0 else "Не торгуется"
        market_text += " ├ " + str(res_name) + ": " + str(amount) + " ед. | Цена: " + str(price_text) + " (" + str(weight) + " кг)\n"

    bot.send_message(chat_id, market_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👥 Экипаж")
def crew_main_menu(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Состояние команды")
    btn_radio = types.KeyboardButton("🎙 Радиосвязь")
    btn_combat = types.KeyboardButton("⚔️ Симулятор Боя")
    btn_camp = types.KeyboardButton("🏕️ Тайный Лагерь")
    btn_back = types.KeyboardButton("🔙 Главное меню")
    
    markup.row(btn_status, btn_radio)
    markup.row(btn_combat, btn_camp)
    markup.row(btn_back)
    
    menu_text = "🛸 **ЛОКАЛЬНЫЙ КОМАНДНЫЙ ЦЕНТР**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\nВы подключились к узлу тактического управления. Выберите сектор:\n\n📊 `Состояние команды` — инспекция стресса и черт офицеров.\n🎙 `Радиосвязь` — прослушивание переговоров экипажа.\n⚔️ `Симулятор Боя` — запуск пошагового пробития дирижабля.\n🏕 `Тайный Лагерь` — управление подземным бункером и производством."
    bot.send_message(chat_id, menu_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔙 Главное меню")
def back_to_main_menu(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_journal = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    bot.send_message(chat_id, "Вы вернулись в главное управление флотом.", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 Состояние команды")
def crew_status_view(message):
    chat_id = message.chat.id
    status_text = CrewViewer.get_bridge_menu(crew_manager)
    
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("👩‍✈️ Досье: Франческа", callback_data="dossier_EIE"))
    inline_markup.add(types.InlineKeyboardButton("👨‍🔬 Досье: Достоевский", callback_data="dossier_EII"))
    inline_markup.add(types.InlineKeyboardButton("👨‍✈️ Досье: Максим Горький", callback_data="dossier_LSI"))
    
    bot.send_message(
        chat_id, 
        status_text + "\n\nПожалуйста, выберите офицера для открытия личного дела:", 
        reply_markup=inline_markup, 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "🎙 Радиосвязь")
def crew_radio_view(message):
    chat_id = message.chat.id
    is_in_flight = False
    if chat_id in USER_SHIPS and USER_SHIPS[chat_id].get("status") == "in_flight":
        is_in_flight = True
        
    if is_in_flight:
        log_text = dialogue_manager.get_flight_log()
        if not log_text:
            log_text = "🎙 _На частоте временное затишье. Офицеры заняты пилотированием._"
    else:
        log_text = dialogue_manager.get_dock_log(current_tick=100)
        if not log_text:
            log_text = "🎙 _Экипаж отдыхает в кают-компании порта._"
            
    bot.send_message(chat_id, log_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "⚔️ Симулятор Боя")
def start_combat_simulation_menu(message):
    chat_id = message.chat.id
    global blueprint, combat_sim
    blueprint = AirshipBlueprint()
    combat_sim = CombatSimulator(dialogue_manager)
    
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("💥 Сделать Ход 1 (Шторм)", callback_data="combat_turn_1"))
    
    welcome_text = "⚔️ **ТАКТИЧЕСКИЙ СИМУЛЯТОР БОЯ**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\nЗапуск срежиссированного боя (3 хода). Система протестирует поагрегатное пробитие отсеков и соционическую реакцию команды на ЧС.\n\n**Начальное состояние корабля:**\n"
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
    bot.send_message(chat_id, "```\n" + str(blueprint.get_ascii_blueprint()) + "\n```", reply_markup=inline_markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🏕️ Тайный Лагерь")
def view_camp_main(message):
    chat_id = message.chat.id
    report_text, markup = get_camp_telegram_view()
    bot.send_message(chat_id, report_text, reply_markup=markup, parse_mode="Markdown")

# === СЛОЙ 7: ИНТЕРАКТИВНАЯ ЛОГИКА (INLINE CALLBACK ОБРАБОТЧИКИ) ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("dossier_"))
def view_officer_dossier(call):
    action_data = call.data.split("_")
    sociotype = action_data[1]  # Исправлено: берем точный тип из ['dossier', 'EIE']
    officer = None
    for member in crew_manager.officers:
        if member.sociotype == sociotype:
            officer = member
            break
            
    if officer:
        dossier_text = CrewViewer.get_officer_dossier(officer)
        bot.send_message(call.message.chat.id, dossier_text, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Офицер не найден в данном экипаже.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("combat_turn_"))
def process_combat_turn(call):
    chat_id = call.message.chat.id
    action_data = call.data.split("_")
    turn = int(action_data[2])  # Исправлено: берем точную цифру из ['combat', 'turn', '1']
    
    combat_sim.next_turn()
    crew_manager.update_tick(is_in_flight=True)
    
    radio_comment = dialogue_manager.get_flight_log()
    if not radio_comment:
        radio_comment = "_*Слышны тяжелые вздохи экипажа в масках...*_"

    inline_markup = types.InlineKeyboardMarkup()
    if turn == 1:
        inline_markup.add(types.InlineKeyboardButton("🔥 Сделать Ход 2 (Пробитие)", callback_data="combat_turn_2"))
    elif turn == 2:
        inline_markup.add(types.InlineKeyboardButton("🏆 Сделать Ход 3 (Финал)", callback_data="combat_turn_3"))
    
    report = "⚔️ **РЕЗУЛЬТАТЫ ХОДА №" + str(turn) + "**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n📻 **Перехват радиосвязи в момент удара:**\n" + str(radio_comment) + "\n\n📊 **Схема повреждений корпуса:**"
    bot.send_message(chat_id, report, parse_mode="Markdown")
    bot.send_message(chat_id, "```\n" + str(blueprint.get_ascii_blueprint()) + "\n```", reply_markup=inline_markup if turn < 3 else None, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

def get_camp_telegram_view():
    report_text = CampViewer.get_camp_report(camp_manager)
    inline_markup = types.InlineKeyboardMarkup()
    
    btn_add = types.InlineKeyboardButton("➕ Назначить рабочего", callback_data="camp_action_add")
    btn_rem = types.InlineKeyboardButton("➖ Снять рабочего", callback_data="camp_action_remove")
    btn_surf = types.InlineKeyboardButton("🏗️ На поверхность", callback_data="camp_path_surface")
    btn_under = types.InlineKeyboardButton("🕳️ В подземелье", callback_data="camp_path_underground")
    btn_tick = types.InlineKeyboardButton("⏳ Прокрутить 1 тик времени", callback_data="camp_time_tick")
    
    inline_markup.row(btn_add, btn_rem)
    inline_markup.row(btn_surf, btn_under)
    inline_markup.row(btn_tick)
    return report_text, inline_markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("camp_"))
def process_camp_actions(call):
    chat_id = call.message.chat.id
    action_data = call.data.split("_")
    category = action_data[1]  # Исправлено: берем точную категорию (action, path, time)
    value = action_data[2]     # Исправлено: берем точное значение (add, remove, surface, tick...)
    
    if category == "action":
        if value == "add":
            camp_manager.add_worker()
        elif value == "remove":
            camp_manager.remove_worker()
    elif category == "path":
        camp_manager.change_path(value)
    elif category == "time":
        if value == "tick":
            camp_manager.update_camp_tick()
            is_flight = False
            if chat_id in USER_SHIPS and USER_SHIPS[chat_id].get("status") == "in_flight":
                is_flight = True
            crew_manager.update_tick(is_flight)
            bot.answer_callback_query(call.id, "⏳ Время продвинулось на 1 шаг!")

    report_text, markup = get_camp_telegram_view()
    try:
        bot.edit_message_text(report_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        pass

# === СЛОЙ 8: ЕДИНАЯ ТОЧКА ЗАПУСКА БОТА ===

if __name__ == '__main__':
    # 1. Сначала запускаем фоновый сервер-заглушку для Render
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    # 2. Затем запускаем самого Telegram-бота
    bot.polling(none_stop=True)

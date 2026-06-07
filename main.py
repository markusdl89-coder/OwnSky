# === СЛОЙ 1: СИСТЕМНЫЕ ИМПОРТЫ И ЗАГЛУШКА ДЛЯ RENDER ===
import http.server
import threading
import time
import os

def run_fake_server():
    server_address = ('', 10000)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(server_address, handler)
    httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# === СЛОЙ 2: ИГРОВЫЕ ИМПОРТЫ И ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРОВ ===
import telebot
from telebot import types

from config import USER_SHIPS, CITIES, RESOURCE_WEIGHTS
from core import GameCore
from database import init_db, register_player, get_player_status

from crew_manifest import CrewManager
from crew_viewer import CrewViewer
from dialogues import DialogueManager
from ballistics import AirshipBlueprint, CombatSimulator
from camp import CampManager, CampViewer

init_db()

crew_manager = CrewManager()
dialogue_manager = DialogueManager(crew_manager)
blueprint = AirshipBlueprint()
combat_sim = CombatSimulator(dialogue_manager)
camp_manager = CampManager()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
bot = telebot.TeleBot(BOT_TOKEN)

# === СЛОЙ 3: ФОНОВЫЙ ИГРОВОЙ ЦИКЛ (СЕРДЦЕ СЕРВЕРА) ===
def game_loop():
    while True:
        time.sleep(3)
        
        for current_chat_id, ship_data in USER_SHIPS.items():
            is_in_flight = False
            if ship_data.get("status") == "in_flight":
                is_in_flight = True
            crew_manager.update_tick(is_in_flight)
        
        GameCore.update_world_production()
        
        for chat_id in list(USER_SHIPS.keys()):
            status = GameCore.process_flight_tick(chat_id)
            
            if status == "arrived":
                ship = USER_SHIPS[chat_id]
                for city_id, city_data in CITIES.items():
                    if city_data["x"] == ship["x"] and city_data["y"] == ship["y"]:
                        ship["current_city_id"] = city_id
                        bot.send_message(chat_id, "🔔 **Бортовой журнал:** Приземлились в порту: " + str(city_data['name']) + "!")
                        break
            elif status == "no_fuel_crash":
                bot.send_message(chat_id, "🚨 **КАТАСТРОФА:** Топливо иссякло. Корабль рухнул. Экипаж погиб.")

threading.Thread(target=game_loop, daemon=True).start()

# === СЛОЙ 4: ОБРАБОТЧИКИ ТЕКСТОВЫХ КОМАНД (СЛЭШИ) ===

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    register_player(chat_id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_journal = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    # === НА БУДУЩЕЕ: ЗДЕСЬ БУДЕТ ВСТАВКА ВИДЕОРОЛИКА-ТРЕЙЛЕРА ЛОРА ИГРЫ ===
    
    bot.send_message(
        chat_id, 
        "Приветствую, Адмирал! Ваш стартовый дирижабль пришвартован в Горне.\n\n📜 **Команды торговли:**\n• Цены в порту: кнопка `📖 Бортовой журнал`\n• Купить груз: `/buy [название] [количество]`\n• Продать груз: `/sell [название] [количество]`\n• Взлет в Пар-Сити: `/fly 400 500`", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['fly'])
def start_flight(message):
    chat_id = message.chat.id
    ship = USER_SHIPS.get(chat_id)
    if ship["status"] == "in_flight":
        bot.send_message(chat_id, "❌ Мы уже в воздухе!")
        return
        
    try:
        parts = message.text.split()
        target_x = float(parts[1])
        target_y = float(parts[2])
        
        ship["target_x"] = target_x
        ship["target_y"] = target_y
        ship["status"] = "in_flight"
        ship["current_city_id"] = None
        bot.send_message(chat_id, "🛫 **Взлет!** Курс на X: " + str(target_x) + ", Y: " + str(target_y) + ".")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/fly 400 500`", parse_mode="Markdown")

@bot.message_handler(commands=['buy'])
def buy_resource(message):
    chat_id = message.chat.id
    ship = USER_SHIPS.get(chat_id)
    if not ship or ship["status"] == "in_flight":
        bot.send_message(chat_id, "❌ Нельзя торговать в полете!")
        return

    try:
        parts = message.text.split()
        resource = parts[1]
        quantity = int(parts[2])
        city = CITIES[ship["current_city_id"]]
        
        if resource not in city["stockpile"] or city["prices"].get(resource, 0) == 0:
            bot.send_message(chat_id, "❌ Товар здесь не продается.")
            return
            
        price = city["prices"][resource]
        total_cost = price * quantity
        added_weight = quantity * RESOURCE_WEIGHTS.get(resource, 0)
        
        if city["stockpile"][resource] < quantity:
            bot.send_message(chat_id, "❌ Нет такого количества на складе.")
            return
        if ship["credits"] < total_cost:
            bot.send_message(chat_id, "❌ Нехватка кредитов.")
            return
        if GameCore.get_cargo_weight(ship) + added_weight > ship["max_cargo_weight"]:
            bot.send_message(chat_id, "❌ Перегруз трюма!")
            return
            
        city["stockpile"][resource] -= quantity
        ship["cargo"][resource] += quantity
        ship["credits"] -= total_cost
        bot.send_message(chat_id, "✅ Куплено " + str(quantity) + " ед. за " + str(total_cost) + " кр.!")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/buy coal 5`", parse_mode="Markdown")

@bot.message_handler(commands=['sell'])
def sell_resource(message):
    chat_id = message.chat.id
    ship = USER_SHIPS.get(chat_id)
    if not ship or ship["status"] == "in_flight":
        bot.send_message(chat_id, "❌ Нельзя торговать в полете!")
        return

    try:
        parts = message.text.split()
        resource = parts[1]
        quantity = int(parts[2])
        city = CITIES[ship["current_city_id"]]
        
        if ship["cargo"].get(resource, 0) < quantity:
            bot.send_message(chat_id, "❌ Нет товара в трюме.")
            return
        if city["prices"].get(resource, 0) == 0:
            bot.send_message(chat_id, "❌ Город не принимает этот товар.")
            return
            
        price = city["prices"][resource]
        total_profit = price * quantity
        
        ship["cargo"][resource] -= quantity
        city["stockpile"][resource] += quantity
        ship["credits"] += total_profit
        bot.send_message(chat_id, "✅ Продано " + str(quantity) + " ед. за " + str(total_profit) + " кр.!")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/sell coal 5`", parse_mode="Markdown")

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
    bot.polling(none_stop=True)

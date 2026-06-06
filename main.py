import http.server # Библиотека для создания мини-сайта
import threading   # Библиотека для запуска процессов в фоне

# Функция, которая обманывает Render и держит порт открытым
def run_fake_server():
    server_address = ('', 10000) # Render по умолчанию проверяет порт 10000
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(server_address, handler)
    httpd.serve_forever() # Запускаем вечный ответ для сервера Render

# Запускаем наш мини-сайт в отдельном независимом потоке
threading.Thread(target=run_fake_server, daemon=True).start()

# --- ТВОЙ СТАРЫЙ КОД НАЧИНАЕТСЯ ЗДЕСЬ ---

import telebot
import os
# Подключаем наши новые модули соционического экипажа
from crew_manifest import CrewManager
from crew_viewer import CrewViewer
from dialogues import DialogueManager

# Инициализируем менеджеры (они будут жить в оперативной памяти)
crew_manager = CrewManager()
dialogue_manager = DialogueManager(crew_manager)

# Подключаем функции нашей базы данных SQLite
from database import init_db, register_player, get_player_status
init_db() # Автоматически создает таблицы и файл ownsky.db при старте

import threading
import time

from telebot import types
from config import USER_SHIPS, CITIES, RESOURCE_WEIGHTS
from core import GameCore

# Поиск токена в секретных настройках Render
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
bot = telebot.TeleBot(BOT_TOKEN)

# Фоновый игровой цикл (сердце сервера)
def game_loop():
        while True:
        time.sleep(3) # 1 тик = 3 секунды реального времени
        
        # Запускаем цикл, который проверяет абсолютно каждый активный корабль на сервере
        for current_chat_id, ship_data in USER_SHIPS.items():
            # Проверяем, летит ли конкретно этот дирижабль прямо сейчас
            is_in_flight = False
            if ship_data.get("status") == "in_flight":
                is_in_flight = True
                
            # Передаем статус полёта в менеджер экипажа.
            # Для MVP у нас один общий менеджер, но этот цикл обеспечит 
            # правильный расчет тиков для всех, кто запустил команду полёта.
            crew_manager.update_tick(is_in_flight)
        
        # Пассивная добыча угля и плавка стали (твой старый код для всего мира)
        GameCore.update_world_production()

        
        # Движение кораблей всех активных игроков
        for chat_id in list(USER_SHIPS.keys()):
            status = GameCore.process_flight_tick(chat_id)
            
            if status == "arrived":
                ship = USER_SHIPS[chat_id]
                # Проверяем, в какой город прилетел корабль
                for city_id, city_data in CITIES.items():
                    if city_data["x"] == ship["x"] and city_data["y"] == ship["y"]:
                        ship["current_city_id"] = city_id
                        bot.send_message(chat_id, f"🔔 **Бортовой журнал:** Приземлились в порту: {city_data['name']}!")
                        break
            elif status == "no_fuel_crash":
                bot.send_message(chat_id, "🚨 **КАТАСТРОФА:** Топливо иссякло. Корабль рухнул. Экипаж погиб.")

# Включение фонового цикла на сервере
threading.Thread(target=game_loop, daemon=True).start()

# Обработчик стартовой команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    register_player(chat_id)
    
    # Кнопки меню внизу экрана
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус дирижабля")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_journal = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    bot.send_message(
        chat_id, 
        "Приветствую, Адмирал! Ваш стартовый дирижабль пришвартован в Горне.\n\n"
        "📜 **Команды торговли:**\n"
        "• Цены в порту: кнопка `📖 Бортовой журнал`\n"
        "• Купить груз: `/buy [название] [количество]`\n"
        "  (Примеры: `/buy coal 5` или `/buy iron_ore 10`)\n"
        "• Продать груз: `/sell [название] [количество]`\n"
        "• Взлет в Пар-Сити: `/fly 400 500`", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Обработчик кнопки "📊 Статус дирижабля"
@bot.message_handler(func=lambda message: message.text == "📊 Статус дирижабля")
def ship_status(message):
    chat_id = message.chat.id
    data = get_player_status(chat_id)  # Запрашиваем данные строго из базы SQLite
    
    if not data:
        register_player(chat_id)  # Если игрока нет, регистрируем его в базе
        data = get_player_status(chat_id)
        
    # Распаковываем данные из SQLite в переменные
    ship_name, credits, fuel, coal, ore, steel = data
    
    # Считаем вес груза (уголь=10кг, руда=20кг, сталь=50кг)
    current_weight = int((coal * 10) + (ore * 20) + (steel * 50))
    
    status_text = (
        f"🛸 **Дирижабль:** {ship_name}\n"
        f"⚙️ **Статус:** В порту ⚓\n"
        f"📍 **Координаты:** X: 0.0, Y: 0.0\n"
        f"⛽ **Топливо:** {fuel:.1f} / 100.0 л.\n"
        f"💰 **Капитал:** {credits:.1f} кредитов\n"
        f"📦 **Трюм ({current_weight} / 500 кг):**\n"
        f" ├ Уголь: {coal:.0f} ед.\n"
        f" ├ Железная руда: {ore:.0f} ед.\n"
        f" ├ Сталь: {steel:.0f} ед.\n"
        f" └ Инструменты: 0 ед.\n"
    )
    
    bot.send_message(chat_id, status_text, parse_mode="Markdown")


# Обработчик кнопки "📖 Бортовой журнал" (Биржа города)
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
    
    market_text = (
        f"⚓ **Вы в порту:** {city['name']}\n"
        f"📍 **Координаты:** X: {city['x']}, Y: {city['y']}\n"
        f"📈 **Эффективность:** {city['production_speed'] * 100:.0f}%\n\n"
        f"🏪 **БИРЖА ГОРОДА (Склады и цены):**\n"
    )
    
    for resource, amount in city["stockpile"].items():
        price = city["prices"].get(resource, 0)
        weight = RESOURCE_WEIGHTS.get(resource, 0)
        
        ru_names = {"coal": "Уголь", "iron_ore": "Железо", "steel": "Сталь", "tools": "Инструменты"}
        res_name = ru_names.get(resource, resource)
        
        price_text = f"{price} кр." if price > 0 else "Не торгуется"
        market_text += f" ├ {res_name}: {amount} ед. | Цена: {price_text} ({weight} кг)\n"

    bot.send_message(chat_id, market_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👥 Экипаж")
def crew_placeholder(message):
    bot.send_message(message.chat.id, "👥 Модуль экипажа находится в разработке.")

# Покупка товара в городе (/buy coal 5)
@bot.message_handler(commands=['buy'])
def buy_resource(message):
    chat_id = message.chat.id
    ship = USER_SHIPS.get(chat_id)
    if not ship or ship["status"] == "in_flight":
        bot.send_message(chat_id, "❌ Нельзя торговать в полете!")
        return

    try:
        parts = message.text.split()
        resource = parts[1] # какой ресурс
        quantity = int(parts[2]) # сколько штук
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
        bot.send_message(chat_id, f"✅ Куплено {quantity} ед. за {total_cost} кр.!")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/buy coal 5`", parse_mode="Markdown")

# Продажа товара в городе (/sell coal 5)
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
        bot.send_message(chat_id, f"✅ Продано {quantity} ед. за {total_profit} кр.!")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/sell coal 5`", parse_mode="Markdown")

# Команда взлета /fly X Y
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
        ship["current_city_id"] = None # Оторвались от земли
        bot.send_message(chat_id, f"🛫 **Взлет!** Курс на X: {target_x}, Y: {target_y}.")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ Формат: `/fly 400 500`", parse_mode="Markdown")

if __name__ == '__main__':
    bot.polling(none_stop=True)

# Обработчик кнопки "👥 Экипаж" (Главное меню управления командой)
@bot.message_handler(func=lambda message: message.text == "👥 Экипаж")
def crew_main_menu(message):
    chat_id = message.chat.id
    
    # Создаем новые кнопки, которые появятся вместо основного меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Состояние команды")
    btn_radio = types.KeyboardButton("🎙 Радиосвязь")
    btn_back = types.KeyboardButton("🔙 Главное меню")
    markup.add(btn_status, btn_radio, btn_back)
    
    menu_text = (
        "🛸 **ОТСЕК ЭКИПАЖА ДИРИЖАБЛЯ**\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "Вы подключились к узлу связи корабля. Выберите действие:\n\n"
        "📊 `Состояние команды` — Инспекция здоровья, стресса и черт характера.\n"
        "🎙 `Радиосвязь` — Прослушивание внутренней частоты переговоров офицеров."
    )
    bot.send_message(chat_id, menu_text, reply_markup=markup, parse_mode="Markdown")


# Обработчик под-кнопки "📊 Состояние команды"
@bot.message_handler(func=lambda message: message.text == "📊 Состояние команды")
def crew_status_view(message):
    chat_id = message.chat.id
    # Берем красивый текстовый шаблон мостика из crew_viewer
    status_text = CrewViewer.get_bridge_menu(crew_manager)
    bot.send_message(chat_id, status_text, parse_mode="Markdown")


# Обработчик под-кнопки "🎙 Радиосвязь"
@bot.message_handler(func=lambda message: message.text == "🎙 Радиосвязь")
def crew_radio_view(message):
    chat_id = message.chat.id
    
    # Проверяем, летит ли корабль
    is_in_flight = False
    if chat_id in USER_SHIPS and USER_SHIPS[chat_id].get("status") == "in_flight":
        is_in_flight = True
        
    if is_in_flight:
        # Если летит — вытаскиваем сюжетную реплику по уровню стресса
        log_text = dialogue_manager.get_flight_log()
        if not log_text:
            log_text = "🎙 _На частоте временное затишье. Офицеры заняты пилотированием._"
    else:
        # If в порту — выдаем случайную редкую фоновую фразу
        # Передаем условный тик 100, чтобы обойти ограничение спама для ручного нажатия
        log_text = dialogue_manager.get_dock_log(current_tick=100)
        if not log_text:
            log_text = "🎙 _Экипаж отдыхает в кают-компании порта._"
            
    bot.send_message(chat_id, log_text, parse_mode="Markdown")


# Обработчик кнопки возврата "🔙 Главное меню"
@bot.message_handler(func=lambda message: message.text == "🔙 Главное меню")
def back_to_main_menu(message):
    chat_id = message.chat.id
    
    # Возвращаем три твои стандартные кнопки нижнего меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус дирижабля")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_journal = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    bot.send_message(chat_id, "Вы вернулись в главное управление флотом.", reply_markup=markup, parse_mode="Markdown")

import time
from bot_instance import bot, ReplyKeyboardMarkup, KeyboardButton
from server import start_hosting
from database import init_db, get_connection
from core import GameCore
import navigation

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎪 Мой Лагерь"), KeyboardButton("🚢 Флот Дирижаблей"))
    markup.row(KeyboardButton("💰 Биржа и Экономика"), KeyboardButton("🎒 Трюм и Предметы"))
    return markup

def get_fleet_menu():
    """Специальное меню для управления штурманским планом."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🗺️ Добавить точку (Тест А -> Б)"))
    markup.row(KeyboardButton("🗑️ Сбросить полетный план"))
    markup.row(KeyboardButton("⬅️ Главное меню"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Добро пожаловать в OwnSky.", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🚢 Флот Дирижаблей")
def handle_fleet(message):
    user_id = message.chat.id
    report = GameCore.get_ship_report(user_id)
    if "error" in report:
        text = report["error"]
    else:
        text = f"🛸 **Статус:** {report['status']}\n⛽ **Топливо:** {report['fuel']}\n\n📋 {report['message']}"
    bot.send_message(message.chat.id, text, reply_markup=get_fleet_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🗑️ Сбросить полетный план")
def handle_clear_plan(message):
    user_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    navigation.clear_flight_plan(cursor, user_id)
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, "🛃 Штурманский план очищен.")

@bot.message_handler(func=lambda msg: msg.text == "🗺️ Добавить точку (Тест А -> Б)")
def handle_add_test_route(message):
    user_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    # Добавляем тестовый маршрут
    navigation.add_flight_point(cursor, user_id, tx=10, ty=20, action="buy:coal:5", strategy="retreat")
    navigation.add_flight_point(cursor, user_id, tx=50, ty=80, action="sell:coal:5", strategy="retreat")
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, "✅ Тестовый маршрут построен!")

@bot.message_handler(func=lambda msg: msg.text == "⬅️ Главное меню")
def handle_back(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text in ["🎪 Мой Лагерь", "💰 Биржа и Экономика", "🎒 Трюм и Предметы"])
def handle_menu(message):
    bot.send_message(message.chat.id, f"Раздел {message.text} в разработке.")

if __name__ == "__main__":
    init_db()
    start_hosting()
    bot.polling(none_stop=True)

import telebot
from telebot import types
import config
from core import GameCore

bot = telebot.TeleBot(config.TOKEN)

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус дирижабля")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_log = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew)
    markup.add(btn_log)
    return markup

@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.from_user.id
    GameCore.init_player_ship(user_id)
    welcome_text = "🛸 **ДОБРО ПОЖАЛОВАТЬ, АДМИРАЛ!** 🛸\n\nПеред вами — ваш Бортовой журнал."
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    ship = GameCore.get_ship(user_id)
    
    if not ship:
        bot.send_message(message.chat.id, "Используйте /start для начала.")
        return

    if message.text == "📊 Статус дирижабля":
        leak_status = "Да" if ship['gas_leak'] else "Нет"
        status_report = f"📋 **ОТЧЕТ**\n\n🚀 Корабль: {ship['name']}\n🛡️ Обшивка: {ship['hull']}%"
        bot.send_message(message.chat.id, status_report, parse_mode="Markdown")
    elif message.text == "👥 Экипаж":
        bot.send_message(message.chat.id, "👥 Экипаж на мостике.", parse_mode="Markdown")
    elif message.text == "📖 Бортовой журнал":
        bot.send_message(message.chat.id, "📖 Запись 1: Полет нормальный.", parse_mode="Markdown")

if __name__ == "__main__":
    bot.polling(none_stop=True)

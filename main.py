import telebot
import os
import threading
import time
from telebot import types
from config import USER_SHIPS
from core import GameCore

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
bot = telebot.TeleBot(BOT_TOKEN)

def game_loop():
    while True:
        time.sleep(3)
        for chat_id in list(USER_SHIPS.keys()):
            status = GameCore.process_flight_tick(chat_id)
            
            if status == "arrived":
                bot.send_message(chat_id, "🔔 **Бортовой журнал:** Дирижабль успешно приземлился в пункте назначения!")
            elif status == "no_fuel_crash":
                bot.send_message(chat_id, "🚨 **КАТАСТРОФА:** Топливо иссякло. Корабль рухнул в облака. Ваш экипаж погиб.")

threading.Thread(target=game_loop, daemon=True).start()

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    GameCore.init_ship(chat_id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Статус дирижабля")
    btn_crew = types.KeyboardButton("👥 Экипаж")
    btn_journal = types.KeyboardButton("📖 Бортовой журнал")
    markup.add(btn_status, btn_crew, btn_journal)
    
    bot.send_message(
        chat_id, 
        "Приветствую, Адмирал! Ваш стартовый дирижабль готов к вылету.\n\n"
        "Используйте кнопки меню для управления.\n"
        "Чтобы отправить корабль в полет, введите команду: `/fly X Y` (например: `/fly 300 400`)", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "📊 Статус дирижабля")
def ship_status(message):
    chat_id = message.chat.id
    if chat_id not in USER_SHIPS:
        GameCore.init_ship(chat_id)
        
    ship = USER_SHIPS[chat_id]
    
    if ship["status"] == "wrecked":
        bot.send_message(chat_id, "💀 Ваш дирижабль разбит. Используйте /start для постройки нового судна.")
        return

    status_text = (
        f"🛸 **Дирижабль:** {ship['name']}\n"
        f"⚙️ **Статус:** {'В полете 🌤️' if ship['status'] == 'in_flight' else 'В порту ⚓'}\n"
        f"📍 **Текущие координаты:** X: {ship['x']:.1f}, Y: {ship['y']:.1f}\n"
        f"⛽ **Топливо:** {ship['fuel']:.1f} / {ship['max_fuel']:.1f} л.\n"
    )
    
    if ship["status"] == "in_flight":
        dist = GameCore.calculate_distance(ship["x"], ship["y"], ship["target_x"], ship["target_y"])
        status_text += f"🎯 **Цель:** X: {ship['target_x']}, Y: {ship['target_y']}\n"
        status_text += f"📏 **Осталось лететь:** {dist:.1f} метров."
        
    bot.send_message(chat_id, status_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in ["👥 Экипаж", "📖 Бортовой журнал"])
def placeholder_buttons(message):
    bot.send_message(message.chat.id, f"Вы нажали '{message.text}'. Этот модуль сейчас находится в разработке.")

@bot.message_handler(commands=['fly'])
def start_flight(message):
    chat_id = message.chat.id
    if chat_id not in USER_SHIPS:
        GameCore.init_ship(chat_id)
        
    ship = USER_SHIPS[chat_id]
    
    if ship["status"] == "in_flight":
        bot.send_message(chat_id, "❌ Корабль уже находится в воздухе! Дождитесь посадки.")
        return
        
    try:
        parts = message.text.split()
        target_x = float(parts[1])
        target_y = float(parts[2])
        
        ship["target_x"] = target_x
        ship["target_y"] = target_y
        ship["status"] = "in_flight"
        
        bot.send_message(chat_id, f"🛫 **Взлет разрешен!** Курс на координаты X: {target_x}, Y: {target_y}.\nСледите за приборами в меню 'Статус'.")
    except (IndexError, ValueError):
        bot.send_message(chat_id, "⚠️ **Ошибка формата.** Пишите команду так:\n`/fly 300 400` (где числа — это X и Y)", parse_mode="Markdown")

if __name__ == '__main__':
    bot.polling(none_stop=True)

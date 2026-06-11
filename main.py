import time
from bot_instance import bot, ReplyKeyboardMarkup, KeyboardButton
from server import start_hosting
# Предполагаем, что в database.py есть функция init_db()
from database import init_db 

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎪 Мой Лагерь"), KeyboardButton("🚢 Флот Дирижаблей"))
    markup.row(KeyboardButton("💰 Биржа и Экономика"), KeyboardButton("🎒 Трюм и Предметы"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Приветствуем в мире OwnSky! Альтернативный 1980-й. Альфа-версия запущена.\n\n"
        "Управляйте лагерем и флотом с помощью панели ниже:",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text in ["🎪 Мой Лагерь", "🚢 Флот Дирижаблей", "💰 Биржа и Экономика", "🎒 Трюм и Предметы"])
def handle_menu(message):
    # Временные заглушки для роутинга слоев логики
    bot.send_message(message.chat.id, f"Вы открыли раздел: {message.text}. Модуль в разработке.")

if __name__ == "__main__":
    print("[System] Инициализация базы данных...")
    try:
        init_db()
    except Exception as e:
        print(f"[Error] Ошибка БД: {e}. Проверьте database.py")
        
    print("[System] Запуск фонового веб-сервера для Render...")
    start_hosting()
    
    print("[System] Бот OwnSky успешно запущен.")
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"[Error] Сбой полинга: {e}")
            time.sleep(5)

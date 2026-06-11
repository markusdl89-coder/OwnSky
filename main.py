import time
from bot_instance import bot, ReplyKeyboardMarkup, KeyboardButton
from server import start_hosting
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
    bot.send_message(message.chat.id, f"Вы открыли раздел: {message.text}. Модуль в разработке.")

if __name__ == "__main__":
    print("[System] Инициализация базы данных...")
    try:
        init_db()
        print("[System] БД успешно инициализирована.")
    except Exception as e:
        print(f"[Error] Ошибка БД: {e}.")
        
    print("[System] Запуск фонового веб-сервера для Render...")
    start_hosting()
    
    print("[System] Бот OwnSky: запуск полинга...")
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"[Polling Error] Сбой: {e}. Перезапуск через 10 сек...")
            time.sleep(10)

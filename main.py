import time
from bot_instance import bot, get_main_menu, get_fleet_menu
from server import start_hosting
from database import get_connection, init_db

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Добро пожаловать в OwnSky.", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🚢 Флот Дирижаблей")
def handle_fleet(message):
    user_id = message.chat.id
    username = message.from_user.username or f"id{user_id}"
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Инициализируем игрока в БД Neon.tech, выдавая дефолтный scout
            cur.execute("""
                INSERT INTO players (user_id, gold, ship_type, route_paused)
                VALUES (%s, 1000, 'scout', FALSE)
                ON CONFLICT (user_id) DO UPDATE 
                SET ship_type = COALESCE(players.ship_type, 'scout')
                RETURNING gold, ship_type, current_route_id;
            """, (user_id,))
            gold, ship_type, current_route_id = cur.fetchone()
            conn.commit()
    except Exception as e:
        conn.rollback()
        bot.send_message(message.chat.id, "❌ Ошибка при обращении к базе данных флота.")
        print(f"Ошибка в handle_fleet: {e}")
        return
    finally:
        conn.close()

    status_text = "⏸ На паузе" if current_route_id else "⚓ В порту"
    
    # Максимально простой вывод без подгрузки сторонних модулей
    report = [
        f"🚢 *Ваш Флот:* Ветроход Скаут",
        f"👤 Капитан: {username}",
        f"💰 Баланс: {gold} золотых",
        f"📍 Статус: {status_text}",
        "",
        "ℹ️характеристики груза временно отключены для проверки стабильности билда."
    ]
    
    bot.send_message(message.chat.id, "\n".join(report), reply_markup=get_fleet_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🗑️ Сбросить полетный план")
def handle_clear_plan(message):
    bot.send_message(message.chat.id, "⚙️ Кнопка временно на техобслуживании.")

@bot.message_handler(func=lambda msg: msg.text == "🗺️ Добавить точку (Тест А -> Б)")
def handle_add_test_route(message):
    bot.send_message(message.chat.id, "⚙️ Старая штурманская заглушка отключена.")

@bot.message_handler(func=lambda msg: msg.text == "⬅️ Главное меню")
def handle_back(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text in ["🎪 Мой Лагерь", "💰 Биржа и Экономика", "🎒 Трюм и Предметы"])
def handle_menu(message):
    bot.send_message(message.chat.id, f"Раздел {message.text} в разработке.")

if __name__ == "__main__":
    init_db()
    
    # Проверяем структуру базы данных напрямую
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE players 
                ADD COLUMN IF NOT EXISTS ship_type TEXT DEFAULT 'scout',
                ADD COLUMN IF NOT EXISTS current_route_id INT,
                ADD COLUMN IF NOT EXISTS current_route_step INT,
                ADD COLUMN IF NOT EXISTS route_paused BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
    except Exception as e:
        print(f"Ошибка БД в блоке main: {e}")
        conn.rollback()
    finally:
        conn.close()

    start_hosting()
    
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка бот-поллинга: {e}")
            time.sleep(5)

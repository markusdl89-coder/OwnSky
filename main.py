import time
from bot_instance import bot, get_main_menu, get_fleet_menu
from server import start_hosting
from database import get_connection, init_db
import core
import navigation

def _get_fleet_cargo_stats(user_id):
    """
    Вспомогательная функция для подсчета реального веса и объема груза 
    на основе реестра ITEMS_REGISTRY из модуля items.
    """
    from items import ITEMS_REGISTRY
    conn = get_connection()
    items_details = []
    total_weight = 0.0
    total_volume = 0.0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id, quantity FROM inventories WHERE user_id = %s AND quantity > 0;", (user_id,))
            for item_id, quantity in cur.fetchall():
                item = ITEMS_REGISTRY.get(item_id)
                if item:
                    w = item.weight * quantity
                    v = item.volume * quantity
                    total_weight += w
                    total_volume += v
                    items_details.append(f"📦 {item.name}: {quantity} шт. ({w:.1f} кг / {v:.1f} сл.)")
                else:
                    items_details.append(f"❓ Неизвестный предмет ({item_id}): {quantity} шт.")
    finally:
        conn.close()
    return items_details, total_weight, total_volume

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Добро пожаловать в OwnSky.", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🚢 Флот Дирижаблей")
def handle_fleet(message):
    user_id = message.chat.id
    username = message.from_user.username or f"id{user_id}"
    
    from ships import SHIPS_BLUEPRINTS, calculate_current_speed
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Безопасно создаем игрока, если его нет, выдавая стартовый 'scout'
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

    # Извлекаем чертеж корабля из ships.py
    blueprint = SHIPS_BLUEPRINTS.get(ship_type)
    if not blueprint:
        bot.send_message(message.chat.id, f"❌ Чертеж корабля '{ship_type}' не найден в системе.")
        return

    # Считаем загрузку трюма и динамическую скорость
    items_list, current_weight, current_volume = _get_fleet_cargo_stats(user_id)
    current_speed = calculate_current_speed(blueprint, current_weight)
    
    w_pct = (current_weight / blueprint.max_weight) * 100
    v_pct = (current_volume / blueprint.max_volume) * 100
    status_text = "⏸ На паузе" if current_route_id else "⚓ В порту"
    
    # Формируем паспорт без лишних расчетов полета А -> Б
    report = [
        f"🚢 *Ваш Флот: {blueprint.name}*",
        f"👤 Капитан: {username}",
        f"💰 Баланс: {gold} золотых",
        "",
        "📊 *Технические характеристики:*",
        f"⚡ Скорость: {current_speed:.1f} узлов (Базовая: {blueprint.base_speed:.1f})",
        f"⚖ Масса груза: {current_weight:.1f} / {blueprint.max_weight} кг ({w_pct:.1f}%)",
        f"📦 Объем груза: {current_volume:.1f} / {blueprint.max_volume} слотов ({v_pct:.1f}%)",
        f"📍 Статус: {status_text}",
        "",
        "🗄 *Содержимое трюма:*"
    ]
    
    if items_list:
        report.extend(items_list)
    else:
        report.append("💨 Трюм пуст")
        
    bot.send_message(message.chat.id, "\n".join(report), reply_markup=get_fleet_menu(), parse_mode="Markdown")

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
    
    # Автосоздание необходимых полей структуры рейсов
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flight_plans (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    queue_order INT,
                    target_x INT,
                    target_y INT,
                    action TEXT,
                    emergency_strategy TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении таблиц: {e}")
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


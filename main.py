import os
import telebot
import pg8000
import threading # Импортируем потоки для одновременной работы
from urllib.parse import urlparse
from bot_instance import bot # Используем твой объект бота
from server import start_hosting # Твой веб-сервер для Render

# Берём ссылку на базу данных из настроек Рендера
DATABASE_URL = os.environ.get('DATABASE_URL')

def scan_neon_database():
    """Сканирует реальную структуру базы данных Neon."""
    if not DATABASE_URL:
        return "❌ Ошибка: Переменная DATABASE_URL не найдена в окружении (Environment Variables)!"
    
    try:
        parsed = urlparse(DATABASE_URL)
        conn = pg8000.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            return "📁 База данных пуста. В ней нет ни одной таблицы."
            
        report = "📋 АКТУАЛЬНАЯ СТРУКТУРА БАЗЫ NEON:\n\n"
        
        # Для каждой таблицы собираем колонки
        for table in tables:
            report += f"🔹 Таблица: {table}\n"
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}';
            """)
            columns = cursor.fetchall()
            for col in columns:
                report += f"  • {col[0]} ({col[1]})\n"
            report += "\n"
            
        cursor.close()
        conn.close()
        return report
        
    except Exception as e:
        return f"❌ Ошибка при подключении к базе данных: {str(e)}"

# Хэндлер для команды /scan
@bot.message_handler(commands=['scan'])
def handle_scan(message):
    print("[System] Получена команда /scan, запускаю проверку базы...")
    db_report = scan_neon_database()
    
    # Разбиваем на части, если отчет будет слишком длинным для одного сообщения
    if len(db_report) > 4096:
        for x in range(0, len(db_report), 4096):
            bot.reply_to(message, db_report[x:x+4096])
    else:
        bot.reply_to(message, db_report)

if __name__ == "__main__":
    print("[System] Запуск технического сканера...")
    
    # ИСПРАВЛЕНИЕ: Запускаем сервер в фоновом потоке, чтобы он не блокировал бота
    server_thread = threading.Thread(target=start_hosting)
    server_thread.daemon = True # Поток закроется сам при остановке бота
    server_thread.start()
    
    print("[System] Сервер заглушка запущен в фоновом режиме.")
    print("[System] Включаю бота. Напишите ему в Telegram команду /scan")
    
    # Теперь бот гарантированно запустится
    bot.infinity_polling(timeout=20, long_polling_timeout=20)

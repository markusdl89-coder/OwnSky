# === СЛОЙ 1: СИСТЕМНЫЕ ИМПОРТЫ И ЗАГЛУШКА ДЛЯ RENDER ===
import http.server
import threading
import time
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Импорты наших новых модулей экономики и базы данных
import database as db
from core import GameCore
from items import ITEMS_REGISTRY, get_item
from economy import calculate_dynamic_price, validate_cargo_space, calculate_cargo_metrics, get_clean_hold_view

# Создаем обработчик, который отвечает "ОК" на проверки Render
class RenderHealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and flying!")

    def log_message(self, format, *args):
        return

def run_fake_server():
    """Запуск HTTP сервера для health check Render."""
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, RenderHealthCheckHandler)
    print(f"🚀 HTTP сервер запущен на порту {port}")
    httpd.serve_forever()

# Инициализация бота
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация базы данных
print("📊 Инициализация базы данных...")
db.init_db()
print("✅ БД инициализирована")

# Запуск фонового веб-сервера ДО запуска бота (КРИТИЧНО для Render)
print("🌐 Запуск HTTP health check сервера...")
web_thread = threading.Thread(target=run_fake_server, daemon=True)
web_thread.start()
time.sleep(1)  # Даем серверу 1 секунду на запуск
print("✅ HTTP сервер запущен")

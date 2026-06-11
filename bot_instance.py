import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Критическая ошибка: BOT_TOKEN не задан в переменных окружения!")

bot = telebot.TeleBot(TOKEN)

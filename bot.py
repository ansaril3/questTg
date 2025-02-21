import json
import os
from telebot import TeleBot, types

TOKEN = '7647314070:AAFkPTQxh_RmyiJPFVoD_i2KIGI9ZiuGxD0'
bot = TeleBot(TOKEN)

# Путь к файлам
CHAPTERS_FILE = 'chapters.json'
SAVES_DIR = 'saves'

# Проверка наличия директории для сохранений
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Загрузка книги
def load_chapters():
    with open(CHAPTERS_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

chapters = load_chapters()

# Загрузка прогресса
def load_progress(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as file:
            return json.load(file)['chapter']
    else:
        return 1  # Начинаем с первой главы

# Сохранение прогресса
def save_progress(user_id, chapter):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    with open(save_file, 'w', encoding='utf-8') as file:
        json.dump({'chapter': chapter}, file)

# Старт игры
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    save_progress(user_id, 1)  # Начинаем с главы 1
    send_chapter(user_id)

# Отправка текущей главы
def send_chapter(chat_id):
    chapter_num = load_progress(chat_id)
    chapter = chapters[str(chapter_num)]
    
    # Создание клавиатуры
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(choice) for choice in chapter['options']]
    markup.add(*buttons)
    
    bot.send_message(chat_id, chapter['text'], reply_markup=markup)

# Обработка выбора игрока
@bot.message_handler(func=lambda message: True)
def handle_choice(message):
    chat_id = message.chat.id
    chapter_num = load_progress(chat_id)
    chapter = chapters[str(chapter_num)]
    
    # Проверка выбора
    if message.text in chapter['options']:
        next_chapter = chapter['options'][message.text]
        save_progress(chat_id, next_chapter)
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Неправильный выбор. Выберите один из предложенных вариантов.")

bot.polling()

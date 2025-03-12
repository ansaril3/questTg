 # Конфигурация и загрузка данных

import os
import json
from dotenv import load_dotenv
from telebot import TeleBot

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = TeleBot(TOKEN)

# Пути к файлам
CHAPTERS_FILE = "data/chapters.json"
INSTRUCTIONS_FILE = "data/instructions.json"
SAVES_DIR = "saves"
TEST_CHAPTERS_FILE = "data/test_chapters.json"

# Создание папки сохранений, если её нет
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Функция загрузки JSON-файла
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Загрузка данных
chapters = load_json(CHAPTERS_FILE)
instructions = load_json(INSTRUCTIONS_FILE)

first_chapter = list(chapters.keys())[0] if chapters else None
first_instruction = list(instructions.keys())[0] if instructions else None


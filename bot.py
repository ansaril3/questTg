import json
import os
import datetime
from collections import deque
from telebot import TeleBot, types
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = TeleBot(TOKEN)

# Пути к файлам
CHAPTERS_FILE = 'chapters.json'
SAVES_DIR = 'saves'
INSTRUCTIONS_FILE = 'instructions.json'
SAVES_LIMIT = 10  # Храним последние 10 сохранений

if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Загрузка книги
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

chapters = load_json(CHAPTERS_FILE)
instructions = load_json(INSTRUCTIONS_FILE)

# Определение первой главы
first_chapter = list(chapters.keys())[0]

# Вывод в консоль при запуске
print("Бот запущен и ожидает команды.")

# Загрузка состояния игрока
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as file:
            state = json.load(file)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)  # Преобразуем список обратно в deque
            return state
    return {"chapter": first_chapter, "health": 100, "in_menu": False, "saves": deque([], maxlen=SAVES_LIMIT)}

# Сохранение состояния игрока
def save_state(user_id, state):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    state_copy = state.copy()
    state_copy["saves"] = list(state_copy["saves"])  # Преобразуем deque в список перед сохранением
    with open(save_file, 'w', encoding='utf-8') as file:
        json.dump(state_copy, file, ensure_ascii=False, indent=4)

# Старт игры
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = {"chapter": first_chapter, "health": 100, "in_menu": False, "saves": deque([], maxlen=SAVES_LIMIT)}
    save_state(user_id, state)
    send_chapter(user_id)

# Отправка текущей главы
def send_chapter(chat_id):
    state = load_state(chat_id)
    state["in_menu"] = False  # Выход из режима меню после загрузки главы
    save_state(chat_id, state)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key, None)
    
    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return
    
    bot.send_message(chat_id, chapter['text'])
    send_main_keyboard(chat_id, chapter)

# Основная клавиатура
def send_main_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(choice) for choice in chapter['options'].keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("Меню"))  # Кнопка "Меню"
    bot.send_message(chat_id, ".", reply_markup=markup)

# Показ меню
def show_menu(chat_id):
    state = load_state(chat_id)
    state["in_menu"] = True
    save_state(chat_id, state)
    
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton("Продолжить игру"),
        types.KeyboardButton("Начать заново"),
        types.KeyboardButton("Сохранить"),
        types.KeyboardButton("Загрузить"),
        types.KeyboardButton("Инструкция")
    )
    bot.send_message(chat_id, "Игровое меню:", reply_markup=markup)

# Сохранение игры
def save_game(chat_id):
    state = load_state(chat_id)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_slot = {
        "name": f"Сохранение {timestamp}",
        "chapter": state["chapter"],
        "health": state["health"]
    }
    
    state["saves"].appendleft(save_slot)  # Добавляем новое сохранение в начало списка
    save_state(chat_id, state)
    bot.send_message(chat_id, "Игра сохранена.")
    send_chapter(chat_id)

# Показ инструкции
def show_instructions(chat_id):
    instruction_text = "\n".join([f"{key}: {value['text']}" for key, value in instructions.items()])
    bot.send_message(chat_id, instruction_text if instruction_text else "Инструкция недоступна.")

# Обработка выбора игрока
@bot.message_handler(func=lambda message: True)
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    
    if state["in_menu"]:
        if message.text == "Продолжить игру":
            state["in_menu"] = False
            save_state(chat_id, state)
            send_chapter(chat_id)
        elif message.text == "Начать заново":
            state = {"chapter": first_chapter, "health": 100, "in_menu": False, "saves": deque([], maxlen=SAVES_LIMIT)}
            save_state(chat_id, state)
            send_chapter(chat_id)
        elif message.text == "Сохранить":
            save_game(chat_id)
        elif message.text == "Инструкция":
            show_instructions(chat_id)
        else:
            bot.send_message(chat_id, "Выберите действие в меню.")
        return
    
    if message.text == "Меню":
        show_menu(chat_id)
        return
    
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key, None)
    if chapter and message.text in chapter['options']:
        state["chapter"] = chapter['options'][message.text]
        save_state(chat_id, state)
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Некорректный выбор. Попробуйте снова.")

bot.polling()

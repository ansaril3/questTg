import json
import os
import datetime
from collections import deque
from telebot import TeleBot, types
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = TeleBot(TOKEN)

# Пути к файлам
CHAPTERS_FILE = 'chapters.json'
SAVES_DIR = 'saves'
SAVES_LIMIT = 5  # Максимальное количество сохранений на игрока

# Создаем папку для сохранений, если её нет
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Функция загрузки JSON-файла
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Загрузка глав квеста
chapters = load_json(CHAPTERS_FILE)
first_chapter = list(chapters.keys())[0] if chapters else None  # Первая глава

# Загрузка состояния игрока
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as file:
            state = json.load(file)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)
            return state
    return {"chapter": first_chapter, "saves": deque([], maxlen=SAVES_LIMIT)}

# Сохранение состояния игрока
def save_state(user_id, state):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    state_copy = state.copy()
    state_copy["saves"] = list(state_copy["saves"])  # Преобразуем deque в список перед сохранением
    with open(save_file, 'w', encoding='utf-8') as file:
        json.dump(state_copy, file, ensure_ascii=False, indent=4)

# Команда /start (начало игры)
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = {"chapter": first_chapter, "saves": deque([], maxlen=SAVES_LIMIT)}
    save_state(user_id, state)
    send_chapter(user_id)

# Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    bot.send_message(chat_id, chapter["text"])
    send_options_keyboard(chat_id, chapter)

# Отправка клавиатуры с вариантами выбора
def send_options_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(option) for option in chapter["options"].keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("📥 Сохранить игру"), types.KeyboardButton("📤 Загрузить игру"))
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Обработка выбора игрока
@bot.message_handler(func=lambda message: message.text in get_all_options())
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if message.text in chapter["options"]:
        state["chapter"] = chapter["options"][message.text]
        save_state(chat_id, state)
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Некорректный выбор. Попробуйте снова.")

# Получение всех доступных вариантов выбора (для фильтрации сообщений)
def get_all_options():
    return {option for chapter in chapters.values() for option in chapter["options"].keys()}

# Сохранение текущего состояния игрока
@bot.message_handler(func=lambda message: message.text == "📥 Сохранить игру")
def save_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Генерация имени сохранения по текущей дате и времени
    save_name = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    state["saves"].append({"name": save_name, "chapter": state["chapter"]})
    save_state(chat_id, state)

    bot.send_message(chat_id, f"✅ Игра сохранена: {save_name}")

    # После сохранения снова отправляем главу и клавиатуру
    send_chapter(chat_id)



# Загрузка сохранения
@bot.message_handler(func=lambda message: message.text == "📤 Загрузить игру")
def load_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    if not state["saves"]:
        bot.send_message(chat_id, "⚠️ Нет доступных сохранений.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for i, save in enumerate(state["saves"]):
        markup.add(types.KeyboardButton(f"Загрузить {i+1} ({save['name']})"))

    bot.send_message(chat_id, "Выберите сохранение:", reply_markup=markup)

# Обработка выбора сохранения
@bot.message_handler(func=lambda message: message.text.startswith("Загрузить "))
def handle_load_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    saves_list = list(state["saves"])  # Преобразуем deque в список
    try:
        save_index = int(message.text.split()[1]) - 1
        if 0 <= save_index < len(saves_list):
            selected_save = saves_list[save_index]

            state["chapter"] = selected_save["chapter"]
            save_state(chat_id, state)

            send_chapter(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ Некорректный выбор сохранения.")
    except ValueError:
        bot.send_message(chat_id, "⚠️ Ошибка выбора сохранения.")

# Запуск бота
bot.polling()

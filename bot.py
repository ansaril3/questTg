import json
import os
from telebot import TeleBot, types
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = TeleBot(TOKEN)

# Путь к файлам
CHAPTERS_FILE = 'chapters.json'
SAVES_DIR = 'saves'

if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Загрузка книги
def load_chapters():
    with open(CHAPTERS_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

chapters = load_chapters()

# Загрузка состояния игрока
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {"chapter": 1, "health": 100, "inventory": [], "map": [[0]*5 for _ in range(5)], "position": [2, 2]}

# Сохранение состояния игрока
def save_state(user_id, state):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    with open(save_file, 'w', encoding='utf-8') as file:
        json.dump(state, file)

# Старт игры
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = {"chapter": 1, "health": 100, "inventory": [], "map": [[0]*5 for _ in range(5)], "position": [2, 2]}
    save_state(user_id, state)
    send_chapter(user_id)

# Отправка текущей главы
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_num = state["chapter"]
    chapter = chapters[str(chapter_num)]
    
    # Обновляем карту
    position = chapter["map"]
    state["map"][position[0]][position[1]] = 1
    state["position"] = position
    save_state(chat_id, state)
    
    # Добавление предметов в инвентарь
    if "items" in chapter:
        state["inventory"].extend(chapter["items"])
        bot.send_message(chat_id, f"Вы нашли: {', '.join(chapter['items'])}")
        save_state(chat_id, state)
    
    # Проверка на врага
    if "enemy" in chapter:
        enemy = chapter["enemy"]
        bot.send_message(chat_id, f"Враг: {enemy['name']} (Здоровье: {enemy['health']})")
    
    # Основная клавиатура с выбором
    send_main_keyboard(chat_id, chapter)

# Основная клавиатура
def send_main_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(choice) for choice in chapter['options']]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("Инвентарь"), types.KeyboardButton("Карта"))
    bot.send_message(chat_id, chapter['text'], reply_markup=markup)

# Отображение карты
def render_map(state):
    map_ = state["map"]
    map_str = ""
    for row in map_:
        map_str += "".join("X" if cell == 1 else "." for cell in row) + "\n"
    return map_str

# Показ карты
@bot.message_handler(func=lambda message: message.text == "Карта")
def show_map(message):
    user_id = message.chat.id
    state = load_state(user_id)
    map_str = render_map(state)
    bot.send_message(user_id, f"Ваша карта:\n{map_str}")
    send_main_keyboard(user_id, chapters[str(state["chapter"])])

# Показ инвентаря
@bot.message_handler(func=lambda message: message.text == "Инвентарь")
def show_inventory(message):
    user_id = message.chat.id
    state = load_state(user_id)
    inventory = ", ".join(state["inventory"]) if state["inventory"] else "пусто"
    bot.send_message(user_id, f"Ваш инвентарь: {inventory}")
    send_main_keyboard(user_id, chapters[str(state["chapter"])])

# Обработка выбора игрока
@bot.message_handler(func=lambda message: True)
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    chapter_num = state["chapter"]
    chapter = chapters[str(chapter_num)]
    
    if message.text in chapter['options']:
        next_step = chapter['options'][message.text]
        if next_step == "fight":
            bot.send_message(chat_id, "Скоро будет боёвка!")
        else:
            state["chapter"] = next_step
            save_state(chat_id, state)
            send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Неправильный выбор.")
        
bot.polling()

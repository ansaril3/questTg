import json
import os
import random
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
INSTRUCTIONS_FILE = 'instructions.json'
SAVES_DIR = 'saves'
SAVES_LIMIT = 5  # Максимальное количество сохранений

# Создаем папку для сохранений, если её нет
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Функция загрузки JSON-файла
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Загрузка глав и инструкции
chapters = load_json(CHAPTERS_FILE)
instructions = load_json(INSTRUCTIONS_FILE)

first_chapter = list(chapters.keys())[0] if chapters else None
first_instruction = list(instructions.keys())[0] if instructions else None

# Генерация случайного числа (например, RND6)
def roll_dice(expression):
    if expression.startswith("RND"):
        dice_max = int(expression[3:])
        return random.randint(1, dice_max)
    return int(expression)

# Вычисление значения характеристики
def calculate_characteristic(expression, state):
    tokens = expression.split()
    total = 0

    for token in tokens:
        if token.startswith("RND"):
            total += roll_dice(token)
        elif token in state["characteristics"]:
            total += state["characteristics"][token]["value"]
        elif token.isdigit() or (token[1:].isdigit() and token[0] in "+-"):
            total += int(token)
    
    return total

# Загрузка состояния игрока
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as file:
            state = json.load(file)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)
            return state
    return {
        "chapter": first_chapter,
        "instruction": None,
        "inventory": [],
        "gold": 0,
        "characteristics": {},
        "saves": deque([], maxlen=SAVES_LIMIT)
    }

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
    state = {
        "chapter": first_chapter,
        "instruction": None,
        "inventory": [],
        "gold": 0,
        "characteristics": {},
        "saves": deque([], maxlen=SAVES_LIMIT)
    }
    save_state(user_id, state)
    send_chapter(user_id)

# Обновление характеристик персонажа
def update_characteristics(state, chapter):
    if "characteristics" in chapter:
        for key, char_data in chapter["characteristics"].items():
            new_value = calculate_characteristic(char_data["value"], state)
            state["characteristics"][key] = {
                "name": char_data.get("name", key),  # Если нет name, используем ключ
                "value": new_value
            }


# Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    update_characteristics(state, chapter)

    if "add_items" in chapter:
        for item in chapter["add_items"]:
            if item not in state["inventory"]:
                state["inventory"].append(item)
    
    if "remove_items" in chapter:
        for item in chapter["remove_items"]:
            if item in state["inventory"]:
                state["inventory"].remove(item)

    if "add_gold" in chapter:
        state["gold"] += chapter["add_gold"]
    
    if "remove_gold" in chapter:
        state["gold"] -= chapter["remove_gold"]

    state["chapter"] = chapter_key
    save_state(chat_id, state)

    bot.send_message(chat_id, chapter["text"])
    send_options_keyboard(chat_id, chapter)

# Отправка раздела инструкции
def send_instruction(chat_id):
    state = load_state(chat_id)
    instruction_key = state["instruction"]
    instruction = instructions.get(instruction_key)

    if not instruction:
        bot.send_message(chat_id, "Ошибка: раздел инструкции не найден.")
        return

    bot.send_message(chat_id, instruction["text"])
    send_instruction_keyboard(chat_id, instruction)

# Отправка клавиатуры с вариантами выбора главы
def send_options_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(option) for option in chapter["options"].keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("📥 Сохранить игру"), types.KeyboardButton("📤 Загрузить игру"))
    markup.add(types.KeyboardButton("📖 Инструкция"), types.KeyboardButton("🎒 Инвентарь"), types.KeyboardButton("📊 Характеристики"))
    bot.send_message(chat_id, ".", reply_markup=markup)

# Отправка клавиатуры для инструкции
def send_instruction_keyboard(chat_id, instruction):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(option) for option in instruction["options"].keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("🔙 Вернуться в игру"))
    bot.send_message(chat_id, "Выберите раздел инструкции:", reply_markup=markup)
# Просмотр инвентаря (с золотыми монетами)
@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    inventory_text = "\n".join(f"🔹 {item}" for item in state["inventory"]) if state["inventory"] else "📭 Пусто"
    bot.send_message(chat_id, f"🎒 Ваш инвентарь:\n{inventory_text}\n\n💰 Золото: {state['gold']} монет")

    # После отображения инвентаря повторно отправляем клавиатуру действий
    send_options_keyboard(chat_id, chapters.get(state["chapter"]))

# Обработка выбора игрока (главы)
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

# Получение всех доступных вариантов выбора (главы)
def get_all_options():
    return {option for chapter in chapters.values() for option in chapter["options"].keys()}

# Вход в режим инструкции
@bot.message_handler(func=lambda message: message.text == "📖 Инструкция")
def enter_instruction(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    state["instruction"] = first_instruction  # Начинаем с первой инструкции
    save_state(chat_id, state)
    send_instruction(chat_id)

# Обработка переходов в инструкции
@bot.message_handler(func=lambda message: message.text in get_instruction_options())
def handle_instruction_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    instruction_key = state["instruction"]
    instruction = instructions.get(instruction_key)

    if message.text in instruction["options"]:
        state["instruction"] = instruction["options"][message.text]
        save_state(chat_id, state)
        send_instruction(chat_id)
    else:
        bot.send_message(chat_id, "Некорректный выбор. Попробуйте снова.")

# Получение всех доступных вариантов выбора (инструкция)
def get_instruction_options():
    return {option for instruction in instructions.values() for option in instruction["options"].keys()}

# Выход из инструкции и возврат в игру
@bot.message_handler(func=lambda message: message.text == "🔙 Вернуться в игру")
def exit_instruction(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    state["instruction"] = None  # Выходим из режима инструкции
    save_state(chat_id, state)
    send_chapter(chat_id)  # Возвращаем игрока в квест

# Просмотр характеристик
@bot.message_handler(func=lambda message: message.text == "📊 Характеристики")
def show_characteristics(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    if not state["characteristics"]:
        bot.send_message(chat_id, "📊 У вас пока нет характеристик.")
    else:
        char_text = "\n".join(
            f"{char.get('name', key)}: {char['value']}" for key, char in state["characteristics"].items()
        )
        bot.send_message(chat_id, f"📊 Ваши характеристики:\n{char_text}")

    send_options_keyboard(chat_id, chapters.get(state["chapter"]))

# Запуск бота
bot.polling()

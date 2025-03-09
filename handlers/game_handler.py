from config import bot, chapters, first_chapter  
from utils.state_manager import load_state, save_state, SAVES_LIMIT
from utils.helpers import check_conditions, calculate_characteristic, process_inventory_action, replace_variables_in_text, evaluate_condition
import telebot.types as types
from collections import deque
from datetime import datetime
import os
import random
import re

DATA_DIR = "data"  # 📂 Папка с изображениями


# ✅ Старт игры
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = {
        "chapter": first_chapter,
        "instruction": None,
        "inventory": [],
        "gold": 0,
        "characteristics": {},
        "saves": deque([], maxlen=SAVES_LIMIT),
        "options": {}
    }
    save_state(user_id, state)
    send_chapter(user_id)

# ✅ Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)
    print(f"------------------------CHAPTER: {chapter_key}")

    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    state["options"] = {}
    buttons = []

    # Выполняем все действия главы
    for action in chapter:
        execute_action(chat_id, state, action, buttons)

    # Отправляем кнопки после выполнения всех действий
    send_buttons(chat_id, buttons)
    save_state(chat_id, state)

# ✅ Общая функция отправки кнопок
def send_buttons(chat_id, buttons):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add(*buttons)

    # ✅ Добавляем стандартные кнопки
    markup.add(
        types.KeyboardButton("📥 Сохранить игру"),
        types.KeyboardButton("📤 Загрузить игру"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("📊 Характеристики"),
    )

    bot.send_message(chat_id, ".", reply_markup=markup)

# ✅ Общая обработка действия
def execute_action(chat_id, state, action, buttons):
    action_type = action["type"]
    value = action["value"]

    print(f"➡️ Action: {action_type} | value: {str(value)[:60]}{'...' if len(str(value)) > 60 else ''}")

    if action_type == "text":
        handle_text(chat_id, value)
    elif action_type == "btn":
        handle_btn(state, value, buttons)
    elif action_type == "xbtn":
        handle_xbtn(chat_id, state, value, buttons)
    elif action_type == "inventory":
        handle_inventory(state, value)
    elif action_type == "gold":
        handle_gold(state, value)
    elif action_type == "assign":
        handle_assign(state, value)
    elif action_type == "goto":
        handle_goto(chat_id, state, value)
    elif action_type == "image":
        handle_image(chat_id, value)
    elif action_type == "if":
        handle_if(chat_id, state, value, buttons)

# ✅ Обработчики конкретных действий
def handle_text(chat_id, value):
    bot.send_message(chat_id, value)

def handle_btn(state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

def handle_xbtn(chat_id, state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

    # Выполняем действия внутри xbtn
    for sub_action in value.get("actions", []):
        execute_action(chat_id, state, sub_action, buttons)

def handle_inventory(state, value):
    process_inventory_action(state, value)

def handle_gold(state, value):
    try:
        if value.startswith("+"):
            state["gold"] += int(value[1:])
        elif value.startswith("-"):
            state["gold"] -= int(value[1:])
        else:
            state["gold"] = int(value)
        print(f"💰 Текущее золото: {state['gold']}")
    except Exception as e:
        print(f"⚠️ Ошибка в обработке золота: {e}")

def handle_assign(state, value):
    key = value["key"]
    new_value = value["value"]
    name = value.get("name", key)

    # Обработка случайных значений типа RND12
    new_value = re.sub(r'RND(\d+)', lambda m: str(random.randint(1, int(m.group(1)))), new_value)

    local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
    try:
        new_value = int(new_value) if new_value.isdigit() else eval(new_value, {}, local_vars)
    except Exception as e:
        print(f"Ошибка в assign: {e}")
        new_value = state["characteristics"].get(key, {"value": 0})["value"]

    state["characteristics"][key] = {"name": name, "value": new_value}

def handle_goto(chat_id, state, value):
    target = value
    if target and target in chapters:
        state["chapter"] = target
        save_state(chat_id, state)
        send_chapter(chat_id)

def handle_image(chat_id, value):
    image_path = DATA_DIR + value.replace("\\", "/")
    if os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            bot.send_photo(chat_id, photo)
    else:
        bot.send_message(chat_id, f"⚠️ Изображение не найдено: {value}")

def handle_if(chat_id, state, value, buttons):
    condition = value["condition"]
    actions = value["actions"]
    else_actions = value.get("else_actions", [])

    if evaluate_condition(state, condition):
        print(f"✅ Условие ИСТИННО: {condition}")
        for sub_action in actions:
            execute_action(chat_id, state, sub_action, buttons)
    else:
        print(f"❌ Условие ЛОЖНО: {condition}")
        for sub_action in else_actions:
            execute_action(chat_id, state, sub_action, buttons)

# ✅ Получаем все доступные варианты кнопок
def get_all_options():
    return {
        option 
        for chapter in chapters.values()
        for action in chapter 
        if action["type"] in ("btn", "xbtn")
        for option in [action["value"]["text"]]
    }

# ✅ Обработка выбора игрока
@bot.message_handler(func=lambda message: message.text in get_all_options())
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    for action in chapter:
        if action["type"] in ("btn", "xbtn") and action["value"]["text"] == message.text:
            handle_goto(chat_id, state, action["value"]["target"])
            return

    bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")

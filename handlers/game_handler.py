from config import bot, chapters, first_chapter  
from utils.state_manager import load_state, save_state, SAVES_LIMIT
from utils.helpers import check_conditions, calculate_characteristic, process_inventory_action, replace_variables_in_text, evaluate_condition
import telebot.types as types
from collections import deque
from datetime import datetime
import os
import random
import re
from collections import deque

DATA_DIR = "data"  # 📂 Папка с изображениями
HISTORY_LIMIT = 10 # ✅ Максимальный размер стека для истории переходов

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
        "options": {},
        "history": deque([], maxlen=HISTORY_LIMIT)  # ✅ Стек для истории переходов
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
        print(f"------ACTION: {action}")
        execute_action(chat_id, state, action, buttons)

    # Отправляем кнопки после выполнения всех действий
    send_buttons(chat_id, buttons)
    save_state(chat_id, state)

# ✅ Общая функция отправки кнопок
def send_buttons(chat_id, buttons):
    if not buttons:
        print("⚠️ Нет кнопок для отображения")
        return

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

    print(f"📌 Отправляю кнопки: {[btn.text for btn in buttons]}")
    bot.send_message(chat_id, ".", reply_markup=markup)


# ✅ Общая обработка действия
def execute_action(chat_id, state, action, buttons):
    action_type = action["type"]
    value = action["value"]

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
    state = load_state(chat_id)
    new_value = replace_variables_in_text(state, value)
    bot.send_message(chat_id, new_value)

def handle_btn(state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

def handle_xbtn(chat_id, state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

    # Выполняем действия внутри xbtn и добавляем их кнопки в общий список
    for sub_action in value.get("actions", []):
        sub_buttons = []  # Локальный список для вложенных кнопок
        execute_action(chat_id, state, sub_action, sub_buttons)
        buttons.extend(sub_buttons)  # Добавляем в родительский список кнопок

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
    if value == "return":
        if state["history"]:
            # ✅ Переход на предыдущую главу из истории
            state["chapter"] = state["history"].pop()
            save_state(chat_id, state)
            send_chapter(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ Нет предыдущей главы для возврата.")
        return
    
    if value and value in chapters:
        # ✅ Добавляем текущую главу в стек перед переходом
        state["history"].append(state["chapter"])
        state["chapter"] = value
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
            target = action["value"]["target"]
            if target == "return":
                if state["history"]:
                    # ✅ Возврат в предыдущую инструкцию
                    state["instruction"] = state["history"].pop()
                    save_state(chat_id, state)
                    handle_goto(chat_id, state, action["value"]["target"])
                else:
                    bot.send_message(chat_id, "⚠️ Нет предыдущей инструкции для возврата.")
                return
            if target in chapters:
                # ✅ Сохраняем текущую инструкцию в историю перед переходом
                state["history"].append(state["instruction"])
                state["instruction"] = target
                save_state(chat_id, state)
                handle_goto(chat_id, state, action["value"]["target"])
                return

    bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")

# ✅ Сохранение текущего состояния игрока
@bot.message_handler(func=lambda message: message.text == "📥 Сохранить игру")
def save_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Генерация имени сохранения по текущей дате и времени
    save_name = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Ограничение количества сохранений по лимиту
    if len(state["saves"]) >= SAVES_LIMIT:
        state["saves"].popleft()  # Удаляем самое старое сохранение, чтобы освободить место
    
    state["saves"].append({"name": save_name, "chapter": state["chapter"]})
    save_state(chat_id, state)

    bot.send_message(chat_id, f"✅ *Игра сохранена:* `{save_name}`", parse_mode="Markdown")

    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
    send_buttons(chat_id, buttons)


# ✅ Загрузка сохранения
@bot.message_handler(func=lambda message: message.text == "📤 Загрузить игру")
def load_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    if not state["saves"]:
        bot.send_message(chat_id, "⚠️ *Нет доступных сохранений!*", parse_mode="Markdown")
        return

    # Формируем меню с доступными сохранениями
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for i, save in enumerate(state["saves"]):
        markup.add(types.KeyboardButton(f"Загрузить {i + 1} ({save['name']})"))

    bot.send_message(chat_id, "🔄 *Выберите сохранение:*", reply_markup=markup, parse_mode="Markdown")


# ✅ Обработка выбора сохранения
@bot.message_handler(func=lambda message: message.text.startswith("Загрузить "))
def handle_load_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Получаем список сохранений
    saves_list = list(state["saves"])
    try:
        save_index = int(message.text.split()[1]) - 1
        if 0 <= save_index < len(saves_list):
            selected_save = saves_list[save_index]

            state["chapter"] = selected_save["chapter"]
            save_state(chat_id, state)

            bot.send_message(chat_id, f"✅ *Сохранение загружено:* `{selected_save['name']}`", parse_mode="Markdown")
            send_chapter(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ *Некорректный выбор сохранения.*", parse_mode="Markdown")
    except (ValueError, IndexError):
        bot.send_message(chat_id, "⚠️ *Ошибка выбора сохранения.*", parse_mode="Markdown")

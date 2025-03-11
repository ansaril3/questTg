from config import bot, chapters  
from utils.state_manager import load_specific_state, save_state, get_state, state_cache, SAVES_LIMIT, SAVES_DIR
from utils.helpers import check_conditions, calculate_characteristic, process_inventory_action, replace_variables_in_text, evaluate_condition
import telebot.types as types
from collections import deque
from datetime import datetime
import os
import random
import re
import json

DATA_DIR = "data"
HISTORY_LIMIT = 10


# ✅ Начало игры
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = get_state(user_id)
    send_chapter(user_id)


# ✅ Отправка главы игроку
def send_chapter(chat_id):
    state = state_cache[chat_id]

    if state.get("end_triggered"):
        state["end_triggered"] = False
        return
    
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)
    print(f"------------------------CHAPTER: {chapter_key}")

    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    state["options"] = {}
    buttons = []

    for action in chapter:
        print(f"------ACTION: {str(action)[:60]}{'...' if len(str(action)) > 60 else ''}")
        execute_action(chat_id, state, action, buttons)

        if state.get("end_triggered"):
            state["end_triggered"] = False
            return

    send_buttons(chat_id, buttons)


# ✅ Общая функция отправки кнопок
def send_buttons(chat_id, buttons):
    if not buttons:
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add(*buttons)

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
    elif action_type == "end":
        if state["history"]:
            state["chapter"] = state["history"].pop()
            state["options"] = {}
            state["end_triggered"] = True
            send_chapter(chat_id)
            return


# ✅ Обработчики действий
def handle_text(chat_id, value):
    state = state_cache[chat_id]
    new_value = replace_variables_in_text(state, value)
    bot.send_message(chat_id, new_value)

def handle_btn(state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

def handle_xbtn(chat_id, state, value, buttons):
    buttons.append(types.KeyboardButton(value["text"]))
    state["options"][value["text"]] = value["target"]

    if "actions" in value:
        state["options"][f"{value['text']}_actions"] = value["actions"]

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
    except Exception as e:
        print(f"Ошибка в обработке золота: {e}")

def handle_assign(state, value):
    key = value["key"].lower()
    new_value = value["value"]
    name = value.get("name", key)

    new_value = re.sub(r'rnd(\d+)', lambda m: str(random.randint(1, int(m.group(1)))), new_value)

    local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
    try:
        new_value = int(new_value) if new_value.isdigit() else eval(new_value, {}, local_vars)
    except Exception as e:
        new_value = state["characteristics"].get(key, {"value": 0})["value"]

    state["characteristics"][key] = {"name": name, "value": new_value}

def handle_goto(chat_id, state, value):
    if value == "return":
        if state["history"]:
            state["chapter"] = state["history"].pop()
            send_chapter(chat_id)
        return
    
    if value in chapters:
        state["history"].append(state["chapter"])
        state["chapter"] = value
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


# ✅ Получаем все доступные варианты кнопок (исправлено)
def get_all_options(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return set()

    # ✅ Добавляем кнопки из главы + временные кнопки из state['options']
    options = set(state.get("options", {}).keys())

    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key, [])

    # ✅ Добавляем кнопки из главы
    options.update(
        action["value"]["text"]
        for action in chapter
        if action["type"] in ("btn", "xbtn")
    )

    print(f"📌 Все доступные варианты: {options}")
    return options


# ✅ Обработка выбора игрока (исправлено)
@bot.message_handler(func=lambda message: message.text in get_all_options(message.chat.id))
def handle_choice(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "⚠️ Ошибка: глава не найдена.")
        return

    for action in chapter:
        if action["type"] in ["btn", "xbtn"] and action["value"]["text"] == message.text:
            target = action["value"]["target"]

            # ✅ Выполняем вложенные действия перед переходом
            actions = state["options"].get(f"{message.text}_actions")
            if actions:
                print(f"✅ Выполняю вложенные действия для {message.text}: {actions}")

                buttons = []
                for sub_action in actions:
                    execute_action(chat_id, state, sub_action, buttons)

                # ✅ Сохраняем изменения состояния после выполнения
                send_buttons(chat_id, buttons)

            # ✅ Выполняем переход только после выполнения вложенных действий
            if target == "return":
                if state["history"]:
                    state["chapter"] = state["history"].pop()
                    send_chapter(chat_id)
                else:
                    bot.send_message(chat_id, "⚠️ Нет предыдущей главы для возврата.")
                return

            if target in chapters:
                state["history"].append(state["chapter"])
                state["chapter"] = target
                send_chapter(chat_id)
                return

    # ✅ Проверяем кнопки из state["options"]
    if message.text in state["options"]:
        target = state["options"][message.text]
        actions = state["options"].get(f"{message.text}_actions")

        # ✅ Выполняем вложенные действия, если есть
        if actions:
            print(f"✅ Выполняю вложенные действия для {message.text}: {actions}")

            buttons = []
            for sub_action in actions:
                execute_action(chat_id, state, sub_action, buttons)

            send_buttons(chat_id, buttons)

        # ✅ Выполняем переход к следующей главе
        if target in chapters:
            state["history"].append(state["chapter"])
            state["chapter"] = target
            send_chapter(chat_id)
            return

    bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")


# ✅ Добавляем лог кнопок после выполнения действий в handle_choice
@bot.message_handler(func=lambda message: True)
def log_buttons(message):
    chat_id = message.chat.id
    state = get_state(chat_id)
    buttons = list(state.get("options", {}).keys())
    print(f"✅ Текущие кнопки: {buttons}")


# ✅ Добавляем сохранение состояния после выполнения действий
@bot.message_handler(func=lambda message: message.text == "📥 Сохранить игру")
def save_game(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    save_state(chat_id)
    last_save = state["saves"][-1]["name"]
    bot.send_message(chat_id, f"✅ *Игра сохранена:* `{last_save}`", parse_mode="Markdown")

    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
    send_buttons(chat_id, buttons)

@bot.message_handler(func=lambda message: message.text == "📤 Загрузить игру")
def load_game(message):
    chat_id = message.chat.id

    save_file = f"{SAVES_DIR}/{chat_id}.json"
    if not os.path.exists(save_file):
        bot.send_message(chat_id, "⚠️ *Нет доступных сохранений!*", parse_mode="Markdown")
        return
    
    with open(save_file, "r", encoding="utf-8") as file:
        existing_data = json.load(file)

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for i, save_name in enumerate(sorted(existing_data.keys(), reverse=True)):
        markup.add(types.KeyboardButton(f"Загрузить {i + 1} ({save_name})"))

    bot.send_message(chat_id, "🔄 *Выберите сохранение:*", reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text.startswith("Загрузить "))
def handle_load_choice(message):
    chat_id = message.chat.id

    try:
        save_index = int(message.text.split()[1]) - 1

        save_file = f"{SAVES_DIR}/{chat_id}.json"
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            save_names = sorted(existing_data.keys(), reverse=True)
            selected_save = save_names[save_index]

            # ✅ Загружаем состояние через state_manager
            load_specific_state(chat_id, selected_save)

            bot.send_message(chat_id, f"✅ *Загружено сохранение:* `{selected_save}`", parse_mode="Markdown")
            send_chapter(chat_id)

    except (ValueError, IndexError) as e:
        print(f"⚠️ Ошибка при выборе сохранения: {e}")
        bot.send_message(chat_id, "⚠️ *Ошибка выбора сохранения.*", parse_mode="Markdown")

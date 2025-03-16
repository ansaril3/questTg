from config import bot, chapters, COMMON_BUTTONS, DATA_DIR, SAVES_DIR
from utils.state_manager import load_specific_state, save_state, get_state, state_cache  
from utils.helpers import process_inventory_action, replace_variables_in_text, evaluate_condition
from handlers.instruction_handler import send_instruction, handle_instruction_action
import telebot.types as types
from collections import deque
from datetime import datetime
import os, random, re, json
from handlers.stats_handler import show_characteristics
from utils.firebase_analytics import log_event



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
    log_event(chat_id, "chapter_opened", {"chapter": chapter_key})
    
    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    state["options"] = {}

    for action in chapter:
        print(f"------ACTION: {str(action)[:60]}{'...' if len(str(action)) > 60 else ''}")
        
        execute_action(chat_id, state, action)

        # ✅ Остановка выполнения, если сработал end
        if state.get("end_triggered"):
            state["end_triggered"] = False
            break

    send_buttons(chat_id)
         
@bot.message_handler(func=lambda message: message.text in get_all_options(message.chat.id))
def handle_choice(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    print(f"🔘 Нажата кнопка: {message.text}")

    target = state["options"].get(message.text)
    actions = state["options"].get(f"{message.text}_actions")

    if actions:
        print(f"✅ Выполняю вложенные действия для {message.text}: {actions}")
        for sub_action in actions:
            execute_action(chat_id, state, sub_action)

    # ✅ Обрабатываем кнопки из COMMON_BUTTONS
    if message.text == "📖 Инструкция":
        enter_instruction(message)
        return
    
    # ✅ Проверяем режим "instruction"
    if state.get("mode") == "instruction":
        handle_instruction_action(chat_id, message.text)
        return

    if message.text == "📊 Характеристики":
        show_characteristics(message)
        return

    if message.text == "🎒 Инвентарь":
        from handlers.inventory_handler import show_inventory
        show_inventory(message)
        return

    if message.text == "📥 Сохранить игру":
        save_game(message)
        return
    
    if message.text == "📤 Загрузить игру":
        load_game(message)
        return

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

    bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")

# ✅ Обработчики действий
def handle_text(chat_id, value):
    state = state_cache[chat_id]
    new_value = replace_variables_in_text(state, value)
    bot.send_message(chat_id, new_value)


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

def handle_if(chat_id, state, value):
    condition = value["condition"]
    actions = value["actions"]
    else_actions = value.get("else_actions", [])

    if evaluate_condition(state, condition):
        print(f"✅ Условие ИСТИННО: {condition}")
        for sub_action in actions:
            execute_action(chat_id, state, sub_action)
    else:
        print(f"❌ Условие ЛОЖНО: {condition}")
        for sub_action in else_actions:
            execute_action(chat_id, state, sub_action,)


# ✅ Обработчик для кнопки "📖 Инструкция"
@bot.message_handler(func=lambda message: message.text == "📖 Инструкция")
def enter_instruction(message):
    chat_id = message.chat.id
    send_instruction(chat_id)

# ✅ Обработчик для возврата из инструкции в игру
@bot.message_handler(func=lambda message: message.text == "⬅️ Вернуться назад")
def handle_back(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    if state.get("mode") == "instruction":
        # ✅ Сохраняем главу инструкции и возвращаемся в игру
        state["instruction_chapter"] = state.get("instruction_chapter")
        state["mode"] = "game"
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "⚠️ Невозможно вернуться назад.")

# ✅ Добавляем сохранение состояния после выполнения действий
@bot.message_handler(func=lambda message: message.text == "📥 Сохранить игру")
def save_game(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    save_state(chat_id)
    last_save = state["saves"][-1]["name"]
    bot.send_message(chat_id, f"✅ *Игра сохранена:* `{last_save}`", parse_mode="Markdown")

    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
    send_buttons(chat_id)

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

# ✅ Отправка кнопок напрямую из options
def send_buttons(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    # ✅ Создаём разметку
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)

    # ✅ Добавляем только реальные кнопки (без _actions)
    dynamic_buttons = [
        types.KeyboardButton(text) 
        for text in state.get("options", {}).keys()
        if not text.endswith("_actions")  # 🚀 Игнорируем action-кнопки
    ]
    for i in range(0, len(dynamic_buttons), 2):
        markup.add(*dynamic_buttons[i:i + 2])

    # ✅ Добавляем общие кнопки в интерфейс (без сохранения в state)
    common_buttons = [types.KeyboardButton(text) for text in COMMON_BUTTONS]
    for i in range(0, len(common_buttons), 2):
        markup.add(*common_buttons[i:i + 2])

    print(f"📌 Отправляю кнопки: {list(state['options'].keys())}")

    # ✅ Отправляем новую клавиатуру
    bot.send_message(chat_id, ".", reply_markup=markup)


# ✅ Упрощаем обработку действий
def execute_action(chat_id, state, action):
    action_type = action["type"]
    value = action["value"]
    print(f"🚀 Вызов действия: {action_type} -> {value}")

    if action_type == "text":
        handle_text(chat_id, value)
    elif action_type == "btn" or action_type == "xbtn":
        # ✅ Удаляем предыдущие связанные кнопки с такими же действиями
        state["options"].pop(value["text"], None)
        state["options"].pop(f"{value['text']}_actions", None)

        # ✅ Добавляем новую кнопку
        state["options"][value["text"]] = value["target"]
        if "actions" in value:
            state["options"][f"{value['text']}_actions"] = value["actions"]
        print(f"✅ Добавлена кнопка: {value['text']} -> {value['target']}")
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
        handle_if(chat_id, state, value)
    elif action_type == "end":
        state["end_triggered"] = True

# ✅ Упрощаем получение всех вариантов кнопок
def get_all_options(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return set()

    options = set(state.get("options", {}).keys())

    # ✅ Добавляем общие кнопки из общей переменной
    options.update(COMMON_BUTTONS)

    return options

# ✅ Добавляем лог кнопок после выполнения действий в handle_choice
@bot.message_handler(func=lambda message: True)
def log_buttons(message):
    chat_id = message.chat.id
    state = get_state(chat_id)
    buttons = list(state.get("options", {}).keys())
    print(f"✅ Текущие кнопки: {buttons}")
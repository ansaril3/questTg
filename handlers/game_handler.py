from config import bot, chapters, COMMON_BUTTONS, DATA_DIR, SAVES_DIR, PROD_MODE
from utils.state_manager import load_specific_state, save_state, get_state, state_cache  
from utils.helpers import process_inventory_action, replace_variables_in_text, evaluate_condition
from handlers.instruction_handler import send_instruction, handle_instruction_action
import telebot.types as types
from collections import deque
from datetime import datetime
import os, random, re, json
from handlers.stats_handler import show_characteristics
from utils.firebase_analytics import log_event
from utils.error_handler import safe_handler

# ✅ Start of the game
@bot.message_handler(commands=['start'])
@safe_handler
def start_game(message):
    user_id = message.chat.id
    state = get_state(user_id)
    send_chapter(user_id)


# ✅ Sending the chapter to the player
def send_chapter(chat_id):
    state = state_cache[chat_id]

    if state.get("end_triggered"):
        state["end_triggered"] = False
        return
    
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)
    print(f"------------------------CHAPTER: {chapter_key}")
    if PROD_MODE == 1:
        log_event(chat_id, "chapter_opened", {"chapter": chapter_key})
    
    if not chapter:
        bot.send_message(chat_id, "Error: Chapter not found.")
        return

    state["options"] = {}

    for action in chapter:
        print(f"------ACTION: {str(action)[:60]}{'...' if len(str(action)) > 60 else ''}")
        
        execute_action(chat_id, state, action)

        # ✅ Stop execution if 'end' is triggered
        if state.get("end_triggered"):
            state["end_triggered"] = False
            break

    send_buttons(chat_id)  # ⚙️ Используем новую inline версию
         

# ✅ Action handlers
def handle_text(chat_id, value):
    state = state_cache[chat_id]
    new_value = replace_variables_in_text(state, value)
    bot.send_message(chat_id, new_value, reply_markup=types.ReplyKeyboardRemove())


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
        print(f"Error in handling gold: {e}")

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
        bot.send_message(chat_id, f"⚠️ Image not found: {value}")

def handle_if(chat_id, state, value):
    condition = value["condition"]
    actions = value["actions"]
    else_actions = value.get("else_actions", [])

    if evaluate_condition(state, condition):
        print(f"✅ Condition is TRUE: {condition}")
        for sub_action in actions:
            execute_action(chat_id, state, sub_action)
    else:
        print(f"❌ Condition is FALSE: {condition}")
        for sub_action in else_actions:
            execute_action(chat_id, state, sub_action,)


# ✅ Instruction button handler
@bot.callback_query_handler(func=lambda call: call.data == "📖 Instructions")
def enter_instruction(call):
    chat_id = call.message.chat.id
    send_instruction(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "⬅️ Go back")
def handle_back(call):
    print(f"------------------handle back instruction")
    chat_id = call.message.chat.id
    state = get_state(chat_id)

    if state.get("mode") == "instruction":
        # ✅ Save instruction chapter and return to the game
        # state["instruction_chapter"] = state.get("instruction_chapter")
        state["mode"] = "game"
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "⚠️ Cannot go back.")

@bot.callback_query_handler(func=lambda call: call.data == "📥 Save game")
def save_game(call):
    chat_id = call.message.chat.id

    save_state(chat_id)  # ✅ Сохраняем текущее состояние
    last_save = sorted(get_saved_states(chat_id))[-1]  # Берем последнее сохранение

    # Возвращаемся к текущим кнопкам главы
    send_buttons(chat_id, f"✅ Game saved: `{last_save}`")


@bot.callback_query_handler(func=lambda call: call.data == "📤 Load game")
def load_game(call):
    chat_id = call.message.chat.id

    save_file = f"{SAVES_DIR}/{chat_id}.json"
    if not os.path.exists(save_file):
        bot.send_message(chat_id, "⚠️ *No available saves!*", parse_mode="Markdown")
        return
    
    with open(save_file, "r", encoding="utf-8") as file:
        existing_data = json.load(file)

    # ✅ Создаем inline-клавиатуру для выбора сохранений (только ключи верхнего уровня)
    save_names = sorted(existing_data.keys(), reverse=True)
    markup = types.InlineKeyboardMarkup(row_width=2)  # ✅ 2 в ряд
    for i, save_name in enumerate(save_names):
        markup.add(types.InlineKeyboardButton(
            f"Load {i + 1} ({save_name})",
            callback_data=f"load_{i}"
        ))

    # Кнопка возврата
    markup.add(types.InlineKeyboardButton("⬅️ Cancel", callback_data="cancel_load"))

    bot.send_message(chat_id, "🔄 *Select a save:*", reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("load_"))
def handle_load_choice(call):
    chat_id = call.message.chat.id
    try:
        save_index = int(call.data.split("_")[1])

        save_file = f"{SAVES_DIR}/{chat_id}.json"
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

        save_names = sorted(existing_data.keys(), reverse=True)
        selected_save = save_names[save_index]

        # ✅ Загружаем состояние
        load_specific_state(chat_id, selected_save)

        bot.send_message(chat_id, f"✅ *Loaded save:* `{selected_save}`", parse_mode="Markdown")
        send_chapter(chat_id)

    except (ValueError, IndexError) as e:
        print(f"⚠️ Error during save selection: {e}")
        bot.send_message(chat_id, "⚠️ *Save selection error.*", parse_mode="Markdown")


def get_saved_states(chat_id):
    """Получает список сохранений (только верхние ключи JSON)"""
    save_file = f"{SAVES_DIR}/{chat_id}.json"
    if not os.path.exists(save_file):
        return []
    
    with open(save_file, "r", encoding="utf-8") as file:
        return sorted(json.load(file).keys(), reverse=True)  # Сортируем от новых к старым

@bot.callback_query_handler(func=lambda call: call.data == "cancel_load")
def cancel_load(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "❌ Load cancelled.")
    send_buttons(chat_id)  # Вернуть текущие игровые кнопки

def handle_donate(call):
    chat_id = call.message.chat.id
    # Пример ссылки для донатов
    donation_url = "https://www.donate.com/yourpage"  # Замените на свой URL донатов
    send_buttons(
        chat_id,
        "💰 Thank you for considering a donation! You can support us here:\n\n" + donation_url)

# ✅ Sending inline buttons directly from options
def send_buttons(chat_id, text="➡️"):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    # ✅ Create inline keyboard layout
    markup = types.InlineKeyboardMarkup(row_width=2)

    # ✅ Add only real buttons (without _actions)
    dynamic_buttons = [
        types.InlineKeyboardButton(text=text, callback_data=text)
        for text in state.get("options", {}).keys()
        if not text.endswith("_actions")  # 🚀 Ignore action buttons
    ]

    # ✅ Add to markup
    for i in range(0, len(dynamic_buttons), 2):
        markup.row(*dynamic_buttons[i:i + 2])

    # ✅ Add common buttons (внизу под основными)
    common_buttons = [
        types.InlineKeyboardButton(text=text, callback_data=text)
        for text in COMMON_BUTTONS
    ]
    for i in range(0, len(common_buttons), 2):
        markup.row(*common_buttons[i:i + 2])

    print(f"📌 Sending inline buttons: {list(state['options'].keys()) + COMMON_BUTTONS}")

    # ✅ Send keyboard
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
@safe_handler
def handle_inline_choice(call):
    chat_id = call.message.chat.id
    message_text = call.data
    state = get_state(chat_id)

    print(f"🔘 Inline button pressed: {message_text}")

    target = state["options"].get(message_text)
    actions = state["options"].get(f"{message_text}_actions")

    if actions:
        print(f"✅ Executing nested actions for {message_text}: {actions}")
        for sub_action in actions:
            execute_action(chat_id, state, sub_action)

    # ✅ Handling buttons from COMMON_BUTTONS
    if message_text == "📖 Instructions":
        enter_instruction(call)
        return

    if state.get("mode") == "instruction":
        handle_instruction_action(call)
        return
    
    if message_text == "💰 Donate":
        handle_donate(call)
        return

    if message_text == "📊 Characteristics":
        show_characteristics(call)
        return

    if message_text == "🎒 Inventory":
        from handlers.inventory_handler import show_inventory
        show_inventory(call)
        return
    
    if call.data.startswith("use_"):
        from handlers.inventory_handler import handle_use_item
        handle_use_item(call)
        return
    
    if message_text == "back_to_game":
        from handlers.inventory_handler import back_to_game
        back_to_game(call)
        return

    if message_text == "📥 Save game":
        save_game(call)
        return
    
    if message_text == "📤 Load game":
        load_game(call)
        return

    if target == "return":
        if state["history"]:
            state["chapter"] = state["history"].pop()
            send_chapter(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ No previous chapter to return to.")
        return

    if target in chapters:
        state["history"].append(state["chapter"])
        state["chapter"] = target
        send_chapter(chat_id)
        return

    bot.send_message(chat_id, "⚠️ Invalid choice. Try again.")


# ✅ Simplify action handling
def execute_action(chat_id, state, action):
    try:
        action_type = action["type"]
        value = action["value"]
        print(f"🚀 Calling action: {action_type} -> {value}")

        if action_type == "text":
            handle_text(chat_id, value)
        elif action_type == "btn" or action_type == "xbtn":
            # ✅ Remove previous related buttons with the same actions
            state["options"].pop(value["text"], None)
            state["options"].pop(f"{value['text']}_actions", None)

            # ✅ Add new button
            state["options"][value["text"]] = value["target"]
            if "actions" in value:
                state["options"][f"{value['text']}_actions"] = value["actions"]
            print(f"✅ Added button: {value['text']} -> {value['target']}")
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
    except Exception as e:
        print(f"❌ Error executing action {action}: {e}")
        bot.send_message(chat_id, "⚠️ An error occurred while executing the action. The game continues.")

# ✅ Simplify getting all button options
def get_all_options(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return set()

    options = set(state.get("options", {}).keys())

    # ✅ Add common buttons from the shared variable
    options.update(COMMON_BUTTONS)

    return options



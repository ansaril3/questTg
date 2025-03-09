# Обработка инструкций

from config import bot, instructions, first_instruction, chapters
from utils.state_manager import load_state, save_state
from handlers.game_handler import send_chapter
import telebot.types as types
import os

DATA_DIR = "data"  # 📂 Папка с изображениями

# Отправка раздела инструкции
def send_instruction(chat_id):
    state = load_state(chat_id)
    instruction_key = state.get("instruction")
    instruction = instructions.get(instruction_key)

    if not instruction:
        bot.send_message(chat_id, "⚠️ Инструкция не найдена.")
        return

    for action in instruction:
        action_type = action["type"]
        value = action["value"]

        if action_type == "text":
            bot.send_message(chat_id, value)  # ✅ Отправляем текст

        elif action_type == "image":
            image_path = DATA_DIR + value.replace("\\", "/")
            if os.path.exists(image_path):
                with open(image_path, "rb") as photo:
                    bot.send_photo(chat_id, photo)
            else:
                bot.send_message(chat_id, f"⚠️ Изображение не найдено: {value}")

        elif action_type == "btn":
            state["options"][value["text"]] = value["target"]

        elif action_type == "goto":
            state["instruction"] = value
            save_state(chat_id, state)
            send_instruction(chat_id)  # ✅ Рекурсивно вызываем переход
            return
        
        elif action_type == "if":
            condition = value.get("condition")
            if evaluate_condition(state, condition):
                for inner_action in value.get("actions", []):
                    handle_instruction_action(chat_id, inner_action)
            else:
                for inner_action in value.get("else_actions", []):
                    handle_instruction_action(chat_id, inner_action)

        elif action_type == "xbtn":
            state["options"][value["text"]] = value["target"]

    send_chapter(chat_id)  # ✅ Показываем кнопки

def handle_instruction_action(chat_id, action):
    action_type = action["type"]
    value = action["value"]

    if action_type == "text":
        bot.send_message(chat_id, value)

    elif action_type == "image":
        image_path = os.path.join(DATA_DIR, value.replace("\\", "/"))
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id, photo)
        else:
            bot.send_message(chat_id, f"⚠️ Изображение не найдено: {value}")

    elif action_type == "btn":
        state = load_state(chat_id)
        state["options"][value["text"]] = value["target"]
        save_state(chat_id, state)

    elif action_type == "goto":
        state = load_state(chat_id)
        state["instruction"] = value
        save_state(chat_id, state)
        send_instruction(chat_id)  # ✅ Рекурсивно вызываем переход


# Отправка клавиатуры для инструкции
def send_instruction_keyboard(chat_id, instruction):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(option) for option in instruction["options"].keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("🔙 Вернуться в игру"))
    bot.send_message(chat_id, "Выберите раздел инструкции:", reply_markup=markup)

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
    instruction_key = state.get("instruction")
    instruction = instructions.get(instruction_key)

    if not instruction:
        bot.send_message(chat_id, "⚠️ Инструкция не найдена.")
        return

    for action in instruction:
        if action["type"] in ["btn", "xbtn"] and action["value"]["text"] == message.text:
            target = action["value"]["target"]
            if target in instructions:
                state["instruction"] = target
                save_state(chat_id, state)
                send_instruction(chat_id)  # ✅ Рекурсивный вызов для перехода к следующей инструкции
                return

    bot.send_message(chat_id, "⚠️ Неверный выбор.")

# Получение всех доступных вариантов выбора (инструкция)
def get_instruction_options():
    options = set()
    for instruction in instructions.values():
        for action in instruction:
            if action["type"] == "btn":
                options.add(action["value"]["text"])
            elif action["type"] == "xbtn":
                options.add(action["value"]["text"])
    return options

# Выход из инструкции и возврат в игру
@bot.message_handler(func=lambda message: message.text == "🔙 Вернуться в игру")
def exit_instruction(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    state["instruction"] = None  # Выходим из режима инструкции
    save_state(chat_id, state)
    send_chapter(chat_id)  # Возвращаем игрока в квест
# Обработка инструкций

from config import bot, instructions, first_instruction, chapters
from utils.state_manager import load_state, save_state
from handlers.game_handler import send_chapter
import telebot.types as types

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
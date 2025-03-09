from config import bot, chapters
from utils.state_manager import load_state
from handlers.game_handler import send_buttons

import telebot.types as types

@bot.message_handler(func=lambda message: message.text == "📊 Характеристики")
def show_characteristics(message):
    chat_id = message.chat.id
    if not isinstance(chat_id, int):
        print(f"⚠️ Ошибка: chat_id должен быть целым числом, а не {type(chat_id)}")
        return

    state = load_state(chat_id)
    characteristics = state.get("characteristics", {})

    if not characteristics:
        bot.send_message(chat_id, "⚠️ У вас пока нет характеристик.")

        # ✅ Получаем кнопки из текущего состояния, если они есть
        buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
        send_buttons(chat_id, buttons)
        return

    message = "📊 *Ваши характеристики:*\n"
    for key, char in characteristics.items():
        message += f"{char.get('name', key) if char.get('name') else key}: {char['value']}\n"

    bot.send_message(chat_id, message, parse_mode="Markdown")

    # ✅ Передаем кнопки из состояния главы
    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
    send_buttons(chat_id, buttons)

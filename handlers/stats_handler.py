from config import bot
from utils.state_manager import state_cache
import telebot.types as types
import re

@bot.callback_query_handler(func=lambda call: call.data == "📊 Characteristics")
def show_characteristics(call):
    chat_id = call.message.chat.id

    if not isinstance(chat_id, int):
        print(f"⚠️ Error: chat_id should be an integer, not {type(chat_id)}")
        return

    # ✅ Directly working with state in memory
    state = state_cache.get(chat_id)
    if not state:
        bot.send_message(chat_id, "⚠️ State not found. Please try again.")
        return

    characteristics = state.get("characteristics", {})

    if not characteristics:
        bot.send_message(chat_id, "⚠️ You don't have any characteristics yet.")
        from handlers.game_handler import send_buttons
        send_buttons(chat_id)  # ✅ Show menu without saving buttons in state
        return

    # ✅ Create message with characteristics
    message_text = "📊 *Your characteristics:*\n"
    for key, char in characteristics.items():
        # Проверяем, есть ли name и не является ли он пустым
        name = char.get('name')
        if name:  # Если name существует и не пустой
            value = char.get('value', 0)
            
            # Убираем все префиксы и суффиксы в квадратных скобках
            name = re.sub(r'\s*\[.*?\]\s*', '', name)
            
            message_text += f"🔹 {name}: *{value}*\n"

    #bot.send_message(chat_id, message_text, parse_mode="Markdown")

    from handlers.game_handler import send_buttons
    send_buttons(chat_id, message_text)  # ✅ Show menu without duplicating buttons

# Обработка характеристик

from config import bot
from utils.state_manager import load_state
from handlers.game_handler import send_options_keyboard

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
from config import bot, chapters
from utils.state_manager import state_cache
from handlers.game_handler import send_buttons

import telebot.types as types

@bot.message_handler(func=lambda message: message.text == "📊 Характеристики")
def show_characteristics(message):
    chat_id = message.chat.id

    if not isinstance(chat_id, int):
        print(f"⚠️ Ошибка: chat_id должен быть целым числом, а не {type(chat_id)}")
        return

    # ✅ Работа напрямую со стейтом в оперативной памяти
    state = state_cache.get(chat_id)
    if not state:
        bot.send_message(chat_id, "⚠️ Состояние не найдено. Попробуйте снова.")
        return

    characteristics = state.get("characteristics", {})

    if not characteristics:
        bot.send_message(chat_id, "⚠️ У вас пока нет характеристик.")

        # ✅ Получаем кнопки из текущего состояния, если они есть
        buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
        send_buttons(chat_id, buttons)
        return

    # ✅ Формируем сообщение с характеристиками
    message_text = "📊 *Ваши характеристики:*\n"
    for key, char in characteristics.items():
        # ✅ Если нет имени характеристики, выводим ключ как fallback
        name = char.get('name') if char.get('name') else key
        value = char.get('value', 0)
        message_text += f"🔹 *{name}*: {value}\n"

    bot.send_message(chat_id, message_text, parse_mode="Markdown")

    # ✅ Передаем кнопки из состояния главы
    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]
    send_buttons(chat_id, buttons)

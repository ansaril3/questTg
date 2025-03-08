# Обработка инвентаря
from config import bot, chapters  # Импортируем bot из config.py
from utils.state_manager import load_state, save_state
from handlers.game_handler import send_options_keyboard
import telebot.types as types

# Просмотр инвентаря (с золотыми монетами)

@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    inventory = state.get("inventory", [])
    inventory_text = "\n".join(
        f"🔹 {item}" for item in inventory
    ) if inventory else "📭 Пусто"

    # Отображаем текст инвентаря
    bot.send_message(chat_id, f"🎒 Ваш инвентарь:\n{inventory_text}")

    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)

    for item in inventory:
        # Если предмет содержит [usable], создаем кнопку "Use"
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            use_button = f"Use {item_name}"
            markup.add(types.KeyboardButton(use_button))

    # Добавляем стандартные кнопки
    markup.add(
        types.KeyboardButton("📥 Сохранить игру"),
        types.KeyboardButton("📤 Загрузить игру"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🔙 Вернуться в игру")
    )

    bot.send_message(chat_id, ".", reply_markup=markup)


# ✅ Обработка нажатия на кнопку "Use"
@bot.message_handler(func=lambda message: message.text.startswith("Use "))
def handle_use_item(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Получаем название предмета (например, "Волшебный меч")
    item_name = message.text.replace("Use ", "").strip()
    use_chapter_key = f"Use_{item_name}"

    if use_chapter_key in chapters:
        state["chapter"] = use_chapter_key
        save_state(chat_id, state)
        from handlers.game_handler import send_chapter
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, f"⚠️ Глава '{use_chapter_key}' не найдена.")

    # Обновляем инвентарь после использования
    show_inventory(message)

    # После отображения инвентаря повторно отправляем клавиатуру действий
    send_options_keyboard(chat_id, chapters.get(state["chapter"]))

# Обработка инвентаря
from config import bot, chapters  # Импортируем bot из config.py
from utils.state_manager import load_state, save_state
from handlers.game_handler import send_buttons 
import telebot.types as types

# Обработка инвентаря
@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    
    # ✅ Передаем кнопки из состояния главы (исправлено)
    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]

    inventory_list = state.get("inventory", [])
    gold = state.get("gold", 0)
    if not inventory_list and gold == 0:
        bot.send_message(chat_id, "🎒 Инвентарь пуст.")
        send_buttons(chat_id, buttons)
        return
    
    message_text = "🎒 *Ваш инвентарь:*\n"
    
    if gold > 0:
        message_text += f"💰 Золото: {gold}\n"

    for item in inventory_list:
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            # ✅ Создаем кнопку правильно через types.KeyboardButton
            buttons.append(types.KeyboardButton(f"Use {item_name}"))
            message_text += f"🔹 {item_name} (✨ usable)\n"
        else:
            message_text += f"🔹 {item}\n"
    
    bot.send_message(chat_id, f"\n{message_text}", parse_mode="Markdown")

    # ✅ Отправляем кнопки после обработки
    send_buttons(chat_id, buttons)


# ✅ Обработка нажатия на кнопку "Use"
@bot.message_handler(func=lambda message: message.text.startswith("Use "))
def handle_use_item(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Получаем название предмета (например, "Волшебный меч")
    item_name = message.text.replace("Use ", "").strip()
    use_chapter_key = f"use_{item_name}"

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
    send_chapter(chat_id)

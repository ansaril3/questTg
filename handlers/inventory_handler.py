from config import bot, chapters  # Импортируем bot из config.py
from utils.state_manager import get_state, state_cache
from handlers.game_handler import send_buttons, send_chapter, show_menu
import telebot.types as types

# ✅ Обработка инвентаря
@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = get_state(chat_id)  # ✅ Работа напрямую со стейтом в памяти
    
    # ✅ Передаем кнопки из состояния главы
    buttons = [types.KeyboardButton(text) for text in state.get("options", {}).keys()]

    inventory_list = state.get("inventory", [])
    gold = state.get("gold", 0)

    if not inventory_list and gold == 0:
        bot.send_message(chat_id, "🎒 Инвентарь пуст.")
        show_menu(chat_id)
        return
    
    message_text = "🎒 *Ваш инвентарь:*\n"
    
    if gold > 0:
        message_text += f"💰 Золото: {gold}\n"

    # ✅ Создание кнопок только для используемых предметов
    for item in inventory_list:
        print(f"Inventory item: {item}")
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            # ✅ Создаем кнопку правильно через types.KeyboardButton
            buttons.append(types.KeyboardButton(f"Use {item_name}"))
            message_text += f"🔹 {item_name} (✨ usable)\n"
        else:
            message_text += f"🔹 {item}\n"
    
    bot.send_message(chat_id, f"\n{message_text}", parse_mode="Markdown")

    # ✅ Отправляем кнопки после обработки инвентаря
    send_buttons(chat_id)

# ✅ Обработка нажатия на кнопку "Use"
@bot.message_handler(func=lambda message: message.text.startswith("Use "))
def handle_use_item(message):
    chat_id = message.chat.id
    state = state_cache[chat_id]  # ✅ Работа напрямую со стейтом в памяти

    # ✅ Получаем название предмета (например, "Волшебный меч")
    item_name = message.text.replace("Use ", "").strip()
    use_chapter_key = f"use_{item_name}"

    if use_chapter_key in chapters:
        # ✅ Добавляем текущую главу в историю перед переходом
        if state["history"] and state["history"][-1] != state["chapter"]:
            state["history"].append(state["chapter"])

        # ✅ Переход в новую главу
        state["chapter"] = use_chapter_key
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, f"⚠️ Глава '{use_chapter_key}' не найдена.")

    # ✅ Убираем повторный вызов главы (вызов обработчика исключён)

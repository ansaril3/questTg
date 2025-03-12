from config import bot, chapters
from utils.state_manager import get_state, state_cache
from handlers.game_handler import send_buttons, send_chapter
import telebot.types as types

# ✅ Обработка инвентаря
@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = get_state(chat_id)

    inventory_list = state.get("inventory", [])
    gold = state.get("gold", 0)

    if not inventory_list and gold == 0:
        bot.send_message(chat_id, "🎒 Инвентарь пуст.")
        send_buttons(chat_id)
        return
    
    message_text = "🎒 *Ваш инвентарь:*\n"
    
    if gold > 0:
        message_text += f"💰 Золото: {gold}\n"

    # ✅ Удаляем только кнопки инвентаря из state["options"], оставляем кнопки основного сценария
    state["options"] = {k: v for k, v in state["options"].items() if not k.startswith("Use ")}

    for item in inventory_list:
        print(f"Inventory item: {item}")
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            # ✅ Добавляем кнопку использования предмета в state["options"]
            state["options"][f"Use {item_name}"] = f"use_{item_name}"
            message_text += f"🔹 {item_name} (✨ usable)\n"
        else:
            message_text += f"🔹 {item}\n"

    # ✅ Отправляем сообщение с инвентарём
    bot.send_message(chat_id, f"\n{message_text}", parse_mode="Markdown")

    # ✅ Отправляем все кнопки, включая сценарные и инвентарные
    send_buttons(chat_id)


# ✅ Обработка нажатия на кнопку "Use"
@bot.message_handler(func=lambda message: message.text.startswith("Use "))
def handle_use_item(message):
    chat_id = message.chat.id
    state = state_cache[chat_id]

    # ✅ Получаем название предмета
    item_name = message.text.replace("Use ", "").strip()
    use_chapter_key = f"use_{item_name}"

    if use_chapter_key in chapters:
        if state["history"] and state["history"][-1] != state["chapter"]:
            state["history"].append(state["chapter"])

        state["chapter"] = use_chapter_key
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, f"⚠️ Глава '{use_chapter_key}' не найдена.")

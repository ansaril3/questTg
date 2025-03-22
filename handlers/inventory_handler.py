from config import bot, config
from utils.state_manager import get_state, state_cache
from handlers.game_handler import send_buttons, send_chapter
import telebot.types as types


# ✅ Показать инвентарь с Inline-кнопками
@bot.callback_query_handler(func=lambda call: call.data == "🎒 Inventory")
def show_inventory(call):
    chat_id = call.message.chat.id
    state = get_state(chat_id)

    inventory_list = state.get("inventory", [])
    gold = state.get("gold", 0)

    if not inventory_list and gold == 0:
        bot.send_message(chat_id, "🎒 Your inventory is empty.")
        send_buttons(chat_id)
        return
    
    message_text = "🎒 *Your inventory:*\n"

    if gold > 0:
        message_text += f"💰 Gold: {gold}\n"

    # ✅ Очищаем старые use_ кнопки
    state["options"] = {k: v for k, v in state["options"].items() if not k.startswith("Use ")}

    # ✅ Создаем Inline-кнопки для предметов
    markup = types.InlineKeyboardMarkup(row_width=2)

    for item in inventory_list:
        print(f"Inventory item: {item}")
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            # ✅ Добавляем кнопку "Использовать"
            state["options"][f"Use {item_name}"] = f"use_{item_name}"
            message_text += f"🔹 {item_name} ✨\n"
            markup.add(types.InlineKeyboardButton(f"Use {item_name}", callback_data=f"use_{item_name}"))
        else:
            message_text += f"🔹 {item}\n"

    # ✅ Кнопка возврата в игру
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_game"))

    # ✅ Показываем сообщение с кнопками
    bot.send_message(chat_id, f"\n{message_text}", parse_mode="Markdown", reply_markup=markup)


# ✅ Обработка нажатия "Use ..." кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def handle_use_item(call):
    chat_id = call.message.chat.id
    state = state_cache[chat_id]

    item_name = call.data.replace("use_", "").strip()

    if call.data in config.chapters:
        if state["history"] and state["history"][-1] != state["chapter"]:
            state["history"].append(state["chapter"])

        state["chapter"] = call.data
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, f"⚠️ Chapter '{call.data}' not found.")


# ✅ Кнопка возврата в игру
@bot.callback_query_handler(func=lambda call: call.data == "back_to_game")
def back_to_game(call):
    chat_id = call.message.chat.id
    send_buttons(chat_id)

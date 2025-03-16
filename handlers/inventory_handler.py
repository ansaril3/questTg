from config import bot, chapters
from utils.state_manager import get_state, state_cache
from handlers.game_handler import send_buttons, send_chapter
import telebot.types as types

# ✅ Inventory handling
@bot.message_handler(func=lambda message: message.text == "🎒 Inventory")
def show_inventory(message):
    chat_id = message.chat.id
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

    # ✅ Remove only inventory buttons from state["options"], leave the main scenario buttons
    state["options"] = {k: v for k, v in state["options"].items() if not k.startswith("Use ")}

    for item in inventory_list:
        print(f"Inventory item: {item}")
        if "[usable]" in item:
            item_name = item.replace("[usable]", "").strip()
            # ✅ Add a button for using the item to state["options"]
            state["options"][f"Use {item_name}"] = f"use_{item_name}"
            message_text += f"🔹 {item_name} (✨ usable)\n"
        else:
            message_text += f"🔹 {item}\n"

    # ✅ Send the message with the inventory
    bot.send_message(chat_id, f"\n{message_text}", parse_mode="Markdown")

    # ✅ Send all buttons, including scenario and inventory buttons
    send_buttons(chat_id)


# ✅ Handling "Use" button press
@bot.message_handler(func=lambda message: message.text.startswith("Use "))
def handle_use_item(message):
    chat_id = message.chat.id
    state = state_cache[chat_id]

    # ✅ Get the item name
    item_name = message.text.replace("Use ", "").strip()
    use_chapter_key = f"use_{item_name}"

    if use_chapter_key in chapters:
        if state["history"] and state["history"][-1] != state["chapter"]:
            state["history"].append(state["chapter"])

        state["chapter"] = use_chapter_key
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, f"⚠️ Chapter '{use_chapter_key}' not found.")

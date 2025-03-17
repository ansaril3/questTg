import os
import json
from config import bot, DATA_DIR
import telebot.types as types
from utils.state_manager import state_cache

# ✅ Load instructions.json
INSTRUCTIONS_FILE = os.path.join(DATA_DIR, "instructions.json")

with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
    instructions = json.load(f)

# ✅ Send instruction to the user
def send_instruction(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    # ✅ If the mode is not "instruction", this is the first entry into the instruction
    if state.get("mode") != "instruction":
        # Save the current chapter of the game in state["chapter"] - TBD
        state["instruction_chapter"] = list(instructions.keys())[0]  # Start with the first chapter
        state["mode"] = "instruction"

    chapter_key = state.get("instruction_chapter")
    instruction_chapter = instructions.get(chapter_key)

    if not instruction_chapter:
        bot.send_message(chat_id, "⚠️ Instruction not found.")
        return
    
    # ✅ Save history for returning
    state["history"].append(chapter_key)

    # ✅ Clear old buttons
    state["options"] = {}

    # ✅ Execute all actions in the chapter
    for action in instruction_chapter:
        execute_instruction_action(chat_id, state, action)

    # ✅ Show buttons
    send_inline_buttons(chat_id)

# ✅ Handle actions inside the instruction
def execute_instruction_action(chat_id, state, action):
    action_type = action["type"]
    value = action["value"]

    if action_type == "text":
        bot.send_message(chat_id, value)
    
    elif action_type == "image":
        image_path = DATA_DIR + value.replace("\\", "/")
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id, photo)
        else:
            bot.send_message(chat_id, f"⚠️ Image not found: {value}")

    elif action_type == "btn":
        state["options"][value["text"]] = value["target"]

# ✅ Send inline buttons to the user
def send_inline_buttons(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)

    # ✅ Add buttons from state["options"]
    buttons = [
        types.InlineKeyboardButton(text, callback_data=text)
        for text in state["options"].keys()
    ]
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i + 2])

    # ✅ Add "⬅️ Go back" button only if there is history
    #if state["history"]:
    markup.add(types.InlineKeyboardButton("⬅️ Go back", callback_data="go_back"))

    # ✅ Send the new inline keyboard
    bot.send_message(chat_id, ".", reply_markup=markup)


def handle_instruction_action(call):
    chat_id = call.message.chat.id
    state = state_cache.get(chat_id)
    if not state:
        return

    message_text = call.data
    target = state["options"].get(message_text)
    print(f"call.data = {call.data}")
    if call.data == "go_back":
        state["mode"] = "game"
        from handlers.game_handler import send_chapter
        send_chapter(chat_id)  # Return to the game
        return
        
    # ✅ If target corresponds to the next chapter in instructions.json
    if target in instructions:
        state["instruction_chapter"] = target
        send_instruction(chat_id)
    else:
        bot.send_message(chat_id, "⚠️ Invalid choice instruction. Please try again.")

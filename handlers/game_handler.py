# Обработка глав и состояния игры

from config import bot, chapters, first_chapter  
from utils.state_manager import load_state, save_state, SAVES_LIMIT
from utils.helpers import check_condition, calculate_characteristic
import telebot.types as types
from collections import deque

# Команда /start (начало игры)
@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.chat.id
    state = {
        "chapter": first_chapter,
        "instruction": None,
        "inventory": [],
        "gold": 0,
        "characteristics": {},
        "saves": deque([], maxlen=SAVES_LIMIT)
    }
    save_state(user_id, state)
    send_chapter(user_id)
    
# Обновление характеристик персонажа
def update_characteristics(state, chapter):
    if "characteristics" in chapter:
        for key, char_data in chapter["characteristics"].items():
            new_value = calculate_characteristic(char_data["value"], state)
            state["characteristics"][key] = {
                "name": char_data.get("name", key),
                "value": new_value,
            }

# Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    update_characteristics(state, chapter)

    if "add_items" in chapter:
        for item in chapter["add_items"]:
            if item not in state["inventory"]:
                state["inventory"].append(item)
    
    if "remove_items" in chapter:
        for item in chapter["remove_items"]:
            if item in state["inventory"]:
                state["inventory"].remove(item)

    if "add_gold" in chapter:
        state["gold"] += chapter["add_gold"]
    
    if "remove_gold" in chapter:
        state["gold"] -= chapter["remove_gold"]

    state["chapter"] = chapter_key
    save_state(chat_id, state)

    bot.send_message(chat_id, chapter["text"])
    send_options_keyboard(chat_id, chapter)

# Отправка клавиатуры с кнопками, учитывая условия
def send_options_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    state = load_state(chat_id)

    buttons = [types.KeyboardButton(option) for option in chapter["options"].keys()]

    if "condition" in chapter:
        result = check_condition(state, chapter["condition"])
        if result:
            btn_target, btn_text = result
            buttons.append(types.KeyboardButton(btn_text))
            state["chapter"] = btn_target

    markup.add(*buttons)
    markup.add(
        types.KeyboardButton("📥 Сохранить игру"),
        types.KeyboardButton("📤 Загрузить игру"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("📊 Характеристики"),
    )
    bot.send_message(chat_id, ".", reply_markup=markup)

# Обработка выбора игрока (главы)
@bot.message_handler(func=lambda message: message.text in get_all_options())
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if message.text in chapter["options"]:
        state["chapter"] = chapter["options"][message.text]
        save_state(chat_id, state)
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Некорректный выбор. Попробуйте снова.")

# Получение всех доступных вариантов выбора (главы)
def get_all_options():
    return {option for chapter in chapters.values() for option in chapter["options"].keys()}

import os
import json
from config import bot, DATA_DIR
import telebot.types as types
from utils.state_manager import state_cache 

# ✅ Загружаем instructions.json
INSTRUCTIONS_FILE = os.path.join(DATA_DIR, "instructions.json")

with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
    instructions = json.load(f)

# ✅ Отправка инструкции пользователю
def send_instruction(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    # ✅ Если глава не указана — берём первую из JSON
    if "chapter" not in state or state["chapter"] not in instructions:
        state["chapter"] = list(instructions.keys())[0]  # Берём первую главу
    
    chapter_key = state["chapter"]
    chapter = instructions.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "⚠️ Инструкция не найдена.")
        return
    
    # ✅ Сохраняем историю для возврата
    state["history"].append(chapter_key)

    # ✅ Очищаем старые кнопки
    state["options"] = {}

    # ✅ Выполняем все действия в главе
    for action in chapter:
        execute_instruction_action(chat_id, state, action)

    # ✅ Показываем кнопки
    send_buttons(chat_id)

# ✅ Обработка действий внутри инструкции
def execute_instruction_action(chat_id, state, action):
    action_type = action["type"]
    value = action["value"]

    if action_type == "text":
        bot.send_message(chat_id, value)
    
    elif action_type == "image":
        image_path = os.path.join(DATA_DIR, value.replace("\\", "/"))
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id, photo)
        else:
            bot.send_message(chat_id, f"⚠️ Изображение не найдено: {value}")

    elif action_type == "btn":
        state["options"][value["text"]] = value["target"]

# ✅ Отправка кнопок пользователю
def send_buttons(chat_id):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)

    # ✅ Добавляем кнопки из state["options"]
    buttons = [
        types.KeyboardButton(text) 
        for text in state["options"].keys()
    ]
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i + 2])

    # ✅ Добавляем кнопку "⬅️ Вернуться назад" только если есть история
    if state["history"]:
        markup.add(types.KeyboardButton("⬅️ Вернуться назад"))

    # ✅ Отправляем новую клавиатуру
    bot.send_message(chat_id, ".", reply_markup=markup)

# ✅ Обработка нажатий внутри инструкции
def handle_instruction_action(chat_id, message_text):
    state = state_cache.get(chat_id)
    if not state:
        return
    
    target = state["options"].get(message_text)

    if target == "return":
        if state["history"]:
            state["chapter"] = state["history"].pop()
            send_instruction(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ Нет предыдущей главы для возврата.")
        return
    
    # ✅ Если target соответствует следующей главе в instructions.json
    if target in instructions:
        state["chapter"] = target
        send_instruction(chat_id)
    else:
        bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")

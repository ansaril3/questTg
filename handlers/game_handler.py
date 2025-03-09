# Обработка глав и состояния игры

from config import bot, chapters, first_chapter  
from utils.state_manager import load_state, save_state, SAVES_LIMIT
from utils.helpers import check_conditions, calculate_characteristic, process_inventory_action, replace_variables_in_text, evaluate_condition
import telebot.types as types
from collections import deque
from datetime import datetime
import os
import random
import re

DATA_DIR = "data"  # 📂 Папка с изображениями
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
        "saves": deque([], maxlen=SAVES_LIMIT),
        "options": {}  # ✅ Добавляем пустой объект для хранения кнопок
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
            print(f"handler | update_characteristics | {key}: {new_value}")

# Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)
    print(f"------------------------CHAPTER: {chapter_key}")
    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    buttons = []
    state["options"] = {}

    # ✅ Выполняем все действия главы построчно
    for action in chapter:
        execute_action(chat_id, state, action, buttons)

    # ✅ Отправляем кнопки в Telegram
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add(*buttons)

    # ✅ Добавляем стандартные кнопки меню
    markup.add(
        types.KeyboardButton("📥 Сохранить игру"),
        types.KeyboardButton("📤 Загрузить игру"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("📊 Характеристики"),
    )

    # ✅ ОТПРАВКА МЕНЮ ПОСЛЕ ВСЕХ ДЕЙСТВИЙ
    bot.send_message(chat_id, ".", reply_markup=markup)
    save_state(chat_id, state)

def execute_action(chat_id, state, action, buttons):
    action_type = action["type"]
    value = action["value"]

    print(f"➡️ Action: {action_type} | value: {str(value)[:60]}{'...' if len(str(value)) > 60 else ''}")

    if action_type == "text":
        bot.send_message(chat_id, value)

    elif action_type == "btn":
        buttons.append(types.KeyboardButton(value["text"]))
        state["options"][value["text"]] = value["target"]

    elif action_type == "xbtn":
        buttons.append(types.KeyboardButton(value["text"]))
        state["options"][value["text"]] = value["target"]

        # ✅ Выполняем вложенные действия в xbtn
        for sub_action in value.get("actions", []):
            execute_action(chat_id, state, sub_action, buttons)

    elif action_type == "inventory":
        # ✅ Обрабатываем строку с форматом "inv+Меч"
        process_inventory_action(state, value)

    elif action_type == "gold":
        if value.startswith("+"):
            state["gold"] += int(value[1:])
        elif value.startswith("-"):
            state["gold"] -= int(value[1:])
        else:
            try:
                state["gold"] = int(value)  # ✅ Если без знака — задаём абсолютное значение
            except Exception as e:
                print(f"⚠️ Ошибка в обработке золота: {e}")

        print(f"💰 Текущее золото: {state['gold']}")


    elif action_type == "assign":
        key = value["key"]
        new_value = value["value"]
        name = value.get("name", key)

        # ✅ Обрабатываем случайные значения вида RND12, RND6 и т.д.
        new_value = re.sub(r'RND(\d+)', lambda m: str(random.randint(1, int(m.group(1)))), new_value)
        local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
        try:
            new_value = int(new_value) if new_value.isdigit() else eval(new_value, {}, local_vars)
        except Exception as e:
            print(f"Ошибка в assign: {e}")
            new_value = state["characteristics"].get(key, {"value": 0})["value"]

        state["characteristics"][key] = {
            "name": name,
            "value": new_value
        }

    elif action_type == "goto":
        target = value
        if target and target in chapters:
            state["chapter"] = target
            save_state(chat_id, state)
            send_chapter(chat_id)
            return

    elif action_type == "if":
        condition = value["condition"]
        actions = value["actions"]
        else_actions = value.get("else_actions", [])

        # ✅ Исправляем '=' на '==' для корректной проверки
        condition = condition.replace("=", "==")
        local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
        try:
            if eval(condition, {}, local_vars):
                for sub_action in actions:
                    execute_action(chat_id, state, sub_action, buttons)
            else:
                for sub_action in else_actions:
                    execute_action(chat_id, state, sub_action, buttons)
        except Exception as e:
            print(f"Ошибка в блоке if: {e}")

    elif action_type == "image":
        image_path = DATA_DIR + value.replace("\\", "/")
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id, photo)
        else:
            bot.send_message(chat_id, f"⚠️ Изображение не найдено: {value}")




def send_options_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    state = load_state(chat_id)

    buttons = []
    state["options"] = {}

    # ✅ Ищем кнопки в списке действий
    for action in chapter:
        if action["type"] == "btn":
            value = action["value"]
            buttons.append(types.KeyboardButton(value["text"]))
            state["options"][value["text"]] = value["target"]

        # ✅ Поддержка xbtn (вложенные действия)
        if action["type"] == "xbtn":
            value = action["value"]
            buttons.append(types.KeyboardButton(value["text"]))
            state["options"][value["text"]] = value["target"]

    # ✅ Добавляем стандартные кнопки меню
    markup.add(*buttons)
    markup.add(
        types.KeyboardButton("📥 Сохранить игру"),
        types.KeyboardButton("📤 Загрузить игру"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🎒 Инвентарь"),
        types.KeyboardButton("📊 Характеристики"),
    )

    # ✅ Отправляем клавиатуру
    bot.send_message(chat_id, ".", reply_markup=markup)
    save_state(chat_id, state)

# Обработка выбора игрока (главы)
@bot.message_handler(func=lambda message: message.text in get_all_options())
def handle_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    if not chapter:
        bot.send_message(chat_id, "⚠️ Ошибка: глава не найдена.")
        return

    for action in chapter:
        if action["type"] == "btn" and action["value"]["text"] == message.text:
            target = action["value"]["target"]
            state["chapter"] = target
            save_state(chat_id, state)
            send_chapter(chat_id)
            return

        if action["type"] == "xbtn" and action["value"]["text"] == message.text:
            target = action["value"]["target"]
            state["chapter"] = target
            
            # ✅ Выполняем все actions, связанные с xbtn
            for sub_action in action["value"]["actions"]:
                execute_action(chat_id, state, sub_action, [])
                
            save_state(chat_id, state)
            send_chapter(chat_id)
            return

    bot.send_message(chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")



# Получение всех доступных вариантов выбора (главы)
def get_all_options():
    return {
        option 
        for chapter in chapters.values()
        for action in chapter 
        if action["type"] == "btn" or action["type"] == "xbtn"
        for option in ([action["value"]["text"]] if action["type"] == "btn" else [action["value"]["text"]])
    }



# Сохранение текущего состояния игрока
@bot.message_handler(func=lambda message: message.text == "📥 Сохранить игру")
def save_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    # Генерация имени сохранения по текущей дате и времени
    save_name = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["saves"].append({"name": save_name, "chapter": state["chapter"]})
    save_state(chat_id, state)

    bot.send_message(chat_id, f"✅ Игра сохранена: {save_name}")

    # После сохранения снова отправляем главу и клавиатуру
    send_chapter(chat_id)

# Загрузка сохранения
@bot.message_handler(func=lambda message: message.text == "📤 Загрузить игру")
def load_game(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    if not state["saves"]:
        bot.send_message(chat_id, "⚠️ Нет доступных сохранений.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for i, save in enumerate(state["saves"]):
        markup.add(types.KeyboardButton(f"Загрузить {i+1} ({save['name']})"))

    bot.send_message(chat_id, "Выберите сохранение:", reply_markup=markup)

# Обработка выбора сохранения
@bot.message_handler(func=lambda message: message.text.startswith("Загрузить "))
def handle_load_choice(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    saves_list = list(state["saves"])  # Преобразуем deque в список
    try:
        save_index = int(message.text.split()[1]) - 1
        if 0 <= save_index < len(saves_list):
            selected_save = saves_list[save_index]

            state["chapter"] = selected_save["chapter"]
            save_state(chat_id, state)

            send_chapter(chat_id)
        else:
            bot.send_message(chat_id, "⚠️ Некорректный выбор сохранения.")
    except ValueError:
        bot.send_message(chat_id, "⚠️ Ошибка выбора сохранения.")



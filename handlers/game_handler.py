# Обработка глав и состояния игры

from config import bot, chapters, first_chapter  
from utils.state_manager import load_state, save_state, SAVES_LIMIT
from utils.helpers import check_conditions, calculate_characteristic, process_inventory_action, replace_variables_in_text
import telebot.types as types
from collections import deque
from datetime import datetime
import os

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
            print(f"handler | update_characteristics | {key}: {new_value}")

# Отправка главы игроку
def send_chapter(chat_id):
    state = load_state(chat_id)
    chapter_key = state["chapter"]
    chapter = chapters.get(chapter_key)

    print(f"handler | ----------------------------- chapter: {chapter_key}")
    if not chapter:
        bot.send_message(chat_id, "Ошибка: глава не найдена.")
        return

    update_characteristics(state, chapter)

    if "add_items" in chapter:
        for item in chapter["add_items"]:
            if item not in state["inventory"]:
                state["inventory"].append(item)
                print(f"handler | add item: {item}")
    
    if "remove_items" in chapter:
        for item in chapter["remove_items"]:
            if item in state["inventory"]:
                state["inventory"].remove(item)
                print(f"handler | remove item: {item}")

    if "add_gold" in chapter:
        state["gold"] += chapter["add_gold"]
        print(f"handler | add gold: {chapter['add_gold']}")
    
    if "remove_gold" in chapter:
        state["gold"] -= chapter["remove_gold"]
        print(f"handler | remove gold: {chapter['remove_gold']}")  

    state["chapter"] = chapter_key
    save_state(chat_id, state)

    chapter_text = replace_variables_in_text(chapter["text"], state)
    if chapter_text == "": 
        chapter_text = '.'
    bot.send_message(chat_id, chapter_text)
    # 📷 Отправляем изображение, если есть
    if "image" in chapter:
        image_path = DATA_DIR + chapter["image"].replace("\\", "/")
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id, photo)
        else:
            bot.send_message(chat_id, f"⚠️ Изображение не найдено: {chapter['image']}")

    send_options_keyboard(chat_id, chapter)

def send_options_keyboard(chat_id, chapter):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    state = load_state(chat_id)

    # Стандартные кнопки из options
    buttons = [types.KeyboardButton(option) for option in chapter["options"].keys()]

    # Проверяем xbtn в корне главы
    if "xbtn" in chapter:
        xbtn = chapter["xbtn"]
        buttons.append(types.KeyboardButton(xbtn["text"]))
        chapter["options"][xbtn["text"]] = {  
            "target": xbtn["target"],  
            "actions": xbtn["actions"]  
        }  # ✅ Сохраняем actions

    # Проверяем условия из "conditions"
    condition_buttons = []
    if "conditions" in chapter:
        condition_buttons, condition_actions = check_conditions(state, chapter["conditions"])

        print(f"handler | condition_buttons: {condition_buttons}")

        # Добавляем кнопки из условий
        for btn in condition_buttons:
            buttons.append(types.KeyboardButton(btn["text"]))
            chapter["options"][btn["text"]] = {  
                "target": btn["target"],  
                "actions": btn["actions"]  
            }  # ✅ Исправлено! Сохраняем actions

        print(f"handler | condition_actions: {condition_actions}")

        # Выполняем действия из условий
        for action in condition_actions:
            print(f"handler | action: {action}")
            if action["type"] == "goto":
                state["chapter"] = action["target"]
                save_state(chat_id, state)
                send_chapter(chat_id)
                return  

            elif action["type"] == "pln":
                if isinstance(action["text"], str):  # ✅ Проверяем, что это строка
                    processed_text = replace_variables_in_text(action["text"], state)
                    if processed_text == "": 
                        processed_text = '.'
                    bot.send_message(chat_id, processed_text)
                else:
                    print(f"Ошибка: ожидалась строка, но получено {type(action['text'])}")

            elif action["type"] == "assign":
                key, value = action["key"], action["value"]
                current_value = state["characteristics"].get(key, {"value": 0})["value"]
                local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
                try:
                    new_value = int(value) if value.isdigit() else eval(value, {}, local_vars)
                except Exception as e:
                    print(f"Ошибка в assign: {e}")
                    new_value = current_value  

                state["characteristics"][key] = {
                    "name": state["characteristics"].get(key, {"name": key})["name"],
                    "value": new_value,
                }

    save_state(chat_id, state)

    # Добавляем основные кнопки
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
        option_data = chapter["options"][message.text]

        # ✅ Исправлено! Теперь actions корректно выполняются перед переходом
        if isinstance(option_data, dict) and "actions" in option_data:
            for action in option_data["actions"]:
                print(f"handler | executing action: {action}")

                if action["type"] == "inv+":
                    process_inventory_action(state, f"Inv+ {action['item']}")
                elif action["type"] == "inv-":
                    process_inventory_action(state, f"Inv- {action['item']}")
                elif action["type"] == "assign":
                    key, value = action["key"], action["value"]
                    current_value = state["characteristics"].get(key, {"value": 0})["value"]
                    local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
                    try:
                        new_value = int(value) if value.isdigit() else eval(value, {}, local_vars)
                    except Exception as e:
                        print(f"Ошибка в assign: {e}")
                        new_value = current_value  

                    state["characteristics"][key] = {
                        "name": state["characteristics"].get(key, {"name": key})["name"],
                        "value": new_value,
                    }

            # ✅ Устанавливаем новую главу только после выполнения действий
            state["chapter"] = option_data["target"]

        else:
            state["chapter"] = option_data

        save_state(chat_id, state)
        send_chapter(chat_id)
    else:
        bot.send_message(chat_id, "Некорректный выбор. Попробуйте снова.")

# Получение всех доступных вариантов выбора (главы)
def get_all_options():
    return {option for chapter in chapters.values() for option in chapter["options"].keys()}

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



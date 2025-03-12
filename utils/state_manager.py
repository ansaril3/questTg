import json
import os
from collections import deque
from config import SAVES_DIR, SAVES_LIMIT, HISTORY_LIMIT, first_chapter
from datetime import datetime

# ✅ Кэш состояний в памяти
state_cache = {}



# ✅ Получаем состояние из кэша или создаём новое состояние
def get_state(user_id):
    if user_id not in state_cache:
        # print(f"⚠️ Состояние для пользователя {user_id} отсутствует — создаём новое состояние.")
        state_cache[user_id] = {
            "chapter": first_chapter,
            "instruction": None,
            "inventory": [],
            "gold": 0,
            "characteristics": {},
            "saves": deque([], maxlen=SAVES_LIMIT),
            "options": {},
            "history": deque([], maxlen=HISTORY_LIMIT)
        }
    return state_cache[user_id]


# ✅ Сохраняем текущее состояние в общий JSON-файл (по имени сохранения)
def save_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    # ✅ Загружаем существующие сохранения из файла (если есть)
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    else:
        existing_data = {}

    # ✅ Подготавливаем текущее состояние для сохранения
    state = state_cache[user_id].copy()
    state["history"] = list(state["history"])
    state["saves"] = list(state["saves"])

    # ✅ Создаём уникальное имя сохранения (дата + глава)
    save_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing_data[save_name] = state

    # ✅ Ограничиваем количество сохранений в файле
    if len(existing_data) > SAVES_LIMIT:
        oldest_key = sorted(existing_data.keys())[0]
        del existing_data[oldest_key]

    # ✅ Сохраняем все данные обратно в JSON-файл
    with open(save_file, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print(f"✅ Состояние сохранено под именем {save_name}")

    # ✅ Добавляем сохранение в кэш (для быстрого отображения в игре)
    state_cache[user_id]["saves"].append({"name": save_name, "chapter": state["chapter"]})


# ✅ Загружаем последнее сохранение из JSON-файла в кэш
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            # ✅ Загружаем самое последнее сохранение по времени
            last_key = sorted(existing_data.keys())[-1]
            state = existing_data[last_key]

            # ✅ Конвертируем в deque для оперативной работы
            state["history"] = deque(state.get("history", []), maxlen=HISTORY_LIMIT)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)

            # ✅ Загружаем в кэш
            state_cache[user_id] = state
            print(f"✅ Загружено сохранение: {last_key}")
            return state

    # ✅ Если данных в файле нет — создаём новое состояние
    return get_state(user_id)


# ✅ Загрузка конкретного сохранения по имени
def load_specific_state(user_id, save_name):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            if save_name in existing_data:
                state = existing_data[save_name]
                state["history"] = deque(state.get("history", []), maxlen=HISTORY_LIMIT)
                state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)

                # ✅ Загружаем в кэш
                state_cache[user_id] = state
                print(f"✅ Загружено сохранение: {save_name}")
                return state

    return None

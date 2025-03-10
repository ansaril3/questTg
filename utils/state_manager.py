import json
import os
from collections import deque
from config import SAVES_DIR, first_chapter

SAVES_LIMIT = 5  # Максимальное количество сохранений
HISTORY_LIMIT = 10  # Лимит на историю

# Глобальный кэш состояний в памяти
state_cache = {}

# ✅ Загрузка состояния игрока в память
def load_state(user_id):
    if user_id in state_cache:
        # ✅ Если состояние уже в кэше — используем его
        return state_cache[user_id]

    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            state = json.load(file)
            state["history"] = deque(state.get("history", []), maxlen=HISTORY_LIMIT)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)
            print(f"✅ State loaded from file for user {user_id}")
    else:
        # ✅ Создание нового состояния при отсутствии файла
        state = {
            "chapter": first_chapter,
            "instruction": None,
            "inventory": [],
            "gold": 0,
            "characteristics": {},
            "saves": deque([], maxlen=SAVES_LIMIT),
            "history": deque([], maxlen=HISTORY_LIMIT),
            "options": {},
            "end_triggered": False,
        }
        print(f"✅ New state created for user {user_id}")

    # ✅ Сохраняем состояние в кэш
    state_cache[user_id] = state
    return state


# ✅ Сохранение состояния игрока (только при необходимости)
def save_state(user_id):
    if user_id not in state_cache:
        print(f"⚠️ State for user {user_id} not found in cache.")
        return
    
    save_file = f"{SAVES_DIR}/{user_id}.json"
    state = state_cache[user_id]

    # ✅ Преобразуем deque в список для сохранения в JSON
    state_copy = state.copy()
    state_copy["history"] = list(state["history"])
    state_copy["saves"] = list(state["saves"])

    with open(save_file, "w", encoding="utf-8") as file:
        json.dump(state_copy, file, ensure_ascii=False, indent=4)
        print(f"✅ State saved to file for user {user_id}")


# ✅ Очистка состояния игрока из кэша
def clear_state(user_id):
    if user_id in state_cache:
        del state_cache[user_id]
        print(f"✅ State cleared from memory for user {user_id}")


# ✅ Пример использования:
# state = load_state(user_id)
# state["gold"] += 10  # Работа напрямую с состоянием в памяти
# save_state(user_id)   # Явное сохранение в файл (по необходимости)

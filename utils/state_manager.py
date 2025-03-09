# Управление состоянием игрока

import json
import os
from collections import deque
from config import SAVES_DIR, first_chapter

SAVES_LIMIT = 5  # Максимальное количество сохранений

# Загрузка состояния игрока
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            state = json.load(file)
            state["history"] = deque(state.get("history", []), maxlen=10)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)
            return state
    return {
        "chapter": first_chapter,
        "instruction": None,
        "inventory": [],
        "gold": 0,
        "characteristics": {},
        "saves": deque([], maxlen=SAVES_LIMIT),
    }

# Сохранение состояния игрока
def save_state(user_id, state):
    save_file = f"{SAVES_DIR}/{user_id}.json"
    state_copy = state.copy()
    state_copy["history"] = list(state["history"])
    state_copy["saves"] = list(state_copy["saves"])  # Преобразуем deque в список перед сохранением
    with open(save_file, "w", encoding="utf-8") as file:
        json.dump(state_copy, file, ensure_ascii=False, indent=4)

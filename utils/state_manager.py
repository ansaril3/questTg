import json
import os
from collections import deque
from config import SAVES_DIR, SAVES_LIMIT, HISTORY_LIMIT, first_chapter
from datetime import datetime

# ✅ State cache in memory
state_cache = {}

# ✅ Get state from cache or create a new state
def get_state(user_id):
    if user_id not in state_cache:
        # print(f"⚠️ State for user {user_id} not found — creating a new state.")
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

# ✅ Save the current state to a shared JSON file (by save name)
def save_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    # ✅ Load existing saves from the file (if any)
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    else:
        existing_data = {}

    # ✅ Prepare the current state for saving
    state = state_cache[user_id].copy()
    state["history"] = list(state["history"])
    state["saves"] = list(state["saves"])

    # ✅ Create a unique save name (date + chapter)
    save_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing_data[save_name] = state

    # ✅ Limit the number of saves in the file
    if len(existing_data) > SAVES_LIMIT:
        oldest_key = sorted(existing_data.keys())[0]
        del existing_data[oldest_key]

    # ✅ Save all data back to the JSON file
    with open(save_file, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print(f"✅ State saved under the name {save_name}")

    # ✅ Add the save to the cache (for quick display in the game)
    state_cache[user_id]["saves"].append({"name": save_name, "chapter": state["chapter"]})

# ✅ Load the last save from the JSON file into the cache
def load_state(user_id):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            # ✅ Load the most recent save by time
            last_key = sorted(existing_data.keys())[-1]
            state = existing_data[last_key]

            # ✅ Convert to deque for efficient operations
            state["history"] = deque(state.get("history", []), maxlen=HISTORY_LIMIT)
            state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)

            # ✅ Load into the cache
            state_cache[user_id] = state
            print(f"✅ Loaded save: {last_key}")
            return state

    # ✅ If no data is in the file — create a new state
    return get_state(user_id)

# ✅ Load a specific save by its name
def load_specific_state(user_id, save_name):
    save_file = f"{SAVES_DIR}/{user_id}.json"

    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            if save_name in existing_data:
                state = existing_data[save_name]
                state["history"] = deque(state.get("history", []), maxlen=HISTORY_LIMIT)
                state["saves"] = deque(state.get("saves", []), maxlen=SAVES_LIMIT)

                # ✅ Load into the cache
                state_cache[user_id] = state
                print(f"✅ Loaded save: {save_name}")
                return state

    return None

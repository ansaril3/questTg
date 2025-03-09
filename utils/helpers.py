# Вспомогательные функции (рандом, условия)

import random
import re

# Генерация случайного числа (например, RND6)
def roll_dice(expression):
    if expression.startswith("RND"):
        dice_max = int(expression[3:])
        return random.randint(1, dice_max)
    return int(expression)

# Вычисление значения характеристики
def calculate_characteristic(expression, state):
    tokens = expression.split()
    total = 0

    for token in tokens:
        if token.startswith("RND"):
            total += roll_dice(token)
        elif token in state["characteristics"]:
            total += state["characteristics"][token]["value"]
        elif token.isdigit() or (token[1:].isdigit() and token[0] in "+-"):
            total += int(token)
    
    return total

def check_conditions(state, conditions):
    buttons = []
    actions = []

    for condition_block in conditions:
        condition = condition_block["condition"]
        actions_list = condition_block["actions"]
        print(f"helper | check_conditions | condition: {condition}")

        if evaluate_condition(state, condition):
            print("helper | check_conditions | condition is true")
            for action in actions_list:
                action_type = action["type"]
                print(f"helper | check_conditions | action: {action}, type: {action_type}")

                if action_type == "btn":
                    buttons.append({"target": action["target"], "text": action["text"]})

                elif action_type == "goto":
                    actions.append({"type": "goto", "target": action["target"]})

                elif action_type == "pln":
                    actions.append({"type": "pln", "text": action["text"]})

                elif action_type == "assign":
                    actions.append({"type": "assign", "key": action["key"], "value": action["value"]})

                elif action_type == "xbtn":
                    buttons.append({"text": action["text"], "target": action["target"], "actions": action["actions"]})
               
                elif action_type == "inv+":
                    process_inventory_action(state, f"inv+ {action['item']}")  # ✅ Добавляем предмет в инвентарь
                elif action_type == "inv-":
                    process_inventory_action(state, f"inv- {action['item']}")  # ✅ Удаляем предмет из инвентаря
                # Обработка действий с инвентарём
                if "inv_action" in action and action_type != "xbtn":
                    process_inventory_action(state, action["inv_action"])

    return buttons, actions

# Обработка инвентарных действий (Inv+ / Inv- / Invkill)
def process_inventory_action(state, action):
    print(f"🔎 Вызов process_inventory_action: action={action}")
    if not action:
        print(f"⚠️ Пустое значение инвентаря: {action}")
        return

    if action.startswith("inv+"):
        item = action[4:].strip()  # Отрезаем "inv+" и обрезаем пробелы
        if item and item not in state["inventory"]:
            state["inventory"].append(item)
            print(f"✅ Добавлен предмет в инвентарь: {item}")

    elif action.startswith("inv-"):
        item = action[4:].strip()  # Отрезаем "inv-" и обрезаем пробелы
        if item and item in state["inventory"]:
            state["inventory"].remove(item)
            print(f"✅ Удалён предмет из инвентаря: {item}")
    else:
        print(f"⚠️ Некорректный формат инвентаря: {action}")
 

def evaluate_condition(state, condition):
    # Сначала обрабатываем сложные операторы (>=, <=, !=), чтобы не ломать их при замене '='
    condition = condition.replace(">=", "⩾").replace("<=", "⩽").replace("!=", "≠")
    
    # Заменяем одиночный `=` на `==`
    condition = condition.replace("=", "==")

    # Восстанавливаем операторы обратно
    condition = condition.replace("⩾", ">=").replace("⩽", "<=").replace("≠", "!=")

    # Обрабатываем переменные, избегая чисел и составных названий предметов
    def replace_variables_safe(match):
        var_name = match.group(1)
        if var_name.isdigit():  # Если число, не заменяем
            return var_name
        return replace_variables(var_name, state)

    # Ищем переменные (характеристики или предметы) и заменяем на их значения
    condition = re.sub(r'\b([A-Za-zА-Яа-яёЁ0-9_]+(?:\s+[A-Za-zА-Яа-яёЁ0-9_]+)*)\b', replace_variables_safe, condition)

    # Восстанавливаем логические операторы после подстановки
    condition = condition.replace("&&", " and ").replace("||", " or ")
    try:
        result = eval(condition)
        print(f"helper |  {condition} result: {result}")
        return result  # Проверяем, истинно ли условие
    except Exception as e:
        print(f"helper | eval error: {e}")
        return False  # Если ошибка — условие не выполняется

# Функция для подстановки значений характеристик и проверки инвентаря
def replace_variables(var_name, state):
    print(f"helper | var_name : {var_name}")

    var_name_lower = var_name.lower()  # Приводим к нижнему регистру

    # Проверяем, является ли переменная характеристикой
    if var_name in state["characteristics"]:
        print(f"helper | its characteristic!")
        return str(state["characteristics"].get(var_name, {"value": 0})["value"])

    # Проверяем, есть ли предмет в инвентаре (без учета регистра)
    inventory_lower = [item.lower() for item in state["inventory"]]
    if var_name_lower in inventory_lower:
        print(f"helper | its in inventory!")
        return "True"

    # Если переменная не найдена, возвращаем "False" (предмета нет)
    print(f"helper | variable didn't found")
    return "False"

def replace_variables_in_text(state, text):
    def replace_match(match):
        key = match.group(1)
        value = state["characteristics"].get(key, {}).get("value", None)
        if value is not None:
            return str(value)
        return match.group(0)  # Если нет значения — оставляем шаблон как есть
    
    # Ищем шаблоны вида #M1$, #V1$ и заменяем их на значения из характеристик
    return re.sub(r'#([A-Za-z0-9_]+)\$', replace_match, text)


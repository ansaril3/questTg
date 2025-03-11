import random
import re

# ✅ Генерация случайного числа (например, RND6)
def roll_dice(expression):
    try:
        if expression.startswith("rnd"):
            dice_max = int(expression[3:])
            return random.randint(1, dice_max)
        return int(expression)
    except ValueError:
        print(f"⚠️ Ошибка в roll_dice: Неверный формат выражения {expression}")
        return 0

# ✅ Вычисление значения характеристики
def calculate_characteristic(expression, state):
    tokens = expression.split()
    total = 0

    for token in tokens:
        if token.startswith("rnd"):
            total += roll_dice(token)
        elif token in state["characteristics"]:
            total += state["characteristics"][token]["value"]
        elif token.lstrip("+-").isdigit():
            total += int(token)
        else:
            print(f"⚠️ Ошибка в calculate_characteristic: Некорректный токен '{token}'")

    return total

# ✅ Проверка условий и формирование действий (работает только с памятью)
def check_conditions(state, conditions):
    buttons = []
    actions = []

    for condition_block in conditions:
        condition = condition_block["condition"]
        actions_list = condition_block["actions"]
        print(f"helper | check_conditions | condition: {condition}")

        if evaluate_condition(state, condition):
            print("✅ Условие истинно")
            for action in actions_list:
                action_type = action["type"]
                print(f"✅ Выполняется действие: {action}")

                if action_type == "btn":
                    buttons.append({"target": action["target"], "text": action["text"]})

                elif action_type == "goto":
                    actions.append({"type": "goto", "target": action["target"]})

                elif action_type == "pln":
                    actions.append({"type": "pln", "text": action["text"]})

                elif action_type == "assign":
                    actions.append({"type": "assign", "key": action["key"], "value": action["value"]})

                elif action_type == "xbtn":
                    buttons.append({
                        "text": action["text"],
                        "target": action["target"],
                        "actions": action["actions"]
                    })
                
                # ✅ Убираем дублирование вызова process_inventory_action
                if action_type in ["inv+", "inv-"]:
                    process_inventory_action(state, f"{action_type} {action['item']}")

    return buttons, actions

# ✅ Обработка инвентарных действий напрямую через память
def process_inventory_action(state, action):
    if not action:
        print(f"⚠️ Пустое значение инвентаря: {action}")
        return

    if action.startswith("inv+"):
        item = action[4:].strip()
        if item and item not in state["inventory"]:
            state["inventory"].append(item)
            print(f"✅ Добавлен предмет в инвентарь: {item}")

    elif action.startswith("inv-"):
        item = action[4:].strip()
        if item in state["inventory"]:
            state["inventory"].remove(item)
            print(f"✅ Удалён предмет из инвентаря: {item}")
    else:
        print(f"⚠️ Некорректный формат инвентаря: {action}")

# ✅ Оценка условий (работает напрямую через стейт в памяти)

def evaluate_condition(state, condition):
    # ✅ Сначала обрабатываем сложные операторы (>=, <=, !=)
    condition = condition.replace(">=", "⩾").replace("<=", "⩽").replace("!=", "≠")

    # ✅ Заменяем одиночное "=" на "=="
    condition = condition.replace("=", "==")

    # ✅ Восстанавливаем операторы обратно
    condition = condition.replace("⩾", ">=").replace("⩽", "<=").replace("≠", "!=")

    # ✅ Логические операторы НЕ ТРОГАЕМ
    condition = condition.replace("&&", " and ").replace("||", " or ")

    # ✅ Список логических операторов
    logical_operators = {"and", "or", "not"}

    # ✅ Заменяем переменные на значения (исключая логические операторы)
    def replace_variables_safe(match):
        var_name = match.group(1)
        if var_name in logical_operators:
            return var_name  # Не заменяем логические операторы
        if var_name.isdigit():
            return var_name
        return replace_variables(var_name, state)

    # ✅ Заменяем переменные через регулярное выражение
    condition = re.sub(r'\b([A-Za-z0-9_]+)\b', replace_variables_safe, condition)

    try:
        # ✅ Ограничиваем eval только значениями из характеристик (для безопасности)
        local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
        result = eval(condition, {}, local_vars)
        print(f"✅ Условие: {condition} → {result}")
        return bool(result)
    except (SyntaxError, ValueError, NameError) as e:
        print(f"⚠️ Ошибка в evaluate_condition: {e}")
        return False

# ✅ Подстановка переменных (остается без изменений)
def replace_variables(var_name, state):
    var_name_lower = var_name.lower()

    # ✅ Проверяем в характеристиках
    if var_name_lower in state["characteristics"]:
        value = state["characteristics"][var_name_lower].get("value", 0)
        print(f"✅ Подстановка из характеристик: {var_name} = {value}")
        return str(value)

    # ✅ Проверяем в инвентаре (без учёта регистра)
    if var_name_lower in [item.lower() for item in state["inventory"]]:
        print(f"✅ Подстановка из инвентаря: {var_name} = True")
        return "True"

    print(f"⚠️ Переменная {var_name} не найдена")
    return "False"

# ✅ Подстановка переменных (работает только со стейтом в памяти)
def replace_variables(var_name, state):
    var_name_lower = var_name.lower()

    # ✅ Проверяем в характеристиках
    if var_name_lower in state["characteristics"]:
        value = state["characteristics"].get(var_name_lower, {}).get("value", 0)
        print(f"✅ Подстановка из характеристик: {var_name} = {value}")
        return str(value)

    # ✅ Проверяем в инвентаре (без учёта регистра)
    if var_name_lower in [item.lower() for item in state["inventory"]]:
        print(f"✅ Подстановка из инвентаря: {var_name} = True")
        return "True"

    print(f"⚠️ Переменная {var_name} не найдена")
    return "False"

# ✅ Подстановка переменных в текст напрямую через стейт в памяти
def replace_variables_in_text(state, text):
    # ✅ Приводим ключи характеристик к нижнему регистру
    state["characteristics"] = {k.lower(): v for k, v in state["characteristics"].items()}
    
    def replace_match(match):
        key = match.group(1).lower()
        if key in state["characteristics"]:
            value = state["characteristics"].get(key, {}).get("value")
            if value is not None:
                print(f"✅ Подстановка значения {key} → {value}")
                return str(value)
            else:
                print(f"⚠️ Значение для {key} отсутствует")
        return match.group(0)
    
    # ✅ Подставляем значения в текст
    processed_text = re.sub(r'#([A-Za-z0-9_]+)\$', replace_match, text, flags=re.IGNORECASE)
    
    print(f"✅ Обработанный текст: {processed_text}")
    return processed_text

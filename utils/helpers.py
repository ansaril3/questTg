import re

# ✅ Логические операторы
logical_operators = {"and", "or", "not"}

# ✅ Проверяем наличие операторов сравнения
def has_comparison_operators(condition):
    operators = {"==", "!=", ">=", "<=", ">", "<"}
    for operator in operators:
        if operator in condition:
            return True
    return False

def evaluate_condition(state, condition):
    # ✅ Если это простое имя без операторов сравнения — это предмет в инвентаре
    if not has_comparison_operators(condition) and not any(op in condition for op in logical_operators):
        print(f"✅ Преобразование условия в проверку инвентаря: {condition}")
        if " " in condition:
            condition = f"'{condition}' in state['inventory']"
        else:
            condition = f"'{condition.strip()}' in state['inventory']"

    # ✅ Сначала обрабатываем сложные операторы (>=, <=, !=)
    condition = condition.replace(">=", "⩾").replace("<=", "⩽").replace("!=", "≠")

    # ✅ Заменяем одиночное "=" на "=="
    condition = condition.replace("=", "==")

    # ✅ Восстанавливаем операторы обратно
    condition = condition.replace("⩾", ">=").replace("⩽", "<=").replace("≠", "!=")

    # ✅ Логические операторы НЕ ТРОГАЕМ
    condition = condition.replace("&&", " and ").replace("||", " or ")

    # ✅ Игнорируем строки в кавычках во время подстановки переменных
    pattern = r"(?<!')\b([A-Za-z0-9_а-яА-ЯЁё]+)\b(?!')"
    condition = re.sub(pattern, lambda m: replace_variables_safe(m, state), condition)

    result = False
    try:
        # ✅ Передаём состояние в eval
        local_vars = {
            k: v["value"] for k, v in state["characteristics"].items()
        }
        local_vars["state"] = state  # Добавляем state в eval-контекст
        result = eval(condition, {}, local_vars)
        print(f"✅ evaluate_condition: {condition} → {result}")
        return result
    except Exception as e:
        print(f"⚠️ Ошибка в evaluate_condition: {e}")
        return False

# ✅ Заменяем переменные на значения в выражении
def replace_variables_safe(match, state):
    var_name = match.group(1)
    
    # ✅ Игнорируем ключевые операторы и зарезервированные слова
    if var_name in logical_operators or var_name in {"in", "state", "inventory"}:
        return var_name
    
    if var_name.isdigit():
        return var_name
    
    return replace_variables(var_name, state)

# ✅ Подстановка переменных из инвентаря или характеристик
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

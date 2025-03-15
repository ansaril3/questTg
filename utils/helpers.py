import re

logical_operators = {"and", "or", "not"}
comparison_operators = {">", "<", ">=", "<=", "==", "!="}

def split_condition(condition):
    # Разбиваем по логическим операторам, сохраняя их в результирующем массиве
    parts = re.split(r'(\band\b|\bor\b|\bnot\b)', condition)
    return [part.strip() for part in parts if part.strip()]

def evaluate_condition(state, condition):
    print(f"🔎 Исходное условие: {condition}")
    
    parts = split_condition(condition)
    evaluated_parts = []
    
    for part in parts:
        if part in logical_operators:
            # Логический оператор добавляем напрямую
            evaluated_parts.append(part)
        elif has_comparison_operators(part):
            # Обрабатываем сравнения через eval()
            try:
                evaluated_part = re.sub(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', 
                                        lambda m: replace_variables_safe(m, state), 
                                        part)
                evaluated_parts.append(f"({evaluated_part})")
            except Exception as e:
                print(f"❌ Ошибка при обработке сравнения: {e}")
                return False
        else:
            # Это может быть имя предмета в инвентаре
            if part in state['inventory']:
                evaluated_parts.append("True")
            else:
                evaluated_parts.append("False")

    # Собираем финальное выражение
    final_condition = " ".join(evaluated_parts)
    print(f"⚙️ Финальное выражение для eval: {final_condition}")
    
    try:
        local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
        local_vars["state"] = state
        result = eval(final_condition, {}, local_vars)
        print(f"✅ Результат eval(): {result}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в evaluate_condition: {e}")
        return False

def has_comparison_operators(condition):
    return any(op in condition for op in comparison_operators)

def replace_variables_safe(match, state):
    var_name = match.group(1).strip()
    if var_name in logical_operators or var_name in {"in", "state", "inventory"}:
        return var_name
    
    if var_name.isdigit():
        return var_name

    return replace_variables(var_name, state)

def replace_variables(var_name, state):
    var_name_lower = var_name.lower()
    if var_name_lower in state["characteristics"]:
        value = state["characteristics"][var_name_lower].get("value", 0)
        print(f"✅ Подстановка из характеристик: {var_name} = {value}")
        return str(value)

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

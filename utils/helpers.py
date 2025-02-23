# Вспомогательные функции (рандом, условия)

import random

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

# Проверка условий из "condition"
def check_condition(state, condition):
    if not condition.startswith("IF "):
        return None

    try:
        parts = condition.split(" ")
        char_key, char_value = parts[1].split("=")
        char_value = int(char_value)
        
        if state["characteristics"].get(char_key, {"value": 0})["value"] == char_value:
            btn_target, btn_text = parts[-1].split(",")
            return btn_target.strip(), btn_text.strip()
    except Exception:
        return None

    return None

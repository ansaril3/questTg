import re

logical_operators = {"and", "or", "not"}
comparison_operators = {">", "<", ">=", "<=", "==", "!="}

def split_condition(condition):
    # Split by logical operators, keeping them in the resulting array
    parts = re.split(r'(\band\b|\bor\b|\bnot\b)', condition)
    return [part.strip() for part in parts if part.strip()]

def evaluate_condition(state, condition):
    print(f"🔎 Original condition: {condition}")
    
    condition = condition.replace("=>", ">=")
    condition = condition.replace("=<", "<=")
    
    # Заменяем одиночные "=" на "==", но не трогаем составные операторы (>=, <=, ==, !=)
    condition = re.sub(r'(?<!<|>|!)=(?!=)', '==', condition)
    
    parts = split_condition(condition)
    evaluated_parts = []
    
    for part in parts:
        if part in logical_operators:
            # Directly add logical operator
            evaluated_parts.append(part)
        elif has_comparison_operators(part):
            # Handle comparisons via eval()
            try:
                evaluated_part = re.sub(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', 
                                       lambda m: replace_variables_safe(m, state), 
                                       part)
                evaluated_parts.append(f"({evaluated_part})")
            except Exception as e:
                print(f"❌ Error while processing comparison: {e}")
                return False
        else:
            # This could be an item name in the inventory
            if part in state['inventory']:
                evaluated_parts.append("True")
            else:
                evaluated_parts.append("False")

    # Build the final expression
    final_condition = " ".join(evaluated_parts)
    print(f"⚙️ Final expression for eval: {final_condition}")
    
    try:
        local_vars = {k: v["value"] for k, v in state["characteristics"].items()}
        local_vars["state"] = state
        result = eval(final_condition, {}, local_vars)
        print(f"✅ Result of eval(): {result}")
        return result
    except Exception as e:
        print(f"❌ Error in evaluate_condition: {e}")
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
        print(f"✅ Substituting from characteristics: {var_name} = {value}")
        return str(value)

    if var_name_lower in [item.lower() for item in state["inventory"]]:
        print(f"✅ Substituting from inventory: {var_name} = True")
        return "True"

    print(f"⚠️ Variable {var_name} not found")
    return "False"

# ✅ Handling inventory actions directly via memory
def process_inventory_action(state, action):
    if not action:
        print(f"⚠️ Empty inventory value: {action}")
        return

    if action.startswith("inv+"):
        item = action[4:].strip()
        if item and item not in state["inventory"]:
            state["inventory"].append(item)
            print(f"✅ Item added to inventory: {item}")

    elif action.startswith("inv-"):
        item = action[4:].strip()
        if item in state["inventory"]:
            state["inventory"].remove(item)
            print(f"✅ Item removed from inventory: {item}")
    else:
        print(f"⚠️ Invalid inventory format: {action}")

# ✅ Substituting variables in text directly via state in memory
def replace_variables_in_text(state, text):
    # ✅ Convert characteristic keys to lowercase
    state["characteristics"] = {k.lower(): v for k, v in state["characteristics"].items()}
    
    def replace_match(match):
        key = match.group(1).lower()
        if key in state["characteristics"]:
            value = state["characteristics"].get(key, {}).get("value")
            if value is not None:
                print(f"✅ Substituting value {key} → {value}")
                return str(value)
            else:
                print(f"⚠️ Value for {key} is missing")
        return match.group(0)
    
    # ✅ Substitute values into text
    processed_text = re.sub(r'#([A-Za-z0-9_]+)\$', replace_match, text, flags=re.IGNORECASE)
    
    return processed_text

import json
import re

def read_file(input_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def split_into_chapters(content):
    # Разделяем по строкам, начинающимся с End
    chapters = re.split(r'\nEnd\b', content)
    # Убираем последний элемент, если он пустой
    if chapters[-1].strip() == "":
        chapters = chapters[:-1]
    return chapters

def collect_usable_items(chapters):
    usable_items = set()
    for chapter in chapters:
        lines = chapter.strip().split('\n')
        chapter_id = lines[0].strip(':')
        if chapter_id.lower().startswith('use_'):
            item_name = chapter_id[4:]
            usable_items.add(item_name.lower())
            print(f"usable:{item_name.lower()}!")
    return usable_items

def parse_action(line, usable_items, chapter_id, rest_data):
    line_lower = line.lower()
    if line.strip().startswith(';') or line.startswith('Pause'):
        return None  # Пропускаем комментарии и строки с Pause

    if line.lower().startswith('pln'):
        return {"type": "text", "value": line[4:].strip()}

    elif line.lower().startswith('btn'):
        parts = line[4:].split(',', 1)
        if len(parts) == 2:
            return {
                "type": "btn",
                "value": {
                    "text": parts[1].strip(),  # Текст кнопки сохраняем как есть
                    "target": parts[0].strip().lower()  # Приводим target к нижнему регистру
                }
            }
        else:
            rest_data.append(f"{chapter_id}: {line}")
            return {"type": "unknown", "value": line}

    elif line.lower().startswith('inv+') or line.lower().startswith('inv-'):
        return parse_inventory_action(line, usable_items, rest_data, chapter_id)

    elif line.lower().startswith('goto '):
        return {"type": "goto", "value": line[5:].strip().lower()}  # Приводим к нижнему регистру

    elif line.lower().startswith('if '):
        return parse_if_action(line, usable_items, chapter_id, rest_data)

    elif line_lower.startswith('xbtn'):
        return parse_xbtn_action(line, usable_items, chapter_id, rest_data)

    elif line_lower.startswith('image'):
        return parse_image_action(line)

    elif line_lower.startswith('end') and line.strip().lower() == 'end':
        # Обрабатываем End только если это отдельная строка
        return {"type": "end", "value": ""}

    elif '=' in line:
        return parse_assign_action(line)

    else:
        rest_data.append(f"{chapter_id}: {line}")
        return {"type": "unknown", "value": line}
    
def parse_inventory_action(line, usable_items, rest_data, chapter_id):
    line_lower = line.lower()
    if 'золотых монет' in line_lower:
        amount = re.findall(r'\d+', line)
        if amount:
            return {"type": "gold", "value": f"+{amount[0]}" if line_lower.startswith('inv+') else f"-{amount[0]}"}
    else:
        item = line[5:].strip().lower()  # Приводим к нижнему регистру
        print(f"check item ={item}!")
        if item in usable_items:
            item += "[usable]"
            print(f"usable!")
        return {"type": "inventory", "value": f"inv+{item}" if line_lower.startswith('inv+') else f"inv-{item}"}
    
def parse_actions(actions_list, usable_items, chapter_id, rest_data):
    parsed_actions = []
    for action in actions_list:
        parsed_action = parse_action(action, usable_items, chapter_id, rest_data)
        if parsed_action:
            parsed_actions.append(parsed_action)
    return parsed_actions

def parse_if_action(line, usable_items, chapter_id, rest_data):
    line_lower = line.lower()  # Приводим всю строку к нижнему регистру
    if "then" in line_lower:
        # Разделяем строку на условие и действия
        condition_part, actions_part = re.split(r'\bthen\b', line, flags=re.IGNORECASE, maxsplit=1)
        condition = condition_part[3:].strip().lower()  # Приводим условие к нижнему регистру

        # Разделяем действия на then и else
        if "else" in line_lower:
            then_actions, else_actions = re.split(r'\belse\b', actions_part, flags=re.IGNORECASE, maxsplit=1)
            else_actions = else_actions.strip()
        else:
            then_actions = actions_part.strip()
            else_actions = ""

        # Парсим действия для then
        then_actions_list = [action.strip() for action in re.split(r'\s*&\s*', then_actions)]
        parsed_then_actions = parse_actions(then_actions_list, usable_items, chapter_id, rest_data)

        # Парсим действия для else, если они есть
        parsed_else_actions = []
        if else_actions:
            else_actions_list = [action.strip() for action in re.split(r'\s*&\s*', else_actions)]
            parsed_else_actions = parse_actions(else_actions_list, usable_items, chapter_id, rest_data)

        # Создаем объект if с then и else действиями
        if_obj = {
            "type": "if",
            "value": {
                "condition": condition,
                "actions": parsed_then_actions
            }
        }

        if parsed_else_actions:
            if_obj["value"]["else_actions"] = parsed_else_actions

        return if_obj
    else:
        rest_data.append(f"{chapter_id}: {line}")
        return {"type": "unknown", "value": line}
  
def parse_xbtn_action(line, usable_items, chapter_id, rest_data):
    parts = [part.strip() for part in line[5:].split(',')]
    if len(parts) >= 2:
        target = parts[0].lower()
        actions_xbtn = parts[1:-1]
        button_text = parts[-1]

        parsed_xbtn_actions = []
        for action in actions_xbtn:
            action_lower = action.lower()
            if action_lower.startswith('inv+') or action_lower.startswith('inv-'):
                parsed_xbtn_actions.append(parse_inventory_action(action, usable_items, rest_data, chapter_id))
            elif '=' in action:
                key, value = action.split('=', 1)
                parsed_xbtn_actions.append({
                    "type": "assign",
                    "value": {
                        "key": key.strip().lower(),
                        "value": value.strip().lower(),
                        "name": ""
                    }
                })
            else:
                rest_data.append(f"{chapter_id}: {action}")
                parsed_xbtn_actions.append({
                    "type": "unknown",
                    "value": action
                })

        return {
            "type": "xbtn",
            "value": {
                "target": target,
                "text": button_text,
                "actions": parsed_xbtn_actions
            }
        }
    else:
        rest_data.append(f"{chapter_id}: {line}")
        return {"type": "unknown", "value": line}
    
def parse_image_action(line):
    image_value = line.split('=', 1)[1].strip().strip('"')
    image_value = image_value.replace('\\', '/')
    return {"type": "image", "value": image_value}

def parse_assign_action(line):
    if '=' in line:
        parts = line.split(';', 1)  # Разделяем по первой точке с запятой
        key_value = parts[0].strip().split('=', 1)  # Разделяем ключ и значение
        key = key_value[0].strip().lower()  # Приводим к нижнему регистру
        value = key_value[1].strip().lower() if len(key_value) > 1 else ""  # Приводим к нижнему регистру
        name = parts[1].strip() if len(parts) > 1 else ""  # Комментарий сохраняем как есть

        return {
            "type": "assign",
            "value": {
                "key": key,
                "value": value,
                "name": name
            }
        }
    else:
        return None  # Если нет '=', это не присваивание
    
def parse_chapter(chapter, usable_items, rest_data):
    lines = chapter.strip().split('\n')
    chapter_id = lines[0].strip(':').lower()  # Приводим к нижнему регистру
    actions = []

    for line in lines[1:]:
        # Игнорируем пустые строки
        if not line.strip():
            continue

        # Парсим действие
        action = parse_action(line, usable_items, chapter_id, rest_data)
        if action:
            actions.append(action)

    return chapter_id, actions

def parse_input_to_json(input_path):
    content = read_file(input_path)
    chapters = split_into_chapters(content)
    usable_items = collect_usable_items(chapters)
    json_data = {}
    rest_data = []

    for chapter in chapters:
        chapter_id, actions = parse_chapter(chapter, usable_items, rest_data)
        json_data[chapter_id] = actions

    return json_data, rest_data

def save_json_to_file(json_data, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

def save_rest_to_file(rest_data, rest_path):
    with open(rest_path, 'w', encoding='utf-8') as file:
        file.write("\n".join(rest_data))


if __name__ == "__main__":
    input_path = 'input.txt'
    output_path = 'output.json'
    rest_path = 'rest.txt'

    json_data, rest_data = parse_input_to_json(input_path)
    save_json_to_file(json_data, output_path)
    save_rest_to_file(rest_data, rest_path)
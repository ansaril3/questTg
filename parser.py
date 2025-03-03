import json
import re

def parse_input_to_json(input_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        content = file.read()

    chapters = content.split('End')[:-1]
    json_data = {}
    rest_data = []

    for chapter in chapters:
        lines = chapter.strip().split('\n')
        chapter_id = lines[0].strip(':')
        json_data[chapter_id] = {"text": "", "options": {}}

        for line in lines[1:]:
            if line.startswith('PLN'):
                json_data[chapter_id]["text"] += line[4:].strip() + " "
            elif line.startswith('BTN'):
                parts = line[4:].split(',', 1)  # Разделяем только по первой запятой
                if len(parts) == 2:
                    json_data[chapter_id]["options"][parts[1].strip()] = parts[0].strip()
                else:
                    rest_data.append(f"{chapter_id}: {line}")
            elif line.lower().startswith('inv+'):
                if 'Золотых монет' in line:
                    amount = re.findall(r'\d+', line)
                    if amount:
                        if "add_gold" not in json_data[chapter_id]:
                            json_data[chapter_id]["add_gold"] = 0
                        json_data[chapter_id]["add_gold"] += int(amount[0])
                else:
                    if "add_items" not in json_data[chapter_id]:
                        json_data[chapter_id]["add_items"] = []
                    json_data[chapter_id]["add_items"].append(line[5:].strip())
            elif line.lower().startswith('inv-'):
                if 'Золотых монет' in line:
                    amount = re.findall(r'\d+', line)
                    if amount:
                        if "remove_gold" not in json_data[chapter_id]:
                            json_data[chapter_id]["remove_gold"] = 0
                        json_data[chapter_id]["remove_gold"] += int(amount[0])
                else:
                    if "remove_items" not in json_data[chapter_id]:
                        json_data[chapter_id]["remove_items"] = []
                    json_data[chapter_id]["remove_items"].append(line[5:].strip())
            elif line.lower().startswith('goto '):
                goto_value = line[5:].strip()  # Извлекаем значение после "GoTo"
                json_data[chapter_id]["options"] = {"->": goto_value}
            elif line.lower().startswith('if '):  # Проверка на "if" в любом регистре
                if "conditions" not in json_data[chapter_id]:
                    json_data[chapter_id]["conditions"] = []
                json_data[chapter_id]["conditions"].append(line.strip())
            elif line.lower().startswith('image'):  # Обработка строк, начинающихся с "Image"
                image_value = line.split('=', 1)[1].strip().strip('"')  # Извлекаем значение после "=" и убираем кавычки
                image_value = image_value.replace('\\', '/')  # Заменяем двойные слеши на одинарные
                json_data[chapter_id]["image"] = image_value
            elif '=' in line:
                if "characteristics" not in json_data[chapter_id]:
                    json_data[chapter_id]["characteristics"] = {}
                parts = line.split(';')
                key_value = parts[0].strip().split('=')
                key = key_value[0].strip()
                value = key_value[1].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
                json_data[chapter_id]["characteristics"][key] = {
                    "value": value,
                    "name": name
                }
            else:
                rest_data.append(f"{chapter_id}: {line}")

        json_data[chapter_id]["text"] = json_data[chapter_id]["text"].strip()

        if "add_gold" in json_data[chapter_id] and json_data[chapter_id]["add_gold"] == 0:
            del json_data[chapter_id]["add_gold"]
        if "remove_gold" in json_data[chapter_id] and json_data[chapter_id]["remove_gold"] == 0:
            del json_data[chapter_id]["remove_gold"]
        if "add_items" in json_data[chapter_id] and not json_data[chapter_id]["add_items"]:
            del json_data[chapter_id]["add_items"]
        if "remove_items" in json_data[chapter_id] and not json_data[chapter_id]["remove_items"]:
            del json_data[chapter_id]["remove_items"]
        if "conditions" in json_data[chapter_id] and not json_data[chapter_id]["conditions"]:
            del json_data[chapter_id]["conditions"]
        if "characteristics" in json_data[chapter_id] and not json_data[chapter_id]["characteristics"]:
            del json_data[chapter_id]["characteristics"]

    return json_data, rest_data

def save_json_to_file(json_data, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

def save_rest_to_file(rest_data, rest_path):
    with open(rest_path, 'w', encoding='utf-8') as file:
        file.write("\n".join(rest_data))

input_path = 'input.txt'
output_path = 'output.json'
rest_path = 'rest.txt'

json_data, rest_data = parse_input_to_json(input_path)
save_json_to_file(json_data, output_path)
save_rest_to_file(rest_data, rest_path)
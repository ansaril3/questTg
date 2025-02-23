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
                parts = line[4:].split(',')
                if len(parts) == 2:
                    json_data[chapter_id]["options"][parts[1].strip()] = parts[0].strip()
                else:
                    rest_data.append(f"{chapter_id}: {line}")
            elif line.startswith('Inv+'):
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
            elif line.startswith('Inv-'):
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
            else:
                rest_data.append(f"{chapter_id}: {line}")

        json_data[chapter_id]["text"] = json_data[chapter_id]["text"].strip()

        # Удаляем пустые поля
        if "add_gold" in json_data[chapter_id] and json_data[chapter_id]["add_gold"] == 0:
            del json_data[chapter_id]["add_gold"]
        if "remove_gold" in json_data[chapter_id] and json_data[chapter_id]["remove_gold"] == 0:
            del json_data[chapter_id]["remove_gold"]
        if "add_items" in json_data[chapter_id] and not json_data[chapter_id]["add_items"]:
            del json_data[chapter_id]["add_items"]
        if "remove_items" in json_data[chapter_id] and not json_data[chapter_id]["remove_items"]:
            del json_data[chapter_id]["remove_items"]

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
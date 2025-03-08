import json
import re

def parse_input_to_json(input_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        content = file.read()

    chapters = content.split('End')[:-1]
    json_data = {}

    # Шаг 1: Собираем список используемых предметов
    usable_items = set()
    for chapter in chapters:
        lines = chapter.strip().split('\n')
        chapter_id = lines[0].strip(':')
        if chapter_id.lower().startswith('use_'):  # Если глава начинается с :Use_
            item_name = chapter_id[4:]  # Извлекаем название предмета (после :Use_)
            usable_items.add(item_name)

    # Шаг 2: Обрабатываем главы и добавляем метку [usable] к используемым предметам
    for chapter in chapters:
        lines = chapter.strip().split('\n')
        chapter_id = lines[0].strip(':')
        actions = []

        for line in lines[1:]:
            line_lower = line.lower()  # Приводим строку к нижнему регистру для проверки
            # Игнорируем строки, начинающиеся с ; (комментарии)
            if line.strip().startswith(';') or line.startswith('Pause'):
                continue  # Пропускаем такие строки

            # Обработка PLN (текст)
            elif line_lower.startswith('pln'):
                actions.append({
                    "type": "text",
                    "value": line[4:].strip()
                })

            # Обработка BTN (кнопка)
            elif line_lower.startswith('btn'):
                parts = line[4:].split(',', 1)  # Разделяем только по первой запятой
                if len(parts) == 2:
                    actions.append({
                        "type": "btn",
                        "value": {
                            "text": parts[1].strip(),
                            "target": parts[0].strip()
                        }
                    })
                else:
                    actions.append({
                        "type": "unknown",
                        "value": line
                    })

            # Обработка Inv+ (добавление в инвентарь)
            elif line_lower.startswith('inv+'):
                if 'золотых монет' in line_lower:  # Проверка на "золотых монет"
                    amount = re.findall(r'\d+', line)
                    if amount:
                        actions.append({
                            "type": "gold",
                            "value": f"+{amount[0]}"
                        })
                else:
                    item = line[5:].strip()
                    # Добавляем метку [usable], если предмет используется
                    if item in usable_items:
                        item += "[usable]"
                    actions.append({
                        "type": "inventory",
                        "value": f"inv+{item}"
                    })

            # Обработка Inv- (удаление из инвентаря)
            elif line_lower.startswith('inv-'):
                if 'золотых монет' in line_lower:  # Проверка на "золотых монет"
                    amount = re.findall(r'\d+', line)
                    if amount:
                        actions.append({
                            "type": "gold",
                            "value": f"-{amount[0]}"
                        })
                else:
                    item = line[5:].strip()
                    # Добавляем метку [usable], если предмет используется
                    if item in usable_items:
                        item += "[usable]"
                    actions.append({
                        "type": "inventory",
                        "value": f"inv-{item}"
                    })

            # Обработка Goto (переход)
            elif line_lower.startswith('goto '):
                goto_value = line[5:].strip()  # Извлекаем значение после "goto"
                actions.append({
                    "type": "goto",
                    "value": goto_value
                })

            # Обработка If (условие)
            elif line_lower.startswith('if '):
                if "then" in line_lower:
                    condition_part, actions_part = re.split(r'\bthen\b', line, flags=re.IGNORECASE, maxsplit=1)
                    condition = condition_part[3:].strip()  # Убираем "if" и лишние пробелы
                    actions_list = [action.strip() for action in re.split(r'\s*&\s*', actions_part)]  # Разделяем действия по "&"

                    parsed_actions = []
                    for action in actions_list:
                        action_lower = action.lower()  # Приводим действие к нижнему регистру
                        if action_lower.startswith('btn'):
                            parts = action[4:].split(',', 1)
                            if len(parts) == 2:
                                parsed_actions.append({
                                    "type": "btn",
                                    "value": {
                                        "text": parts[1].strip(),
                                        "target": parts[0].strip()
                                    }
                                })
                        elif action_lower.startswith('goto'):
                            target = action[5:].strip()
                            parsed_actions.append({
                                "type": "goto",
                                "value": target
                            })
                        elif action_lower.startswith('pln'):
                            text = action[4:].strip()
                            parsed_actions.append({
                                "type": "text",
                                "value": text
                            })
                        elif action_lower.startswith('inv+'):
                            item = action[5:].strip()
                            # Добавляем метку [usable], если предмет используется
                            if item in usable_items:
                                item += "[usable]"
                            parsed_actions.append({
                                "type": "inventory",
                                "value": f"inv+{item}"
                            })
                        elif action_lower.startswith('inv-'):
                            item = action[5:].strip()
                            # Добавляем метку [usable], если предмет используется
                            if item in usable_items:
                                item += "[usable]"
                            parsed_actions.append({
                                "type": "inventory",
                                "value": f"inv-{item}"
                            })
                        elif action_lower.startswith('xbtn'):
                            parts = [part.strip() for part in action[5:].split(',')]  # Разделяем по запятым
                            if len(parts) >= 2:
                                target = parts[0]  # Первая часть — целевое поле
                                actions_xbtn = parts[1:-1]  # Действия (все, кроме первого и последнего)
                                button_text = parts[-1]  # Последняя часть — текст кнопки

                                parsed_xbtn_actions = []
                                for act in actions_xbtn:
                                    act_lower = act.lower()  # Приводим действие к нижнему регистру
                                    if act_lower.startswith('inv+'):
                                        item = act[5:].strip()
                                        # Добавляем метку [usable], если предмет используется
                                        if item in usable_items:
                                            item += "[usable]"
                                        parsed_xbtn_actions.append({
                                            "type": "inventory",
                                            "value": f"inv+{item}"
                                        })
                                    elif act_lower.startswith('inv-'):
                                        item = act[5:].strip()
                                        # Добавляем метку [usable], если предмет используется
                                        if item in usable_items:
                                            item += "[usable]"
                                        parsed_xbtn_actions.append({
                                            "type": "inventory",
                                            "value": f"inv-{item}"
                                        })
                                    elif '=' in act:  # Обработка присваивания значений
                                        key, value = act.split('=', 1)
                                        parsed_xbtn_actions.append({
                                            "type": "assign",
                                            "value": {
                                                "key": key.strip(),
                                                "value": value.strip(),
                                                "name": ""
                                            }
                                        })
                                    else:
                                        parsed_xbtn_actions.append({
                                            "type": "unknown",
                                            "value": act
                                        })

                                parsed_actions.append({
                                    "type": "xbtn",
                                    "value": {
                                        "target": target,
                                        "text": button_text,
                                        "actions": parsed_xbtn_actions
                                    }
                                })
                        elif '=' in action:  # Обработка присваивания значений
                            key, value = action.split('=', 1)
                            parsed_actions.append({
                                "type": "assign",
                                "value": {
                                    "key": key.strip(),
                                    "value": value.strip(),
                                    "name": ""
                                }
                            })
                        else:
                            parsed_actions.append({
                                "type": "unknown",
                                "value": action
                            })

                    actions.append({
                        "type": "if",
                        "value": {
                            "condition": condition,
                            "actions": parsed_actions
                        }
                    })
                else:
                    actions.append({
                        "type": "unknown",
                        "value": line
                    })

            # Обработка XBTN (специальная кнопка)
            elif line_lower.startswith('xbtn'):
                parts = [part.strip() for part in line[5:].split(',')]  # Разделяем по запятым
                if len(parts) >= 2:
                    target = parts[0]  # Первая часть — целевое поле
                    actions_xbtn = parts[1:-1]  # Действия (все, кроме первого и последнего)
                    button_text = parts[-1]  # Последняя часть — текст кнопки

                    parsed_xbtn_actions = []
                    for action in actions_xbtn:
                        action_lower = action.lower()  # Приводим действие к нижнему регистру
                        if action_lower.startswith('inv+'):
                            item = action[5:].strip()
                            # Добавляем метку [usable], если предмет используется
                            if item in usable_items:
                                item += "[usable]"
                            parsed_xbtn_actions.append({
                                "type": "inventory",
                                "value": f"inv+{item}"
                            })
                        elif action_lower.startswith('inv-'):
                            item = action[5:].strip()
                            # Добавляем метку [usable], если предмет используется
                            if item in usable_items:
                                item += "[usable]"
                            parsed_xbtn_actions.append({
                                "type": "inventory",
                                "value": f"inv-{item}"
                            })
                        elif '=' in action:  # Обработка присваивания значений
                            key, value = action.split('=', 1)
                            parsed_xbtn_actions.append({
                                "type": "assign",
                                "value": {
                                    "key": key.strip(),
                                    "value": value.strip(),
                                    "name": ""
                                }
                            })
                        else:
                            parsed_xbtn_actions.append({
                                "type": "unknown",
                                "value": action
                            })

                    actions.append({
                        "type": "xbtn",
                        "value": {
                            "target": target,
                            "text": button_text,
                            "actions": parsed_xbtn_actions
                        }
                    })
                else:
                    actions.append({
                        "type": "unknown",
                        "value": line
                    })

            # Обработка Image (изображение)
            elif line_lower.startswith('image'):
                image_value = line.split('=', 1)[1].strip().strip('"')  # Извлекаем значение после "=" и убираем кавычки
                image_value = image_value.replace('\\', '/')  # Заменяем двойные слеши на одинарные
                actions.append({
                    "type": "image",
                    "value": image_value
                })

            # Обработка характеристик (assign)
            elif '=' in line:
                parts = line.split(';')
                key_value = parts[0].strip().split('=')
                key = key_value[0].strip()
                value = key_value[1].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
                actions.append({
                    "type": "assign",
                    "value": {
                        "key": key,
                        "value": value,
                        "name": name
                    }
                })

            # Обработка неизвестных строк
            else:
                actions.append({
                    "type": "unknown",
                    "value": line
                })

        json_data[chapter_id] = actions

    return json_data

def save_json_to_file(json_data, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

input_path = 'input.txt'
output_path = 'output.json'

json_data = parse_input_to_json(input_path)
save_json_to_file(json_data, output_path)
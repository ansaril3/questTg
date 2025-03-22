import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, config
from handlers.game_handler import handle_inline_choice, enter_instruction, handle_back, send_chapter, execute_action, save_game, load_game, handle_load_choice
from handlers.inventory_handler import show_inventory, handle_use_item
from utils.state_manager import get_state, save_state, load_specific_state, state_cache
import subprocess
from handlers.stats_handler import show_characteristics
from handlers.instruction_handler import send_instruction, handle_instruction_action

# Remove __pycache__
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ All __pycache__ folders have been deleted")

# Load test chapters
TEST_CHAPTERS_FILE = "tests/test_chapters.json"
print(f"📂 Opening JSON: {TEST_CHAPTERS_FILE}")
with open(TEST_CHAPTERS_FILE, "r", encoding="utf-8") as file:
    test_chapters = json.load(file)
print(f"✅ Chapters loaded: {list(test_chapters.keys())}")

# Mock Telegram API
bot.send_message = MagicMock()
bot.send_photo = MagicMock()


class TestBotActions(unittest.TestCase):
    def setUp(self):
        print(f"\n🚀🚀🚀🚀🚀🚀🚀 --------------------------Running test: {self._testMethodName}")
        self.chat_id = 123456789
        self.state = get_state(self.chat_id) or {
            "chapter": "test_start",
            "history": [],
            "options": {},
            "inventory": [],
            "gold": 100,
            "end_triggered": False,
            "characteristics": {}
        }
        save_state(self.chat_id)

    def simulate_inline(self, data):
        """Simulate pressing inline button (callback_query)"""
        return type("CallbackQuery", (), {
            "message": type("Message", (), {"chat": type("Chat", (), {"id": self.chat_id})}),
            "data": data
        })

    def test_xbtn(self):
        print("➡️ Running test_xbtn")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            action = {
                "type": "xbtn",
                "value": {
                    "text": "🔥 Secret Path",
                    "target": "test_secret",
                    "actions": [
                        {
                            "type": "assign",
                            "value": {
                                "key": "secret",
                                "value": "1",
                                "name": "Секрет"
                            }
                        }
                    ]
                }
            }
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["options"]["🔥 Secret Path"], "test_secret")
            self.assertNotIn("secret", self.state["characteristics"])

            # ✅ Simulate inline button click
            query = self.simulate_inline("🔥 Secret Path")
            handle_inline_choice(query)

            # ✅ Check updates
            self.assertEqual(self.state["characteristics"]["secret"]["value"], 1)
            self.assertEqual(self.state["chapter"], "test_secret")

        print("✅ Test passed!")

    def test_end(self):
        print("➡️ Running test_end")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            # ✅ Устанавливаем главу "test_end"
            self.state["chapter"] = "test_end"
            self.state["characteristics"] = {}

            # ✅ Вызываем send_chapter
            send_chapter(self.chat_id)

            # ✅ Проверяем, что скорость установилась в 10 и не изменилась на 20
            self.assertEqual(self.state["characteristics"]["speed"]["value"], 10, "Скорость должна быть 10!")

        print("✅ Test passed!")


    def test_btn(self):
        print("➡️ Running test_btn")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                action = {
                    "type": "btn",
                    "value": {
                        "text": "➡️ Продолжить",
                        "target": "test_end"
                    }
                }

                # ✅ Выполняем action
                execute_action(self.chat_id, self.state, action)

                # ✅ Проверяем, что inline-кнопка "➡️ Продолжить" появилась
                self.assertIn("➡️ Продолжить", self.state["options"])
                self.assertEqual(self.state["options"]["➡️ Продолжить"], "test_end")

                # ✅ Симулируем нажатие кнопки
                query = self.simulate_inline("➡️ Продолжить")
                handle_inline_choice(query)

                # ✅ Проверяем, что глава изменилась на test_end
                self.assertEqual(self.state["chapter"], "test_end")

        print("✅ Test passed!")

    def test_image(self):
        print("➡️ Running test_image")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_photo") as mock_send_photo:
                # ✅ Устанавливаем главу "test_image"
                self.state["chapter"] = "test_image"

                # ✅ Вызываем send_chapter
                send_chapter(self.chat_id)

                # ✅ Проверяем, что bot.send_photo был вызван с правильным изображением
                mock_send_photo.assert_called_once()
                actual_path = mock_send_photo.call_args[0][1]  # Второй аргумент (путь к изображению)
                expected_path = 'data/Images/3.JPG'
                self.assertTrue(actual_path.name.endswith(expected_path), 
                            f"Expected path to end with '{expected_path}', but got '{actual_path}'")

        print("✅ Test passed!")

    def test_return_goto(self):
        print("➡️ Running test_return")
        test_chapters = {
            "test_start": [
                {
                    "type": "text",
                    "value": "Начало теста"
                },
                {
                    "type": "gold",
                    "value": "20"
                }
            ],
            "test_return": [
                {
                    "type": "goto",
                    "value": "return"
                },
                {
                    "type": "gold",
                    "value": "40"
                }
            ]
        }
        with patch("handlers.game_handler.config.chapters", test_chapters):
            # ✅ Устанавливаем начальное состояние
            self.state["chapter"] = "test_start"
            self.state["history"].append("test_start")
            self.assertEqual(self.state["chapter"], "test_start")
            
            self.state["chapter"] = "test_return"
            self.assertEqual(self.state["chapter"], "test_return")

            # ✅ Выполняем action главы test_return
            action = test_chapters["test_return"][0]  # {'type': 'goto', 'value': 'return'}
            execute_action(self.chat_id, self.state, action)
            
            # ✅ Проверяем, что вернулись в test_start
            self.assertEqual(self.state["gold"], 20)
            self.assertEqual(self.state["chapter"], "test_start", "Глава должна вернуться в test_start!")
        
        print("✅ Test passed!")

    def test_gold(self):
        print("➡️ Running test_gold")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            self.state["gold"] = 0
            
            actions = test_chapters["test_secret"]
            for action in actions:
                execute_action(self.chat_id, self.state, action)
            
            self.assertEqual(self.state["gold"], 20)
        print("✅ Test passed!")

    def test_condition(self):
        print("➡️ Running test_condition")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                self.state["chapter"] = "test_start"
                send_chapter(self.chat_id)
                # ✅ Проверяем сообщение о несоответствии условия
                found = any(
                    "Condition met" in call.args[1] for call in mock_send.call_args_list
                )
                self.assertTrue(found, "Success")
            
        print("✅ Test passed!")

    def test_assign_characteristics(self):
        print("➡️ Running test_characteristics")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                action = test_chapters["test_end"][0]
                execute_action(self.chat_id, self.state, action)
            
                # ✅ Simulate Characteristics inline button
                query = self.simulate_inline("📊 Characteristics")
                show_characteristics(query)

                # ✅ Check message content
                expected_message = "📊 Your characteristics:\n🔹 Speed: 10\n"
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_args[1], expected_message)

        print("✅ Test passed!")


    def test_inventory(self):
        print("➡️ Running test_inventory")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                self.state["inventory"] = ["vial of magic potion[usable]"]
                self.state["options"]["🎒 Inventory"] = "🎒 Inventory"
                self.state["gold"] = 130

                # ✅ Simulate Inventory inline button
                query = self.simulate_inline("🎒 Inventory")
                show_inventory(query)

                # ✅ Check inventory message
                expected_message = (
                    "🎒 *Your inventory:*\n"
                    "💰 Gold: 130\n"
                    "🔹 vial of magic potion (✨ usable)\n"
                )
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_args[1].strip(), expected_message.strip())
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

                # ✅ Check use item button
                self.assertIn("Use vial of magic potion", self.state["options"])

                # ✅ Simulate using item
                query_use = self.simulate_inline("Use vial of magic potion")
                handle_use_item(query_use)

                # ✅ Check characteristic updated
                self.assertEqual(self.state["characteristics"]["speed"]["value"], 10)

        print("✅ Test passed!")

    def test_save_and_load(self):
        """✅ Test saving and loading game"""
        print("➡️ Running test_save_and_load")

        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:

                # ✅ Очистка состояния перед тестом
                self.state["chapter"] = "inv_check"
                self.state["inventory"] = []
                self.state["gold"] = 100
                self.state["history"] = []
                self.state["options"] = {}

                # ✅ Сохраняем игру
                query = self.simulate_inline("📥 Save game")
                save_game(query)

                # ✅ Проверяем сообщение о сохранении
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                self.assertEqual(actual_args[0], self.chat_id)
                self.assertIn("✅ Game saved:", actual_args[1])
                print(f"Game saved: {actual_args[1]}")
                print(f"Chapter : {self.state["chapter"]}")
                # ✅ Получаем название последнего сохранения
                save_file = f"{config.SAVES_DIR}/{self.chat_id}.json"
                with open(save_file, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
                    last_save_name = sorted(existing_data.keys(), reverse=True)[0]
                print(f"last_save_name={last_save_name}")

                # ✅ Меняем главу, чтобы проверить, изменится ли она после загрузки
                self.state["chapter"] = "test_end"
                self.assertEqual(self.state["chapter"], "test_end")

                # ✅ Эмулируем открытие меню загрузки
                query = self.simulate_inline("📤 Load game")
                load_game(query)

                # ✅ Проверяем сообщение о загрузке 
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                self.assertEqual(actual_args[0], self.chat_id)
                self.assertIn("🔄 *Select a save:*", actual_args[1])

                # ✅ Эмулируем выбор последнего сохранения
                load_specific_state(self.chat_id, last_save_name)
                self.state = state_cache[self.chat_id]
                # ✅ Проверяем, что глава сменилась обратно на `inv_check`
                self.assertEqual(self.state["chapter"], "inv_check", "Глава после загрузки должна быть 'inv_check'!")

        print("✅ Test successfully passed!")

    def test_instruction_navigation(self):
        print("➡️ Running test_instruction_navigation")
        with patch("handlers.game_handler.config.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                # ✅ Устанавливаем главу "test_game_ch"
                self.state["chapter"] = "test_game_ch"
                # ✅ Вызываем send_chapter
                send_chapter(self.chat_id)
                
                # ✅ Нажимаем на кнопку "📖 Инструкция"
                query = self.simulate_inline("📖 Instructions")
                enter_instruction(query)

                # ✅ Проверяем, что state["mode"] == "instruction"
                self.assertEqual(self.state["mode"], "instruction", "Mode должен быть 'instruction'!")

                # ✅ Нажимаем на кнопку "⬅️ Go back"
                query = self.simulate_inline("⬅️ Go back")
                handle_back(query)  # возвращаемся к главе "test_game_ch"

                # ✅ Проверяем, что отображается текст "this is game"
                # ✅ Проверяем, что state["mode"] == "instruction"
                self.assertEqual(self.state["mode"], "game", "Mode должен быть 'instruction'!")
        print("✅ Test passed!")

    

if __name__ == "__main__":
    unittest.main()

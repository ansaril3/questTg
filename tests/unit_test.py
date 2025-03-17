import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, CHAPTERS_FILE, COMMON_BUTTONS, SAVES_DIR
from handlers.game_handler import handle_inline_choice, send_chapter, execute_action, save_game, load_game, handle_load_choice
from handlers.inventory_handler import show_inventory, handle_use_item
from utils.state_manager import get_state, save_state, state_cache
import subprocess
from handlers.stats_handler import show_characteristics

# Remove __pycache__
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ All __pycache__ folders have been deleted")

# Load test chapters
CHAPTERS_FILE = "tests/test_chapters.json"
print(f"📂 Opening JSON: {CHAPTERS_FILE}")
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
    test_chapters = json.load(file)
print(f"✅ Chapters loaded: {list(test_chapters.keys())}")

# Mock Telegram API
bot.send_message = MagicMock()
bot.send_photo = MagicMock()


class TestBotActions(unittest.TestCase):
    def setUp(self):
        print(f"\n🚀 -----------Running test: {self._testMethodName}")
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
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][5]
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

    def test_return(self):
        print("➡️ Running test_return")
        with patch("handlers.game_handler.chapters", test_chapters):
            self.state["chapter"] = "test_secret"
            send_chapter(self.chat_id)
            self.state["history"].append("test_secret")
            self.state["chapter"] = "test_return"
            send_chapter(self.chat_id)

            # ✅ Simulate inline return button click
            query = self.simulate_inline("🔙 Back")
            handle_inline_choice(query)

            self.assertEqual(self.state["chapter"], "test_secret")
        print("✅ Test passed!")

    def test_characteristics(self):
        print("➡️ Running test_characteristics")
        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                self.state["characteristics"] = {"speed": {"value": 10}}
                self.state["chapter"] = "test_end"
                for button in COMMON_BUTTONS:
                    self.state["options"][button] = button
                send_chapter(self.chat_id)

                # ✅ Simulate Characteristics inline button
                query = self.simulate_inline("📊 Characteristics")
                show_characteristics(query)

                # ✅ Check message content
                expected_message = "📊 Your characteristics:\n🔹 Speed: 10\n"
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_args[1], expected_message)
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

        print("✅ Test passed!")

    def test_inventory(self):
        print("➡️ Running test_inventory")
        with patch("handlers.game_handler.chapters", test_chapters):
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
        """✅✅✅✅✅✅✅✅✅✅✅✅ Test saving and loading game"""
        print("➡️ Running test_save_and_load")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:

                # ✅ Clear state for a clean test
                self.state["chapter"] = "inv_check"
                self.state["inventory"] = []
                self.state["gold"] = 100
                self.state["history"] = []
                self.state["options"] = {}

                # ✅ Simulate game save
                save_game(type("Message", (), {"chat": type("Chat", (), {"id": self.chat_id})}))

                # ✅ Check penultimate message — save confirmation
                last_call = mock_send.call_args_list[-2]
                actual_args, actual_kwargs = last_call

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertIn("✅ *Game saved:*", actual_args[1])
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

                # ✅ Get save file name from state
                save_file = f"{SAVES_DIR}/{self.chat_id}.json"
                with open(save_file, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
                    last_save_name = sorted(existing_data.keys(), reverse=True)[0]

                # ✅ Change chapter to check if it changes after load
                self.state["chapter"] = "test_end"
                self.assertEqual(self.state["chapter"], "test_end")

                # ✅ Simulate opening load menu
                load_game(type("Message", (), {"chat": type("Chat", (), {"id": self.chat_id})}))

                # ✅ Checking the output of the save menu (last call)
                last_call = mock_send.call_args_list[-1]
                actual_args, actual_kwargs = last_call
                print(f"----- saves: {actual_args[1]}")

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertIn("🔄 *Select a save:*", actual_args[1])
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

                # ✅ Check that inline keyboard is present
                reply_markup = actual_kwargs.get("reply_markup")
                self.assertIsNotNone(reply_markup, "❌ No inline keyboard found")
                self.assertTrue(hasattr(reply_markup, "inline_keyboard"), "❌ reply_markup has no inline_keyboard")

                # ✅ Check that there is at least one save button
                buttons = reply_markup.inline_keyboard
                self.assertGreater(len(buttons), 0, "❌ No buttons found in inline keyboard")
                print(f"✅ Inline buttons for saves: {buttons}")

                # ✅ Simulate selecting the first save (callback query imitation)
                # Assuming buttons are formatted like [{'text': 'Save 1 (timestamp)', 'callback_data': 'load:timestamp'}]
                first_button = buttons[0][0]  # First row, first button
                callback_data = first_button.callback_data
                self.assertTrue(callback_data.startswith("load:"), "❌ Callback data does not start with 'load:'")

                # ✅ Now simulate CallbackQuery with this callback_data
                load_message = type(
                    "CallbackQuery",
                    (),
                    {"message": type("Message", (), {"chat": type("Chat", (), {"id": self.chat_id})}),
                    "data": callback_data}
                )
                handle_load_choice(load_message)

                # ✅ 🔥 UPDATE LOCAL STATE AFTER LOADING!
                self.state = state_cache[self.chat_id]

                # ✅ Check that the chapter switched back to 'inv_check'
                self.assertEqual(self.state["chapter"], "inv_check")

        print("✅ Test successfully passed!")


if __name__ == "__main__":
    unittest.main()

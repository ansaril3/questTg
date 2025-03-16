import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, CHAPTERS_FILE, COMMON_BUTTONS, SAVES_DIR
from handlers.game_handler import handle_choice, send_chapter, execute_action, save_game, load_game, handle_load_choice
from handlers.inventory_handler import show_inventory, handle_use_item
from utils.state_manager import get_state, save_state, state_cache
import subprocess
from handlers.stats_handler import show_characteristics

# Remove all __pycache__ folders
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ All __pycache__ folders have been deleted")

# Log when opening JSON
print(f"📂 Opening JSON: {CHAPTERS_FILE}")
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
    test_chapters = json.load(file)
print(f"✅ Chapters loaded from JSON: {list(test_chapters.keys())}")

# Mock Telegram API
bot.send_message = MagicMock()
bot.send_photo = MagicMock()

class TestBotActions(unittest.TestCase):
    def setUp(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Creating test state"""
        # Log test call
        print(f"\n🚀 Running test: {self._testMethodName}")

        self.chat_id = 123456789
        self.state = get_state(self.chat_id)

        if not self.state:
            self.state = {
                "chapter": "test_start",
                "history": [],
                "options": {},
                "inventory": [],
                "gold": 100,
                "end_triggered": False,
                "characteristics": {}
            }
            save_state(self.chat_id)

    def test_assign(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test assign action"""
        print("➡️ Running test_assign")

        # ✅ Mock chapters with test data
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][1]
            execute_action(self.chat_id, self.state, action)

        self.assertEqual(self.state["characteristics"]["strength"]["value"], 10)

    def test_gold(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test gold action"""
        print("➡️ Running test_gold")

        # ✅ Mock chapters with test data
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][2]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 100)

            action = test_chapters["test_secret"][1]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 120)  # +20 from test_secret

            action = {"type": "gold", "value": "-10"}
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 110)  # 120 - 10

    def test_if_condition_true(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test if condition when true"""
        print("➡️ Running test_if_condition_true")

        self.state["characteristics"]["strength"] = {"value": 10}
        self.state["inventory"] = ["sword"]
        # ✅ Mock chapters with test data
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][3]
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                execute_action(self.chat_id, self.state, action)
                mock_send.assert_called_with(self.chat_id, "Condition met")

    def test_if_condition_false(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test if condition when false"""
        print("➡️ Running test_if_condition_false")

        self.state["characteristics"]["strength"] = {"value": 55}

        # ✅ Mock chapters with test data
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][3]
            # ✅ Mock send_message method from handlers.game_handler
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                execute_action(self.chat_id, self.state, action)
                mock_send.assert_called_with(self.chat_id, "Condition not met")


    def test_xbtn(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test xbtn action and nested actions"""
        print("➡️ Running test_xbtn")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][5]
            execute_action(self.chat_id, self.state, action)

            # ✅ Check that the button was added to options
            self.assertEqual(self.state["options"]["🔥 Secret Path"], "test_secret")
            
            # ✅ Check that the characteristic secret has NOT been initialized yet
            self.assertNotIn("secret", self.state["characteristics"])

            # ✅ Simulate button click
            message = type(
                "Message", 
                (), 
                {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🔥 Secret Path"}
            )
            handle_choice(message)

            # ✅ Check that the nested action (assign) was executed
            self.assertEqual(self.state["characteristics"]["secret"]["value"], 1)

            # ✅ Check that the chapter changed to "test_secret"
            self.assertEqual(self.state["chapter"], "test_secret")

        print("✅ Test passed!")

    def test_goto(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test goto action"""
        print("➡️ Running test_goto")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][6]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["chapter"], "test_secret")

    def test_end(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test end action"""
        print("➡️ Running test_end")

        # ✅ Mock chapters with test data
        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                with patch("handlers.game_handler.bot.send_photo") as mock_send_photo:
                    # ✅ Set chapter and call send_chapter()
                    self.state["chapter"] = "test_end"
                    send_chapter(self.chat_id)  

                    # ✅ Check that the first action (assign) worked
                    self.assertEqual(self.state["characteristics"]["speed"]["value"], 10)

                    # ✅ Check final speed value (should not change)
                    self.assertEqual(self.state["characteristics"]["speed"]["value"], 10)

        print("✅ Test passed!")

    def test_return(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test return to previous chapter"""
        print("➡️ Running test_return")

        with patch("handlers.game_handler.chapters", test_chapters):
            # ✅ Set chapter to "test_secret"
            self.state["chapter"] = "test_secret"
            send_chapter(self.chat_id)

            # ✅ Save history state
            self.state["history"].append("test_secret")

            # ✅ Change chapter to "test_return"
            self.state["chapter"] = "test_return"
            send_chapter(self.chat_id)

            # ✅ Success condition: we are back at "test_secret"
            self.assertEqual(self.state["chapter"], "test_secret")

        print("✅ Test passed!")

    def test_image(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test image sending"""
        print("➡️ Running test_image")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_photo") as mock_send_photo:
                # ✅ Set chapter and call send_photo
                self.state["chapter"] = "test_image"
                send_chapter(self.chat_id)

                # ✅ Check that send_photo was called with the correct path
                mock_send_photo.assert_called_once()

                # ✅ Check call parameters
                args, _ = mock_send_photo.call_args
                file_path = args[1].name if len(args) > 1 else None
                self.assertEqual(file_path, "data/Images/3.JPG")

        print("✅ Test passed!")

    def test_characteristics(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test characteristics display on 📊 Characteristics button"""
        print("➡️ Running test_characteristics")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                self.state["characteristics"] = {}
                # ✅ Set initial chapter
                self.state["chapter"] = "test_end"

                # ✅ Add all buttons from COMMON_BUTTONS to state["options"]
                for button in COMMON_BUTTONS:
                    self.state["options"][button] = button

                send_chapter(self.chat_id)

                # ✅ Simulate press of Characteristics button
                message = type(
                    "Message", 
                    (), 
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "📊 Characteristics"}
                )
                show_characteristics(message)

                # ✅ Check the penultimate call (message with characteristics)
                expected_message = "📊 Your characteristics:\n🔹 Speed: 10\n"
                last_call = mock_send.call_args_list[-2]  # Penultimate call
                actual_args, actual_kwargs = last_call

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_args[1], expected_message)
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

        print("✅ Test passed!")


    def test_inventory(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test inventory functionality"""
        print("➡️ Running test_inventory")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                
                # ✅ Clear inventory and gold before test
                self.state["inventory"] = []
                self.state["options"] = {}
                self.state["gold"] = 130

                # ✅ Set initial chapter
                self.state["chapter"] = "inv_check"

                # ✅ Pass chapter to bot
                send_chapter(self.chat_id)
                self.state["options"]["🎒 Inventory"] = "🎒 Inventory"

                # ✅ Check that item was added to inventory
                self.assertIn("vial of magic potion[usable]", self.state["inventory"])

                # ✅ Check that the button is displayed in state["options"]
                self.assertIn("🎒 Inventory", self.state["options"])

                # ✅ Press "🎒 Inventory" button
                message = type(
                    "Message",
                    (),
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🎒 Inventory"}
                )
                show_inventory(message)

                # ✅ Check penultimate call (inventory message)
                expected_message = (
                    "🎒 *Your inventory:*\n"
                    "💰 Gold: 130\n"  
                    "🔹 vial of magic potion (✨ usable)\n"
                )
                last_call = mock_send.call_args_list[-2]  # Penultimate call (without dots)
                actual_args, actual_kwargs = last_call

                # 🔥 Remove unnecessary newlines from both sides
                actual_message = actual_args[1].strip()
                expected_message = expected_message.strip()

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_message, expected_message)
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

                # ✅ Check that the item use button was added to the interface
                self.assertIn("Use vial of magic potion", self.state["options"])

                # ✅ Press "Use vial of magic potion" button
                use_message = type(
                    "Message",
                    (),
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "Use vial of magic potion"}
                )
                handle_use_item(use_message)

                # ✅ Check that chapter changed to "use_vial of magic potion"
                self.assertEqual(self.state["chapter"], "use_vial of magic potion")

        print("✅ Test passed!")


    def test_save_and_load(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Test saving and loading game"""
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

                # ✅ Check that the chapter indeed changed
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

                # ✅ Simulate selecting the first save with an exact date
                load_message = type(
                    "Message",
                    (),
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": f"Load 1 ({last_save_name})"}
                )
                handle_load_choice(load_message)

                # ✅ 🔥 UPDATE LOCAL STATE AFTER LOADING!
                self.state = state_cache[self.chat_id]

                # ✅ Check that the chapter switched to `inv_check`
                self.assertEqual(self.state["chapter"], "inv_check")

        print("✅ Test successfully passed!")



if __name__ == "__main__":
    unittest.main()
                # ✅ Check saved games menu output

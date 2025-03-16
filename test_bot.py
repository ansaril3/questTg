import unittest
import json, subprocess
from unittest.mock import MagicMock, patch
from config import TOKEN, CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter
from utils.state_manager import load_state, save_state, state_cache
import telebot
import sys
from contextlib import redirect_stdout, redirect_stderr

# Remove all __pycache__ folders
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ All __pycache__ folders have been deleted")

# Load chapters
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
    chapters = json.load(file)
    print(f"📖 Loaded {len(chapters)} chapters from {CHAPTERS_FILE}")

# Create the bot (disable real Telegram API)
bot = telebot.TeleBot(TOKEN)

# Globally mock all Telegram message sending functions
bot.send_message = MagicMock()
bot.send_photo = MagicMock()
bot.send_document = MagicMock()
bot.send_video = MagicMock()
bot.send_audio = MagicMock()


class TestBotSequential(unittest.TestCase):
    """Test for Telegram bot: sequentially go through all chapters"""

    def setUp(self):
        """Initialize data for the test"""
        self.chat_id = 123456789  # Test ID
        self.errors = []  # List of errors

    def send_message_and_check(self, message_text, current_chapter):
        """Simulate button press and check"""
        message = type(
            "Message",
            (),
            {"chat": type("Chat", (), {"id": self.chat_id}), "text": message_text},
        )
        try:
            with patch("telebot.TeleBot.send_message", new=MagicMock()), \
                 patch("telebot.TeleBot.send_photo", new=MagicMock()), \
                 patch("telebot.TeleBot.send_document", new=MagicMock()), \
                 patch("telebot.TeleBot.send_video", new=MagicMock()), \
                 patch("telebot.TeleBot.send_audio", new=MagicMock()):
                handle_choice(message)  # Simulate the press
            return True
        except Exception as e:
            error_msg = f"❌ Error in chapter '{current_chapter}' when pressing '{message_text}': {e}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def extract_options_from_chapter(self, chapter_key):
        """Extract all buttons from a chapter"""
        chapter = chapters.get(chapter_key.lower(), [])
        options = {}
        for action in chapter:
            action_type = action["type"]
            value = action["value"]
            if action_type in ("btn", "xbtn"):  # Only buttons
                options[value["text"]] = value["target"].lower()
        return options

    def test_chapters_sequentially(self):
        """Main test: go through all chapters in order"""
        all_chapters = list(chapters.keys())
        print(f"🚀 Starting test for {len(all_chapters)} chapters in order...")

        for chapter_key in all_chapters:
            print(f"\n📝 Testing chapter: {chapter_key}")

            # Set the current chapter state
            state = {
                "chapter": chapter_key.lower(),
                "history": [],
                "options": {},
                "end_triggered": False,
                "inventory": [
            "фиал волшебного питья[usable]",
            "кольчуга",
            "меч"
        ],
        "gold": 5,
        "characteristics": {
            "m": {
                "name": "Мастерство: начальный уровень",
                "value": 11
            },
            "m1": {
                "name": "Мастерство: текущий уровень",
                "value": 11
            },
            "v": {
                "name": "Выносливость: начальный уровень",
                "value": 16
            },
            "v1": {
                "name": "Выносливость: текущий уровень",
                "value": 16
            },
            "u": {
                "name": "удачливость: начальный уровень",
                "value": 9
            },
            "u1": {
                "name": "Удачливость: Текущий уровень",
                "value": 9
            },
            "kps": {
                "name": "",
                "value": -1
            },
            "kpg": {
                "name": "",
                "value": -1
            },
            "kpp": {
                "name": "",
                "value": -1
            },
            "og": {
                "name": "",
                "value": -1
            }
            },
                "saves":[]
            } 
            state_cache[self.chat_id] = state  # Кладем в кэш
            save_state(self.chat_id)  # Сохраняем

            # Пробуем отправить главу
            try:
                with patch("telebot.TeleBot.send_message", new=MagicMock()), \
                     patch("telebot.TeleBot.send_photo", new=MagicMock()), \
                     patch("telebot.TeleBot.send_document", new=MagicMock()), \
                     patch("telebot.TeleBot.send_video", new=MagicMock()), \
                     patch("telebot.TeleBot.send_audio", new=MagicMock()):
                    send_chapter(self.chat_id)  # Simulate sending the chapter
            except Exception as e:
                error_msg = f"❌ Error displaying chapter '{chapter_key}': {e}"
                print(error_msg)
                self.errors.append(error_msg)
                continue  # Move to next chapter

            # Extract buttons and try pressing them
            options = self.extract_options_from_chapter(chapter_key)
            for button_text, target_chapter in options.items():
                print(f"➡️ Checking button: '{button_text}' (→ {target_chapter})")
                self.send_message_and_check(button_text, chapter_key)

        # ✅ Report
        print("\n📊 TEST COMPLETED")
        if self.errors:
            print(f"\n❗️ Found {len(self.errors)} errors:")
            for error in self.errors:
                print(error)
            self.fail(f"Found {len(self.errors)} errors. See above.")
        else:
            print("🎉 All chapters passed without errors!")


if __name__ == "__main__":
    with open('test.log', 'w') as f_log:
        with redirect_stdout(f_log), redirect_stderr(f_log):
            unittest.main()

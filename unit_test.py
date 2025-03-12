import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, TEST_CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter, execute_action
from utils.state_manager import get_state, save_state
import subprocess

# Удаляем все папки __pycache__ с помощью системной команды
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ Все папки __pycache__ удалены")

# Лог при открытии JSON
print(f"📂 Открываем JSON: {TEST_CHAPTERS_FILE}")
with open(TEST_CHAPTERS_FILE, "r", encoding="utf-8") as file:
    test_chapters = json.load(file)
print(f"✅ Загружены главы из JSON: {list(test_chapters.keys())}")

# Подменяем Telegram API
bot.send_message = MagicMock()
bot.send_photo = MagicMock()

class TestBotActions(unittest.TestCase):
    def setUp(self):
        """Создание тестового состояния"""
        # Лог вызова теста
        print(f"\n🚀 Выполняется тест: {self._testMethodName}")

        self.chat_id = 123456789
        self.state = get_state(self.chat_id)

        if not self.state:
            self.state = {
                "chapter": "test_start",
                "history": [],
                "options": {},
                "inventory": [],
                "gold": 100,   # ✅ Устанавливаем начальное значение золота
                "end_triggered": False
            }
            save_state(self.chat_id)

    def test_assign(self):
        """Тест действия assign"""
        print("➡️ Запуск test_assign")
        action = test_chapters["test_start"][1]
        execute_action(self.chat_id, self.state, action)
        self.assertEqual(self.state["characteristics"]["strength"]["value"], 10)


    def test_btn(self):
        """Тест действия btn"""
        print("➡️ Запуск test_btn")
        action = test_chapters["test_start"][4]
        execute_action(self.chat_id, self.state, action)
        self.assertEqual(self.state["options"]["➡️ Продолжить"], "test_end")

    

if __name__ == "__main__":
    unittest.main()

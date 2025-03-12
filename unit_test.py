import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter, execute_action
from utils.state_manager import get_state, save_state
import subprocess

# Удаляем все папки __pycache__
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ Все папки __pycache__ удалены")

# Лог при открытии JSON
print(f"📂 Открываем JSON: {CHAPTERS_FILE}")
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
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
                "gold": 100,
                "end_triggered": False,
                "characteristics": {}
            }
            save_state(self.chat_id)

    def test_assign(self):
        """Тест действия assign"""
        print("➡️ Запуск test_assign")

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][1]
            execute_action(self.chat_id, self.state, action)

        self.assertEqual(self.state["characteristics"]["strength"]["value"], 10)

    def test_gold(self):
        """Тест действия gold"""
        print("➡️ Запуск test_gold")

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][2]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 100)

            action = test_chapters["test_secret"][1]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 120)  # +20 из test_secret

            action = {"type": "gold", "value": "-10"}
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["gold"], 110)  # 120 - 10

    def test_if_condition_true(self):
        """Тест выполнения if при истинном условии"""
        print("➡️ Запуск test_if_condition_true")

        self.state["characteristics"]["strength"] = {"value": 10}

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][3]
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                execute_action(self.chat_id, self.state, action)
                mock_send.assert_called_with(self.chat_id, "Условие выполнено")

    def test_if_condition_false(self):
        """Тест выполнения if при ложном условии"""
        print("➡️ Запуск test_if_condition_false")

        self.state["characteristics"]["strength"] = {"value": 55}

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][3]
            # ✅ Патчим метод send_message из handlers.game_handler
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                execute_action(self.chat_id, self.state, action)
                mock_send.assert_called_with(self.chat_id, "Условие не выполнено")


    def test_xbtn(self):
        """Тест действия xbtn и выполнения вложенных действий"""
        print("➡️ Запуск test_xbtn")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][5]
            execute_action(self.chat_id, self.state, action)

            self.assertEqual(self.state["options"]["🔥 Тайный путь"], "test_secret")

            message = type(
                "Message", 
                (), 
                {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🔥 Тайный путь"}
            )
            handle_choice(message)

            # ✅ Проверяем выполнение вложенного действия (assign)
            self.assertEqual(self.state["characteristics"]["secret"]["value"], 1)

    def test_goto(self):
        """Тест действия goto"""
        print("➡️ Запуск test_goto")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][6]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["chapter"], "test_secret")

    def test_end(self):
        """Тест выполнения end"""
        print("➡️ Запуск test_end")

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                with patch("handlers.game_handler.bot.send_photo") as mock_send_photo:
                    # ✅ Устанавливаем главу и вызываем send_chapter()
                    self.state["chapter"] = "test_end"
                    send_chapter(self.chat_id)  

                    # ✅ Проверяем, что первое действие (assign) сработало
                    self.assertEqual(self.state["characteristics"]["speed"]["value"], 10)

                    # ✅ Проверяем финальное значение speed (не должно измениться)
                    self.assertEqual(self.state["characteristics"]["speed"]["value"], 10)

        print("✅ Тест успешно пройден!")


if __name__ == "__main__":
    unittest.main()

import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, TEST_CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter, execute_action
from utils.state_manager import get_state, save_state

# Загружаем тестовые главы из JSON
with open(TEST_CHAPTERS_FILE, "r", encoding="utf-8") as file:
    test_chapters = json.load(file)

# Подменяем Telegram API
bot.send_message = MagicMock()
bot.send_photo = MagicMock()

class TestBotActions(unittest.TestCase):
    def setUp(self):
        """Создание тестового состояния"""
        self.chat_id = 123456789
        self.state = get_state(self.chat_id)
        self.state["chapter"] = "test_start"
        self.state["history"] = []
        self.state["options"] = {}
        self.state["characteristics"] = {"strength": {"value": 10}, "gold": {"value": 100}}
        save_state(self.chat_id)

    def test_assign(self):
        """Тест действия assign"""
        action = test_chapters["test_start"][1]  # Берём assign из JSON
        execute_action(self.chat_id, self.state, action)
        self.assertEqual(self.state["characteristics"]["strength"]["value"], 10)

    def test_if_condition_true(self):
        """Тест выполнения if при истинном сложном условии (and)"""
        action = test_chapters["test_start"][2]
        with patch("telebot.TeleBot.send_message") as mock_send:
            execute_action(self.chat_id, self.state, action)
            mock_send.assert_called_with(self.chat_id, "Условие выполнено")

    def test_if_condition_false(self):
        """Тест выполнения if при ложном сложном условии (and)"""
        self.state["characteristics"]["gold"]["value"] = 20
        action = test_chapters["test_start"][2]
        with patch("telebot.TeleBot.send_message") as mock_send:
            execute_action(self.chat_id, self.state, action)
            mock_send.assert_called_with(self.chat_id, "Условие не выполнено")

    def test_btn(self):
        """Тест действия btn"""
        action = test_chapters["test_start"][3]
        execute_action(self.chat_id, self.state, action)
        self.assertEqual(self.state["options"]["➡️ Продолжить"], "test_end")

    def test_xbtn(self):
        """Тест действия xbtn и выполнения его вложенных действий"""
        action = test_chapters["test_start"][4]
        execute_action(self.chat_id, self.state, action)

        # Проверяем, что кнопка добавлена в опции
        self.assertEqual(self.state["options"]["🔥 Тайный путь"], "test_secret")

        # Имитация нажатия кнопки
        message = type(
            "Message", 
            (), 
            {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🔥 Тайный путь"}
        )
        handle_choice(message)

        # Проверяем, что выполнены вложенные действия
        self.assertEqual(self.state["characteristics"]["secret"]["value"], 1)
        self.assertEqual(self.state["chapter"], "test_secret")

    def test_goto(self):
        """Тест действия goto"""
        action = test_chapters["test_start"][5]
        execute_action(self.chat_id, self.state, action)
        self.assertEqual(self.state["chapter"], "test_end")

    def test_end(self):
        """Тест действия end"""
        action = test_chapters["test_end"][1]
        execute_action(self.chat_id, self.state, action)
        self.assertTrue(self.state["end_triggered"])

    def test_image(self):
        """Тест действия image (файл должен существовать)"""
        action = {"type": "image", "value": "/Images/1.JPG"}
        with patch("telebot.TeleBot.send_photo") as mock_send:
            execute_action(self.chat_id, self.state, action)
            mock_send.assert_called()

    def test_start_chapter(self):
        """Тест начала главы"""
        with patch("telebot.TeleBot.send_message") as mock_send:
            send_chapter(self.chat_id)
            mock_send.assert_any_call(self.chat_id, "Начало игры")

    def test_invalid_choice(self):
        """Тест обработки неверного выбора"""
        message = type(
            "Message", 
            (), 
            {"chat": type("Chat", (), {"id": self.chat_id}), "text": "Неверный выбор"}
        )
        with patch("telebot.TeleBot.send_message") as mock_send:
            handle_choice(message)
            mock_send.assert_called_with(self.chat_id, "⚠️ Некорректный выбор. Попробуйте снова.")

if __name__ == "__main__":
    unittest.main()

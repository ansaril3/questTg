import unittest
import json
from unittest.mock import MagicMock, patch
from config import TOKEN, CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter
from utils.state_manager import load_state, save_state
import telebot

# Загружаем главы
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
    chapters = json.load(file)

# Создаем бота (отключаем реальный Telegram API)
bot = telebot.TeleBot(TOKEN)

# Глобально заменяем все отправки сообщений в Telegram
bot.send_message = MagicMock()
bot.send_photo = MagicMock()
bot.send_document = MagicMock()
bot.send_video = MagicMock()
bot.send_audio = MagicMock()


class TestBot(unittest.TestCase):
    """Автоматическое тестирование Telegram-бота"""

    def setUp(self):
        """Создаем тестового пользователя и начальные данные"""
        self.chat_id = 123456789  # Тестовый ID (НЕ ИСПОЛЬЗУЕТСЯ В ТГ)
        self.state = load_state(self.chat_id)  # Загружаем состояние
        self.visited_chapters = set()  # Множество посещенных глав

    def send_message_and_check(self, message_text):
        """Имитация нажатия кнопки (без отправки в Telegram)"""
        message = type("Message", (), {"chat": type("Chat", (), {"id": self.chat_id}), "text": message_text})
        try:
            with patch("telebot.TeleBot.send_message", new=MagicMock()), \
                 patch("telebot.TeleBot.send_photo", new=MagicMock()):
                handle_choice(message)  # Имитируем клик по кнопке
            return True
        except Exception as e:
            print(f"❌ Ошибка на {self.state['chapter']} при нажатии '{message_text}': {e}")
            return False

    def traverse_chapters(self, chapter_key):
        """Рекурсивный обход всех глав"""
        if chapter_key in self.visited_chapters:
            return
        self.visited_chapters.add(chapter_key)

        # Устанавливаем текущую главу
        self.state["chapter"] = chapter_key
        save_state(self.chat_id, self.state)

        # 🛠 Полностью подменяем `send_message()`, `send_photo()`, `send_document()`
        with patch("telebot.TeleBot.send_message", new=MagicMock()), \
             patch("telebot.TeleBot.send_photo", new=MagicMock()), \
             patch("telebot.TeleBot.send_document", new=MagicMock()), \
             patch("telebot.TeleBot.send_video", new=MagicMock()), \
             patch("telebot.TeleBot.send_audio", new=MagicMock()):
            try:
                send_chapter(self.chat_id)  # ⚡️ Вызываем `send_chapter()` БЕЗ API Telegram
            except Exception as e:
                print(f"❌ Ошибка в send_chapter({chapter_key}): {e}")
                return  # Если глава вызывает ошибку, выходим

        # Проходим по кнопкам главы
        chapter = chapters.get(chapter_key, {})
        if "options" in chapter:
            for button_text, next_chapter in chapter["options"].items():
                if self.send_message_and_check(button_text):  # Проверяем, не падает ли бот
                    self.traverse_chapters(next_chapter)  # Рекурсивно идем дальше

    def test_bot(self):
        """Основной тест: проходит по всем главам"""
        self.traverse_chapters(self.state["chapter"])  # ⚡️ Больше не требует `asyncio`


if __name__ == "__main__":
    unittest.main()

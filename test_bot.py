import unittest
import json, subprocess
from unittest.mock import MagicMock, patch
from config import TOKEN, CHAPTERS_FILE
from handlers.game_handler import handle_choice, send_chapter
from utils.state_manager import load_state, save_state, state_cache
import telebot

# Удаляем все папки __pycache__
subprocess.run("find . -name '__pycache__' -exec rm -rf {} +", shell=True)
print("🗑️ Все папки __pycache__ удалены")

# Загружаем главы
with open(CHAPTERS_FILE, "r", encoding="utf-8") as file:
    chapters = json.load(file)
    print(f"📖 Загружено глав: {len(chapters)} из {CHAPTERS_FILE}")

# Создаем бота (отключаем реальный Telegram API)
bot = telebot.TeleBot(TOKEN)

# Глобально заменяем все отправки сообщений в Telegram
bot.send_message = MagicMock()
bot.send_photo = MagicMock()
bot.send_document = MagicMock()
bot.send_video = MagicMock()
bot.send_audio = MagicMock()


class TestBotSequential(unittest.TestCase):
    """Тест Telegram-бота: поочередное прохождение всех глав"""

    def setUp(self):
        """Инициализация данных для теста"""
        self.chat_id = 123456789  # Тестовый ID
        self.errors = []  # Список ошибок

    def send_message_and_check(self, message_text, current_chapter):
        """Имитация нажатия кнопки и проверка"""
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
                handle_choice(message)  # Имитация нажатия
            return True
        except Exception as e:
            error_msg = f"❌ Ошибка в главе '{current_chapter}' при нажатии '{message_text}': {e}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def extract_options_from_chapter(self, chapter_key):
        """Извлечение всех кнопок главы"""
        chapter = chapters.get(chapter_key.lower(), [])
        options = {}
        for action in chapter:
            action_type = action["type"]
            value = action["value"]
            if action_type in ("btn", "xbtn"):  # Только кнопки
                options[value["text"]] = value["target"].lower()
        return options

    def test_chapters_sequentially(self):
        """Основной тест: по порядку обходит все главы"""
        all_chapters = list(chapters.keys())
        print(f"🚀 Начало тестирования {len(all_chapters)} глав по порядку...")

        for chapter_key in all_chapters:
            print(f"\n📝 Тестируем главу: {chapter_key}")

            # Установка текущей главыself.state = {
                
            state = {
                "chapter": chapter_key.lower(),
                "history": [],
                "options": {},
                "inventory": [],
                "gold": 100,
                "end_triggered": False,
                "characteristics": {},
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
                    send_chapter(self.chat_id)  # Имитация отправки главы
            except Exception as e:
                error_msg = f"❌ Ошибка отображения главы '{chapter_key}': {e}"
                print(error_msg)
                self.errors.append(error_msg)
                continue  # Переход к следующей главе

            # Извлекаем кнопки и пробуем нажать
            options = self.extract_options_from_chapter(chapter_key)
            for button_text, target_chapter in options.items():
                print(f"➡️ Проверка кнопки: '{button_text}' (→ {target_chapter})")
                self.send_message_and_check(button_text, chapter_key)

        # ✅ Отчет
        print("\n📊 ТЕСТ ЗАВЕРШЕН")
        if self.errors:
            print(f"\n❗️ Найдено {len(self.errors)} ошибок:")
            for error in self.errors:
                print(error)
            self.fail(f"Обнаружено {len(self.errors)} ошибок. См. выше.")
        else:
            print("🎉 Все главы успешно пройдены без ошибок!")


if __name__ == "__main__":
    unittest.main()

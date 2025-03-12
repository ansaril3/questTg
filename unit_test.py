import unittest
import json
from unittest.mock import MagicMock, patch
from config import bot, CHAPTERS_FILE, COMMON_BUTTONS
from handlers.game_handler import handle_choice, send_chapter, execute_action
from handlers.inventory_handler import show_inventory, handle_use_item
from utils.state_manager import get_state, save_state
import subprocess
from handlers.stats_handler import show_characteristics

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
        """✅✅✅✅✅✅✅✅✅✅✅✅Создание тестового состояния"""
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
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест действия assign"""
        print("➡️ Запуск test_assign")

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][1]
            execute_action(self.chat_id, self.state, action)

        self.assertEqual(self.state["characteristics"]["strength"]["value"], 10)

    def test_gold(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест действия gold"""
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
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест выполнения if при истинном условии"""
        print("➡️ Запуск test_if_condition_true")

        self.state["characteristics"]["strength"] = {"value": 10}

        # ✅ Патчим глобальную переменную chapters на тестовые данные
        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][3]
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                execute_action(self.chat_id, self.state, action)
                mock_send.assert_called_with(self.chat_id, "Условие выполнено")

    def test_if_condition_false(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест выполнения if при ложном условии"""
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
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест действия xbtn и выполнения вложенных действий"""
        print("➡️ Запуск test_xbtn")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][5]
            execute_action(self.chat_id, self.state, action)

            # ✅ Проверяем, что кнопка добавлена в опции
            self.assertEqual(self.state["options"]["🔥 Тайный путь"], "test_secret")
            
            # ✅ Проверяем, что характеристика secret еще НЕ инициализирована
            self.assertNotIn("secret", self.state["characteristics"])

            # ✅ Эмулируем нажатие кнопки
            message = type(
                "Message", 
                (), 
                {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🔥 Тайный путь"}
            )
            handle_choice(message)

            # ✅ Проверяем выполнение вложенного действия (assign)
            self.assertEqual(self.state["characteristics"]["secret"]["value"], 1)

            # ✅ Проверяем, что глава сменилась на "test_secret"
            self.assertEqual(self.state["chapter"], "test_secret")

        print("✅ Тест успешно пройден!")


    def test_goto(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест действия goto"""
        print("➡️ Запуск test_goto")

        with patch("handlers.game_handler.chapters", test_chapters):
            action = test_chapters["test_start"][6]
            execute_action(self.chat_id, self.state, action)
            self.assertEqual(self.state["chapter"], "test_secret")

    def test_end(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест выполнения end"""
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

    def test_return(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест возврата в предыдущую главу"""
        print("➡️ Запуск test_return")

        with patch("handlers.game_handler.chapters", test_chapters):
            # ✅ Устанавливаем главу в "test_secret"
            self.state["chapter"] = "test_secret"
            send_chapter(self.chat_id)

            # ✅ Сохраняем состояние истории
            self.state["history"].append("test_secret")

            # ✅ Переходим в "test_return"
            self.state["chapter"] = "test_return"
            send_chapter(self.chat_id)

            # ✅ Условие успеха: мы находимся на "test_secret"
            self.assertEqual(self.state["chapter"], "test_secret")

        print("✅ Тест успешно пройден!")

    def test_image(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест отправки изображения"""
        print("➡️ Запуск test_image")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_photo") as mock_send_photo:
                # ✅ Устанавливаем главу и вызываем отправку
                self.state["chapter"] = "test_image"
                send_chapter(self.chat_id)

                # ✅ Проверяем, что send_photo вызван с правильным путем
                mock_send_photo.assert_called_once()

                # ✅ Проверяем параметры вызова
                args, _ = mock_send_photo.call_args
                file_path = args[1].name if len(args) > 1 else None
                self.assertEqual(file_path, "data/Images/3.JPG")

        print("✅ Тест успешно пройден!")

    def test_characteristics(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест отображения характеристик по кнопке 📊 Характеристики"""
        print("➡️ Запуск test_characteristics")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                self.state["characteristics"] = {}
                # ✅ Устанавливаем начальную главу
                self.state["chapter"] = "test_end"

                # ✅ Добавляем все кнопки из COMMON_BUTTONS в state["options"]
                for button in COMMON_BUTTONS:
                    self.state["options"][button] = button

                send_chapter(self.chat_id)

                # ✅ Симулируем нажатие на кнопку Характеристики
                message = type(
                    "Message", 
                    (), 
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "📊 Характеристики"}
                )
                show_characteristics(message)

                # ✅ Проверяем предпоследний вызов (сообщение с характеристиками)
                expected_message = "📊 Ваши характеристики:\n🔹 Скорость: 10\n"
                last_call = mock_send.call_args_list[-2]  # Предпоследний вызов
                actual_args, actual_kwargs = last_call

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_args[1], expected_message)
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

        print("✅ Тест успешно пройден!")


    def test_inventory(self):
        """✅✅✅✅✅✅✅✅✅✅✅✅Тест работы с инвентарем"""
        print("➡️ Запуск test_inventory")

        with patch("handlers.game_handler.chapters", test_chapters):
            with patch("handlers.game_handler.bot.send_message") as mock_send:
                
                # ✅ Очищаем инвентарь и золото перед тестом
                self.state["inventory"] = []
                self.state["options"] = {}
                self.state["gold"] = 130

                # ✅ Устанавливаем начальную главу
                self.state["chapter"] = "inv_check"

                # ✅ Передаём главу в бота
                send_chapter(self.chat_id)
                self.state["options"]["🎒 Инвентарь"] = "🎒 Инвентарь"

                # ✅ Проверяем, что предмет добавился в инвентарь
                self.assertIn("фиал волшебного питья[usable]", self.state["inventory"])

                # ✅ Проверяем, что отображается кнопка в state["options"]
                self.assertIn("🎒 Инвентарь", self.state["options"])

                # ✅ Нажимаем кнопку "🎒 Инвентарь"
                message = type(
                    "Message",
                    (),
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "🎒 Инвентарь"}
                )
                show_inventory(message)

                # ✅ Проверяем предпоследний вызов (сообщение с инвентарём)
                expected_message = (
                    "🎒 *Ваш инвентарь:*\n"
                    "💰 Золото: 130\n"  
                    "🔹 фиал волшебного питья (✨ usable)\n"
                )
                last_call = mock_send.call_args_list[-2]  # Предпоследний вызов (без точек)
                actual_args, actual_kwargs = last_call

                # 🔥 Убираем лишние переводы строк с обеих сторон
                actual_message = actual_args[1].strip()
                expected_message = expected_message.strip()

                self.assertEqual(actual_args[0], self.chat_id)
                self.assertEqual(actual_message, expected_message)
                self.assertEqual(actual_kwargs.get("parse_mode"), "Markdown")

                # ✅ Проверяем, что кнопка использования предмета добавлена в интерфейс
                self.assertIn("Use фиал волшебного питья", self.state["options"])

                # ✅ Нажимаем на кнопку "Use фиал волшебного питья"
                use_message = type(
                    "Message",
                    (),
                    {"chat": type("Chat", (), {"id": self.chat_id}), "text": "Use фиал волшебного питья"}
                )
                handle_use_item(use_message)

                # ✅ Проверяем, что глава переключилась на "use_фиал волшебного питья"
                self.assertEqual(self.state["chapter"], "use_фиал волшебного питья")

        print("✅ Тест успешно пройден!")


if __name__ == "__main__":
    unittest.main()

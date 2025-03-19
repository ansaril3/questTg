from dataclasses import dataclass, field
import os
import json
from dotenv import load_dotenv
from telebot import TeleBot

# Загрузка переменных окружения
load_dotenv()

@dataclass
class Config:
    # Переменные окружения
    TOKEN: str = os.getenv("TOKEN")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID")
    MEASUREMENT_ID: str = os.getenv("MEASUREMENT_ID")
    API_SECRET: str = os.getenv("API_SECRET")
    PROVIDER_TOKEN: str = os.getenv("PROVIDER_TOKEN")
    TEST_PROVIDER_TOKEN: str = os.getenv("TEST_PROVIDER_TOKEN")

    # Настройки платежей
    CURRENCY: str = "RUB"
    PRICE: str = "9900"

    # Режим работы (0 — тестовый, 1 — продакшн)
    PROD_MODE: int = 0

    # Пути к файлам и директориям
    CHAPTERS_FILE: str = "data/chapters.json"
    INSTRUCTIONS_FILE: str = "data/instructions.json"
    SAVES_DIR: str = "saves"
    DATA_DIR: str = "data"

    # Лимиты
    HISTORY_LIMIT: int = 10
    SAVES_LIMIT: int = 5

    # Кнопки
    COMMON_BUTTONS: list = field(default_factory=lambda: [
        "📥 Save game",
        "📤 Load game",
        "📊 Characteristics",
        "🎒 Inventory",
        "📖 Instructions"
    ])

    # Данные, загруженные из JSON
    chapters: dict = field(default_factory=dict)
    instructions: dict = field(default_factory=dict)

    # Первые главы и инструкции
    first_chapter: str = None
    first_instruction: str = None

    def __post_init__(self):
        # Создание директории для сохранений, если её нет
        if not os.path.exists(self.SAVES_DIR):
            os.makedirs(self.SAVES_DIR)

        # Загрузка данных из JSON
        self.chapters = self.load_json(self.CHAPTERS_FILE)
        self.instructions = self.load_json(self.INSTRUCTIONS_FILE)

        # Определение первой главы и инструкции
        self.first_chapter = list(self.chapters.keys())[0] if self.chapters else None
        self.first_instruction = list(self.instructions.keys())[0] if self.instructions else None

    @staticmethod
    def load_json(file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

# Создание объекта конфигурации
config = Config()

# Создание объекта бота отдельно
bot = TeleBot(config.TOKEN)
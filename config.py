# Configuration and data loading

import os
import json
from dotenv import load_dotenv
from telebot import TeleBot

# Loading environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")  # Create Firebase project -> Settings 
MEASUREMENT_ID = os.getenv("MEASUREMENT_ID")  # ⚙️ Find it in Firebase > Analytics > Data Streams
API_SECRET = os.getenv("API_SECRET")  # ⚙️ Create in Measurement Protocol API (Google Analytics 4)

bot = TeleBot(TOKEN)

# File paths
# ✅ Test mode (0 — production mode, 1 — test mode)
TEST_MODE = 1

# ✅ Set file path depending on the mode
CHAPTERS_FILE = "data/chapters.json" if TEST_MODE == 0 else "data/test_chapters.json"
INSTRUCTIONS_FILE = "data/instructions.json"
SAVES_DIR = "saves"
DATA_DIR = "data"
HISTORY_LIMIT = 10
SAVES_LIMIT = 5
COMMON_BUTTONS = [
    "📥 Save game",
    "📤 Load game",
    "📊 Characteristics",
    "🎒 Inventory",
    "📖 Instructions"
]
HISTORY_LIMIT = 10

# Create the saves directory if it doesn't exist
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

# Function to load a JSON file
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Loading data
chapters = load_json(CHAPTERS_FILE)
instructions = load_json(INSTRUCTIONS_FILE)

first_chapter = list(chapters.keys())[0] if chapters else None
first_instruction = list(instructions.keys())[0] if instructions else None

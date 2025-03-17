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

# ✅ Prod mode (0 — test mode turn off firebase, 1 — production mode)
PROD_MODE = 1

CHAPTERS_FILE = "data/chapters.json" 
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
    #"💰 Donate" 
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

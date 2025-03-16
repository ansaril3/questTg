
# QuestTG — Telegram Text Quest Interpreter Bot

**QuestTG** is a Telegram bot for interactive text-based quests.  
⚙️ This Python implementation is a port of [PolyQuest](https://github.com/PolyQuest/PolyQuest.github.io).

---

## 📜 Features

- Support for non-linear interactive text quests.
- Save and load game progress.
- Inventory system, player stats, and choice-based navigation.
- Easily switch between chapters and track history.

---

## 🚀 Installation and Deployment on a Remote Server (Linux, VPS, SSH)

### 1. 📥 Clone the repository

```bash
git clone https://github.com/ansaril3/questTg.git
cd questTg
```

---

### 2. 🐍 Install Python 3.8+ and venv (if not already installed)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```

---

### 3. ⚙️ Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 4. 📦 Install dependencies

```bash
pip install -r requirements.txt
```

---

### 5. 🔑 Create a `.env` file with your configuration

```bash
nano .env
```

Example content:

```ini
TOKEN=your_telegram_bot_token
FIREBASE_PROJECT_ID=your_firebase_project_id
MEASUREMENT_ID=your_google_analytics_id
API_SECRET=your_google_api_secret
```

> ⚠️ **Note**: Never share your `.env` file publicly.

---

### 6. ✅ Run the bot

```bash
python bot.py
```

---

## 💡 Optional: Run in Background Using `screen`

To keep the bot running after disconnecting from SSH:

```bash
sudo apt install screen
screen -S bot_session
python bot.py
```

To reattach to the session later:

```bash
screen -r bot_session
```

---

## 📂 Project Structure

```bash
questTg/
│
├── bot.py                # Main bot file
├── config.py             # Configuration for paths and settings
├── requirements.txt      # List of dependencies
├── .env                  # Secret keys and tokens (created manually)
│
├── data/                 # Game chapters and instructions
│   ├── chapters.json
│   └── instructions.json
│
├── saves/                # Game saves directory
│
├── utils/                # Utilities (state manager, helpers)
│
├── handlers/             # Handlers for bot commands and actions
│
└── tests/                # Unit tests and test data
```

---



## 📝 License

MIT License

---

**Feel free to contribute or raise issues!**

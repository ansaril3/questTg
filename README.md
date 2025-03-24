
# QuestTG — Telegram Interactive Fiction Bot (Text Quests)

**QuestTG** is a Telegram bot for interactive text-based quests.  

⚙️ This is a Python implementation of [PolyQuest](https://github.com/PolyQuest/PolyQuest.github.io) which is based on [URQW](https://github.com/urqw/UrqW) language.  
✅ Demo - [Telegram Quest Bot](https://t.me/QuestStroryBot)

<img width="461" alt="image" src="https://github.com/user-attachments/assets/35e8dd0e-90a9-4354-88a3-87a4aa460eb7" />


---

## 📜 Features

- Support for non-linear interactive text quests.
- Save and load game progress.
- Inventory system, player stats, and choice-based navigation.
- Easily switch between chapters and adding new quests.
- Users activity monitoring with google analytics.

---

## 🚀 Installation and Deployment

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
TOKEN=your_telegram_bot_token # get from BotFather
MEASUREMENT_ID=your_google_analytics_id #for google Analytics
API_SECRET=your_google_api_secret #for google Analytics
```

> ⚠️ **Note**: Never share your `.env` file publicly.

---


### 6. ✅ Run the bot

```bash
python bot.py
```

---

## 💡 Optional: Run in Background Using `tmux`

To keep the bot running after disconnecting from SSH:

```bash
sudo apt install tmux
tmux new -s bot_session
python bot.py
```
To disconnect from session:   
```bash
Ctrl + B, next D
```

To reattach to the session later:
```bash
tmux attach -t bot_session
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

## 📜 Adding New Quests

You can easily add your own quests to the bot using the following steps:

### 1. Prepare the Quest File

Place your URQ quest file named `input.txt` inside the `data/` folder.  
To convert this file into a working JSON format, run the parser:  

```bash
python utils/parser.py
```

This will generate a `chapters.json` file containing all quest chapters in a format readable by the bot.

#### ✅ Example `input.txt` (URQ format)

```
:Prolog3
Inv+ Медное кольцо
PLN Как-то раз, следуя по древней Стезе Королей, ты набредаешь на скорчившуюся в пыли старую женщину. Ты переносишь её в тень раскидистой акации и даешь ей напиться из своей фляги. Вскоре она приходит в себя, но, желая убедиться, что с ней всё в порядке, ты решаешь проводить её до ближайшего города.
BTN Prolog4,Далее
End
```

#### ✅ Example `chapters.json` (output)

```json
"prolog3": [
    {
        "type": "inventory",
        "value": "inv+медное кольцо"
    },
    {
        "type": "text",
        "value": "Как-то раз, следуя по древней Стезе Королей, ты набредаешь на скорчившуюся в пыли старую женщину. Ты переносишь её в тень раскидистой акации и даешь ей напиться из своей фляги. Вскоре она приходит в себя, но, желая убедиться, что с ней всё в порядке, ты решаешь проводить её до ближайшего города."
    },
    {
        "type": "btn",
        "value": {
            "text": "Далее",
            "target": "prolog4"
        }
    }
]
```

> ⚠️ **Note:** If some lines were not parsed correctly, they will be saved to `data/rest.txt` for manual review.

If you want to import non-URQ quest, write me to expand parser.

---

### 2. Test Your Quest Automatically

To automatically test all chapters and ensure the bot can navigate through them, run:

```bash
python -m tests.test_chapters
```

The test results will be saved in `tests/test_chapters.log`.  
If any issues are found (missing chapters, incorrect links, etc.), they will be reported for fixing.

---

### 3. Run Unit Tests

The bot includes unit tests for core actions like button presses, inventory display, and other mechanics.  
To run all unit tests, use:

```bash
python -m unittest tests/unit_test.py -v
```

---

With these tools, you can quickly add and validate new quests for the bot.


## 📝 License

MIT License

---
Contact: ansaril3g@gmail.com  
Join in Telegram - https://t.me/tg_quest  
**Feel free to contribute or raise issues!**

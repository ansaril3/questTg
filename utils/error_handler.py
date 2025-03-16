from functools import wraps
from config import bot
import traceback
from datetime import datetime
from utils.firebase_analytics import log_event

def safe_handler(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        try:
            return func(message, *args, **kwargs)
        except Exception as e:
            chat_id = message.chat.id
            error_message = f"❌ Ошибка в обработчике {func.__name__}: {e}\n{traceback.format_exc()}"
            print(error_message)
            with open("logs/errors.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{datetime.now()} - {error_message}\n")
            bot.send_message(chat_id, "⚠️ Произошла ошибка, но вы можете продолжить игру. Попробуйте снова.")
            log_event(chat_id, "error_occurred", {
                "function": func.__name__,
                "error": str(e),
                "traceback": traceback.format_exc()[:1000]  # Ограничим размер, если нужно
            })
    return wrapper


def safe_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"❌ Ошибка в функции {func.__name__}: {e}")
            log_event("system", "error_occurred", {
                "function": func.__name__,
                "error": str(e),
                "traceback": traceback.format_exc()[:1000]  # Ограничим размер, если нужно
            })
    return wrapper

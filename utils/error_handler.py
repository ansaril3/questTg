from functools import wraps
from config import bot
import traceback
from datetime import datetime
from utils.firebase_analytics import log_event

# ✅ Для message и callback_query
def safe_handler(func):
    @wraps(func)
    def wrapper(obj, *args, **kwargs):
        try:
            return func(obj, *args, **kwargs)
        except Exception as e:
            # ✅ Определяем chat_id в зависимости от типа объекта
            if hasattr(obj, 'chat'):  # message
                chat_id = obj.chat.id
            elif hasattr(obj, 'message'):  # callback_query
                chat_id = obj.message.chat.id
            else:
                chat_id = "unknown"

            # ✅ Готовим и логируем ошибку
            error_message = f"❌ Ошибка в обработчике {func.__name__}: {e}\n{traceback.format_exc()}"
            print(error_message)
            with open("logs/errors.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{datetime.now()} - {error_message}\n")

            # ✅ Сообщаем пользователю
            if chat_id != "unknown":
                bot.send_message(chat_id, "⚠️ Произошла ошибка, но вы можете продолжить игру. Попробуйте снова.")

            # ✅ Логируем в аналитику
            log_event(chat_id, "error_occurred", {
                "function": func.__name__,
                "error": str(e),
                "traceback": traceback.format_exc()[:1000]  # ограничение по размеру
            })
    return wrapper


# ✅ Для обычных функций (без привязки к message/callback_query)
def safe_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = f"❌ Ошибка в функции {func.__name__}: {e}\n{traceback.format_exc()}"
            print(error_message)
            with open("logs/errors.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{datetime.now()} - {error_message}\n")
            log_event("system", "error_occurred", {
                "function": func.__name__,
                "error": str(e),
                "traceback": traceback.format_exc()[:1000]  # ограничение по размеру
            })
    return wrapper

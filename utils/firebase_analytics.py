from config import MEASUREMENT_ID, API_SECRET
import requests
import time

# ✅ Функция отправки события
def log_event(user_id: int, event_name: str, params: dict = None):
    """Отправить кастомное событие в Firebase Analytics (GA4) через Measurement Protocol"""
    if params is None:
        params = {
          engagement_time_msec: '10000'
        }

    # URL для Measurement Protocol
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"

    # Тело запроса
    payload = {
        "client_id": str(user_id),  # Используем user_id как client_id (можно добавить session_id)
        "timestamp_micros": int(time.time() * 1_000_000),  # Текущее время в микросекундах
        "events": [
            {
                "name": event_name,
                "params": params
            }
        ]
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Проверить статус ответа
        print(f"✅ Событие '{event_name}' отправлено для пользователя {user_id}")
    except requests.RequestException as e:
        print(f"❌ Ошибка отправки события '{event_name}': {e}")

"""
Сервис датчиков: записывает в MongoDB данные о температуре, влажности и качестве воздуха.
Имитирует показания сенсоров для демонстрации EL-пайплайна.
"""
import os
import time
import random
from datetime import datetime, timezone
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@localhost:27017/?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "sensors")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "30"))


def get_client():
    return MongoClient(MONGODB_URI)


def generate_measurement():
    """Генерирует одно измерение: температура, влажность, AQI."""
    return {
        "temperature_celsius": round(random.uniform(18.0, 28.0), 2),
        "humidity_percent": round(random.uniform(30.0, 80.0), 2),
        "air_quality_aqi": random.randint(0, 150),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def write_measurement(client):
    """Записывает одно измерение в MongoDB."""
    db = client[MONGODB_DB]
    coll = db[MONGODB_COLLECTION]
    doc = generate_measurement()
    doc["_id"] = f"{doc['recorded_at']}_{random.getrandbits(32)}"
    coll.insert_one(doc)
    return doc


def run_loop():
    """Цикл записи измерений с заданным интервалом."""
    client = get_client()
    print(f"Подключение к MongoDB, БД={MONGODB_DB}, коллекция={MONGODB_COLLECTION}")
    print(f"Интервал записи: {INTERVAL_SECONDS} сек. Остановка: Ctrl+C")
    while True:
        try:
            doc = write_measurement(client)
            print(f"[{datetime.now().isoformat()}] Записано: temp={doc['temperature_celsius']}°C, "
                  f"humidity={doc['humidity_percent']}%, aqi={doc['air_quality_aqi']}")
        except Exception as e:
            print(f"Ошибка записи: {e}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_loop()

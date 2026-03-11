"""
Сервис датчиков: API для генерации измерений в MongoDB (температура, влажность, AQI).
По запросу генерирует одну запись и пишет в MongoDB. Вызов из Airflow по расписанию.
"""
import os
import random
from datetime import datetime, timezone
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@localhost:27017/?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "sensors")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")

app = FastAPI(title="Sensor API", description="Генерация измерений по запросу")
_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


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


@app.post("/measurements/generate")
def generate_and_save():
    """Генерирует одну случайную запись и сохраняет в MongoDB. Вызывается из Airflow."""
    try:
        client = get_client()
        doc = write_measurement(client)
        return {
            "ok": True,
            "measurement": {
                "id": str(doc["_id"]),
                "temperature_celsius": doc["temperature_celsius"],
                "humidity_percent": doc["humidity_percent"],
                "air_quality_aqi": doc["air_quality_aqi"],
                "recorded_at": doc["recorded_at"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}

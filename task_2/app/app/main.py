"""
Сервис датчиков (Task 2): API для генерации sensors, measurements (с sensor_id) и alerts в MongoDB.
Эндпоинты: POST /sensors/seed, POST /measurements/generate (при AQI>100 создаёт alert).
"""

import os
import random
from datetime import datetime, timezone
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@localhost:27017/?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "sensors")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")
MONGODB_SENSORS = os.getenv("MONGODB_SENSORS", "sensors")
MONGODB_ALERTS = os.getenv("MONGODB_ALERTS", "alerts")

# Порог AQI для автоматического создания алерта при генерации измерения
ALERT_AQI_THRESHOLD = 100

app = FastAPI(title="Sensor API (Task 2)", description="Генерация sensors, measurements и alerts по запросу")
_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


# --- Sensors ---

DEFAULT_SENSORS = [
    {"sensor_id": "sensor_01", "name": "Hall North", "location_code": "HN"},
    {"sensor_id": "sensor_02", "name": "Hall South", "location_code": "HS"},
    {"sensor_id": "sensor_03", "name": "Lab A", "location_code": "LA"},
    {"sensor_id": "sensor_04", "name": "Lab B", "location_code": "LB"},
    {"sensor_id": "sensor_05", "name": "Outdoor", "location_code": "OUT"},
]


def ensure_sensors_seeded(client):
    """Если коллекция sensors пуста — вставить дефолтный набор (для вызова при generate)."""
    db = client[MONGODB_DB]
    coll = db[MONGODB_SENSORS]
    if coll.count_documents({}) == 0:
        now = datetime.now(timezone.utc).isoformat()
        for s in DEFAULT_SENSORS:
            doc = {**s, "installed_at": now}
            coll.update_one({"sensor_id": s["sensor_id"]}, {"$setOnInsert": doc}, upsert=True)


@app.post("/sensors/seed")
def seed_sensors():
    """Заполняет справочник датчиков (если пуст). Вызывать до генерации измерений."""
    try:
        client = get_client()
        db = client[MONGODB_DB]
        coll = db[MONGODB_SENSORS]
        now = datetime.now(timezone.utc).isoformat()
        inserted = 0
        for s in DEFAULT_SENSORS:
            doc = {"sensor_id": s["sensor_id"], "name": s["name"], "location_code": s["location_code"], "installed_at": now}
            r = coll.update_one({"sensor_id": s["sensor_id"]}, {"$setOnInsert": doc}, upsert=True)
            if r.upserted_id:
                inserted += 1
        return {"ok": True, "inserted": inserted, "total": coll.count_documents({})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_random_sensor_id(client):
    """Возвращает случайный sensor_id из коллекции sensors; при пустой — сначала seed."""
    ensure_sensors_seeded(client)
    db = client[MONGODB_DB]
    coll = db[MONGODB_SENSORS]
    sensors = list(coll.find({}, {"sensor_id": 1}))
    if not sensors:
        return "sensor_01"
    return random.choice(sensors)["sensor_id"]


# --- Measurements ---

def generate_measurement(client):
    """Генерирует одно измерение с привязкой к датчику."""
    sensor_id = get_random_sensor_id(client)
    return {
        "sensor_id": sensor_id,
        "temperature_celsius": round(random.uniform(18.0, 28.0), 2),
        "humidity_percent": round(random.uniform(30.0, 80.0), 2),
        "air_quality_aqi": random.randint(0, 150),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def write_measurement(client):
    """Записывает одно измерение в MongoDB. При AQI > порога создаёт запись в alerts."""
    db = client[MONGODB_DB]
    coll_m = db[MONGODB_COLLECTION]
    coll_a = db[MONGODB_ALERTS]

    doc = generate_measurement(client)
    doc["_id"] = f"{doc['recorded_at']}_{random.getrandbits(32)}"
    coll_m.insert_one(doc)

    # При высоком AQI — создать алерт
    if doc.get("air_quality_aqi", 0) > ALERT_AQI_THRESHOLD:
        severity = "high" if doc["air_quality_aqi"] > 120 else "medium"
        alert_doc = {
            "_id": f"alert_{doc['_id']}",
            "measurement_id": str(doc["_id"]),
            "severity": severity,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        coll_a.insert_one(alert_doc)

    return doc


@app.post("/measurements/generate")
def generate_and_save():
    """Генерирует одну запись измерения (с sensor_id) и сохраняет в MongoDB. При AQI > 100 создаёт алерт."""
    try:
        client = get_client()
        doc = write_measurement(client)
        return {
            "ok": True,
            "measurement": {
                "id": str(doc["_id"]),
                "sensor_id": doc["sensor_id"],
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

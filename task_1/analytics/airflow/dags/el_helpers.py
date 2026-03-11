"""
Общая логика для PythonOperator: EL (MongoDB → PostgreSQL) и генерация данных в MongoDB.
Переменные окружения (MONGODB_URI, PG_*) задаются в docker-compose аналитики.
"""
import os
import random
from datetime import datetime, timezone

from pymongo import MongoClient
import psycopg2
from psycopg2.extras import execute_values

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@host.docker.internal:27017/?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "sensors")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")

# PostgreSQL
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER", "airflow")
PG_PASSWORD = os.getenv("PG_PASSWORD", "airflow")
PG_ANALYTICS_DB = os.getenv("PG_ANALYTICS_DB", "analytics")
PG_TABLE = "sensor_measurements"


def _parse_recorded_at(recorded_at):
    if isinstance(recorded_at, datetime):
        return recorded_at
    if isinstance(recorded_at, str):
        try:
            return datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
    return datetime.utcnow()


def _extract_from_mongo():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    coll = db[MONGODB_COLLECTION]
    rows = []
    for doc in coll.find():
        recorded_at = _parse_recorded_at(doc.get("recorded_at", datetime.utcnow()))
        rows.append({
            "measurement_id": str(doc.get("_id", "")),
            "temperature_celsius": float(doc.get("temperature_celsius", 0)),
            "humidity_percent": float(doc.get("humidity_percent", 0)),
            "air_quality_aqi": doc.get("air_quality_aqi"),
            "recorded_at": recorded_at,
        })
    client.close()
    return rows


def _load_to_postgres(rows):
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_ANALYTICS_DB,
    )
    cur = conn.cursor()
    if not rows:
        conn.close()
        return 0
    values = [
        (
            r["measurement_id"],
            r["temperature_celsius"],
            r["humidity_percent"],
            r["air_quality_aqi"],
            r["recorded_at"],
        )
        for r in rows
    ]
    execute_values(
        cur,
        """
        INSERT INTO sensor_measurements (measurement_id, temperature_celsius, humidity_percent, air_quality_aqi, recorded_at)
        VALUES %s
        ON CONFLICT (measurement_id) DO NOTHING
        """,
        values,
        template="(%s, %s, %s, %s, %s::timestamptz)",
    )
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def run_el(**context):
    """Извлечение из MongoDB и загрузка в PostgreSQL. Вызывается из PythonOperator."""
    rows = _extract_from_mongo()
    context.get("ti").xcom_push(key="extracted_count", value=len(rows))
    if not rows:
        return
    inserted = _load_to_postgres(rows)
    context["ti"].xcom_push(key="inserted_count", value=inserted)


def run_generate_sensor_data(count: int = 5, **context):
    """Записывает count измерений в MongoDB. Вызывается из PythonOperator."""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    coll = db[MONGODB_COLLECTION]
    inserted = 0
    for _ in range(count):
        doc = {
            "_id": f"airflow_{datetime.now(timezone.utc).isoformat()}_{random.getrandbits(32)}",
            "temperature_celsius": round(random.uniform(18.0, 28.0), 2),
            "humidity_percent": round(random.uniform(30.0, 80.0), 2),
            "air_quality_aqi": random.randint(0, 150),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        coll.insert_one(doc)
        inserted += 1
    client.close()
    context["ti"].xcom_push(key="inserted_count", value=inserted)

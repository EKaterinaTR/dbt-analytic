"""
Общая логика для PythonOperator: EL (MongoDB → PostgreSQL) и генерация данных в MongoDB.
Конфиг берётся из Airflow Variables (Admin → Variables), при отсутствии — значения по умолчанию.
"""
import random
import requests
from datetime import datetime, timezone

from airflow.models import Variable
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import execute_values

PG_TABLE = "sensor_measurements"


def _get_config():
    """Читает конфиг из Airflow Variables с fallback на дефолты."""
    return {
        "MONGODB_URI": Variable.get(
            "MONGODB_URI",
            default_var="mongodb://root:example@host.docker.internal:27017/?authSource=admin",
        ),
        "MONGODB_DB": Variable.get("MONGODB_DB", default_var="sensors"),
        "MONGODB_COLLECTION": Variable.get("MONGODB_COLLECTION", default_var="measurements"),
        "PG_HOST": Variable.get("PG_HOST", default_var="postgres"),
        "PG_PORT": int(Variable.get("PG_PORT", default_var="5432")),
        "PG_USER": Variable.get("PG_USER", default_var="airflow"),
        "PG_PASSWORD": Variable.get("PG_PASSWORD", default_var="airflow"),
        "PG_ANALYTICS_DB": Variable.get("PG_ANALYTICS_DB", default_var="analytics"),
        "SENSOR_API_URL": Variable.get("SENSOR_API_URL", default_var="http://host.docker.internal:8000"),
    }


def _parse_recorded_at(recorded_at):
    if isinstance(recorded_at, datetime):
        return recorded_at
    if isinstance(recorded_at, str):
        try:
            return datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
    return datetime.utcnow()


def _extract_from_mongo(cfg):
    client = MongoClient(cfg["MONGODB_URI"])
    db = client[cfg["MONGODB_DB"]]
    coll = db[cfg["MONGODB_COLLECTION"]]
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


def _load_to_postgres(cfg, rows):
    conn = psycopg2.connect(
        host=cfg["PG_HOST"],
        port=cfg["PG_PORT"],
        user=cfg["PG_USER"],
        password=cfg["PG_PASSWORD"],
        dbname=cfg["PG_ANALYTICS_DB"],
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
    """Извлечение из MongoDB и загрузка в PostgreSQL. Конфиг из Airflow Variables."""
    cfg = _get_config()
    rows = _extract_from_mongo(cfg)
    context["ti"].xcom_push(key="extracted_count", value=len(rows))
    if not rows:
        return
    inserted = _load_to_postgres(cfg, rows)
    context["ti"].xcom_push(key="inserted_count", value=inserted)


def trigger_sensor_api(**context):
    """Вызывает API приложения для генерации одной записи в MongoDB."""
    cfg = _get_config()
    url = cfg["SENSOR_API_URL"].rstrip("/") + "/measurements/generate"
    try:
        resp = requests.post(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        context["ti"].xcom_push(key="api_ok", value=data.get("ok", False))
        return data
    except Exception as e:
        raise RuntimeError(f"Сбой вызова API датчиков {url}: {e}")


"""
Task 2: EL из MongoDB (sensors, measurements, alerts) в PostgreSQL.
Конфиг — Airflow Variables.
"""
from datetime import datetime, timezone

from airflow.models import Variable
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import execute_values


def _get_config():
    return {
        "MONGODB_URI": Variable.get(
            "MONGODB_URI",
            default_var="mongodb://root:example@host.docker.internal:27017/?authSource=admin",
        ),
        "MONGODB_DB": Variable.get("MONGODB_DB", default_var="sensors"),
        "MONGODB_COLLECTION": Variable.get("MONGODB_COLLECTION", default_var="measurements"),
        "MONGODB_SENSORS": Variable.get("MONGODB_SENSORS", default_var="sensors"),
        "MONGODB_ALERTS": Variable.get("MONGODB_ALERTS", default_var="alerts"),
        "PG_HOST": Variable.get("PG_HOST", default_var="postgres"),
        "PG_PORT": int(Variable.get("PG_PORT", default_var="5432")),
        "PG_USER": Variable.get("PG_USER", default_var="airflow"),
        "PG_PASSWORD": Variable.get("PG_PASSWORD", default_var="airflow"),
        "PG_ANALYTICS_DB": Variable.get("PG_ANALYTICS_DB", default_var="analytics"),
        "SENSOR_API_URL": Variable.get("SENSOR_API_URL", default_var="http://host.docker.internal:8000"),
    }


def _parse_ts(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


# --- Sensors ---

def _extract_sensors(cfg):
    client = MongoClient(cfg["MONGODB_URI"])
    db = client[cfg["MONGODB_DB"]]
    coll = db[cfg["MONGODB_SENSORS"]]
    rows = []
    for doc in coll.find():
        rows.append({
            "sensor_id": str(doc.get("sensor_id", "")),
            "name": doc.get("name"),
            "location_code": doc.get("location_code"),
            "installed_at": _parse_ts(doc.get("installed_at")),
        })
    client.close()
    return rows


def _load_sensors(cfg, rows):
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
    values = [(r["sensor_id"], r["name"], r["location_code"], r["installed_at"]) for r in rows]
    execute_values(
        cur,
        """
        INSERT INTO sensors (sensor_id, name, location_code, installed_at)
        VALUES %s
        ON CONFLICT (sensor_id) DO UPDATE SET
            name = EXCLUDED.name,
            location_code = EXCLUDED.location_code,
            installed_at = EXCLUDED.installed_at
        """,
        values,
        template="(%s, %s, %s, %s::timestamptz)",
    )
    conn.commit()
    n = cur.rowcount
    cur.close()
    conn.close()
    return n


def run_el_sensors(**context):
    cfg = _get_config()
    rows = _extract_sensors(cfg)
    context["ti"].xcom_push(key="extracted_count", value=len(rows))
    if rows:
        n = _load_sensors(cfg, rows)
        context["ti"].xcom_push(key="loaded_count", value=n)


# --- Measurements ---

def _extract_measurements(cfg):
    client = MongoClient(cfg["MONGODB_URI"])
    db = client[cfg["MONGODB_DB"]]
    coll = db[cfg["MONGODB_COLLECTION"]]
    rows = []
    for doc in coll.find():
        rows.append({
            "measurement_id": str(doc.get("_id", "")),
            "sensor_id": str(doc.get("sensor_id", "")) if doc.get("sensor_id") else None,
            "temperature_celsius": float(doc.get("temperature_celsius", 0)),
            "humidity_percent": float(doc.get("humidity_percent", 0)),
            "air_quality_aqi": doc.get("air_quality_aqi"),
            "recorded_at": _parse_ts(doc.get("recorded_at", datetime.now(timezone.utc))),
        })
    client.close()
    return rows


def _load_measurements(cfg, rows):
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
            r["sensor_id"],
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
        INSERT INTO sensor_measurements (measurement_id, sensor_id, temperature_celsius, humidity_percent, air_quality_aqi, recorded_at)
        VALUES %s
        ON CONFLICT (measurement_id) DO UPDATE SET
            sensor_id = EXCLUDED.sensor_id,
            temperature_celsius = EXCLUDED.temperature_celsius,
            humidity_percent = EXCLUDED.humidity_percent,
            air_quality_aqi = EXCLUDED.air_quality_aqi,
            recorded_at = EXCLUDED.recorded_at
        """,
        values,
        template="(%s, %s, %s, %s, %s, %s::timestamptz)",
    )
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def run_el_measurements(**context):
    cfg = _get_config()
    rows = _extract_measurements(cfg)
    context["ti"].xcom_push(key="extracted_count", value=len(rows))
    if rows:
        n = _load_measurements(cfg, rows)
        context["ti"].xcom_push(key="loaded_count", value=n)


# --- Alerts ---

def _extract_alerts(cfg):
    client = MongoClient(cfg["MONGODB_URI"])
    db = client[cfg["MONGODB_DB"]]
    coll = db[cfg["MONGODB_ALERTS"]]
    rows = []
    for doc in coll.find():
        rows.append({
            "alert_id": str(doc.get("_id", "")),
            "measurement_id": str(doc.get("measurement_id", "")),
            "severity": str(doc.get("severity", "medium")),
            "created_at": _parse_ts(doc.get("created_at", datetime.now(timezone.utc))),
        })
    client.close()
    return rows


def _load_alerts(cfg, rows):
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
    values = [(r["alert_id"], r["measurement_id"], r["severity"], r["created_at"]) for r in rows]
    execute_values(
        cur,
        """
        INSERT INTO alerts (alert_id, measurement_id, severity, created_at)
        VALUES %s
        ON CONFLICT (alert_id) DO NOTHING
        """,
        values,
        template="(%s, %s, %s, %s::timestamptz)",
    )
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def run_el_alerts(**context):
    cfg = _get_config()
    rows = _extract_alerts(cfg)
    context["ti"].xcom_push(key="extracted_count", value=len(rows))
    if rows:
        n = _load_alerts(cfg, rows)
        context["ti"].xcom_push(key="loaded_count", value=n)


# --- Trigger sensor API (seed + generate) ---

def trigger_sensor_api(**context):
    """Вызывает seed (если нужно) и generate для одной записи в MongoDB."""
    import requests
    cfg = _get_config()
    base = cfg["SENSOR_API_URL"].rstrip("/")
    # Сначала seed датчиков (идемпотентно)
    try:
        requests.post(f"{base}/sensors/seed", timeout=10)
    except Exception:
        pass
    url = f"{base}/measurements/generate"
    try:
        resp = requests.post(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        context["ti"].xcom_push(key="api_ok", value=data.get("ok", False))
        return data
    except Exception as e:
        raise RuntimeError(f"Сбой вызова API датчиков {url}: {e}")

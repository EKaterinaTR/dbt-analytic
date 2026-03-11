"""
Task 2 DAG: EL — извлечение из MongoDB (sensors, measurements, alerts) и загрузка в PostgreSQL.
Три таска: sensors, measurements, alerts. Конфиг — Airflow Variables.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from el_helpers import run_el_sensors, run_el_measurements, run_el_alerts

with DAG(
    dag_id="el_mongodb_to_postgres",
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Extract from MongoDB (sensors, measurements, alerts), Load to PostgreSQL (analytics)",
    schedule=timedelta(minutes=5),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["el", "mongodb", "postgres", "task_2"],
) as dag:

    extract_load_sensors = PythonOperator(
        task_id="extract_load_sensors",
        python_callable=run_el_sensors,
    )
    extract_load_measurements = PythonOperator(
        task_id="extract_load_measurements",
        python_callable=run_el_measurements,
    )
    extract_load_alerts = PythonOperator(
        task_id="extract_load_alerts",
        python_callable=run_el_alerts,
    )

    # Порядок: sensors первым (справочник), затем measurements и alerts параллельно
    extract_load_sensors >> [extract_load_measurements, extract_load_alerts]

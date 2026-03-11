"""
DAG: триггер генерации — вызывает API приложения для создания одной записи в MongoDB.
Расписание задаётся отдельно от EL (например, каждые 1–5 мин).
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from el_helpers import trigger_sensor_api

with DAG(
    dag_id="trigger_sensor_generate",
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    description="Trigger sensor API to generate one measurement into MongoDB",
    schedule=timedelta(minutes=5),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["sensor", "generate", "api"],
) as dag:

    trigger_generate = PythonOperator(
        task_id="trigger_generate",
        python_callable=trigger_sensor_api,
    )

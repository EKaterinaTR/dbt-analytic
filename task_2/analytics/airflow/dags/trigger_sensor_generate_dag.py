"""
Task 2 DAG: по расписанию вызывает API датчиков — seed sensors и генерация одного измерения (и алерта при AQI>100).
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
        "retry_delay": timedelta(minutes=2),
    },
    description="Trigger sensor API: seed sensors + generate one measurement (and alert if AQI>100)",
    schedule=timedelta(minutes=5),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["sensor", "task_2"],
) as dag:

    trigger_generate = PythonOperator(
        task_id="trigger_generate",
        python_callable=trigger_sensor_api,
    )

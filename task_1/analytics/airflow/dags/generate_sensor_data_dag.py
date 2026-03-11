"""
DAG: генерация нагрузки — запись измерений в MongoDB (на хосте, порт 27017).
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from el_helpers import run_generate_sensor_data

with DAG(
    dag_id="generate_sensor_data",
    default_args={
        "owner": "airflow",
        "retries": 0,
    },
    description="Generate sensor measurements in MongoDB (host)",
    schedule=timedelta(minutes=2),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["load", "mongodb", "sensors"],
) as dag:

    generate = PythonOperator(
        task_id="generate_measurements",
        python_callable=run_generate_sensor_data,
        op_kwargs={"count": 5},
    )

"""
DAG: EL — извлечение из MongoDB (на хосте, порт 27017) и загрузка в PostgreSQL.
Переменные MONGODB_URI, PG_* задаются в docker-compose аналитики.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from el_helpers import run_el

with DAG(
    dag_id="el_mongodb_to_postgres",
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Extract from MongoDB (host), Load to PostgreSQL (analytics)",
    schedule=timedelta(minutes=5),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["el", "mongodb", "postgres"],
) as dag:

    extract_load = PythonOperator(
        task_id="extract_load",
        python_callable=run_el,
    )

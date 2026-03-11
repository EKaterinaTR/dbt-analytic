"""
Task 2 DAG: запуск dbt run и dbt test по расписанию.
Требует смонтированный проект dbt в /opt/airflow/dbt_analytics и переменные PG_* в окружении.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="dbt_run",
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Run dbt models and tests (staging, ods, marts, elementary)",
    schedule=timedelta(minutes=30),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "task_2"],
) as dag:

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command="cd /opt/airflow/dbt_analytics && dbt deps",
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_analytics && dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_analytics && dbt test",
    )

    dbt_deps >> dbt_run >> dbt_test

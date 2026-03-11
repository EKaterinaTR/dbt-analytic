# Аналитическая инфраструктура: PostgreSQL + Airflow

Отдельный compose только для аналитики. Подключение к MongoDB — по хосту (`host.docker.internal:27017`), т.к. MongoDB запущен в папке `app/`.

- **PostgreSQL** — метаданные Airflow и БД `analytics` (витрина после EL).
- **Airflow** — DAG’и EL (MongoDB → Postgres) и генерация нагрузки в MongoDB.

Перед запуском должен быть поднят стек **app/** (MongoDB на порту 27017).

## Запуск

```bash
docker compose up -d --build
```

Airflow: http://localhost:8080 (admin / admin).

## Конфиг через Airflow Variables

Параметры подключения к MongoDB и PostgreSQL задаются в **Admin → Variables**. Значения по умолчанию подставляются при первом запуске из файла **`airflow/variables_default.json`** (импорт в шаге `airflow-init`). Файл можно править в репозитории — после пересоздания БД Airflow переменные снова загрузятся из него.

При необходимости переменные можно переопределить в UI (Admin → Variables); они хранятся в метаданных Airflow.

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

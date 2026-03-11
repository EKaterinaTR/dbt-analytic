# Задание 1: ETL/ELT и основы работы с данными

Два отдельных стека: **приложение** (Python + MongoDB) и **аналитическая инфраструктура** (PostgreSQL + Airflow).  
MongoDB запускается вместе с приложением; порт **27017** проброшен на хост, чтобы Airflow мог читать данные.

## Структура

| Папка | Содержимое | Compose |
|-------|------------|--------|
| **app/** | Python-сервис датчиков + MongoDB | `app/docker-compose.yml` |
| **analytics/** | PostgreSQL + Airflow (EL-пайплайн) | `analytics/docker-compose.yml` |

- В **app** лежит всё, что относится к «продовому» приложению: сервис датчиков и его БД (MongoDB).
- В **analytics** — только аналитика: Postgres (витрина) и Airflow (извлечение из MongoDB, загрузка в Postgres).  
- Airflow подключается к MongoDB по адресу **host.docker.internal:27017** (хост), т.к. MongoDB в другом compose.

## Порты

- **app:** MongoDB — `27017` (обязательно проброшен, чтобы analytics мог читать).
- **analytics:** PostgreSQL — `5432`, Airflow UI — `8080`.

## Запуск

Сначала поднять приложение (MongoDB должна слушать на хосте 27017):

```bash
cd task_1/app
docker compose up -d --build
```

Затем поднять аналитику (Airflow будет подключаться к MongoDB на хосте):

```bash
cd task_1/analytics
docker compose up -d --build
```

Порядок важен: сначала **app**, потом **analytics**.

## Доступ

| Что | Где |
|-----|-----|
| Airflow UI | http://localhost:8080 (логин `admin`, пароль `admin`) |
| PostgreSQL | localhost:5432, пользователь `airflow`, пароль `airflow`, БД `airflow` (метаданные) и `analytics` (витрина) |
| MongoDB | localhost:27017 (пользователь `root`, пароль `example`) — из контейнеров analytics через `host.docker.internal:27017` |

## Проверка

1. **Данные в MongoDB** — сервис в `app/` пишет в БД `sensors`, коллекция `measurements`.
2. **EL в Airflow** — включите DAG **el_mongodb_to_postgres** (каждые 5 мин: MongoDB → PostgreSQL).
3. **Данные в PostgreSQL:**
   ```bash
   docker compose -f analytics/docker-compose.yml exec postgres psql -U airflow -d analytics -c "SELECT COUNT(*) FROM sensor_measurements;"
   ```
   (выполнять из `task_1` или указать путь к `analytics`.)

## Артефакты

- Один compose и одна папка для Python-приложения и MongoDB (порт 27017 для чтения Airflow).
- Отдельный compose и папка для аналитики (PostgreSQL + Airflow).
- Airflow читает MongoDB с хоста по настроенным портам.

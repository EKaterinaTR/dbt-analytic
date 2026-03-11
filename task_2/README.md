# Задание 2: DBT, витрины, тесты, документация

Полный цикл: **MongoDB → Airflow (EL) → PostgreSQL → DBT (витрины)** с тестами и документацией.

## Структура

| Папка | Содержимое |
|-------|------------|
| **app/** | Python-сервис: sensors (seed), measurements (с sensor_id), alerts (при AQI>100) |
| **analytics/** | PostgreSQL (init-analytics.sql), Airflow (EL + dbt DAG), dbt_analytics (DBT-проект) |

## Данные

- **MongoDB:** БД `sensors`, коллекции `sensors`, `measurements`, `alerts`.
- **PostgreSQL:** БД `analytics`, таблицы `sensors`, `sensor_measurements`, `alerts` (сырой слой для DBT).
- **DBT:** Слои staging → ods → marts (витрины). Два типа инкремента: **merge** (dm_daily_measurements), **insert+delete** (dm_alerts_recent).

## Запуск

### 1. Приложение (MongoDB + API)

```bash
cd task_2/app
docker compose up -d --build
```

Опционально один раз заполнить справочник датчиков:

```bash
curl -X POST http://localhost:8000/sensors/seed
```

### 2. Аналитика (PostgreSQL + Airflow)

```bash
cd task_2/analytics
docker compose up -d --build
```

Порядок: сначала **app**, затем **analytics**.

### 3. Локальный DBT (по желанию)

Из папки `task_2/analytics/dbt_analytics` при установленном dbt и доступном PostgreSQL:

```bash
export PG_HOST=localhost PG_USER=airflow PG_PASSWORD=airflow PG_ANALYTICS_DB=analytics
dbt deps
dbt run
dbt test
```

## Airflow DAGs

| DAG | Расписание | Описание |
|-----|------------|----------|
| **trigger_sensor_generate** | 5 мин | Вызов API: seed sensors + одно измерение (и алерт при AQI>100) |
| **el_mongodb_to_postgres** | 5 мин | EL: MongoDB (sensors, measurements, alerts) → PostgreSQL |
| **dbt_run** | 30 мин | dbt deps → dbt run → dbt test |

## Витрины (куда смотреть)

Подключение к PostgreSQL: хост `localhost`, порт `5432`, пользователь `airflow`, пароль `airflow`, БД `analytics`.

- **Сырые таблицы (заполняет EL):** `public.sensor_measurements`, `public.sensors`, `public.alerts`.
- **Витрины (строит DBT):**
  - `marts.dm_daily_measurements` — дневные агрегаты по датчику (incremental merge).
  - `marts.dm_alerts_recent` — алерты за последние 30 дней (incremental append + delete старых).
- **Промежуточные слои:** `staging.stg_*`, `ods.ods_*`.

## Тесты и документация

- Встроенные тесты DBT: unique, not_null, relationships (в `models/staging/schema.yml`).
- Кастомные тесты: `tests/assert_temperature_in_range.sql`, `assert_recorded_at_not_future.sql`, `assert_severity_allowed.sql`.
- Elementary: пакет подключён в `packages.yml`, схемы в `elementary`.
- Описание источников и моделей: `models/sources.yml`, `models/staging/schema.yml`, `models/models_schema.yml`.

## Порты

- **app:** MongoDB 27017, API 8000.
- **analytics:** PostgreSQL 5432, Airflow UI 8080 (логин `admin` / пароль `admin`).

# Архитектура проекта (UML)

## 1. Диаграмма верхнего уровня — полный контур данных

```mermaid
flowchart LR
    subgraph sources["Источники данных"]
        MongoDB[(MongoDB)]
    end

    subgraph orchestration["Оркестрация и загрузка"]
        Airflow[Airflow]
    end

    subgraph storage["Хранилище"]
        PostgreSQL[(PostgreSQL)]
    end

    subgraph transform["Трансформации"]
        dbt[dbt_analytics]
    end

    subgraph analytics["Аналитика"]
        Raw[Raw tables]
        Staging[Staging]
        ODS[ODS]
        Marts[Marts]
    end

    MongoDB -->|EL: Extract & Load| Airflow
    Airflow -->|Загрузка сырых данных| PostgreSQL
    PostgreSQL -->|source| dbt
    dbt -->|staging, ods, marts| PostgreSQL
```

## 2. Компонентная диаграмма — слои и потоки данных

```mermaid
flowchart TB
    subgraph external["Внешние системы"]
        MongoDB[(MongoDB)]
        Airflow[Airflow EL]
    end

    subgraph raw["Raw (PostgreSQL public)"]
        T1[(sensor_measurements)]
        T2[(sensors)]
        T3[(alerts)]
    end

    subgraph staging["Staging (schema: staging)"]
        STG1[stg_measurements]
        STG2[stg_sensors]
        STG3[stg_alerts]
    end

    subgraph ods["ODS (schema: ods)"]
        ODS1[ods_measurements]
        ODS2[ods_sensors]
    end

    subgraph marts["Marts (schema: marts)"]
        DM1[dm_daily_measurements]
        DM2[dm_alerts_recent]
    end

    MongoDB --> Airflow
    Airflow --> T1
    Airflow --> T2
    Airflow --> T3

    T1 --> STG1
    T2 --> STG2
    T3 --> STG3

    STG1 --> ODS1
    STG2 --> ODS2

    ODS1 --> DM1
    STG3 --> DM2
    STG1 --> DM2
```

## 3. Развёртывание (окружения)

```mermaid
flowchart TB
    subgraph people[""]
        dev[Разработчик]
        prod[CI/CD]
    end

    subgraph systems["Системы"]
        mongo[(MongoDB)]
        airflow[Airflow]
        dbt[dbt_analytics]
        db[(PostgreSQL)]
    end

    dev -->|dbt run dev| dbt
    prod -->|dbt run prod| dbt
    airflow -->|EL| mongo
    airflow -->|Load raw| db
    dbt -->|Build models| db
```

## 4. Краткое описание слоёв

| Слой      | Схема   | Назначение |
|-----------|---------|------------|
| **MongoDB** | —     | Исходные данные: сенсоры, измерения, алерты. |
| **Airflow** | —     | EL: извлечение из MongoDB и загрузка в PostgreSQL (raw). |
| **Raw**   | public  | Сырые таблицы в PostgreSQL: sensor_measurements, sensors, alerts. |
| **Staging** | staging | Приведение типов, ключи (pk), обогащение. |
| **ODS**   | ods     | Бизнес-правила, валидация. |
| **Marts** | marts   | Витрины: дневные агрегаты, недавние алерты. |

Тесты: Elementary + кастомные (`tests/assert_*.sql`).

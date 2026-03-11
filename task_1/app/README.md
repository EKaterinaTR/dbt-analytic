# Приложение: сервис датчиков + MongoDB

Всё, что относится к «продовому» приложению: Python-сервис датчиков и MongoDB.

- **MongoDB** — порт **27017** проброшен на хост, чтобы аналитический стек (Airflow в папке `analytics/`) мог подключаться к этой БД.
- **sensor-service** — пишет в MongoDB (БД `sensors`, коллекция `measurements`) показания температуры, влажности и AQI каждые 30 сек.

## Запуск

```bash
docker compose up -d --build
```

Подключение к MongoDB с хоста: `mongodb://root:example@localhost:27017/?authSource=admin`.

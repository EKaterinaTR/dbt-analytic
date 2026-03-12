# Task 2 — Kubernetes

Deploy Task 2 (sensor app + analytics Airflow/PostgreSQL/dbt) to a Kubernetes cluster.

## Prerequisites

- `kubectl` configured for your cluster
- Images built and pushed to a registry (see [Build images](#build-images))

## Deploy order

1. **App** (MongoDB + sensor API):

   ```bash
   kubectl apply -k task_2/k8s/app
   ```

2. **Analytics** (PostgreSQL + Airflow):

   ```bash
   kubectl apply -k task_2/k8s/analytics
   ```

3. Wait for `airflow-db-init` Job to complete, then webserver/scheduler will become ready.

## Build images

From repo root:

```bash
cd task_2/scripts
export REGISTRY=ghcr.io/ekaterinatr/dbt-analytic   # по умолчанию уже этот путь (lowercase для GHCR)
bash build-push-images.sh
```

В манифестах уже указан строчный образ: `ghcr.io/ekaterinatr/dbt-analytic/task2-airflow:latest` и `task2-sensor:latest`.

- `task_2/k8s/app/sensor-deployment.yaml` → `image: ghcr.io/ekaterinatr/dbt-analytic/task2-sensor:latest`
- `task_2/k8s/analytics/airflow-*.yaml` → `image: ghcr.io/ekaterinatr/dbt-analytic/task2-airflow:latest`

## Optional: Ingress

To expose Airflow UI and sensor API:

```bash
# Edit task_2/k8s/ingress.yaml (hosts, ingressClassName), then:
kubectl apply -f task_2/k8s/ingress.yaml
```

## DBT

DBT is included in the Airflow image built with `Dockerfile.airflow-k8s` (copies `dbt_analytics` into the image). The `dbt_run` DAG runs `dbt deps`, `dbt run`, `dbt test` on schedule; no extra manifests needed.

## Подключение к сервисам для проверки данных

Сервисы в кластере доступны по ClusterIP. Чтобы подключиться с локальной машины, используйте **port-forward**. В отдельном терминале запустите нужный туннель и не закрывайте его.

### 1. MongoDB (namespace task2-app)

```bash
kubectl port-forward -n task2-app svc/mongodb 27017:27017
```

Подключение (в другом терминале):

```bash
mongosh "mongodb://root:example@localhost:27017/?authSource=admin"
```

Проверка данных:

```javascript
use sensors
db.sensors.countDocuments()
db.measurements.countDocuments()
db.alerts.countDocuments()
db.measurements.find().limit(3)
```

### 2. PostgreSQL (namespace task2-analytics)

```bash
kubectl port-forward -n task2-analytics svc/postgres 5432:5432
```

Подключение (в другом терминале):

```bash
PGPASSWORD=airflow psql -h localhost -p 5432 -U airflow -d analytics
```

Проверка данных:

```sql
\dt public.*
SELECT COUNT(*) FROM public.sensors;
SELECT COUNT(*) FROM public.sensor_measurements;
SELECT COUNT(*) FROM public.alerts;
SELECT * FROM public.sensor_measurements LIMIT 5;
```

### 3. Airflow UI (namespace task2-analytics)

```bash
kubectl port-forward -n task2-analytics svc/airflow-webserver 8080:8080
```

В браузере откройте **http://localhost:8080**.

- Логин: `admin`  
- Пароль: `admin`

Проверка: DAGs → статус запусков, логи тасков, Variables.

### Краткая сводка

| Сервис    | Namespace       | Port-forward                          | Подключение |
|-----------|-----------------|----------------------------------------|-------------|
| MongoDB   | task2-app       | `svc/mongodb 27017:27017`             | `mongosh ... root:example@localhost:27017` |
| PostgreSQL| task2-analytics | `svc/postgres 5432:5432`              | `psql -h localhost -U airflow -d analytics` |
| Airflow UI| task2-analytics | `svc/airflow-webserver 8080:8080`     | http://localhost:8080 (admin / admin) |


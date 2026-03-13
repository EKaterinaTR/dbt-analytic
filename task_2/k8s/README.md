# Task 2 — Kubernetes

Deploy Task 2 (sensor app + analytics Airflow/PostgreSQL/dbt) to a Kubernetes cluster.

## Последовательность действий

Делайте по шагам:

1. **Настроить доступ к кластеру**  
   `kubectl` должен быть настроен и подключаться к вашему кластеру.

2. **Собрать и запушить образы** (если ещё не сделано):
   ```bash
   cd task_2/scripts
   export REGISTRY=ghcr.io/ekaterinatr/dbt-analytic
   bash build-push-images.sh
   ```
   Либо через GitHub Actions: **Build and push images**.

3. **Задеплоить приложение (MongoDB + Sensor API)**:
   ```bash
   kubectl apply -k task_2/k8s/app
   ```

4. **Задеплоить аналитику (PostgreSQL + Airflow)**:
   ```bash
   kubectl apply -k task_2/k8s/analytics
   ```

5. **Дождаться готовности**:
   ```bash
   kubectl get pods -n task2-app
   kubectl get pods -n task2-analytics
   kubectl get job -n task2-analytics airflow-db-init
   ```
   Все поды в `task2-app` и `task2-analytics` — `Running`, Job `airflow-db-init` — `COMPLETIONS 1/1`.

6. **Проверить данные** (через port-forward или из сети):
   - MongoDB: `kubectl port-forward -n task2-app svc/mongodb 27017:27017` → `mongosh "mongodb://root:example@localhost:27017/?authSource=admin"`.
   - PostgreSQL: `kubectl port-forward -n task2-analytics svc/postgres 5432:5432` → `psql -h localhost -U airflow -d analytics`.
   - Airflow UI: `kubectl port-forward -n task2-analytics svc/airflow-webserver 8080:8080` → браузер http://localhost:8080 (admin / admin).

7. **Доступ из сети**: все сервисы с типом **LoadBalancer** получают EXTERNAL-IP. Узнать IP:
   ```bash
   kubectl get svc -n task2-app
   kubectl get svc -n task2-analytics
   ```
   Airflow — `http://<AIRFLOW-EXTERNAL-IP>:8080`, Swagger — `http://<SENSOR-EXTERNAL-IP>:8000/docs`, БД — по своим EXTERNAL-IP (см. раздел про LoadBalancer ниже).

Если деплой идёт через **GitHub Actions**: запустите workflow **Deploy to Kubernetes** (при необходимости укажите тег образа). Шаги 3–4 выполнятся в пайплайне; шаги 5–7 — у себя по выводу `kubectl`.

---

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

## Optional: Ingress и доступ из сети

Чтобы все сервисы были доступны по URL из сети (для презентации, отчёта, проверки):

### Selectel Managed Kubernetes (MKS)

В Selectel для доступа из интернета можно использовать:

| Способ | Когда использовать | Плюсы |
|--------|--------------------|--------|
| **LoadBalancer** | Один сервис на один публичный IP | Проще всего: в манифесте указать `type: LoadBalancer` — Selectel создаст балансировщик и выдаст публичный IP. |
| **Ingress** | Несколько HTTP/HTTPS сервисов на один IP | Один IP для Airflow и Sensor API, маршрутизация по домену/пути, возможность TLS. Рекомендуется для веб-интерфейсов и API. |
| **LoadBalancer (БД)** | MongoDB и PostgreSQL — тип LoadBalancer | У каждого свой EXTERNAL-IP, доступ из сети по портам 27017 и 5432. |
| **TCP через Ingress** | MongoDB/PostgreSQL через тот же Ingress | Нужна настройка ConfigMap Ingress Controller (tcp-services). Сложнее, но один вход для всего. |

**Рекомендация для текущей архитектуры:**

- **Airflow UI и Sensor API (Swagger)** — **Ingress** (один публичный IP, два хоста: `airflow.<IP>.nip.io` и `sensor-api.<IP>.nip.io`). В панели Selectel: вкладка «Приложения» → установить **Nginx Ingress Controller**.
- **MongoDB и PostgreSQL** — сервисы типа **LoadBalancer** (отдельный EXTERNAL-IP на каждую БД), доступ из сети по портам 27017 и 5432.

**Как получить URL API (Swagger) в Selectel:**

1. Установите **Nginx Ingress Controller** через вкладку «Приложения» в панели управления кластером. [2]
2. Дождитесь появления у сервиса Ingress публичного **EXTERNAL-IP** (балансировщик создаётся автоматически):
   ```bash
   kubectl get svc -A | grep -i ingress
   ```
3. В `task_2/k8s/ingress.yaml` укажите хосты через **nip.io**: `airflow.<EXTERNAL-IP>.nip.io` и `sensor-api.<EXTERNAL-IP>.nip.io`.
4. Примените Ingress: `kubectl apply -f task_2/k8s/ingress.yaml`.
5. **Swagger:** `http://sensor-api.<EXTERNAL-IP>.nip.io/docs`, **Airflow:** `http://airflow.<EXTERNAL-IP>.nip.io`.

[1] [Load Balancers — Selectel](https://docs.selectel.ru/en/managed-kubernetes/networks/load-balancers/)  
[2] [Set up Ingress — Selectel](https://docs.selectel.ru/en/managed-kubernetes/networks/set-up-ingress/)  
[4] [Expose TCP services — Selectel](https://docs.selectel.ru/en/managed-kubernetes/networks/expose-tcp-services/)

---

### 1. Включить доступ по HTTP (Airflow + Sensor API / Swagger)

В `task_2/k8s/ingress.yaml` замените хост на свой адрес:
- либо домен (например `airflow.mydomain.com`),
- либо **nip.io**: если внешний IP Ingress-контроллера равен `1.2.3.4`, укажите хосты `airflow.1.2.3.4.nip.io` и `sensor-api.1.2.3.4.nip.io`.

Узнать внешний IP (после установки Ingress-контроллера):

```bash
kubectl get svc -A | grep -i ingress
# или для nginx: kubectl get svc -n ingress-nginx
```

Применить Ingress:

```bash
kubectl apply -f task_2/k8s/ingress.yaml
```

### 2. MongoDB, PostgreSQL, Airflow и Sensor API (LoadBalancer)

Сервисы БД и приложений имеют тип **LoadBalancer** и доступны из сети по своему EXTERNAL-IP (namespace у каждого свой: task2-app / task2-analytics):

- **MongoDB:** порт **27017** — `kubectl get svc -n task2-app mongodb`
- **PostgreSQL:** порт **5432** — `kubectl get svc -n task2-analytics postgres`
- **Airflow UI:** порт **8080** — `kubectl get svc -n task2-analytics airflow-webserver`
- **Sensor API (Swagger):** порт **8000** — `kubectl get svc -n task2-app sensor-service`

Узнать IP ноды (для подключения снаружи):

```bash
kubectl get nodes -o wide
```

Используйте **EXTERNAL-IP** или **INTERNAL-IP** одной из нод (с той же сети, откуда подключаетесь).

### 3. Шаблон URL для презентации / отчёта

После деплоя и применения Ingress подставьте свои значения (IP или домен) и заполните:

| Поле | Значение | Пример |
|------|----------|--------|
| **Airflow URL** | Веб-интерфейс Airflow | `http://<AIRFLOW-EXTERNAL-IP>:8080` |
| **Swagger URL** | Документация API датчиков | `http://<SENSOR-EXTERNAL-IP>:8000/docs` |
| **MongoDB URL** | Строка подключения к MongoDB | `mongodb://root:example@<MONGO-EXTERNAL-IP>:27017/?authSource=admin` |
| **PostgreSQL URL** | Строка подключения к PostgreSQL | `postgresql://airflow:airflow@<PG-EXTERNAL-IP>:5432/analytics` |
| **Airflow User** | Логин | `admin` |
| **Airflow Password** | Пароль | `admin` |
| **Elementary EDR report URL** | Если поднимаете отдельный отчёт Elementary | укажите URL или «генерируется в DBT» |
| **Презентация URL** | Ссылка на слайды | по желанию |

Где взять:
- **&lt;AIRFLOW-EXTERNAL-IP&gt;** — EXTERNAL-IP сервиса `airflow-webserver` (task2-analytics). **&lt;SENSOR-EXTERNAL-IP&gt;** — сервиса `sensor-service` (task2-app).
- **&lt;MONGO-EXTERNAL-IP&gt;** и **&lt;PG-EXTERNAL-IP&gt;** — EXTERNAL-IP сервисов `mongodb` (task2-app) и `postgres` (task2-analytics). Все четыре — через `kubectl get svc -n task2-app` и `kubectl get svc -n task2-analytics`.

Если Ingress не используется, для Airflow и Swagger можно продолжать использовать port-forward (доступ только с localhost).

## DBT

DBT is included in the Airflow image built with `Dockerfile.airflow-k8s` (copies `dbt_analytics` into the image). The `dbt_run` DAG runs `dbt deps`, `dbt run`, `dbt test` on schedule; no extra manifests needed.

## Подключение к сервисам для проверки данных

Сервисы в кластере доступны по ClusterIP. Чтобы подключиться с локальной машины, используйте **port-forward**. В отдельном терминале запустите нужный туннель и не закрывайте его.

**Для Git Bash (Windows)** — все команды ниже выполняйте в Git Bash как есть.

### 1. MongoDB (namespace task2-app)

Терминал 1 — туннель:

```bash
kubectl port-forward -n task2-app svc/mongodb 27017:27017
```

Терминал 2 — подключение и проверка:

```bash
mongosh "mongodb://root:example@localhost:27017/?authSource=admin"
```

Если `mongosh` не найден, попробуйте `mongo` (старый клиент).

В консоли MongoDB:

```javascript
use sensors
db.sensors.countDocuments()
db.measurements.countDocuments()
db.alerts.countDocuments()
db.measurements.find().limit(3)
```

### 2. PostgreSQL (namespace task2-analytics)

Терминал 1 — туннель:

```bash
kubectl port-forward -n task2-analytics svc/postgres 5432:5432
```

Терминал 2 — подключение (Git Bash):

```bash
export PGPASSWORD=airflow
psql -h localhost -p 5432 -U airflow -d analytics
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

Терминал 1 — туннель:

```bash
kubectl port-forward -n task2-analytics svc/airflow-webserver 8080:8080
```

В браузере откройте **http://localhost:8080**.

- Логин: `admin`  
- Пароль: `admin`

Проверка: DAGs → статус запусков, логи тасков, Variables.

### Краткая сводка (Git Bash)

| Сервис     | Port-forward (терминал 1) | Подключение (терминал 2) |
|------------|---------------------------|----------------------------|
| MongoDB    | `kubectl port-forward -n task2-app svc/mongodb 27017:27017` | `mongosh "mongodb://root:example@localhost:27017/?authSource=admin"` |
| PostgreSQL | `kubectl port-forward -n task2-analytics svc/postgres 5432:5432` | `export PGPASSWORD=airflow` затем `psql -h localhost -p 5432 -U airflow -d analytics` |
| Airflow UI | `kubectl port-forward -n task2-analytics svc/airflow-webserver 8080:8080` | Браузер: http://localhost:8080 (admin / admin) |


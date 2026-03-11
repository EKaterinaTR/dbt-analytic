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
export REGISTRY=your-registry   # e.g. docker.io/myuser or ghcr.io/myorg
bash build-push-images.sh
```

Then set the same image names in the manifests (search for `your-registry` and replace):

- `task_2/k8s/app/sensor-deployment.yaml` → `image: $REGISTRY/task2-sensor:latest`
- `task_2/k8s/analytics/airflow-db-init-job.yaml` → `image: $REGISTRY/task2-airflow:latest`
- `task_2/k8s/analytics/airflow-webserver-deployment.yaml` → same
- `task_2/k8s/analytics/airflow-scheduler-deployment.yaml` → same

## Optional: Ingress

To expose Airflow UI and sensor API:

```bash
# Edit task_2/k8s/ingress.yaml (hosts, ingressClassName), then:
kubectl apply -f task_2/k8s/ingress.yaml
```

## DBT

DBT is included in the Airflow image built with `Dockerfile.airflow-k8s` (copies `dbt_analytics` into the image). The `dbt_run` DAG runs `dbt deps`, `dbt run`, `dbt test` on schedule; no extra manifests needed.

#!/usr/bin/env bash
# Build and push Task 2 images for Kubernetes.
# Set REGISTRY (e.g. docker.io/myuser or ghcr.io/myorg) before running.
set -e
REGISTRY="${REGISTRY:-your-registry}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# task_2 directory (parent of scripts)
TASK2_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Using registry: $REGISTRY"
echo "Task 2 root: $TASK2_ROOT"

# Sensor service (from task_2/app)
echo "Building task2-sensor..."
docker build -t "$REGISTRY/task2-sensor:latest" "$TASK2_ROOT/app"
docker push "$REGISTRY/task2-sensor:latest"

# Airflow + dbt (from task_2/analytics, use Dockerfile.airflow-k8s)
echo "Building task2-airflow..."
docker build -f "$TASK2_ROOT/analytics/Dockerfile.airflow-k8s" -t "$REGISTRY/task2-airflow:latest" "$TASK2_ROOT/analytics"
docker push "$REGISTRY/task2-airflow:latest"

echo "Done. Update image names in k8s manifests to $REGISTRY/task2-sensor:latest and $REGISTRY/task2-airflow:latest"

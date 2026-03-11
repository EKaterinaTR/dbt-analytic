# Деплой через GitHub

##  GitHub Actions: сборка + деплой в Kubernetes (реализовано)

**Файл:** `.github/workflows/deploy-k8s.yml`

- **Триггеры:** ручной запуск (ввод тега образа) или публикация Release.
- **Действия:** подставляет образы из GHCR в манифесты (Kustomize), выполняет `kubectl apply -k` для `task_2/k8s/app` и `task_2/k8s/analytics`.

**Секреты в Settings → Secrets and variables → Actions:**

| Секрет        | Описание |
|---------------|----------|
| `KUBE_CONFIG` | kubeconfig кластера в **base64**: `base64 -w0 ~/.kube/config` |

Либо не использовать `KUBE_CONFIG`, а подключить кластер через OIDC/сервисный аккаунт (см. ниже).

**Опционально:** создать Environment `production` в Settings → Environments и привязать секреты к нему (и при необходимости включить approval).


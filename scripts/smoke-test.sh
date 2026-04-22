#!/usr/bin/env bash
set -euo pipefail

docker compose up --build -d
trap 'docker compose down --remove-orphans' EXIT

backend_status=$(curl -s http://localhost/api/health/live || true)
model_status=$(docker compose exec -T model-analiz wget -qO- http://localhost:8001/health/live || true)

if [[ "$backend_status" != *"ok"* ]]; then
  echo "backend health check failed"
  exit 1
fi

if [[ "$model_status" != *"ok"* ]]; then
  echo "model service health check failed"
  exit 1
fi

echo "smoke test passed"

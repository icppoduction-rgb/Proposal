PYTHON ?= python3

.PHONY: up down backend-test normalization-test training-test model-test log-test frontend-test smoke

up:
	docker compose up --build -d

down:
	docker compose down --remove-orphans

backend-test:
	cd backend && pytest

normalization-test:
	cd services/normalization_data && pytest

training-test:
	cd services/training_service && pytest

model-test:
	cd services/model_analiz && pytest

log-test:
	cd services/log_service && pytest

frontend-test:
	cd frontend && npm test

smoke:
	./scripts/smoke-test.sh

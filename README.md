# Behaviour-Driven Hybrid Learning for Data Exfiltration Detection

Monorepo for a contract-first cybersecurity platform that implements the project proposal from `Project Proposal.docx` as an operational stack:

- `frontend`: React + Vite + MUI control plane
- `backend`: FastAPI API gateway with local JWT RBAC
- `normalization-data`: Celery worker for dataset validation, profiling, quality audit, and normalization
- `training-service`: Celery worker for hybrid training, asynchronous inference orchestration, and SHAP generation
- `model-analiz`: FastAPI inference service that serves only promoted model artifacts
- `log-service`: FastAPI microservice for structured JSONL log browsing and filtering
- `postgres`, `redis`, `nginx`: runtime infrastructure

The repository is intentionally strict about missing data. Real datasets are not bundled, so registration works immediately, but validation, training, and inference fail fast if required files or contract columns are absent.

## Why this repo exists

The original proposal is not a generic ML platform. It is a domain-specific detection system for multi-stage data exfiltration that combines:

- host telemetry
- network telemetry
- classical ensemble models
- deep learning branches
- sequence modelling
- SHAP explainability

This implementation reshapes the earlier generic README into a cybersecurity-specific platform with explicit datasets, feature schemas, training runs, promoted artifacts, inference jobs, and explanation jobs.

## Repository layout

```text
.
├── app-data/
│   ├── raw/
│   ├── parsed/
│   ├── normalized/
│   ├── models/
│   ├── reports/
│   ├── explanations/
│   └── tmp/
├── backend/
├── frontend/
├── nginx/
├── services/
│   ├── model_analiz/
│   ├── normalization_data/
│   └── training_service/
├── shared/python/
├── docker-compose.yml
└── scripts/smoke-test.sh
```

## Core domain model

- `Dataset`: source type, manifest, validation state, detected format, normalization profile/summary, lineage, raw and normalized paths
- `FeatureSchema`: canonical mappings, required fields, feature families, optional MITRE tactic alignment
- `TrainingRun`: dataset + schema + hyperparameters + status + metrics
- `ModelArtifact`: branch models and fusion model, each with candidate/promoted/deprecated lifecycle
- `InferenceJob` + `DetectionResult`: asynchronous scoring and persisted predictions
- `ExplanationJob` + `ExplanationResult`: SHAP generation and stored analyst-facing explanation payloads
- `User` + `Role`: local JWT auth with `admin` and `analyst`

## ML implementation

The current implementation is contract-first and proposal-aligned:

- normalization-data detects `csv` / `tsv` / `parquet` / `xlsx` / `json` / `pcap` / `res` / `sc`, profiles DNS datasets, emits quality reports, and produces normalized CSV event datasets
- training worker builds:
  - `RandomForestClassifier`
  - `XGBClassifier`
  - a true PyTorch `1D-CNN` event branch
  - a sliding-window PyTorch `LSTM` sequence branch
  - a late-fusion average over branch probabilities
- inference service loads only promoted artifacts
- SHAP explanations are generated from the promoted random forest branch and stored as JSON together with feature-family and MITRE tactic hints

## API surface

All external backend routes are mounted under `/api`.

- `/api/auth/*`: login, refresh, logout, current user
- `/api/users/*`: admin-managed local users
- `/api/datasets/*`: register, upload, list, get, validate
- `/api/feature-schemas/*`: list/create/get/update
- `/api/training-runs/*`: list/create/get/cancel
- `/api/models/*`: list/get/promote/deprecate/download
- `/api/inference-jobs/*`: submit/list/get/results
- `/api/explanations/*`: request/list/get/result
- `/api/logs/*`: structured log browsing via backend gateway and internal log-service
- `/api/tasks/*`: polling layer for long-running work
- `/api/health/*`: liveness/readiness

## Local run

1. Copy `.env.example` to `.env` if you want local overrides.
2. Start the stack:

```bash
docker compose up --build -d
```

3. Open:

- frontend via [http://localhost](http://localhost)
- backend docs via [http://localhost/api/docs](http://localhost/api/docs)

Default admin credentials:

- `admin@example.com`
- `admin123456`

## Developer workflows

Frontend:

```bash
cd frontend
npm install
npm run build
npm test
```

Python syntax check:

```bash
python3 -m compileall backend shared/python services
```

Smoke test:

```bash
./scripts/smoke-test.sh
```

## Current limitations

- Real datasets are not bundled, so end-to-end training requires the user to place raw files into `app-data/raw/` and register manifests that match those files.
- Backend and service tests are available locally; some suites depend on the full Python/ML dependency set and isolated test data paths.
- The frontend currently uses polling, not WebSockets.
- The model registry is functional, but no external model store or experiment tracker is configured yet.
- Alembic migrations are not yet added; schema bootstrap is done with SQLAlchemy `create_all()` during service startup.

## Recommended next steps

- add Alembic migrations and GitHub Actions CI
- add OpenAPI-driven frontend client generation
- add richer SHAP visualizations and downloadable analyst reports

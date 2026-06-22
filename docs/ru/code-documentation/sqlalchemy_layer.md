# Слой SQLAlchemy

## Расположение

```text
scripts/db/
  config.py
  session.py
  smoke_check.py
  models/
  repositories/
  migrations/
```

## Конфигурация

Файл: `scripts/db/config.py`.

`load_database_settings()` читает:

| Env | Значение по умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | обязательное | строка подключения SQLAlchemy |
| `SQLALCHEMY_ECHO_SQL` | `false` | логирование SQL |
| `SQLALCHEMY_POOL_PRE_PING` | `true` | pre-ping подключений |

Если `DATABASE_URL` не задан, функция поднимает `ValueError`.

## Управление сессиями

Файл: `scripts/db/session.py`.

`session_scope()`:

```python
@contextmanager
def session_scope(...):
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Свойства:

- commit транзакции после успешного блока;
- rollback при exception;
- close выполняется всегда;
- `expire_on_commit=False`;
- `autoflush=False`, `autocommit=False`.

Вложенные операции по отдельным файлам в normalization используют `session.begin_nested()`, чтобы failing file не обязательно ломал весь batch.

## Модели

Модели находятся в `scripts/db/models` и экспортируются через `scripts/db/models/__init__.py`.

Ключевые модели:

- `Dataset`;
- `DatasetFile`;
- `IngestionRun`;
- `ParserRegistry`;
- `SchemaVersion`;
- `ParserRun`;
- `NormalizedArtifact`;
- `FeatureArtifact`;
- `PreprocessingArtifact`;
- `ModelReadyArtifact`;
- `LabelMappingRule`;
- `DataQualityReport`.

Общие constants: `scripts/db/models/constants.py`.

Важные constants:

```text
BRANCH_VALUES = dns, host, network, hybrid
ROLE_VALUES = TRAIN, VALIDATION, TEST, EXPERIMENTS
ACTIVE_DATASET_ROLE_VALUES = TRAIN, VALIDATION, TEST
ACTIVE_CATALOG_SOURCE_GROUP = PATH_FOLDER_DATASETS_FILTER
```

## Репозитории

Repositories инкапсулируют записи/запросы и не управляют commit самостоятельно.

| Repository | Назначение |
|---|---|
| `DatasetRepository` | получение/создание datasets |
| `IngestionRepository` | start/finish/failed для ingestion runs |
| `DatasetFileRepository` | bulk upsert файлов, выбор ready files, обновление статуса |
| `ParserRepository` | parser registry rows и жизненный цикл parser run |
| `SchemaRepository` | регистрация schema version |
| `ArtifactRepository` | регистрация normalized/feature/model-ready artifacts |
| `PreprocessingRepository` | регистрация preprocessing artifacts |
| `LabelRepository` | поиск label mapping |
| `DataQualityRepository` | регистрация quality/leakage reports |

`DatasetFileRepository.bulk_upsert_files()` использует PostgreSQL `ON CONFLICT` по `(dataset_id, file_path)`. Если hash файла изменился, статус становится `CHANGED`; иначе существующий статус сохраняется.

## Миграции Alembic

Конфигурация: `scripts/db/migrations/alembic.ini`.

Миграция:

```text
scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py
```

Применение:

```bash
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Миграция создает все таблицы catalog Stage Two:

- `data_quality_reports`;
- `datasets`;
- `ingestion_runs`;
- `label_mapping_rules`;
- `parser_registry`;
- `schema_versions`;
- `dataset_files`;
- `parser_runs`;
- `normalized_artifacts`;
- `feature_artifacts`;
- `preprocessing_artifacts`;
- `model_ready_artifacts`.

## Smoke-проверка

Файл: `scripts/db/smoke_check.py`.

`run_smoke_checks()`:

- создает dataset;
- проверяет unique/check constraints;
- создает ingestion run;
- вставляет dataset file;
- создает parser registry/schema/parser run;
- регистрирует normalized, feature, preprocessing и model-ready artifacts;
- проверяет, что `PreprocessingArtifact(fitted_on_role='TEST')` падает;
- создает quality report;
- откатывает все smoke data в конце.

Рекомендуемая команда:

```bash
python - <<'PY'
from scripts.db.smoke_check import run_smoke_checks
print(run_smoke_checks())
PY
```

Требует рабочий `DATABASE_URL` и примененные migrations.

## Эксплуатационные замечания

- Методы repository ожидают session, управляемую снаружи.
- Ни один repository не должен хранить большие row tables в PostgreSQL.
- DB constraints защищают домены branch/role/status, но сами по себе не предотвращают ML leakage; нужны model-ready contracts и leakage checks.
- Для долгих запусков normalization предпочитайте `normalize-format` с ограниченным `--batch-size` и явным `--limit`.

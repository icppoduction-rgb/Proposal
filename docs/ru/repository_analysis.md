# Анализ репозитория

Дата сверки: 2026-07-08.

Документ фиксирует текущее состояние кода и документации репозитория `Proposal` после анализа entrypoints, CLI, Stage One/Two/Three модулей, тестов, схем и storage artifacts.

## Краткий вывод

Репозиторий реализует pipeline подготовки данных до model-ready artifacts:

```text
Stage One:   raw datasets -> inventories/sorted path maps/content reports
Stage Two:   raw catalog -> parser registry -> normalized Parquet -> quality/leakage/traceability
Stage Three: normalized Parquet -> feature artifacts -> model-ready X/y/metadata/traceability -> readiness report
Stage Four:  training/evaluation/explainability, пока не опубликован как CLI
```

Stage Four остается следующим этапом: обучение RF/XGBoost/CNN/LSTM, threshold tuning, SHAP/XAI и экспериментальная оценка в текущем CLI не реализованы.

## Масштаб кода и документации

Фактический срез:

| Область | Количество |
| --- | ---: |
| Python-файлы | 334 |
| Тестовые Python-файлы | 66 |
| Markdown в `docs/` | 106 |
| Markdown в `docs/ru` | 52 до добавления этого файла |
| Markdown в `docs/en` | 52 до добавления английской версии |

Основные директории:

```text
scripts/
  handlers/        # Stage One handlers
  stage_two/       # catalog, parsers, normalization, checks
  stage_three/     # feature/model-ready preparation
  db/              # SQLAlchemy models, repositories, Alembic
schemas/           # normalized/features/model_ready JSON contracts
tests/
  stage_two/
  stage_three/
docs/
  ru/
  en/
```

## Entry points и routing

Главная точка входа:

```powershell
python manage.py <module> <service> [action] [args]
```

Фактическая маршрутизация:

| Слой | Файл | Назначение |
| --- | --- | --- |
| `manage.py` | `manage.py` | тонкий CLI entrypoint; отдельно прокидывает `stage-three` в argparse-router |
| root router | `scripts/router_script.py` | отправляет команды в `handlers`, `stage_two`, `stage_three` |
| Stage One | `scripts/handlers/router_handler.py` | legacy handlers для анализа/сортировки датасетов |
| Stage Two | `scripts/stage_two/cli.py` | фактический router normalization pipeline |
| Stage Three | `scripts/stage_three/cli.py` | argparse router feature/model-ready preparation |

Важно: `python manage.py stage-two --help` в текущем состоянии не является надежным источником help. Он выводит ошибку `unknown Stage Two command` и старый fallback `config.manage_commands`. Полный фактический список Stage Two команд нужно брать из `scripts/stage_two/cli.py` и `docs/ru/normalization/stage_two_commands.md`.

## Stage One

Stage One находится в `scripts/handlers` и выполняет filesystem-level подготовку:

- анализ DNS/Host raw dataset roots;
- фильтрацию Host источников;
- сортировку по role/format;
- экспорт JSON path maps;
- content analysis reports для DNS/Host buckets.

Stage One не пишет normalized Parquet и не регистрирует артефакты в PostgreSQL catalog.

## Stage Two

Stage Two находится в `scripts/stage_two`, `scripts/db`, `schemas`.

Фактические команды router:

- `bootstrap-storage`
- `catalog-ingest`
- `seed-parser-registry`
- `parser-coverage`
- `mark-ready`
- `normalize-format`
- `normalize-all`
- `benchmark-normalization`
- `split-large-files`
- `normalize-dns`
- `normalize-host`
- `run-duckdb-checks`
- `run-leakage-checks`
- `trace-artifact`

Ключевые подсистемы:

| Подсистема | Файлы |
| --- | --- |
| storage bootstrap | `scripts/stage_two/storage/bootstrap.py` |
| catalog ingestion | `scripts/stage_two/ingestion/` |
| parser registry/resolver | `scripts/stage_two/parser_registry/` |
| parsers | `scripts/stage_two/parsers/` |
| normalization runner | `scripts/stage_two/normalization/` |
| execution policy | `scripts/stage_two/execution/` |
| Parquet writer | `scripts/stage_two/parquet/writer.py` |
| DuckDB analytics | `scripts/stage_two/duckdb/service.py` |
| quality/leakage | `scripts/stage_two/quality/` |
| traceability | `scripts/stage_two/traceability/service.py` |

Stage Two отвечает за переход `raw -> normalized` и не должен выполнять обучение моделей.

## Stage Three

Stage Three находится в `scripts/stage_three`.

Фактические команды:

- `validate-inputs`
- `build-feature-catalog`
- `probe-runtime-backend`
- `extract-features`
- `align-labels`
- `build-sequences`
- `build-model-ready`
- `rebalance-dns-supervised`
- `run-quality-checks`
- `run-leakage-checks`
- `trace-artifact`
- `final-report`

Ключевые подсистемы:

| Подсистема | Файлы |
| --- | --- |
| typed CLI requests | `scripts/stage_three/requests.py` |
| storage bootstrap | `scripts/stage_three/storage/bootstrap.py` |
| readiness gate | `scripts/stage_three/readiness/` |
| feature catalog | `scripts/stage_three/feature_catalog/feature_catalog.yml` |
| runtime profiles/backend | `scripts/stage_three/runtime/` |
| extraction | `scripts/stage_three/extraction/` |
| labels/window policies | `scripts/stage_three/labels/` |
| preprocessing | `scripts/stage_three/preprocessing/` |
| model-ready builder | `scripts/stage_three/model_ready/` |
| quality/leakage/traceability | `scripts/stage_three/quality/` |
| final reports/console output | `scripts/stage_three/reports/` |
| DNS supervised split rebuild | `scripts/stage_three/dns_rebalance.py` |

Stage Three является preparation layer. Он готовит artifacts для Stage Four, но не обучает модели.

## Feature catalog

Machine-readable catalog находится в:

```text
scripts/stage_three/feature_catalog/feature_catalog.yml
```

Он задает:

- `forbidden_X_columns`;
- feature groups для DNS, Host, Network, Hybrid и Sequence;
- source fields и output features;
- dtype/nullability/preprocessing policy.

Ключевое правило: label/source/path/parser/raw/metadata/traceability поля не должны попадать в model-ready X.

## Storage

Фактический storage root:

```text
C:\Users\Public\PythonProjects\storage
```

Основные зоны:

- `parquet/normalized`
- `parquet/features`
- `parquet/model_ready`
- `duckdb/proposal_analytics.duckdb`
- `reports/{ru,en}/stage-one`
- `reports/{ru,en}/stage-two`
- `reports/{ru,en}/stage-three`
- `temp_data`
- `schemas`
- `config`
- `logs`
- `backups`

Подробно см. `docs/storage.md`.

## Тесты

Тесты разделены по этапам:

- `tests/stage_two/` - parsers, catalog ingestion, normalization, Parquet writer, DuckDB, leakage, parser reports, status tools.
- `tests/stage_three/` - CLI routing, runtime, feature catalog, extraction, label alignment, preprocessing, model-ready builder, quality/leakage, final report, console output.

Минимальная проверка документационных правок:

```powershell
git diff --check -- docs
```

Целевые тесты после изменения Stage Two/Three кода:

```powershell
pytest tests/stage_two
pytest tests/stage_three
```

## Инварианты

1. Raw datasets не изменяются.
2. `TRAIN`, `VALIDATION`, `TEST` не смешиваются.
3. `TEST` не используется для training, preprocessing fit, feature selection или threshold tuning.
4. Labels не являются input features.
5. Отсутствующий label не означает benign.
6. Отсутствующий timestamp нельзя заменять текущим временем.
7. Большие таблицы хранятся в Parquet; PostgreSQL хранит metadata/status/lineage.
8. `temp_data` не является source of truth.
9. Переход к Stage Four допустим только после Stage Three `final-report` со статусом `READY_FOR_STAGE_FOUR`.

## Gaps

| Область | Статус |
| --- | --- |
| Stage Four training/evaluation | Не опубликован как CLI |
| RF/XGBoost configs | Proposal-level |
| CNN/LSTM architecture | Proposal-level |
| SHAP/XAI | Proposal-level |
| Late fusion | Proposal-level |
| CV folds/statistical tests/seeds | Требуют отдельного experiment config |
| Production Host/Network/Hybrid readiness | Требует проверки по конкретным `branch`, `role`, `feature_group`, `experiment_id` |

# Stage Two: нормализация данных

Stage Two - это слой нормализации данных и PostgreSQL control plane. Его актуальный вход - отфильтрованное дерево датасетов из `PATH_FOLDER_DATASETS_FILTER`. Stage Two регистрирует эти файлы в PostgreSQL, выбирает parser через parser registry, пишет normalized events в Parquet и сохраняет traceability в catalog tables.

Текущий реализованный CLI scope:

```text
PATH_FOLDER_DATASETS_FILTER -> catalog ingestion -> parser registry -> parser run -> normalized Parquet -> catalog artifact registration -> quality/leakage/readiness checks
```

Feature и model-ready schemas, catalog tables и artifact contracts уже есть в `schemas/features/feature_artifact_v1.json`, `schemas/model_ready/model_ready_v1.json`, `scripts/stage_two/features/`, `scripts/stage_two/model_ready/`. Production CLI для построения всех feature/model-ready artifacts на полном корпусе не входит в текущий parser workflow.

## Основные команды

```powershell
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two seed-parser-registry
python manage.py stage-two catalog-ingest
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Stage Two smoke-скрипты поддерживаются только в module form, например `python -m scripts.stage_two.parser_smoke`. Не запускайте их как file paths вроде `python scripts/stage_two/parser_smoke.py`, потому что этот режим может сломать package imports.

Backward-compatible aliases остаются доступны:

```powershell
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

## Карта документации

- [Stage Two usage guide](usage_guide.md): операционный сценарий от filtered datasets до normalized artifacts.
- [Parser strategy](parser_strategy.md): source formats, parser classes, statuses и registry behavior.
- [Parser development guide](parser_development_guide.md): как безопасно добавить новый parser.
- [PostgreSQL catalog schema](postgresql_catalog_schema.md): catalog tables и связи.
- [Normalized event schema](normalized_event_schema.md): canonical normalized event contract.
- [Storage architecture](storage_architecture.md): storage roots и generated artifact paths.
- [Parquet and DuckDB artifacts](parquet_duckdb_artifacts.md): Parquet writer и DuckDB checks.
- [Data quality checks](data_quality_checks.md): quality/readiness checks и reports.
- [Data leakage prevention](data_leakage_prevention.md): label и split safety rules.
- [Шаблон финального отчета Codex](final_summary_template.md): формат финального отчета и staged validation commands.

## Ключевые инварианты

- `PATH_FOLDER_DATASETS_FILTER` является authoritative input для Stage Two.
- `PATH_FOLDER_DATASETS` сохраняется для immutable raw sources, Stage One discovery и аудита/traceback; по умолчанию он не попадает в Stage Two catalog ingestion.
- Raw datasets никогда не изменяются Stage Two.
- PostgreSQL хранит metadata, statuses, relationships, parser runs и artifact records; большие normalized данные хранятся в Parquet.
- Активные рабочие роли: TRAIN, VALIDATION, TEST. `EXPERIMENTS` оставлен только как legacy-compatible значение схемы БД и не используется в catalog ingestion, mark-ready, normalization, reports и downstream checks.
- TRAIN, VALIDATION и TEST разделены логически в catalog rows и физически в Parquet paths.
- `catalog-ingest` не переводит файлы в `READY_FOR_PARSING` автоматически; `mark-ready` является явным operational gate.
- `normalize-format` обрабатывает ровно один срез `branch`/`role`/`source_format`.
- `normalize-all` обрабатывает одну branch группами role/source_format, а не одной неконтролируемой смешанной транзакцией.
- Missing source values представлены как `None`/SQL `NULL`/Parquet null.
- Unknown source fields сохраняются в `raw_fields_json`, `features_json` или `metadata_json`.
- Labels не должны попадать в X/model input columns. TEST filename heuristics отключены.
- Parser failures должны быть видны через `parser_runs`, `dataset_files.status`, reports и counters.

## Текущие parser groups

| Branch | Parser class | Source formats |
| --- | --- | --- |
| dns | `DnsCsvParser` | `csv` |
| dns | `DnsPcapCsvParser` | `pcap.csv` |
| dns | `DnsTxtDomainListParser` | `txt` для DNS VALIDATION |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` |
| host | `HostCsvParser` | `csv` |
| host | `HostJsonLinesParser` | `json`, `json-1` |
| host | `HostLineLogParser` | host line-log formats и metric log buckets |
| host | `HostMetricbeatParser` | metric formats через delegation из `HostLineLogParser` |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` |
| host | `HostBsonSandboxParser` | `bson` для host TEST |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` |
| host | `HostXmlParser` | `xml` |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` для host TRAIN/VALIDATION |

Перед массовой нормализацией запускайте authoritative coverage:

```powershell
python manage.py stage-two parser-coverage
```

Report path:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md
PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md
```

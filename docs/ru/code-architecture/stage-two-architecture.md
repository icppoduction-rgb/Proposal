# Stage Two Architecture: Data Normalization

## Назначение

Stage Two превращает filtered dataset files в управляемые normalized artifacts. Authoritative input для Stage Two - `PATH_FOLDER_DATASETS_FILTER`. `PATH_FOLDER_DATASETS` сохраняется как immutable raw source root для Stage One и аудита/traceback, но не сканируется `catalog-ingest` по умолчанию. Stage Two отвечает за:

- catalog ingestion filtered files в PostgreSQL;
- parser registry и проверку покрытия source formats;
- безопасный перевод файлов в `READY_FOR_PARSING`;
- запуск parser implementations;
- запись normalized Parquet;
- регистрацию `parser_runs` и `normalized_artifacts`;
- RU/EN diagnostic reports;
- DuckDB, leakage и readiness checks.

## Пакеты Stage Two

| Путь | Назначение |
| --- | --- |
| `scripts/stage_two/cli.py` | Stage Two CLI router и parsing helpers. |
| `scripts/stage_two/status_tools.py` | `mark-ready` workflow и status transition counts. |
| `scripts/stage_two/parser_coverage.py` | Coverage matrix по catalog/scanner/registry/resolver. |
| `scripts/stage_two/storage/bootstrap.py` | Создание storage/report/parquet directories. |
| `scripts/stage_two/ingestion/scanner.py` | Inference branch/role/source_format/dataset slug. |
| `scripts/stage_two/ingestion/catalog_ingestion_service.py` | Создание ingestion runs, datasets и dataset_files. |
| `scripts/stage_two/parser_registry/seed.py` | Seed `schema_versions` и `parser_registry`. |
| `scripts/stage_two/parser_registry/resolver.py` | Выбор active parser class и class availability validation. |
| `scripts/stage_two/parsers/*` | Parser contracts, UniversalInputReader и parser implementations. |
| `scripts/stage_two/normalization/runner.py` | Shared batch runner для `normalize-format`, `normalize-all` и aliases. |
| `scripts/stage_two/normalization/dns_service.py` | DNS parser service. |
| `scripts/stage_two/normalization/host_service.py` | Host parser service. |
| `scripts/stage_two/parquet/writer.py` | Запись normalized/features/model-ready Parquet. |
| `scripts/stage_two/reports/parser_reports.py` | Parser/normalization/coverage report writer. |
| `scripts/stage_two/labels/resolver.py` | LabelResolver и leakage-safe label mapping. |
| `scripts/stage_two/duckdb/service.py` | DuckDB views/checks over Parquet artifacts. |
| `scripts/stage_two/quality/checkers.py` | Data quality и leakage checks. |
| `scripts/stage_two/traceability/service.py` | Chain lookup от artifact к raw source. |
| `scripts/stage_two/readiness_check.py` | Operational readiness checks. |

## Command lifecycle

```text
bootstrap-storage
  -> alembic upgrade
  -> seed-parser-registry
  -> catalog-ingest
  -> parser-coverage
  -> mark-ready
  -> normalize-format / normalize-all
  -> run-duckdb-checks
  -> run-leakage-checks
  -> readiness_check
```

`seed-parser-registry` и `catalog-ingest` можно запускать повторно: seed должен быть idempotent, ingestion выполняет upsert и фиксирует изменения hash/status.

## Catalog ingestion

`catalog-ingest` использует scanner:

1. Обходит `PATH_FOLDER_DATASETS_FILTER`.
2. Определяет `branch`, `role`, `source_format`, `dataset_slug`.
3. Считает file hash.
4. Создает/обновляет `datasets`.
5. Создает/обновляет `dataset_files`.
6. Создает `ingestion_runs` с counters.

`source_format` должен сохранять compound names: `pcap.csv`, `process.summary.log`, `socket.summary.log`, `netflow_day`, `netflow_ids`, `wls_day`, `auth.log`, `syslog-1` и другие bucket-specific names. Если файл лежит в sorted tree bucket, bucket name имеет приоритет над extension heuristic.

## Parser registry и resolver

Parser registry связывает:

```text
branch + source_format + role -> parser_module + parser_class + parser_name + schema
```

Resolver выбирает только active entries и проверяет, что class импортируется. Missing class должен попадать в coverage diagnostics, а не приводить к скрытому exception во время batch.

Поддерживаемые parser groups:

| Branch | Форматы | Parser classes |
| --- | --- | --- |
| DNS | `csv` | `DnsCsvParser` |
| DNS | `pcap.csv` | `DnsPcapCsvParser` |
| DNS | `txt` | `DnsTxtDomainListParser` |
| DNS | `pcap`, `pcapng`, `cap` | `DnsPacketCaptureParser` |
| Host | `csv` | `HostCsvParser` |
| Host | `json`, `json-1` | `HostJsonLinesParser` |
| Host | line logs: `auth.log`, `syslog*`, `messages*`, `mainlog*`, `journal*`, `mail-*`, `log-*`, `info` | `HostLineLogParser` |
| Host | metric logs: `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | `HostMetricbeatParser` |
| Host | `ghc`, `sc`, `txt` | `HostSyscallTraceParser` |
| Host | `bson` | `HostBsonSandboxParser` |
| Host | `netflow_day`, `netflow_ids`, `wls_day` | `HostNetflowParser` |
| Host | `xml` | `HostXmlParser` |
| Host | `pcap`, `pcapng`, `cap` | `HostPacketCaptureParser` |

## Normalization runner

`normalize-format` обрабатывает строго один `branch/role/source_format`:

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
```

`normalize-all` обрабатывает все `READY_FOR_PARSING` файлы выбранной ветки из `PATH_FOLDER_DATASETS_FILTER`, группируя их по role/source_format:

```powershell
python manage.py stage-two normalize-all --branch dns --limit 1000
```

Файл обрабатывается независимо: ошибка одного файла не должна прерывать весь batch. Runner/service layer регистрирует:

- `parser_runs`;
- parser status/counters/errors;
- normalized Parquet path/hash/row count;
- `normalized_artifacts`;
- parser/normalization reports.

## Parser result contract

Parser classes возвращают `ParseResult`, содержащий normalized `ParsedEvent` records и counters:

- `rows_read`;
- `rows_parsed`;
- `rows_failed`;
- `bytes_read`;
- `files_read`;
- `warnings_count`;
- `parse_errors_count`.

Статусы рассчитываются единообразно:

| Статус | Условие |
| --- | --- |
| `SUCCESS` | Есть parsed rows и нет failures. |
| `PARTIAL_SUCCESS` / `PARTIALLY_PARSED` | Есть parsed rows и есть failed rows. |
| `EMPTY_FILE` | Нет контента. |
| `FAILED` | Parser не смог прочитать файл. |
| `SKIPPED` | Файл намеренно пропущен как helper/context file. |
| `UNSUPPORTED_FORMAT` | Нет parser entry/class для формата. |

## Reports

Reports пишутся в:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/
PATH_DATA_STORAGE/reports/ru/stage-two/parser/
PATH_DATA_STORAGE/reports/en/stage-two/normalization/
PATH_DATA_STORAGE/reports/ru/stage-two/normalization/
```

Coverage reports:

```text
parser_coverage_matrix.json
parser_coverage_matrix.md
```

Parser/normalization reports включают branch, role, source_format, dataset/file IDs, source path/hash, parser info, counters, status, warnings, error samples и encoding/compression/base64 hints. Full raw payload в report не сохраняется.

## Checks

| Команда | Назначение |
| --- | --- |
| `python manage.py stage-two run-duckdb-checks` | Проверяет чтение Parquet и базовые schema/data quality assumptions. |
| `python manage.py stage-two run-leakage-checks` | Проверяет leakage-prone columns, split contamination и label safety. |
| `python -m scripts.stage_two.readiness_check` | Проверяет readiness catalog/storage/parser coverage. |
| `python -m scripts.stage_two.parser_smoke` | Direct parser smokes без full DB dependency. |
| `python -m scripts.stage_two.parser_input_smoke` | Encoding/base64/compression reader smokes. |
| `python -m scripts.stage_two.parser_catalog_smoke` | Synthetic catalog -> parser -> Parquet -> catalog artifact smoke с cleanup/rollback behavior. |
| `python -m scripts.stage_two.cli_operational_smoke` | CLI workflow smoke. |

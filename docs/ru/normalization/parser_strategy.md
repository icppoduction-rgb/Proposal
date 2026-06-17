# Стратегия парсеров

Stage Two нормализует файлы через catalog-driven parser layer:

```text
dataset_files.source_format -> parser_registry -> ParserResolver -> parser class -> normalized Parquet
```

Seed registry хранится в `scripts/stage_two/parser_registry/parser_registry_seed.json` и загружается командой:

```powershell
python manage.py stage-two seed-parser-registry
```

`ParserResolver` выбирает активный parser по `branch`, `source_format`, опциональным `supported_roles` и `priority`. Сервисы нормализации получают классы parser только через resolver и регистрируют `parser_runs` и `normalized_artifacts` для каждого обработанного файла.

## Операционный поток

1. `catalog-ingest` регистрирует файлы в PostgreSQL и сохраняет `branch`, `role`, `source_format`, путь, размер и hash.
2. `parser-coverage` сравнивает catalog formats с активными registry entries и пишет RU/EN отчеты покрытия.
3. `mark-ready` переводит только разрешенные статусы в `READY_FOR_PARSING`.
4. `normalize-format` обрабатывает один срез `branch`/`role`/`source_format`.
5. `normalize-all` обрабатывает все ready-файлы одной ветки по role и format, без смешивания ролей в одной неконтролируемой batch-транзакции.

## Покрытие парсеров

| Branch | Source format | Покрытие ролей | Parser class | Примечание |
| --- | --- | --- | --- | --- |
| dns | `csv` | TRAIN, VALIDATION, TEST | `DnsCsvParser` | Domain lists, headered feature CSV, PhishTank-like rows и DNS TEST 22-column headerless rows. |
| dns | `pcap.csv` | TRAIN, VALIDATION, TEST | `DnsPcapCsvParser` | Packet-derived CSV с DNS/network fields. |
| dns | `txt` | VALIDATION | `DnsTxtDomainListParser` | Validation/domain-list файлы в формате one-domain-per-line. |
| dns | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION, TEST | `DnsPacketCaptureParser` | Summary-level packet extraction без хранения full payload. |
| host | `csv` | TRAIN, VALIDATION, TEST | `HostCsvParser` | ADFA-like rows, headerless CSV, runs-like metadata и безопасная обработка helper-файлов. |
| host | `json`, `json-1` | TRAIN, VALIDATION, TEST | `HostJsonLinesParser` | JSON Lines, JSON arrays, single objects, ECS/Filebeat/Metricbeat-like nested records. |
| host | `auth.log`, `info`, `journal`, `journal~`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `messages`, `messages-1`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log` | TRAIN, VALIDATION, TEST | `HostLineLogParser` | Syslog/auth/mail/journal/raw line logs, включая mixed JSON-lines. |
| host | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | TRAIN, VALIDATION, TEST | `HostLineLogParser` -> `HostMetricbeatParser` | Metric formats остаются совместимыми с registry как line logs и делегируются внутри metric parser. |
| host | `ghc`, `sc`, `txt` | TRAIN, VALIDATION, TEST | `HostSyscallTraceParser` | Syscall/API/trace-like ordered line streams. |
| host | `bson` | TEST | `HostBsonSandboxParser` | BSON sandbox telemetry document streams. |
| host | `netflow_day`, `netflow_ids`, `wls_day` | TRAIN, VALIDATION, TEST | `HostNetflowParser` | Delimited, whitespace, CSV-like или JSON-line network flow и WLS rows. |
| host | `xml` | TRAIN, VALIDATION, TEST | `HostXmlParser` | Безопасный event-like XML без DTD и external entity resolution. |
| host | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION | `HostPacketCaptureParser` | Summary-level host/network packet extraction. |

Матрица покрытия генерируется в:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md`

## Поведение Input Reader

`UniversalInputReader` является общим слоем чтения для parser classes.

- Text, lines, CSV rows, JSON Lines и record modes по возможности работают streaming-режимом.
- Binary modes для PCAP/CAP/PCAPNG/BSON не декодируют bytes как text.
- Encoding detection поддерживает UTF-8 BOM и fallback chain, включая `utf-8`, `utf-8-sig`, `cp1252`, `latin-1`, `ascii`; неустранимые decode-проблемы фиксируются warnings.
- Compression detection поддерживает gzip, bz2, xz/lzma и безопасное in-memory чтение ZIP member без archive path traversal.
- Base64 handling консервативный: whole-file, line-level и JSON payload values декодируются только при успешной validation, размере меньше `STAGE_TWO_MAX_BASE64_DECODE_BYTES` и похожести decoded bytes на поддерживаемый text/structured/binary format.
- Reader metadata сохраняет encoding, compression, base64, decode strategy, bytes read, warnings и errors, но не сохраняет full raw payload.

## Статусы и ошибки

| Status | Значение |
| --- | --- |
| `SUCCESS` | Есть хотя бы одна parsed row/event и нет row-level failures. |
| `PARTIAL_SUCCESS` / `PARTIALLY_PARSED` | Есть parsed row/event и есть хотя бы одна failed row. |
| `EMPTY_FILE` | Во входном файле нет usable content. |
| `FAILED` | Parser не может безопасно прочитать или разобрать файл. |
| `SKIPPED` | Helper/context file намеренно пропущен или отдал только безопасные metadata. |
| `UNSUPPORTED_FORMAT` | Для cataloged format нет активного parser. |

Counters включают `rows_read`, `rows_parsed`, `rows_failed`, `bytes_read`, `files_read`, `warnings_count` и `parse_errors_count`. Error samples ограничены `STAGE_TWO_MAX_ERROR_SAMPLES`.

## CLI-примеры

Покрытие:

```powershell
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
```

Перевод файлов в ready. Dry-run является безопасным режимом по умолчанию; для записи нужен `--apply`:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
```

Нормализация одного выбранного формата:

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role VALIDATION --format pcap --limit 100
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Нормализация branch контролируемыми batch по role/format:

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
python manage.py stage-two normalize-all host:1000
```

Backward-compatible aliases остаются доступны:

```powershell
python manage.py stage-two normalize-host 10
python manage.py stage-two normalize-dns 10
```

## Безопасность labels

Parsers используют `LabelResolver` и не допускают label fields в model input features.

- Role-safe embedded labels и configured `label_mapping_rules` разрешены.
- TEST filename heuristics отключены.
- Отсутствующие labels остаются `label_binary=None` и `label_status=unlabeled`.
- Source path, dataset role, scenario name, parser metadata и file metadata остаются только traceability/context.

## Известные ограничения

- `catalog-ingest` не переводит файлы в `READY_FOR_PARSING` автоматически; после проверки coverage нужно использовать `mark-ready`.
- Host packet capture registry entries активны только для TRAIN и VALIDATION. Для TEST нужно отдельное решение по label/leakage policy.
- BSON sandbox parsing активен только для TEST.
- Packet parsers извлекают summary fields и легковесные DNS details; full packet payload не сохраняется в PostgreSQL, reports или metadata JSON.
- Файлы coverage report отражают последний запуск `parser-coverage`, включая branch filter, если он использовался.

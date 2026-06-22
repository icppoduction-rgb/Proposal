# Стратегия parser registry и выбора parser

Parser strategy состоит из трех частей:

1. `parser_registry_seed.json` описывает поддерживаемые parser groups.
2. `ParserRegistrySeeder` разворачивает groups в строки `parser_registry`.
3. `ParserResolver` выбирает активный parser для конкретного `dataset_files` по `branch`, `role`, `source_format`.

## Seed registry

Файл:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Seed загружается командой:

```bash
python manage.py stage-two seed-parser-registry
```

Seeder проверяет, что `parser_module` и `parser_class` импортируются. Если класс отсутствует или не наследуется от `BaseParser`, entry может быть сохранен как inactive с diagnostic metadata в `config_json.class_validation`.

## Как выбирается parser

`ParserResolver` ищет active entries:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
supported_role == dataset_file.role OR supported_role IS NULL
is_active == true
```

Затем сортирует по `priority`, потом `id`. Role-specific entry имеет преимущество только через порядок/priority; универсальная запись с `supported_role = NULL` подходит для всех ролей.

Если parser не найден:

- `resolve_or_mark_unsupported()` переводит файл в `UNSUPPORTED_FORMAT`;
- `normalize-format` возвращает status `UNSUPPORTED_FORMAT` для выбранного bucket;
- parser run не должен имитировать успешную нормализацию.

## Реализованные parser groups

### DNS

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `DnsCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsPcapCsvParser` | `pcap.csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsTxtDomainListParser` | `txt` | `VALIDATION` | `scripts.stage_two.parsers.dns` |
| `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all active roles | `scripts.stage_two.parsers.dns` |

### Host

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `HostCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.host` |
| `HostJsonLinesParser` | `json`, `json-1` | all active roles | `scripts.stage_two.parsers.host` |
| `HostLineLogParser` | `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `info`, `journal`, `journal~`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `uptime.log` | all active roles | `scripts.stage_two.parsers.host` |
| `HostSyscallTraceParser` | `txt`, `sc`, `ghc` | all active roles | `scripts.stage_two.parsers.host` |
| `HostXmlParser` | `xml` | all active roles | `scripts.stage_two.parsers.host` |
| `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all active roles | `scripts.stage_two.parsers.host` |
| `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | `TRAIN`, `VALIDATION` | `scripts.stage_two.parsers.host` |
| `HostBsonSandboxParser` | `bson` | `TEST` | `scripts.stage_two.parsers.host` |

Metricbeat-like логи обрабатываются через существующие host parser modules/helpers; отдельной active seed group с именем `HostMetricbeatParser` в текущем registry seed нет.

## Lifecycle statuses parser

| Уровень | Status | Значение |
| --- | --- | --- |
| parser run | `SUCCESS` | Parser completed and emitted events without failed rows. |
| parser run | `PARTIAL_SUCCESS` | Parser emitted events, but some rows/records failed. |
| parser run | `FAILED` | Parser failed for the file. |
| parser run | `SKIPPED` | File intentionally skipped. |
| dataset file | `PARSED` | Файл успешно нормализован. |
| dataset file | `PARTIALLY_PARSED` | Есть normalized events, но были ошибки. |
| dataset file | `FAILED` | Нормализация не удалась. |
| dataset file | `SKIPPED` | Файл пропущен по parser/result policy. |
| dataset file | `UNSUPPORTED_FORMAT` | Для `branch/role/source_format` нет parser. |

Stage One analysis statuses вроде `READY_FOR_FEATURE_EXTRACTION`, `NEEDS_CUSTOM_PARSER`, `PARTIALLY_SUPPORTED`, `BROKEN_OR_EMPTY` используются как input guidance для parser strategy, но Stage Two catalog lifecycle использует DB statuses выше.

## Контракт ParserResult

Parser возвращает `ParserResult`:

- `events`: список normalized event rows;
- counters: rows read/parsed/failed, events emitted;
- errors/warnings/metadata;
- optional `status_override`: `EMPTY_FILE`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.

`ParserResult.status_decision` преобразует результат в parser run/file statuses. Empty output без явной причины не должен маскироваться как успешный benign dataset.

## Ошибки и граничные случаи

| Сценарий | Поведение |
| --- | --- |
| Missing parser class | Seed entry становится inactive или получает validation diagnostics. |
| Parser не найден | `dataset_files.status = UNSUPPORTED_FORMAT`. |
| Binary PCAP/PCAPNG большой | Использовать `--packet-mode packet-summary` или `sample`; учитывать performance risk. |
| TEST labels в имени файла | Filename hints отключены для `TEST`. |
| Mixed schema CSV/JSON | Parser должен сохранять неизвестные поля в JSON payload и фиксировать warnings. |
| Partially corrupt file | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, counters должны показывать failed rows. |

## Проверка покрытия

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

Проверка сравнивает зарегистрированные `dataset_files` combinations с `parser_registry`. Ее нужно запускать после `catalog-ingest` и `seed-parser-registry`.

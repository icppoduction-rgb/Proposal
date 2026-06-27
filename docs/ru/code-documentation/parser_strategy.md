# Стратегия парсеров

Стратегия парсеров состоит из seed JSON, PostgreSQL `parser_registry`, `ParserResolver`, конкретных parser classes и контрактов статусов парсинга.

## Заполнение registry

Seed-файл: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Команда seed:

```bash
python manage.py stage-two seed-parser-registry
```

Каждая parser group задает:

| Поле | Значение |
|---|---|
| `parser_name` | логический parser id |
| `parser_version` | версия parser |
| `branch` | `dns` или `host` в текущем seed |
| `source_formats` | один или несколько source format buckets |
| `supported_roles` | null для всех ролей или явный список ролей |
| `normalized_schema_name/version` | целевая normalized schema |
| `parser_module` | Python module |
| `parser_class` | имя class |
| `priority` | меньшее значение имеет приоритет |
| `supports_streaming` | registry metadata |
| `requires_external_tools` | registry metadata |

Валидация seed импортирует класс и проверяет `issubclass(BaseParser)`. Отсутствующие классы сохраняются как inactive rows с диагностикой.

## Разрешение parser

Файл: `scripts/stage_two/parser_registry/resolver.py`.

Запрос выбора:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
is_active == true
supported_role == dataset_file.role OR supported_role IS NULL
ORDER BY priority, id
```

Если подходящая запись не найдена, file получает статус `UNSUPPORTED_FORMAT`.

## Базовый контракт parser

Файл: `scripts/stage_two/parsers/base.py`.

Конкретный parser должен реализовать:

```python
class MyParser(BaseParser):
    parser_name = "..."
    parser_version = "v1"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        ...
```

Потоковые parsers должны переопределять `parse_batches()`.

`ParserContext` передает catalog metadata:

```text
dataset_id, file_id, dataset_name, dataset_role, branch, source_format,
source_file_path, source_file_hash, parser_run_id, metadata
```

`ParserResult` передает counters, events, warnings, bytes read, error samples и optional status override.

## Маппинг статусов

| Условие parser | Статус parser | `parser_runs.status` | `dataset_files.status` |
|---|---|---|---|
| строки распарсены, ошибок нет | `SUCCESS` | `SUCCESS` | `PARSED` |
| часть строк распарсена, часть завершилась ошибкой | `PARTIAL_SUCCESS` | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| ни одна строка не распарсена | `FAILED` | `FAILED` | `FAILED` |
| ошибка чтения | `FAILED` | `FAILED` | `FAILED` |
| empty file | `EMPTY_FILE` | `SKIPPED` | `EMPTY_FILE` |
| unsupported format | `UNSUPPORTED_FORMAT` | `SKIPPED` | `UNSUPPORTED_FORMAT` |
| intentionally skipped | `SKIPPED` | `SKIPPED` | `SKIPPED` |

В формулировке задачи упомянут `PARTIALLY_PARSED`; в текущем коде это статус файла, а статус parser run равен `PARTIAL_SUCCESS`.

## Классы DNS parser

| Класс | Модуль | Source formats | Примечания |
|---|---|---|---|
| `DnsCsvParser` | `scripts.stage_two.parsers.dns` | `csv` | DNS CSV с учетом схемы, поддерживает TEST CSV без header |
| `DnsPcapCsvParser` | `scripts.stage_two.parsers.dns` | `pcap.csv` | расширяет обработку DNS CSV для CSV, полученных из packet data |
| `DnsTxtDomainListParser` | `scripts.stage_two.parsers.dns` | `txt` для `VALIDATION` | parser списков доменов |
| `DnsPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` | packet summary parser, DNS modality для DNS packets |

## Классы Host parser

| Класс | Модуль | Source formats | Примечания |
|---|---|---|---|
| `HostCsvParser` | `scripts.stage_two.parsers.host` | `csv` | host CSV/event/metadata tables |
| `HostJsonLinesParser` | `scripts.stage_two.parsers.host` | `json`, `json-1` | JSON lines, arrays, objects и смешанная telemetry |
| `HostLineLogParser` | `scripts.stage_two.parsers.host` | многие `*.log`, rotated logs, `messages`, `syslog`, `mainlog` | line-oriented log parser |
| `HostSyscallTraceParser` | `scripts.stage_two.parsers.host` | `txt`, `sc`, `ghc` | syscall/API traces |
| `HostPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` для `TRAIN`, `VALIDATION` | host network packet summaries |
| `HostBsonSandboxParser` | `scripts.stage_two.parsers.bson` | `bson` для `TEST` | BSON sandbox process/API telemetry |

Дополнительные реализованные и seed-нутые классы:

| Класс | Модуль | Source formats |
|---|---|---|
| `HostXmlParser` | `scripts.stage_two.parsers.host` через import from `xml.py` | `xml` |
| `HostNetflowParser` | `scripts.stage_two.parsers.host` через import from `netflow.py` | `netflow_day`, `netflow_ids`, `wls_day` |

Дополнительно реализовано, но не включено напрямую в текущий seed:

| Класс | Модуль | Примечания |
|---|---|---|
| `HostMetricbeatParser` | `scripts.stage_two.parsers.metrics` | используется/импортируется для поддержки Metricbeat-like telemetry |

## Неподдерживаемые форматы

Неподдерживаемый формат означает, что для `(branch, role, source_format)` нет active row в parser registry. Обработка:

1. `ParserResolver.resolve_or_mark_unsupported()` выставляет `dataset_files.status='UNSUPPORTED_FORMAT'`.
2. `normalize-format` возвращает status `UNSUPPORTED_FORMAT`, если для выбранных файлов нет parser.
3. Parser coverage report показывает gaps.

## Обработка ошибок

- Ошибки парсинга отдельных строк увеличивают `rows_failed` и сохраняют ограниченные error samples.
- Исключения parser помечают `parser_runs.status='FAILED'` и `dataset_files.status='FAILED'`.
- `save_parser_run_reports()` пишет parser diagnostics.
- `STAGE_TWO_MAX_ERROR_SAMPLES` ограничивает error samples.

## Чеклист расширения parser

1. Добавить parser class в `scripts/stage_two/parsers`.
2. Наследовать `BaseParser`.
3. Отдавать events через `base_event()`.
4. Сохранять `timestamp_type`, `event_index`, labels и traceability fields.
5. Добавить entry в parser registry seed.
6. Запустить parser tests и `python manage.py stage-two seed-parser-registry`.
7. Запустить `python manage.py stage-two parser-coverage <branch>`.

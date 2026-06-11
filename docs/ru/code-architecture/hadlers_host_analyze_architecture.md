# Архитектура handlers: host_analyze

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Общая цепочка вызовов](#4-общая-цепочка-вызовов)
- [5. Router и run_action](#5-router-и-run_action)
- [6. Общий контракт Host content-analysis handler](#6-общий-контракт-host-content-analysis-handler)
- [7. Host TRAIN handlers](#7-host-train-handlers)
- [8. Host TEST handlers](#8-host-test-handlers)
- [9. Host VALIDATION handlers](#9-host-validation-handlers)
- [10. Наследование и переиспользование логики](#10-наследование-и-переиспользование-логики)
- [11. Выходные артефакты](#11-выходные-артефакты)
- [12. Ошибки и ограничения](#12-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/host_analyze` анализирует содержимое отсортированных Host-файлов и генерирует техническую документацию по каждому формату. Service работает после этапов:

1. `analyze-dataset host-dataset-handler`;
2. `filter-dataset filter-host-dataset-handler`;
3. `sort sort-host-dataset-handler`;
4. `save-sort save-sort-host-dataset-handler`.

Главный вход для всех Host analysis handlers:

```text
PATH_TEMP_DATA/sort-path-host-file.json
```

## 2. Файлы пакета

| Группа файлов | Назначение |
|---|---|
| `router_host.py` | Сопоставляет строковый action с функцией запуска. |
| `run_action.py` | Создает нужный handler-класс и печатает результат. |
| `__init__.py` | Экспортирует все Host content-analysis handlers. |
| `analyze_host_*_dataset_handler.py` | Анализ конкретного role/format набора. |

Пакет покрывает три группы:

- Host `TRAIN`;
- Host `TEST`;
- Host `VALIDATION`.

## 3. Как запускается service

Формат:

```bash
python manage.py handlers host-analyze <action>
```

Примеры:

```bash
python manage.py handlers host-analyze analyze-csv-content
python manage.py handlers host-analyze analyze-test-json-content
python manage.py handlers host-analyze analyze-validation-pcapng-content
```

## 4. Общая цепочка вызовов

```text
python manage.py handlers host-analyze <action>
-> manage.manage()
-> router_commands("handlers", "host-analyze", action)
-> router_commands_handlers("host-analyze", action)
-> router_host(action)
-> analyze_*_content()
-> Host*ContentAnalysisHandler(PATH_TEMP_DATA, PROJECT_ROOT, PATH_REPORT)
-> analyze_and_generate_docs()
-> _read_source_json() / _read_host_source_json()
-> _extract_*_paths(...) / _extract_paths(...)
-> _select_sample_paths(...)
-> _build_summary(...)
-> JsonDataManager(summary_json).write(...)
-> _build_ru_markdown(...) / _build_en_markdown(...) / _build_markdown(...)
-> _build_ru_readme(...) / _build_en_readme(...) / _build_readme(...)
-> _build_ru_report(...) / _build_en_report(...) / _build_report(...)
-> _write_text_file(...)
-> print_data(...)
```

## 5. Router и run_action

### `router_host(action: str)`

`router_host` содержит длинную цепочку `if/elif`. Каждая ветка сравнивает `action` со строкой команды и вызывает функцию из `run_action.py`.

Если action неизвестен, печатается `manage_commands`.

### `run_action.py`

Каждая функция запуска:

1. Создает конкретный handler-класс.
2. Передает:
   - `temp_data_path=PATH_TEMP_DATA`;
   - `project_root=PROJECT_ROOT`;
   - `report_path=PATH_REPORT`.
3. Вызывает `handler.analyze_and_generate_docs()`.
4. Передает результат в `print_data()`.

`print_data()` выводит:

- summary JSON;
- RU/EN docs;
- RU/EN README;
- RU/EN reports;
- total files;
- sampled files;
- status.

## 6. Общий контракт Host content-analysis handler

### Входной JSON

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

### Result dataclass

Почти каждый handler возвращает dataclass с полями:

- `summary_json_file`;
- `docs_ru_file`;
- `docs_en_file`;
- `docs_ru_readme_file`;
- `docs_en_readme_file`;
- `report_ru_file`;
- `report_en_file`;
- `total_files_count`;
- `sampled_files_count`;
- `status`.

### Типовые методы

| Метод | Назначение |
|---|---|
| `analyze_and_generate_docs()` | Главный orchestration method. |
| `_read_source_json()` / `_read_host_source_json()` | Читает `sort-path-host-file.json`. |
| `_extract_paths()` / `_extract_<format>_paths()` | Извлекает пути нужной роли и формата. |
| `_select_sample_paths()` | Выбирает sample для больших наборов. |
| `_build_summary()` | Формирует technical summary. |
| `_detect_encoding()` | Подбирает кодировку для текстовых файлов. |
| `_infer_type()` / `_safe_extract_numeric()` | Определяет типы/числа. |
| `_build_ru_markdown()` / `_build_en_markdown()` / `_build_markdown()` | Генерирует документацию. |
| `_build_ru_readme()` / `_build_en_readme()` / `_build_readme()` | Генерирует индекс директории. |
| `_build_ru_report()` / `_build_en_report()` / `_build_report()` | Генерирует отчет. |
| `_load_host_format_counts()` / `_load_host_test_format_counts()` / `_load_counts()` | Загружает count-сводки. |
| `_load_optional_status()` | Подтягивает статус другого анализа. |
| `_summary_json_excerpt()` | Готовит короткий JSON-фрагмент для report. |
| `_write_text_file()` | Создает директорию и пишет markdown. |

## 7. Host TRAIN handlers

Actions без префикса `test` или `validation` относятся к Host TRAIN.

| Action | Handler | Основная задача |
|---|---|---|
| `analyze-csv-content` | `HostCSVContentAnalysisHandler` | CSV schema, delimiter, header, field statistics. |
| `analyze-auth-log-content` | `HostAuthLogContentAnalysisHandler` | Auth log messages, actions, host/security indicators. |
| `analyze-cpu-log-content` | `HostCPULogContentAnalysisHandler` | CPU numeric metrics. |
| `analyze-diskio-log-content` | `HostDiskioLogContentAnalysisHandler` | Disk IO numeric metrics. |
| `analyze-filesystem-log-content` | `HostFilesystemLogContentAnalysisHandler` | Filesystem metrics and status. |
| `analyze-fsstat-log-content` | `HostFSStatLogContentAnalysisHandler` | FS stat metrics. |
| `analyze-ghc-content` | `HostGHCContentAnalysisHandler` | GHC/scenario-like host traces. |
| `analyze-info-content` | `HostInfoContentAnalysisHandler` | Info messages and action markers. |
| `analyze-journal-content` | `HostJournalContentAnalysisHandler` | Journal-style text statistics. |
| `analyze-journal-tilde-content` | `HostJournalTildeContentAnalysisHandler` | `journal~` rotated/backup variant. |
| `analyze-json-content` | `HostJSONContentAnalysisHandler` | JSON/raw JSON-like files. |
| `analyze-json-1-content` | `HostJSON1ContentAnalysisHandler` | `json-1` rotated variant. |
| `analyze-load-log-content` | `HostLoadLogContentAnalysisHandler` | Load metrics. |
| `analyze-log-content` | `HostLogContentAnalysisHandler` | Generic log files. |
| `analyze-log-1-content` | `HostLog1ContentAnalysisHandler` | Rotated `log-1`. |
| `analyze-log-2-content` | `HostLog2ContentAnalysisHandler` | Rotated `log-2`. |
| `analyze-log-3-content` | `HostLog3ContentAnalysisHandler` | Rotated `log-3`. |
| `analyze-mail-info-1-content` | `HostMailInfo1ContentAnalysisHandler` | Mail info logs. |
| `analyze-mail-warn-1-content` | `HostMailWarn1ContentAnalysisHandler` | Mail warning logs. |
| `analyze-mainlog-content` | `HostMainlogContentAnalysisHandler` | Main logs. |
| `analyze-mainlog-1-content` | `HostMainlog1ContentAnalysisHandler` | Rotated mainlog-1. |
| `analyze-mainlog-2-content` | `HostMainlog2ContentAnalysisHandler` | Rotated mainlog-2. |
| `analyze-mainlog-3-content` | `HostMainlog3ContentAnalysisHandler` | Rotated mainlog-3. |
| `analyze-memory-log-content` | `HostMemoryLogContentAnalysisHandler` | Memory metrics. |
| `analyze-messages-content` | `HostMessagesContentAnalysisHandler` | System messages. |
| `analyze-messages-1-content` | `HostMessages1ContentAnalysisHandler` | Rotated messages-1. |
| `analyze-netflow-ids-content` | `HostNetflowIdsContentAnalysisHandler` | Netflow id files. |
| `analyze-network-log-content` | `HostNetworkLogContentAnalysisHandler` | Network metrics. |
| `analyze-pcap-content` | `HostPCAPContentAnalysisHandler` | PCAP-like host files. |
| `analyze-process-log-content` | `HostProcessLogContentAnalysisHandler` | Process metrics/logs. |
| `analyze-process-summary-log-content` | `HostProcessSummaryLogContentAnalysisHandler` | Process summary metrics. |
| `analyze-sc-content` | `HostSCContentAnalysisHandler` | SC trace format. |
| `analyze-service-log-content` | `HostServiceLogContentAnalysisHandler` | Service metrics/logs. |
| `analyze-socket-summary-log-content` | `HostSocketSummaryLogContentAnalysisHandler` | Socket summary metrics. |
| `analyze-syslog-content` | `HostSyslogContentAnalysisHandler` | Syslog format. |
| `analyze-syslog-1-content` | `HostSyslog1ContentAnalysisHandler` | Rotated syslog-1. |
| `analyze-syslog-2-content` | `HostSyslog2ContentAnalysisHandler` | Rotated syslog-2. |
| `analyze-syslog-3-content` | `HostSyslog3ContentAnalysisHandler` | Rotated syslog-3. |
| `analyze-syslog-4-content` | `HostSyslog4ContentAnalysisHandler` | Rotated syslog-4. |
| `analyze-syslog-log-content` | `HostSyslogLogContentAnalysisHandler` | `syslog.log` semantic format. |
| `analyze-txt-content` | `HostTXTContentAnalysisHandler` | Text host traces. |
| `analyze-uptime-log-content` | `HostUptimeLogContentAnalysisHandler` | Uptime metrics. |
| `analyze-xml-content` | `HostXMLContentAnalysisHandler` | XML content structure. |

### TRAIN handler patterns

TRAIN handlers делятся на несколько типов:

- CSV-specific: `HostCSVContentAnalysisHandler` использует `CSVFileProbe`, delimiter/header detection и field statistics.
- Numeric log handlers: CPU, diskio, filesystem, fsstat, load, memory, network, process, service, socket, uptime извлекают числовые признаки и статистики.
- Text/log handlers: auth, info, journal, log, mail, messages, syslog анализируют строки, prefix/action patterns и примеры.
- Structured handlers: JSON/XML/PCAP/SC/GHC строят summary по структуре или техническим признакам формата.

## 8. Host TEST handlers

| Action | Handler | Важные классы/методы |
|---|---|---|
| `analyze-test-bson-content` | `HostTestBSONContentAnalysisHandler` | `BSONFileProbe`, `BSONDocumentProbe.parse_many()`, `_parse_document()` |
| `analyze-test-csv-content` | `HostTestCSVContentAnalysisHandler` | `CSVProbe`, `_probe_file()`, `_infer_type()` |
| `analyze-test-json-content` | `HostTestJSONContentAnalysisHandler` | `JSONProbe`, `_parse_json_like()`, `_classify_schema()`, `_collect_record()` |
| `analyze-test-log-content` | `HostTestLogContentAnalysisHandler` | `LogProbe`, `_message_prefix()`, `_render_counter_rows()` |
| `analyze-test-netflow-day-content` | `HostTestNetflowDayContentAnalysisHandler` | `NetflowDayProbe`, `_infer_type()`, `_render_fields()` |
| `analyze-test-txt-content` | `HostTestTXTContentAnalysisHandler` | `TXTProbe`, `_parse_key_value_line()`, `_infer_type()` |
| `analyze-test-wls-day-content` | `HostTestWLSDayContentAnalysisHandler` | `WLSDayProbe`, `_format_example()`, `_render_fields()` |

TEST handlers обычно пишут документы в:

```text
docs/ru/analysis-dataset/host/test
docs/en/analysis-dataset/host/test
```

## 9. Host VALIDATION handlers

| Action | Handler | Важные классы/методы |
|---|---|---|
| `analyze-validation-cap-content` | `HostValidationCAPContentAnalysisHandler` | `CAPProbe`, `_probe_cap()`, `_decode_ethernet_packet()` |
| `analyze-validation-csv-content` | `HostValidationCSVContentAnalysisHandler` | `_extract_paths()`, `_build_summary()`, `_fields_table()` |
| `analyze-validation-json-content` | `HostValidationJSONContentAnalysisHandler` | `_collect_record()`, `_get_nested()`, `_format_example()` |
| `analyze-validation-netflow-day-content` | `HostValidationNetflowDayContentAnalysisHandler` | наследует TEST netflow logic |
| `analyze-validation-pcap-content` | `HostValidationPCAPContentAnalysisHandler` | наследует CAP logic |
| `analyze-validation-pcapng-content` | `HostValidationPCAPNGContentAnalysisHandler` | `PCAPNGProbe`, `_probe_pcapng()`, `_decode_ethernet_packet()` |
| `analyze-validation-txt-content` | `HostValidationTXTContentAnalysisHandler` | наследует TEST txt logic |
| `analyze-validation-wls-day-content` | `HostValidationWLSDayContentAnalysisHandler` | наследует TEST wls_day logic |

VALIDATION handlers пишут документы в:

```text
docs/ru/analysis-dataset/host/validation
docs/en/analysis-dataset/host/validation
```

## 10. Наследование и переиспользование логики

В `host_analyze` есть явное наследование:

| Класс | Наследуется от | Назначение |
|---|---|---|
| `HostValidationNetflowDayContentAnalysisHandler` | `HostTestNetflowDayContentAnalysisHandler` | Переиспользует netflow_day parsing для validation. |
| `HostValidationPCAPContentAnalysisHandler` | `HostValidationCAPContentAnalysisHandler` | Переиспользует packet/cap analysis logic для pcap. |
| `HostValidationTXTContentAnalysisHandler` | `HostTestTXTContentAnalysisHandler` | Переиспользует txt parsing. |
| `HostValidationWLSDayContentAnalysisHandler` | `HostTestWLSDayContentAnalysisHandler` | Переиспользует wls_day parsing. |

Кроме наследования, много handlers имеют одинаковую структуру методов. Это упрощает чтение, но приводит к дублированию генерации markdown/readme/report.

## 11. Выходные артефакты

Типовые выходы:

```text
PATH_TEMP_DATA/analysis-host-*-summary.json
docs/ru/analysis-dataset/host/<role>/<format>.md
docs/en/analysis-dataset/host/<role>/<format>.md
docs/ru/analysis-dataset/host/<role>/README.md
docs/en/analysis-dataset/host/<role>/README.md
PATH_REPORT/ru/stage-one/analysis-dataset/host/<role>/*.md
PATH_REPORT/en/stage-one/analysis-dataset/host/<role>/*.md
```

Status обычно принимает значения:

- `READY_FOR_FEATURE_EXTRACTION`;
- `PARTIALLY_SUPPORTED`;
- `NEEDS_CUSTOM_PARSER`;
- `BROKEN_OR_EMPTY`.

## 12. Ошибки и ограничения

- Все handlers зависят от свежего `sort-path-host-file.json`.
- Если нужный format отсутствует в JSON, часть handlers выбрасывает `ValueError`.
- Большие наборы анализируются по sample, поэтому summary отражает выборку.
- Для бинарных/packet форматов анализ ограничен техническим пробингом и не заменяет специализированный parser.
- Добавление нового Host format требует синхронных изменений в handler-файле, `__init__.py`, `run_action.py`, `router_host.py`, `manage_commands` и, возможно, `HostDatasetSortHandler._detect_format_group()`.
- В пакете много повторяющегося кода генерации markdown/report; при изменении структуры документации нужно обновлять несколько handlers.

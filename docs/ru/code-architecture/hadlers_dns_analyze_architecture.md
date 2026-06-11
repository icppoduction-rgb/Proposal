# Архитектура handlers: dns_analyze

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Общая цепочка вызовов](#4-общая-цепочка-вызовов)
- [5. Router и run_action](#5-router-и-run_action)
- [6. Общий контракт content-analysis handler](#6-общий-контракт-content-analysis-handler)
- [7. DNS TRAIN handlers](#7-dns-train-handlers)
- [8. DNS TEST handlers](#8-dns-test-handlers)
- [9. DNS VALIDATION handlers](#9-dns-validation-handlers)
- [10. Выходные артефакты](#10-выходные-артефакты)
- [11. Ошибки и ограничения](#11-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/dns_analyze` анализирует содержимое DNS-файлов после сортировки и экспорта путей. Service читает `sort-path-dns-file.json`, выбирает конкретную роль и формат, строит summary JSON и генерирует двуязычную markdown-документацию.

Этот service является последним этапом DNS pipeline.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `router_dns.py` | Маршрутизирует DNS analysis actions. |
| `run_action.py` | Создает нужные handler-классы и печатает результат. |
| `__init__.py` | Экспортирует DNS content-analysis handler-классы. |
| `analyze_dns_train_csv_dataset_handler.py` | Анализ `TRAIN/csv`. |
| `analyze_dns_train_pcap_dataset_handler.py` | Анализ `TRAIN/pcap`. |
| `analyze_dns_train_pcap_csv_dataset_handler.py` | Анализ `TRAIN/pcap.csv`. |
| `analyze_dns_test_csv_dataset_handler.py` | Анализ `TEST/csv`. |
| `analyze_dns_test_pcap_dataset_handler.py` | Анализ `TEST/pcap`. |
| `analyze_dns_test_pcap_csv_dataset_handler.py` | Анализ `TEST/pcap.csv`. |
| `analyze_dns_validation_pcap_dataset_handler.py` | Анализ `VALIDATION/pcap`. |
| `analyze_dns_validation_txt_dataset_handler.py` | Анализ `VALIDATION/txt`. |

## 3. Как запускается service

Формат:

```bash
python manage.py handlers dns-analyze <action>
```

Перед запуском должен существовать:

```text
PATH_TEMP_DATA/sort-path-dns-file.json
```

Обычно файл создается командой:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

## 4. Общая цепочка вызовов

```text
python manage.py handlers dns-analyze <action>
-> manage.manage()
-> router_commands("handlers", "dns-analyze", action)
-> router_commands_handlers("dns-analyze", action)
-> router_dns(action)
-> analyze_*_content()
-> DNS*ContentAnalysisHandler(PATH_TEMP_DATA, PROJECT_ROOT, PATH_REPORT)
-> analyze_and_generate_docs()
-> _read_source_json()
-> _extract_paths(...)
-> _select_sample_paths(...)                 # если handler использует sampling
-> _build_summary(...)
-> JsonDataManager(summary_json).write(...)
-> _build_markdown(...) / _build_readme(...) / _build_report(...)
-> _write_text_file(...)
-> print_data(...)
```

## 5. Router и run_action

### `router_dns(action: str)`

| Action | Функция запуска |
|---|---|
| `analyze-train-csv-content` | `analyze_train_csv_content()` |
| `analyze-train-pcap-content` | `analyze_train_pcap_content()` |
| `analyze-train-pcap-csv-content` | `analyze_train_pcap_csv_content()` |
| `analyze-test-csv-content` | `analyze_test_csv_content()` |
| `analyze-test-pcap-content` | `analyze_test_pcap_content()` |
| `analyze-test-pcap-csv-content` | `analyze_test_pcap_csv_content()` |
| `analyze-validation-pcap-content` | `analyze_validation_pcap_content()` |
| `analyze-validation-txt-content` | `analyze_validation_txt_content()` |

Неизвестный action печатает `manage_commands`.

### `run_action.py`

Каждая функция:

1. Создает handler-класс.
2. Передает `PATH_TEMP_DATA`, `PROJECT_ROOT`, `PATH_REPORT`.
3. Вызывает `analyze_and_generate_docs()`.
4. Передает результат в `print_data()`.

`print_data(description, result)` выводит:

- summary JSON;
- RU/EN docs;
- RU/EN README;
- RU/EN reports;
- total/sample counts;
- status.

## 6. Общий контракт content-analysis handler

Большинство DNS handlers следуют одному шаблону.

### Вход

```text
PATH_TEMP_DATA/sort-path-dns-file.json
```

Форма:

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  }
}
```

### Основной метод

`analyze_and_generate_docs()`:

1. Читает source JSON.
2. Извлекает список путей для фиксированной роли и формата.
3. Выбирает sample, если файлов больше лимита.
4. Строит summary.
5. Пишет summary JSON в `PATH_TEMP_DATA`.
6. Пишет RU/EN markdown docs в `docs/...`.
7. Пишет RU/EN `README.md`.
8. Пишет RU/EN report в `PATH_REPORT`.
9. Возвращает result dataclass.

### Типовые helper methods

| Метод | Назначение |
|---|---|
| `_read_source_json()` | Читает `sort-path-dns-file.json`. |
| `_extract_paths(...)` | Возвращает пути нужной роли/формата. |
| `_select_sample_paths(...)` | Выбирает равномерную выборку файлов. |
| `_build_summary(...)` | Формирует техническое summary. |
| `_build_markdown(...)` | Генерирует документ формата. |
| `_build_readme(...)` | Генерирует индекс директории. |
| `_build_report(...)` | Генерирует report. |
| `_load_counts()` | Читает счетчики форматов, если нужны для README. |
| `_load_optional_status()` | Читает статус другого summary, если нужен для сводки. |
| `_summary_json_excerpt()` | Формирует короткий JSON excerpt для отчета. |
| `_write_text_file(...)` | Создает директорию и пишет markdown. |

## 7. DNS TRAIN handlers

### `DNSTrainCSVContentAnalysisHandler`

Файл:

- `analyze_dns_train_csv_dataset_handler.py`

Назначение: анализирует `TRAIN/csv` файлы с domain/DNS табличными признаками.

Классы:

| Класс | Назначение |
|---|---|
| `DNSTrainCSVContentAnalysisResult` | Результат генерации summary/docs/reports. |
| `CSVProbe` | Техническая проба одного CSV-файла. |
| `DNSTrainCSVContentAnalysisHandler` | Основной handler. |

Важные методы:

- `_probe_file()` читает CSV, определяет header, число строк, распределение колонок, ошибки парсинга.
- `_schema_kind()` классифицирует схему.
- `_class_hint()` извлекает подсказку класса из имени/пути.
- `_infer_type()` определяет тип значения.
- `_fields_table()` строит markdown-таблицу полей.

### `DNSTrainPCAPContentAnalysisHandler`

Файл:

- `analyze_dns_train_pcap_dataset_handler.py`

Назначение: анализирует `TRAIN/pcap` packet capture файлы.

Классы:

- `DNSTrainPCAPContentAnalysisResult`;
- `DNSPCAPProbe`;
- `DNSTrainPCAPContentAnalysisHandler`.

Важные методы:

- `_probe_file()` собирает технические признаки PCAP;
- `_build_summary()` определяет статус и пригодность к feature extraction;
- `_load_optional_status()` подтягивает дополнительные статусы для сводок.

### `DNSTrainPCAPCSVContentAnalysisHandler`

Файл:

- `analyze_dns_train_pcap_csv_dataset_handler.py`

Назначение: анализирует CSV-производные из PCAP (`TRAIN/pcap.csv`).

Классы:

- `DNSTrainPCAPCSVContentAnalysisResult`;
- `PCAPCSVProbe`;
- `DNSTrainPCAPCSVContentAnalysisHandler`.

Важные методы:

- `_probe_csv()` анализирует строки и колонки;
- `_field_summaries()` собирает сведения о полях;
- `_class_hint()` помогает определить класс по имени файла.

## 8. DNS TEST handlers

### `DNSTestCSVContentAnalysisHandler`

Файл:

- `analyze_dns_test_csv_dataset_handler.py`

Назначение: анализирует `TEST/csv` данные для проверки inference-ready обработки.

Классы:

- `DNSTestCSVContentAnalysisResult`;
- `DNSTestCSVProbe`;
- `DNSTestCSVContentAnalysisHandler`.

Особенности:

- использует `_probe_csv()` и `_field_summaries()`;
- строит статус для тестового CSV;
- генерирует README и reports для TEST директории.

### `DNSTestPCAPContentAnalysisHandler`

Файл:

- `analyze_dns_test_pcap_dataset_handler.py`

Назначение: описывает `TEST/pcap` набор. Если файлов нет или они пустые, формирует статус `BROKEN_OR_EMPTY`.

### `DNSTestPCAPCSVContentAnalysisHandler`

Файл:

- `analyze_dns_test_pcap_csv_dataset_handler.py`

Назначение: описывает `TEST/pcap.csv` набор, включая случаи пустого или отсутствующего набора.

## 9. DNS VALIDATION handlers

### `DNSValidationPCAPContentAnalysisHandler`

Файл:

- `analyze_dns_validation_pcap_dataset_handler.py`

Наследуется от:

```text
DNSTrainPCAPContentAnalysisHandler
```

Назначение: переиспользует train PCAP analysis logic, но меняет роль, директории документов и тексты отчетов для `VALIDATION/pcap`.

Ключевые методы:

- `analyze_and_generate_docs()`;
- `_build_validation_markdown()`;
- `_build_validation_readme()`;
- `_build_validation_report()`;
- `_label_values()`.

### `DNSValidationTXTContentAnalysisHandler`

Файл:

- `analyze_dns_validation_txt_dataset_handler.py`

Назначение: анализирует `VALIDATION/txt`, проверяет domain-like строки и class hints.

Классы:

- `DNSValidationTXTContentAnalysisResult`;
- `DNSTXTProbe`;
- `DNSValidationTXTContentAnalysisHandler`.

Важные методы:

- `_probe_txt()` читает и классифицирует текстовые строки;
- `_is_domain_like()` проверяет, похожа ли строка на домен;
- `_class_hint()` извлекает класс из пути/имени.

## 10. Выходные артефакты

Каждый handler возвращает dataclass с полями:

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

Типовые пути:

```text
PATH_TEMP_DATA/analysis-dns-*-summary.json
docs/ru/analysis-dataset/dns/<role>/<format>.md
docs/en/analysis-dataset/dns/<role>/<format>.md
PATH_REPORT/ru/stage-one/analysis-dataset/dns/<role>/*.md
PATH_REPORT/en/stage-one/analysis-dataset/dns/<role>/*.md
```

## 11. Ошибки и ограничения

- Все DNS analysis routes зависят от `sort-path-dns-file.json`.
- Если в JSON нет нужной роли или формата, handler выбрасывает `ValueError` или сообщает о пустом наборе в summary, в зависимости от реализации.
- Sampling ограничивает глубину анализа больших наборов.
- PCAP handlers дают технический обзор, но не заменяют полноценный packet parser.
- Добавление нового формата требует изменений в handler-файле, `__init__.py`, `run_action.py`, `router_dns.py` и `manage_commands`.

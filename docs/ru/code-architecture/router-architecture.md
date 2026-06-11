# Архитектура маршрутов команд

## Оглавление

- [1. Назначение документа](#1-назначение-документа)
- [2. Общая модель команды](#2-общая-модель-команды)
- [3. Путь выполнения команды](#3-путь-выполнения-команды)
- [4. Уровень `module`](#4-уровень-module)
- [5. Уровень `service`](#5-уровень-service)
- [6. Уровень `action`](#6-уровень-action)
- [7. Маршруты `analyze-dataset`](#7-маршруты-analyze-dataset)
- [8. Маршруты `filter-dataset`](#8-маршруты-filter-dataset)
- [9. Маршруты `sort`](#9-маршруты-sort)
- [10. Маршруты `save-sort`](#10-маршруты-save-sort)
- [11. Маршруты `dns-analyze`](#11-маршруты-dns-analyze)
- [12. Маршруты `host-analyze`](#12-маршруты-host-analyze)
- [13. Поведение при неизвестных командах](#13-поведение-при-неизвестных-командах)
- [14. Зависимости маршрутов от конфигурации](#14-зависимости-маршрутов-от-конфигурации)
- [15. Как добавить новый маршрут](#15-как-добавить-новый-маршрут)
- [16. Технические замечания](#16-технические-замечания)

## 1. Назначение документа

Документ описывает, как команды из `manage.py` проходят через маршрутизаторы в `scripts/*`, какие `service` и `action` поддерживаются, какие обработчики вызываются и какие входные/выходные артефакты ожидаются на каждом маршруте.

Маршруты реализованы без отдельного CLI framework: команда разбирается через `argparse`, затем передается в цепочку функций-router. Каждый router сравнивает строковое значение аргумента с поддерживаемыми командами через `if/elif`.

## 2. Общая модель команды

Базовый формат:

```bash
python manage.py <module> <service> <action>
```

В текущем коде поддерживается только один `module`:

```bash
python manage.py handlers <service> <action>
```

Аргументы:

| Аргумент | Источник | Назначение |
|---|---|---|
| `module` | `manage.py` | Верхний раздел команд. Сейчас рабочее значение только `handlers`. |
| `service` | `scripts/handlers/router_handler.py` | Группа маршрутов: анализ, фильтрация, сортировка, экспорт путей или content-analysis. |
| `action` | router конкретного service | Конкретное действие внутри service. |

`manage.py` использует `parse_known_args()`, поэтому неизвестные дополнительные аргументы не вызывают ошибку argparse и сейчас просто игнорируются.

## 3. Путь выполнения команды

Общая цепочка вызовов:

```text
python manage.py handlers <service> <action>
        |
        v
manage.manage()
        |
        v
scripts.router_script.router_commands(module, service, action)
        |
        v
scripts.handlers.router_handler.router_commands_handlers(service, action)
        |
        v
service router
        |
        v
run function
        |
        v
handler class
```

Пример для DNS train CSV analysis:

```text
python manage.py handlers dns-analyze analyze-train-csv-content
        |
        v
router_commands("handlers", "dns-analyze", "analyze-train-csv-content")
        |
        v
router_commands_handlers("dns-analyze", "analyze-train-csv-content")
        |
        v
router_dns("analyze-train-csv-content")
        |
        v
analyze_train_csv_content()
        |
        v
DNSTrainCSVContentAnalysisHandler(...).analyze_and_generate_docs()
```

## 4. Уровень `module`

Файл:

- `scripts/router_script.py`

Логика:

```python
if module == "handlers":
    router_commands_handlers(service, action)
else:
    console.print(manage_commands)
```

Поддерживаемые значения:

| `module` | Результат |
|---|---|
| `handlers` | Команда передается в `scripts.handlers.router_handler.router_commands_handlers`. |
| любое другое значение или `None` | Печатается справка `manage_commands`. |

На этом уровне нет валидации `service` и `action`; они передаются дальше как строки или `None`.

## 5. Уровень `service`

Файл:

- `scripts/handlers/router_handler.py`

`router_commands_handlers(service, action)` выбирает один из service-router.

| `service` | Router | Назначение |
|---|---|---|
| `analyze-dataset` | `router_analyze(action)` | Первичное сканирование исходных DNS/Host датасетов. |
| `filter-dataset` | `router_filter(action)` | Фильтрация Host датасетов по правилам проекта. |
| `sort` | `router_sort(action)` | Раскладка файлов по ролям и форматам. |
| `save-sort` | `router_save(action)` | Экспорт путей из отсортированной структуры в JSON. |
| `dns-analyze` | `router_dns(action)` | Content-analysis DNS файлов и генерация документации. |
| `host-analyze` | `router_host(action)` | Content-analysis Host файлов и генерация документации. |
| другое значение или `None` | `manage_commands` | Вывод справки. |

## 6. Уровень `action`

`action` выбирается внутри router конкретного service. Общий паттерн одинаковый:

1. Router сравнивает `action` с известной строкой.
2. При совпадении вызывает функцию запуска.
3. Функция запуска создает handler-класс.
4. Handler выполняет бизнес-логику.
5. Router/runner печатает краткий результат.

Для `dns-analyze` и `host-analyze` используется дополнительный слой `run_action.py`: router вызывает функцию запуска, а функция запуска создает content-analysis handler.

## 7. Маршруты `analyze-dataset`

Файл:

- `scripts/handlers/analyze_dataset/router_analyze.py`

Назначение service: первично просканировать исходные директории датасетов и сохранить JSON со списками путей и имен файлов.

| Action | Функция | Handler | Основные входы | Основные выходы |
|---|---|---|---|---|
| `dns-dataset-handler` | `dns_dataset_handler()` | `DNSDatasetHandler` | `PATH_DNS_DATASETS`, `PATH_TEMP_DATA` | `dns-path-file.json`, `dns-file.json` |
| `host-dataset-handler` | `host_dataset_handler()` | `HostDatasetHandler` | `PATH_HOST_DATASETS`, `PATH_TEMP_DATA` | `host-path-file.json`, `host-file.json` |

Логика DNS route:

1. Создается `DNSDatasetHandler`.
2. Handler рекурсивно сканирует `PATH_DNS_DATASETS`.
3. Роль определяется по токенам в пути: `TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`.
4. Результат записывается в JSON.
5. В консоль выводятся пути к JSON-файлам.

Логика Host route:

1. Создается `HostDatasetHandler`.
2. Handler рекурсивно сканирует `PATH_HOST_DATASETS`.
3. Роль определяется по токенам в пути: `TRAIN`, `TEST`, `VALIDATION`.
4. Нераспознанные Host пути попадают в `TEST`.
5. Результат записывается в JSON.

## 8. Маршруты `filter-dataset`

Файл:

- `scripts/handlers/filter_dataset/router_filter.py`

Назначение service: отфильтровать Host-файлы после первичного анализа.

| Action | Функция | Handler | Основные входы | Основные выходы |
|---|---|---|---|---|
| `filter-host-dataset-handler` | `filter_host_dataset_handler()` | `HostDatasetFilterHandler` | `PATH_TEMP_DATA`, `PATH_FILTER_LOG` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, log исключений |

Логика route:

1. Создается `HostDatasetFilterHandler`.
2. Handler читает `host-path-file.json` и `host-file.json`.
3. Для каждого файла определяется dataset name из пути.
4. Проверяется, разрешен ли dataset для роли.
5. Проверяется, разрешено ли расширение файла.
6. Исключенные файлы пишутся в лог с причиной.
7. Оставшиеся файлы сохраняются в `filter_dataset-host-*.json`.

Этот этап используется только для Host pipeline. DNS pipeline сортируется напрямую после `analyze-dataset`.

## 9. Маршруты `sort`

Файл:

- `scripts/handlers/sort/router_sort.py`

Назначение service: материализовать структуру файлов по ролям и форматам.

| Action | Функция | Handler | Основные входы | Основные выходы |
|---|---|---|---|---|
| `sort-host-dataset-handler` | `sort_host_dataset_handler()` | `HostDatasetSortHandler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, `PATH_HOST_DATASETS_FILTER` | дерево `PATH_HOST_DATASETS_FILTER/<ROLE>/<format>/`, `sort-host-format-summary.json` |
| `sort-dns-dataset-handler` | `sort_dns_dataset_handler()` | `DNSDatasetSortHandler` | `dns-path-file.json`, `dns-file.json`, `PATH_DNS_DATASETS_FILTER` | дерево `PATH_DNS_DATASETS_FILTER/<ROLE>/<format>/`, `sort-dns-format-summary.json` |

Логика route:

1. Создается sort handler.
2. Handler проверяет целевую директорию.
3. Читает JSON со списками путей и имен.
4. Проверяет обязательные роли.
5. Определяет format group по имени файла.
6. Создает директорию `<ROLE>/<format>`.
7. Пытается создать hardlink через `os.link`.
8. Если hardlink невозможен, копирует файл через `shutil.copy2`.
9. При коллизии имен добавляет hash от исходного пути.
10. Пишет summary JSON с метриками.

Метрики результата:

- `created_links_count`;
- `copied_files_count`;
- `skipped_existing_count`;
- `missing_source_count`;
- `name_mismatch_count`;
- `files_by_role_and_format`.

## 10. Маршруты `save-sort`

Файл:

- `scripts/handlers/save_sort/router_save.py`

Назначение service: просканировать отсортированную структуру и сохранить JSON со сгруппированными путями.

| Action | Функция | Handler | Основные входы | Основные выходы |
|---|---|---|---|---|
| `save-sort-host-dataset-handler` | `save_sort_host_dataset_handler()` | `HostSortedPathExportHandler` | `PATH_HOST_DATASETS_FILTER`, `PATH_TEMP_DATA` | `sort-path-host-file.json`, `sort-path-host-file-summary.json` |
| `save-sort-dns-dataset-handler` | `save_sort_dns_dataset_handler()` | `DNSSortedPathExportHandler` | `PATH_DNS_DATASETS_FILTER`, `PATH_TEMP_DATA` | `sort-path-dns-file.json`, `sort-path-dns-file-summary.json` |

Логика route:

1. Создается export handler.
2. Handler проверяет существование отсортированной директории.
3. Для каждой роли сканирует format-директории.
4. Собирает абсолютные пути файлов.
5. Пишет JSON вида `role -> format -> list[path]`.
6. Пишет summary с количеством файлов по ролям и форматам.

## 11. Маршруты `dns-analyze`

Файлы:

- `scripts/handlers/dns_analyze/router_dns.py`;
- `scripts/handlers/dns_analyze/run_action.py`.

Назначение service: анализировать содержимое отсортированных DNS-файлов и генерировать JSON summary, RU/EN docs, RU/EN reports.

Общая логика каждого route:

1. `router_dns(action)` выбирает функцию запуска.
2. Функция запуска создает соответствующий DNS content-analysis handler.
3. Handler получает `PATH_TEMP_DATA`, `PROJECT_ROOT`, `PATH_REPORT`.
4. Handler читает `sort-path-dns-file.json`.
5. Handler выбирает нужную роль и формат.
6. Выполняется анализ файлов или выборки файлов.
7. Генерируются summary JSON, документы и отчеты.
8. `print_data()` выводит пути к созданным артефактам и статус.

| Action | Функция запуска | Handler | Роль | Формат |
|---|---|---|---|---|
| `analyze-train-csv-content` | `analyze_train_csv_content()` | `DNSTrainCSVContentAnalysisHandler` | `TRAIN` | `csv` |
| `analyze-train-pcap-content` | `analyze_train_pcap_content()` | `DNSTrainPCAPContentAnalysisHandler` | `TRAIN` | `pcap` |
| `analyze-train-pcap-csv-content` | `analyze_train_pcap_csv_content()` | `DNSTrainPCAPCSVContentAnalysisHandler` | `TRAIN` | `pcap.csv` |
| `analyze-test-csv-content` | `analyze_test_csv_content()` | `DNSTestCSVContentAnalysisHandler` | `TEST` | `csv` |
| `analyze-test-pcap-content` | `analyze_test_pcap_content()` | `DNSTestPCAPContentAnalysisHandler` | `TEST` | `pcap` |
| `analyze-test-pcap-csv-content` | `analyze_test_pcap_csv_content()` | `DNSTestPCAPCSVContentAnalysisHandler` | `TEST` | `pcap.csv` |
| `analyze-validation-pcap-content` | `analyze_validation_pcap_content()` | `DNSValidationPCAPContentAnalysisHandler` | `VALIDATION` | `pcap` |
| `analyze-validation-txt-content` | `analyze_validation_txt_content()` | `DNSValidationTXTContentAnalysisHandler` | `VALIDATION` | `txt` |

## 12. Маршруты `host-analyze`

Файлы:

- `scripts/handlers/host_analyze/router_host.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Назначение service: анализировать содержимое отсортированных Host-файлов и генерировать JSON summary, RU/EN docs, RU/EN reports.

Общая логика каждого route:

1. `router_host(action)` выбирает функцию запуска.
2. Функция запуска создает соответствующий Host content-analysis handler.
3. Handler получает `PATH_TEMP_DATA`, `PROJECT_ROOT`, `PATH_REPORT`.
4. Handler читает `sort-path-host-file.json`.
5. Handler выбирает нужную роль и формат.
6. Выполняется анализ файлов или выборки файлов.
7. Генерируются summary JSON, документы и отчеты.
8. `print_data()` выводит пути к созданным артефактам и статус.

### 12.1. Host TRAIN routes

Эти actions анализируют Host TRAIN форматы. В названиях action без префикса `test` или `validation` подразумевается TRAIN-набор.

| Action | Handler |
|---|---|
| `analyze-csv-content` | `HostCSVContentAnalysisHandler` |
| `analyze-auth-log-content` | `HostAuthLogContentAnalysisHandler` |
| `analyze-cpu-log-content` | `HostCPULogContentAnalysisHandler` |
| `analyze-diskio-log-content` | `HostDiskioLogContentAnalysisHandler` |
| `analyze-filesystem-log-content` | `HostFilesystemLogContentAnalysisHandler` |
| `analyze-fsstat-log-content` | `HostFSStatLogContentAnalysisHandler` |
| `analyze-ghc-content` | `HostGHCContentAnalysisHandler` |
| `analyze-info-content` | `HostInfoContentAnalysisHandler` |
| `analyze-journal-content` | `HostJournalContentAnalysisHandler` |
| `analyze-journal-tilde-content` | `HostJournalTildeContentAnalysisHandler` |
| `analyze-json-content` | `HostJSONContentAnalysisHandler` |
| `analyze-json-1-content` | `HostJSON1ContentAnalysisHandler` |
| `analyze-load-log-content` | `HostLoadLogContentAnalysisHandler` |
| `analyze-log-content` | `HostLogContentAnalysisHandler` |
| `analyze-log-1-content` | `HostLog1ContentAnalysisHandler` |
| `analyze-log-2-content` | `HostLog2ContentAnalysisHandler` |
| `analyze-log-3-content` | `HostLog3ContentAnalysisHandler` |
| `analyze-mail-info-1-content` | `HostMailInfo1ContentAnalysisHandler` |
| `analyze-mail-warn-1-content` | `HostMailWarn1ContentAnalysisHandler` |
| `analyze-mainlog-content` | `HostMainlogContentAnalysisHandler` |
| `analyze-mainlog-1-content` | `HostMainlog1ContentAnalysisHandler` |
| `analyze-mainlog-2-content` | `HostMainlog2ContentAnalysisHandler` |
| `analyze-mainlog-3-content` | `HostMainlog3ContentAnalysisHandler` |
| `analyze-memory-log-content` | `HostMemoryLogContentAnalysisHandler` |
| `analyze-messages-content` | `HostMessagesContentAnalysisHandler` |
| `analyze-messages-1-content` | `HostMessages1ContentAnalysisHandler` |
| `analyze-netflow-ids-content` | `HostNetflowIdsContentAnalysisHandler` |
| `analyze-network-log-content` | `HostNetworkLogContentAnalysisHandler` |
| `analyze-pcap-content` | `HostPCAPContentAnalysisHandler` |
| `analyze-process-log-content` | `HostProcessLogContentAnalysisHandler` |
| `analyze-process-summary-log-content` | `HostProcessSummaryLogContentAnalysisHandler` |
| `analyze-sc-content` | `HostSCContentAnalysisHandler` |
| `analyze-service-log-content` | `HostServiceLogContentAnalysisHandler` |
| `analyze-socket-summary-log-content` | `HostSocketSummaryLogContentAnalysisHandler` |
| `analyze-syslog-content` | `HostSyslogContentAnalysisHandler` |
| `analyze-syslog-1-content` | `HostSyslog1ContentAnalysisHandler` |
| `analyze-syslog-2-content` | `HostSyslog2ContentAnalysisHandler` |
| `analyze-syslog-3-content` | `HostSyslog3ContentAnalysisHandler` |
| `analyze-syslog-4-content` | `HostSyslog4ContentAnalysisHandler` |
| `analyze-syslog-log-content` | `HostSyslogLogContentAnalysisHandler` |
| `analyze-txt-content` | `HostTXTContentAnalysisHandler` |
| `analyze-uptime-log-content` | `HostUptimeLogContentAnalysisHandler` |
| `analyze-xml-content` | `HostXMLContentAnalysisHandler` |

### 12.2. Host TEST routes

| Action | Handler |
|---|---|
| `analyze-test-bson-content` | `HostTestBSONContentAnalysisHandler` |
| `analyze-test-csv-content` | `HostTestCSVContentAnalysisHandler` |
| `analyze-test-json-content` | `HostTestJSONContentAnalysisHandler` |
| `analyze-test-log-content` | `HostTestLogContentAnalysisHandler` |
| `analyze-test-netflow-day-content` | `HostTestNetflowDayContentAnalysisHandler` |
| `analyze-test-txt-content` | `HostTestTXTContentAnalysisHandler` |
| `analyze-test-wls-day-content` | `HostTestWLSDayContentAnalysisHandler` |

### 12.3. Host VALIDATION routes

| Action | Handler |
|---|---|
| `analyze-validation-cap-content` | `HostValidationCAPContentAnalysisHandler` |
| `analyze-validation-csv-content` | `HostValidationCSVContentAnalysisHandler` |
| `analyze-validation-json-content` | `HostValidationJSONContentAnalysisHandler` |
| `analyze-validation-netflow-day-content` | `HostValidationNetflowDayContentAnalysisHandler` |
| `analyze-validation-pcap-content` | `HostValidationPCAPContentAnalysisHandler` |
| `analyze-validation-pcapng-content` | `HostValidationPCAPNGContentAnalysisHandler` |
| `analyze-validation-txt-content` | `HostValidationTXTContentAnalysisHandler` |
| `analyze-validation-wls-day-content` | `HostValidationWLSDayContentAnalysisHandler` |

## 13. Поведение при неизвестных командах

На каждом уровне используется fallback на справку:

- неизвестный `module` -> `manage_commands`;
- неизвестный `service` -> `manage_commands`;
- неизвестный `action` -> `manage_commands`.

Текущая реализация не возвращает явный ненулевой exit code для неизвестной команды. Ошибка также не поднимается как исключение: пользователь видит справку, но автоматический CI/CD может не отличить неверную команду от успешного завершения.

## 14. Зависимости маршрутов от конфигурации

Маршруты не принимают пути через CLI. Все пути приходят из `config.py`.

| Переменная | Используется в маршрутах |
|---|---|
| `PATH_HOST_DATASETS` | `analyze-dataset host-dataset-handler` |
| `PATH_DNS_DATASETS` | `analyze-dataset dns-dataset-handler` |
| `PATH_TEMP_DATA` | почти все handlers; хранит промежуточные JSON |
| `PATH_HOST_DATASETS_FILTER` | `sort-host-dataset-handler`, `save-sort-host-dataset-handler` |
| `PATH_DNS_DATASETS_FILTER` | `sort-dns-dataset-handler`, `save-sort-dns-dataset-handler` |
| `PATH_FILTER_LOG` | `filter-host-dataset-handler` |
| `PROJECT_ROOT` | content-analysis handlers для построения путей docs |
| `PATH_REPORT` | content-analysis handlers для отчетов |

Практическое следствие: перед запуском маршрутов нужно корректно заполнить `.env` или окружение, иначе handler может упасть на проверке пути или записать артефакты в неожиданное место.

## 15. Как добавить новый маршрут

### 15.1. Новый service

1. Создать новый router в `scripts/handlers/<service>/router_<name>.py`.
2. Добавить функцию service-router.
3. Импортировать router в `scripts/handlers/router_handler.py`.
4. Добавить ветку `elif service == "<service>"`.
5. Добавить команду в `manage_commands`.

### 15.2. Новый action в существующий service

1. Реализовать handler-класс или функцию действия.
2. Если service использует `run_action.py`, добавить туда функцию запуска.
3. Импортировать функцию запуска в router.
4. Добавить ветку `elif action == "<new-action>"`.
5. Добавить команду в `manage_commands`.
6. Проверить, какие JSON-артефакты нужны до запуска нового route.

### 15.3. Новый content-analysis route

Для DNS:

1. Добавить handler в `scripts/handlers/dns_analyze/`.
2. Экспортировать класс в `scripts/handlers/dns_analyze/__init__.py`.
3. Добавить функцию запуска в `dns_analyze/run_action.py`.
4. Добавить action в `dns_analyze/router_dns.py`.

Для Host:

1. Добавить handler в `scripts/handlers/host_analyze/`.
2. Экспортировать класс в `scripts/handlers/host_analyze/__init__.py`.
3. Добавить функцию запуска в `host_analyze/run_action.py`.
4. Добавить action в `host_analyze/router_host.py`.

## 16. Технические замечания

1. Router-логика простая и читаемая, но при росте числа команд длинные `if/elif` блоки становятся хрупкими.
2. В `manage.py` используется `parse_known_args()`, поэтому лишние аргументы игнорируются. Для строгого CLI лучше использовать `parse_args()`.
3. Неизвестные команды печатают справку, но не сигнализируют об ошибке через exit code.
4. В маршрутах нет централизованной проверки зависимостей между этапами. Например, `dns-analyze` ожидает, что `sort-path-dns-file.json` уже существует.
5. Команды и router-ветки дублируются в `manage_commands`; при добавлении route нужно синхронизировать код и справку вручную.
6. Для production-поддержки разумно заменить `if/elif` маршруты на словари `action -> callable` и добавить тест, который сверяет router-команды со справкой.

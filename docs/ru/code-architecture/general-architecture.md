# Общая архитектура кода

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Точка входа CLI](#2-точка-входа-cli)
- [3. Общая схема маршрутизации](#3-общая-схема-маршрутизации)
- [4. Основные слои кода](#4-основные-слои-кода)
- [5. Пайплайн обработки датасетов](#5-пайплайн-обработки-датасетов)
- [6. JSON-артефакты и документы](#6-json-артефакты-и-документы)
- [7. Команды управления](#7-команды-управления)
- [8. Как добавлять новый обработчик](#8-как-добавлять-новый-обработчик)
- [9. Технические ограничения и риски](#9-технические-ограничения-и-риски)
- [10. Рекомендации по развитию](#10-рекомендации-по-развитию)

## 1. Назначение

Код в `manage.py` и `scripts/*` реализует CLI-инструмент для подготовки, сортировки и анализа DNS/Host датасетов. Основные задачи кода:

- просканировать исходные директории датасетов;
- распределить файлы по ролям `TRAIN`, `TEST`, `VALIDATION` и, для DNS, `EXPERIMENTS`;
- отфильтровать Host-файлы по разрешенным датасетам и расширениям;
- разложить файлы по форматам;
- сохранить промежуточные JSON-артефакты;
- сгенерировать markdown-документацию и отчеты по содержимому файлов.

Код ориентирован на batch-запуск через командную строку. Состояние между этапами передается через JSON-файлы в `PATH_TEMP_DATA`.

## 2. Точка входа CLI

Главная точка входа находится в `manage.py`.

`manage.py`:

- создает `argparse.ArgumentParser`;
- принимает три позиционных аргумента:
  - `module`;
  - `service`;
  - `action`;
- вызывает `scripts.router_script.router_commands(module, service, action)`.

Общая форма команды:

```bash
python manage.py handlers <service> <action>
```

Если `module` не равен `handlers`, CLI выводит справку `manage_commands` из `config.py`.

## 3. Общая схема маршрутизации

Маршрутизация построена как дерево простых функций.

```text
manage.py
└── scripts/router_script.py
    └── scripts/handlers/router_handler.py
        ├── analyze-dataset  -> scripts/handlers/analyze_dataset/router_analyze.py
        ├── filter-dataset   -> scripts/handlers/filter_dataset/router_filter.py
        ├── sort             -> scripts/handlers/sort/router_sort.py
        ├── save-sort        -> scripts/handlers/save_sort/router_save.py
        ├── dns-analyze      -> scripts/handlers/dns_analyze/router_dns.py
        └── host-analyze     -> scripts/handlers/host_analyze/router_host.py
```

Каждый router принимает строковый `action`, сравнивает его с известными именами действий и вызывает соответствующий обработчик. Если action не найден, выводится `manage_commands`.

## 4. Основные слои кода

### 4.1. CLI и маршрутизация

Файлы:

- `manage.py`;
- `scripts/router_script.py`;
- `scripts/handlers/router_handler.py`;
- `scripts/handlers/*/router_*.py`;
- `scripts/handlers/dns_analyze/run_action.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Назначение слоя:

- принять команду пользователя;
- выбрать нужный service/action;
- создать handler-класс;
- передать ему пути из `config.py`;
- вывести краткий результат выполнения через `rich.console.Console`.

### 4.2. Общий JSON-слой

Файлы:

- `scripts/handlers/json_handler/json_data.py`;
- `scripts/handlers/json_handler/json-data.py`.

`JsonDataManager` инкапсулирует работу с JSON:

- создание директории перед записью;
- проверка существования файла;
- чтение JSON-объекта;
- полная перезапись JSON;
- обновление данных верхнего уровня.

Модуль `json-data.py` является совместимой оберткой и реэкспортирует `JsonDataManager` из `json_data.py`.

### 4.3. Первичный анализ структуры датасетов

Файлы:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`;
- `scripts/handlers/analyze_dataset/host_dataset_handler.py`.

DNS и Host обработчики сканируют исходные директории, определяют роль файла по токенам в пути и сохраняют два JSON-файла:

- `<type>-path-file.json` - полные пути файлов по ролям;
- `<type>-file.json` - имена файлов по ролям.

Для DNS поддерживаются роли:

- `TRAIN`;
- `TEST`;
- `VALIDATION`;
- `EXPERIMENTS`.

Для Host поддерживаются роли:

- `TRAIN`;
- `TEST`;
- `VALIDATION`.

Если роль Host не распознана, файл попадает в `TEST`. Если роль DNS не распознана, файл попадает в `EXPERIMENTS`.

### 4.4. Фильтрация Host-датасетов

Файл:

- `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`.

`HostDatasetFilterHandler` читает:

- `host-path-file.json`;
- `host-file.json`.

Затем применяет стратегию фильтрации по имени датасета, роли и расширению файла.

Основные проверки:

- корректность типа пути;
- возможность извлечь имя датасета из пути;
- разрешен ли датасет для роли;
- разрешено ли расширение файла для конкретного датасета;
- присутствует ли имя файла в `host-file.json`.

Результат фильтрации:

- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`;
- лог исключенных файлов.

### 4.5. Сортировка по ролям и форматам

Файлы:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`;
- `scripts/handlers/sort/sort_host_dataset_handler.py`.

Сортировка читает промежуточные JSON-файлы и формирует структуру:

```text
PATH_*_DATASETS_FILTER/
└── <ROLE>/
    └── <format>/
        └── <file>
```

Для материализации файлов используется:

1. `os.link` - hardlink без копирования данных;
2. `shutil.copy2` - fallback, если hardlink создать нельзя.

При коллизии имен целевой файл получает hash от исходного пути. Это снижает риск перезаписи файлов с одинаковыми именами из разных директорий.

### 4.6. Экспорт отсортированных путей

Файлы:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`;
- `scripts/handlers/save_sort/save_sort_host_path_handler.py`.

Экспорт сканирует уже отсортированную структуру `PATH_*_DATASETS_FILTER` и сохраняет JSON вида:

```json
{
  "TRAIN": {
    "csv": ["/abs/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Основные выходные файлы:

- `sort-path-dns-file.json`;
- `sort-path-dns-file-summary.json`;
- `sort-path-host-file.json`;
- `sort-path-host-file-summary.json`.

### 4.7. Контент-анализ DNS

Файлы:

- `scripts/handlers/dns_analyze/*`;
- `scripts/handlers/dns_analyze/router_dns.py`;
- `scripts/handlers/dns_analyze/run_action.py`.

DNS content-analysis обработчики читают `sort-path-dns-file.json`, выбирают роль и формат, анализируют выборку файлов и генерируют:

- summary JSON;
- markdown-документ в `docs/ru/...`;
- markdown-документ в `docs/en/...`;
- `README.md` для соответствующего раздела;
- markdown-отчеты в `report/...`.

Поддерживаемые направления анализа:

| Роль | Форматы |
|---|---|
| `TRAIN` | `csv`, `pcap`, `pcap.csv` |
| `TEST` | `csv`, `pcap`, `pcap.csv` |
| `VALIDATION` | `pcap`, `txt` |

### 4.8. Контент-анализ Host

Файлы:

- `scripts/handlers/host_analyze/*`;
- `scripts/handlers/host_analyze/router_host.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Host content-analysis обработчики читают `sort-path-host-file.json`, анализируют конкретную пару `role/format` и генерируют двуязычные документы.

Поддерживаемые группы:

- `TRAIN`: `csv`, `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `ghc`, `info`, `journal`, `journal~`, `json`, `json-1`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `netflow_ids`, `network.log`, `pcap`, `process.log`, `process.summary.log`, `sc`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `txt`, `uptime.log`, `xml`;
- `TEST`: `bson`, `csv`, `json`, `log`, `netflow_day`, `txt`, `wls_day`;
- `VALIDATION`: `cap`, `csv`, `json`, `netflow_day`, `pcap`, `pcapng`, `txt`, `wls_day`.

## 5. Пайплайн обработки датасетов

Рекомендуемая последовательность для DNS:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <dns-action>
```

Рекомендуемая последовательность для Host:

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <host-action>
```

Зависимости между этапами:

| Этап | Вход | Выход |
|---|---|---|
| `analyze-dataset` | исходные директории `PATH_HOST_DATASETS` / `PATH_DNS_DATASETS` | `host-path-file.json`, `host-file.json`, `dns-path-file.json`, `dns-file.json` |
| `filter-dataset` | `host-path-file.json`, `host-file.json` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` |
| `sort` | DNS: `dns-*.json`; Host: `filter_dataset-host-*.json` | отсортированные директории, `sort-*-format-summary.json` |
| `save-sort` | отсортированные директории | `sort-path-*-file.json`, `sort-path-*-file-summary.json` |
| `dns-analyze` / `host-analyze` | `sort-path-*-file.json` | summary JSON, docs, reports |

## 6. JSON-артефакты и документы

### 6.1. Временные JSON-файлы

Все промежуточные JSON-файлы сохраняются в `PATH_TEMP_DATA`.

Ключевые файлы:

- `dns-path-file.json`;
- `dns-file.json`;
- `host-path-file.json`;
- `host-file.json`;
- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`;
- `sort-dns-format-summary.json`;
- `sort-host-format-summary.json`;
- `sort-path-dns-file.json`;
- `sort-path-host-file.json`;
- `analysis-*-summary.json`.

### 6.2. Документация

Content-analysis обработчики записывают markdown-файлы в:

- `docs/ru/analysis-dataset/...`;
- `docs/en/analysis-dataset/...`.

Для каждого формата обычно создаются:

- детальный документ формата;
- `README.md` со сводной таблицей по директории.

### 6.3. Отчеты

Отчеты пишутся в `PATH_REPORT` по путям из `config.py`, например:

```text
reports/ru/stage-one/analysis-dataset/host/train
reports/en/stage-one/analysis-dataset/dns/train
```

## 7. Команды управления

### 7.1. Первичный анализ

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers analyze-dataset dns-dataset-handler
```

### 7.2. Фильтрация Host

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

### 7.3. Сортировка

```bash
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
```

### 7.4. Экспорт путей после сортировки

```bash
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

### 7.5. DNS-анализ

```bash
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py handlers dns-analyze analyze-train-pcap-content
python manage.py handlers dns-analyze analyze-train-pcap-csv-content
python manage.py handlers dns-analyze analyze-test-csv-content
python manage.py handlers dns-analyze analyze-test-pcap-content
python manage.py handlers dns-analyze analyze-test-pcap-csv-content
python manage.py handlers dns-analyze analyze-validation-pcap-content
python manage.py handlers dns-analyze analyze-validation-txt-content
```

### 7.6. Host-анализ

Host-команды имеют форму:

```bash
python manage.py handlers host-analyze <action>
```

Примеры:

```bash
python manage.py handlers host-analyze analyze-csv-content
python manage.py handlers host-analyze analyze-test-json-content
python manage.py handlers host-analyze analyze-validation-pcapng-content
```

Полный список команд хранится в `config.py` в переменной `manage_commands`.

## 8. Как добавлять новый обработчик

### 8.1. Новый формат DNS

1. Добавить handler-файл в `scripts/handlers/dns_analyze/`.
2. Реализовать dataclass результата и handler-класс с методом `analyze_and_generate_docs()`.
3. Читать входные пути из `sort-path-dns-file.json`.
4. Генерировать summary JSON, RU/EN docs, RU/EN reports.
5. Добавить импорт в `scripts/handlers/dns_analyze/__init__.py`.
6. Добавить функцию запуска в `scripts/handlers/dns_analyze/run_action.py`.
7. Добавить action в `scripts/handlers/dns_analyze/router_dns.py`.
8. Добавить команду в `manage_commands`.

### 8.2. Новый формат Host

1. Проверить, что сортировка умеет определить формат в `HostDatasetSortHandler._detect_format_group()`.
2. Добавить handler-файл в `scripts/handlers/host_analyze/`.
3. Реализовать `analyze_and_generate_docs()`.
4. Добавить экспорт класса в `scripts/handlers/host_analyze/__init__.py`.
5. Добавить функцию запуска в `scripts/handlers/host_analyze/run_action.py`.
6. Добавить action в `scripts/handlers/host_analyze/router_host.py`.
7. Добавить команду в `manage_commands`.

## 9. Технические ограничения и риски

### 9.1. Сильная связность через `config.py`

Большая часть кода получает пути из `config.py`. Это упрощает CLI-запуск, но усложняет тестирование отдельных обработчиков и повышает риск ошибок конфигурации.

### 9.2. Промежуточное состояние хранится в JSON

Этапы пайплайна зависят от файлов в `PATH_TEMP_DATA`. Если один из JSON-файлов устарел или был создан для другого набора данных, следующие этапы могут обработать неверные входные данные.

### 9.3. Роутинг реализован через длинные `if/elif`

Такой подход прост, но плохо масштабируется. При добавлении нового action нужно синхронно менять router, `run_action.py`, `__init__.py` и `manage_commands`.

### 9.4. Обнаруженные конфигурационные несоответствия

В текущем `config.py` есть места, которые требуют проверки перед production-использованием:

- `PATH_FILTER_LOG = f"{PATH_DATA_STORAGE}/logs/filter_log",` создает tuple из-за завершающей запятой, а не строку.
- `DOCS_RU_ANALYSIS_DNS_TRAIN` указывает на `docs/ru/analysis-dataset/host/train`, хотя по названию должен указывать на DNS train-директорию.

Эти места могут приводить к записи логов или DNS train-документов не туда, куда ожидается.

### 9.5. Нет единой базовой абстракции для content-analysis

Многие обработчики повторяют один и тот же шаблон:

- чтение `sort-path-*-file.json`;
- выборка файлов;
- построение summary;
- запись markdown;
- запись report.

Это рабочий подход, но при росте количества форматов увеличивает стоимость поддержки.

## 10. Рекомендации по развитию

1. Заменить `if/elif` роутеры на словари action -> callable. Это снизит риск ошибок при добавлении новых команд.
2. Вынести общую логику content-analysis в базовый класс или composable helper-функции.
3. Добавить автоматические тесты для:
   - определения роли датасета;
   - определения format group;
   - фильтрации Host-файлов;
   - чтения/записи JSON;
   - генерации путей документации.
4. Валидировать `config.py` при старте CLI и явно сообщать о пустых или некорректных env-переменных.
5. Добавить версионирование JSON-артефактов или timestamp/metadata, чтобы избежать использования устаревшего состояния.
6. Исправить конфигурационные несоответствия, перечисленные в разделе рисков.

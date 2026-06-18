# Proposal

## 1. Краткое описание

`Proposal` - Python-проект для инвентаризации, фильтрации, сортировки и анализа DNS/Host датасетов, используемых в исследовании behaviour-driven гибридного ML-подхода к обнаружению многоэтапной эксфильтрации данных.

Текущая стадия проекта сфокусирована не на обучении моделей, а на подготовке надежной базы для последующего ML/MLOps pipeline:

- анализ структуры исходных датасетов;
- разделение данных на `TRAIN`, `TEST`, `VALIDATION`;
- фильтрация нерелевантных Host-источников;
- сортировка файлов по ролям и форматам;
- генерация JSON-инвентарей;
- генерация RU/EN markdown-документации и отчетов по форматам;
- фиксация требований к будущей нормализации, feature extraction и parser layers.

## 2. Основная идея проекта

Проект рассматривает два домена данных:

| Домен | Назначение | Основные источники признаков |
|---|---|---|
| `dns` | DNS exfiltration / DNS tunneling / DNS amplification сценарии | domain lists, DNS CSV, packet captures, `pcap.csv` |
| `host` | Host behaviour, telemetry, process/syscall/log activity, Windows/Sysmon-like events | logs, JSON Lines telemetry, BSON, syscall/API traces, NetFlow-like данные, PCAP/CAP |

Целевая архитектурная идея будущего ML-пайплайна:

1. Отдельно нормализовать DNS, Host и Network/Hybrid источники.
2. Извлекать признаки на уровне событий, потоков, временных окон и поведенческих последовательностей.
3. Не смешивать `TRAIN`, `TEST`, `VALIDATION`.
4. Присоединять labels только через явный label mapping с сохранением происхождения метки.
5. Использовать результаты анализа датасетов как контракт для parser/feature extraction слоев.

## 3. Структура репозитория

```text
.
|-- manage.py                         # Главная CLI-точка входа
|-- requirements.txt                  # Минимальные Python-зависимости
|-- .env.example                      # Пример конфигурации путей
|-- scripts/
|   |-- json_data.py                  # Утилита безопасной работы с JSON-файлами
|   `-- handlers/                     # Handler-классы этапов pipeline
|-- docs/
|   |-- ru/                           # Русская документация
|   `-- en/                           # Английская документация
`-- planning/
    |-- stage-one/                    # План и задачи этапа анализа датасетов
    `-- stage-two/                    # План этапа нормализации данных
```

Ключевые количественные ориентиры текущего состояния:

| Область | Количество |
|---|---:|
| Python-файлы | 78 |
| Markdown-файлы | 158 |
| Handler-файлы в `scripts/handlers` | 156 |
| CLI-команды в `manage.py` | 72 |
| Отчеты анализа датасетов в `docs/ru/analysis-dataset` | 73 |
| Отчеты анализа датасетов в `docs/en/analysis-dataset` | 73 |
| Плановые task-файлы анализа датасетов | 67 |

## 4. Конфигурация окружения

Проект использует `.env` и `python-dotenv`. Пример находится в `.env.example`.

```env
PATH_DATA_STORAGE=C:\Users\Public\PythonProjects\storage

PATH_FOLDER_DATASETS=C:\Users\Public\PythonProjects\storages\datasets

PATH_FOLDER_DATASETS_FILTER=C:\Users\Public\PythonProjects\storages\datasets-filter
```

В `manage.py` на основе этих переменных формируются дополнительные пути:

| Переменная | Назначение |
|---|---|
| `PATH_DATA_STORAGE` | Корневая директория для служебных данных проекта |
| `PATH_REPORT` | Путь к отчетам: `PATH_DATA_STORAGE/reports` |
| `PATH_TEMP_DATA` | Путь к промежуточным JSON: `PATH_DATA_STORAGE/temp_data` |
| `PATH_FOLDER_DATASETS` | Корень исходных датасетов |
| `PATH_FOLDER_DATASETS_FILTER` | Корень отсортированных/отфильтрованных датасетов |
| `PATH_HOST_DATASETS` | Host-датасеты, по умолчанию `PATH_FOLDER_DATASETS\host` |
| `PATH_DNS_DATASETS` | DNS-датасеты, по умолчанию `PATH_FOLDER_DATASETS\dns` |
| `PATH_HOST_DATASETS_FILTER` | Host-результаты сортировки, `PATH_FOLDER_DATASETS_FILTER\host` |
| `PATH_DNS_DATASETS_FILTER` | DNS-результаты сортировки, `PATH_FOLDER_DATASETS_FILTER\dns` |
| `PATH_FILTER_LOG` | Лог фильтрации Host-датасетов |

Важно: `.env` содержит локальные абсолютные пути и не должен использоваться как переносимый контракт. Для переноса проекта редактируйте `.env.example` или создавайте новый `.env` под конкретную машину.

## 5. Установка

Поддерживаемый runtime для production/dev окружений - Python 3.11.x. Локально проект проверяется через conda environment `proposal2`: `C:\Users\fmark\.conda\envs\proposal2`, текущий интерпретатор - Python 3.11.15.

Минимальная установка для локального запуска:

```powershell
cd C:\Users\Public\PythonProjects\Proposal
conda activate proposal2
python --version
python -m pip install -r requirements-dev.txt
copy .env.example .env
```

Если conda activation недоступен в текущем PowerShell, используйте интерпретатор напрямую:

```powershell
& "C:\Users\fmark\.conda\envs\proposal2\python.exe" --version
& "C:\Users\fmark\.conda\envs\proposal2\python.exe" -m pip install -r requirements-dev.txt
& "C:\Users\fmark\.conda\envs\proposal2\python.exe" -m pytest -q
```

После копирования `.env` проверьте, что пути к `storages`, `datasets`, `datasets-filter` и `storage` существуют или могут быть созданы.

Зависимости на текущем этапе минимальные:

| Пакет | Назначение |
|---|---|
| `python-dotenv` | Загрузка `.env` |
| `rich` | Форматированный вывод CLI |

Если `rich` не установлен, в `manage.py` есть fallback-консоль, но штатный режим предполагает установку зависимостей из `requirements.txt`.

## 6. Основной pipeline

### 6.1 DNS pipeline

```text
PATH_DNS_DATASETS
  -> dataset dns analyze
  -> dns dataset sort
  -> dns dataset save-paths
  -> dns dataset analyze-*-content
  -> docs/{ru,en}/analysis-dataset/dns
  -> PATH_REPORT/{ru,en}
```

Базовые команды:

```powershell
python manage.py dataset dns analyze
python manage.py dns dataset sort
python manage.py dns dataset save-paths
```

Команды анализа содержимого DNS:

```powershell
python manage.py dns dataset analyze-train-csv-content
python manage.py dns dataset analyze-train-pcap-content
python manage.py dns dataset analyze-train-pcap-csv-content
python manage.py dns dataset analyze-test-csv-content
python manage.py dns dataset analyze-test-pcap-content
python manage.py dns dataset analyze-test-pcap-csv-content
python manage.py dns dataset analyze-validation-pcap-content
python manage.py dns dataset analyze-validation-txt-content
```

DNS-этапы создают инвентари путей/файлов, группируют их по ролям и форматам, затем генерируют документацию по форматам: CSV, PCAP, `pcap.csv`, TXT.

### 6.2 Host pipeline

```text
PATH_HOST_DATASETS
  -> host dataset analyze
  -> host dataset filter
  -> host dataset sort
  -> host dataset save-paths
  -> host dataset analyze-*-content
  -> docs/{ru,en}/analysis-dataset/host
  -> PATH_REPORT/{ru,en}
```

Базовые команды:

```powershell
python manage.py host dataset analyze
python manage.py host dataset filter
python manage.py host dataset sort
python manage.py host dataset save-paths
```

Host pipeline содержит дополнительный этап `filter`, потому что исходные Host-датасеты неоднородны и не все файлы должны попадать в анализ. Фильтрация учитывает роль датасета, допустимые наборы данных и допустимые расширения/форматы.

## 7. Основные JSON-артефакты

Промежуточные JSON-файлы пишутся в `PATH_TEMP_DATA`.

| Файл | Источник | Назначение |
|---|---|---|
| `dns-path-file.json` | `dataset dns analyze` | Пути DNS-файлов по ролям |
| `dns-file.json` | `dataset dns analyze` | Имена DNS-файлов по ролям |
| `host-path-file.json` | `host dataset analyze` | Пути Host-файлов по ролям |
| `host-file.json` | `host dataset analyze` | Имена Host-файлов по ролям |
| `filter-host-path-file.json` | `host dataset filter` | Отфильтрованные Host-пути |
| `filter-host-file.json` | `host dataset filter` | Отфильтрованные Host-имена файлов |
| `sort-host-format-summary.json` | `host dataset sort` | Сводка сортировки Host по форматам |
| `sort-path-host-file.json` | `host dataset save-paths` | Пути отсортированных Host-файлов по ролям/форматам |
| `sort-path-host-file-summary.json` | `host dataset save-paths` | Сводка экспортированных Host-путей |

Handler-ы анализа содержимого также создают summary JSON для конкретных форматов. Эти summary используются для генерации Markdown-документов и отчетов.

## 8. Документация проекта

Основная документация находится в `docs/ru` и `docs/en`.

| Документ | Назначение |
|---|---|
| `docs/*/project_proposal_analysis.md` | Анализ проектного proposal |
| `docs/*/functional_project_cheatsheet.md` | Краткая функциональная шпаргалка по проекту |
| `docs/*/dns_dataset_strategy.md` | Стратегия работы с DNS-датасетами |
| `docs/*/host_datasets_analysis.md` | Анализ Host-датасетов |
| `docs/*/dataset_feature_extraction_map.md` | Карта признаков и feature extraction |
| `docs/*/repository_qa_section_3_8.md` | QA/уточнения по разделам проекта |
| `docs/*/analysis-dataset/analysis-dataset.md` | Общая сводка анализа датасетов |
| `docs/*/analysis-dataset/**.md` | Отчеты по конкретным ролям и форматам |

Отчеты анализа датасетов продублированы на русском и английском языках.

## 9. Сводка анализа датасетов

По текущей сводной документации анализ покрывает 66 форматных отчетов и 361675 файлов датасетов.

| Группа | Форматных отчетов | Файлов датасетов | Основной смысл |
|---|---:|---:|---|
| `dns/test` | 3 | 1 | DNS TEST, фактически доступен только CSV |
| `dns/train` | 3 | 26 | DNS TRAIN: CSV, PCAP, `pcap.csv` |
| `dns/validation` | 2 | 8 | DNS VALIDATION: PCAP и TXT |
| `host/test` | 7 | 294589 | Большой Host TEST: BSON, JSON, logs, traces, flows, WLS |
| `host/train` | 43 | 60365 | Host TRAIN: telemetry, logs, mixed JSON/JSON-lines, traces, flows, pcap |
| `host/validation` | 8 | 6686 | Host VALIDATION: metadata, JSON-lines, flows, traces, packet captures |

Статусы готовности форматов:

| Статус | Количество форматов | Смысл |
|---|---:|---|
| `READY_FOR_FEATURE_EXTRACTION` | 44 | Формат можно подключать к feature extraction после стандартной потоковой обработки |
| `NEEDS_CUSTOM_PARSER` | 14 | Нужен специализированный parser или schema-aware layer |
| `PARTIALLY_SUPPORTED` | 6 | Формат частично пригоден, но содержит под-схемы или служебные файлы |
| `BROKEN_OR_EMPTY` | 2 | В подготовленном наборе нет входных файлов |

Главный технический вывод: проект нельзя развивать через один универсальный reader. Нужна маршрутизация по `domain/split/format` и отдельные parser layers для packet capture, BSON, Mongo-style JSON, mixed JSON/JSON-lines и больших trace/log источников.

## 10. Handler-архитектура

Код организован вокруг handler-классов в `scripts/handlers`.

| Группа handler-ов | Количество | Назначение |
|---|---:|---|
| DNS analysis handlers | 8 | Анализ содержимого DNS TRAIN/TEST/VALIDATION форматов |
| Host analysis handlers | 58 | Анализ содержимого Host TRAIN/TEST/VALIDATION форматов |
| DNS base handlers | 3 | Инвентаризация, сортировка и экспорт DNS-путей |
| Host base handlers | 4 | Инвентаризация, фильтрация, сортировка и экспорт Host-путей |
| Utility handlers | 1 | Пример/служебная команда |

Типичный handler:

1. Читает входной JSON-инвентарь через `JsonDataManager`.
2. Валидирует роли, пути и ожидаемую структуру.
3. Анализирует sample или полный список файлов выбранного формата.
4. Формирует summary JSON.
5. Генерирует RU/EN Markdown-документацию.
6. Генерирует RU/EN report-файлы в `PATH_REPORT`.

## 11. Форматы и parser priorities

Высокий приоритет для дальнейшей реализации:

| Формат/семейство | Причина |
|---|---|
| DNS `pcap` / `pcapng` | Нужны packet-level DNS признаки |
| Host `bson` | Важен для TEST behaviour sequences |
| Host `json` | Много файлов, есть JSON Lines и Mongo-style варианты |
| Host `txt` | Очень большой объем syscall/API traces, нужен streaming parser |
| Host `cap` / `pcap` / `pcapng` | Нужны для network/hybrid validation |

Средний приоритет:

- `auth.log`, `journal`, `journal~`, `log`, `ghc`;
- mixed JSON/JSON-lines parser для `syslog*`, `mainlog*`, `messages*`, `xml`, `pcap`;
- CSV normalizer для DNS TEST и Host TRAIN metadata/telemetry разделения.

Низкий риск, можно подключать раньше:

- JSON-lines telemetry: `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`;
- flow-like источники: `netflow_day`, `netflow_ids`;
- validation metadata CSV.

## 12. Правила работы с labels

В проекте нет единой label-схемы для всех источников.

Рекомендуемая политика:

1. DNS TRAIN/VALIDATION: назначать label из имени файла или директории только там, где отчет явно фиксирует классы.
2. Host TRAIN: использовать `ground_truth.csv`, scenario metadata, `exploit`, `container.role`, `alert` и другие context-поля через явный mapping.
3. Host TEST: не использовать для обучения; если нужны labels для evaluation, присоединять их внешним источником.
4. TXT/domain-list с `unknown` не смешивать с `benign`/`attack` без отдельной policy.
5. Для mixed-schema файлов label extraction должен быть частью schema-aware parser, а не глобальным regex.

## 13. Правила работы со временем

Временные поля неоднородны:

- JSON-lines telemetry: часто `@timestamp` или `timestamp`;
- scenario JSON: вложенные поля вроде `time.container_ready.absolute`;
- PCAP/PCAPNG/CAP: packet timestamp из packet parser;
- CSV/netflow: timestamp, duration, start/end fields в зависимости от схемы.

Рекомендуемая нормализация:

1. Приводить timestamps к UTC.
2. Сохранять исходное поле времени в audit metadata.
3. Сортировать события внутри `host/session/file/scenario` перед sequence features.
4. Для sliding windows явно задавать window size, stride и grouping key.

## 14. Рекомендуемый порядок запуска

Минимальный порядок для воспроизводимого анализа:

```powershell
# 1. Инвентаризация DNS
python manage.py dataset dns analyze

# 2. Инвентаризация Host
python manage.py host dataset analyze

# 3. Фильтрация Host
python manage.py host dataset filter

# 4. Сортировка Host
python manage.py host dataset sort

# 5. Экспорт путей Host
python manage.py host dataset save-paths

# 6. Анализ конкретных форматов
python manage.py dns dataset analyze-train-pcap-csv-content
python manage.py host dataset analyze-filesystem-log-content
```

Для полного покрытия нужно запускать все `analyze-*-content` команды по DNS и Host. Практически лучше запускать их группами и проверять summary JSON после каждой группы.

## 15. Проверка проекта

Базовые проверки:

```powershell
python manage.py --help
python -m compileall manage.py scripts
git diff --check
```

Проверка конфигурации:

```powershell
python - <<'PY'
from pathlib import Path
for path in [
    r"C:\Users\Public\PythonProjects\storages\datasets",
    r"C:\Users\Public\PythonProjects\storages\datasets-filter",
    r"C:\Users\Public\PythonProjects\storage",
]:
    print(path, Path(path).exists())
PY
```

## 16. Ограничения текущего состояния

- Проект находится на стадии анализа и подготовки данных; полноценный training/inference pipeline пока не реализован в корне репозитория.
- Многие Python-файлы содержат комментарии/docstring на русском; часть файлов исторически могла иметь нестабильную кодировку, поэтому новые документы лучше хранить в UTF-8.
- Packet formats (`pcap`, `pcapng`, `cap`) нельзя анализировать как обычный текст.
- Большие источники (`txt`, `bson`, `json`, `log`, `wls_day`, `netflow_day`) должны обрабатываться потоково.
- Отчеты и temp JSON зависят от локальных путей из `.env`.
- В рабочем дереве могут быть внешние изменения и сгенерированные артефакты; перед коммитом нужно отдельно проверить `git status`.

## 17. Практические рекомендации для следующего этапа

Следующий логичный этап - `stage-two`: нормализация данных.

Рекомендуемый план:

1. Зафиксировать канонические сущности: `event`, `metric`, `flow`, `packet`, `trace`, `metadata`.
2. Реализовать единый registry parser-ов по ключу `domain/split/format`.
3. Добавить streaming readers для больших текстовых и JSON-lines источников.
4. Добавить отдельные parser layers для BSON, PCAP/PCAPNG/CAP, Mongo-style JSON и mixed schema logs.
5. Ввести audit metadata для каждого преобразования: source path, parser version, schema version, label source.
6. Добавить тесты на маленьких fixtures для каждого критичного parser-а.
7. Сформировать feature extraction contracts до обучения моделей.

## 18. Короткий итог

`Proposal` - это подготовительный backend/data engineering проект для исследования DNS/Host-based detection pipeline. Его текущая ценность - не в моделях, а в подробной инвентаризации, классификации и документировании сложных датасетов. Репозиторий уже содержит CLI, handler-архитектуру, JSON-артефакты и RU/EN документацию, достаточные для перехода к нормализации данных и дальнейшему feature extraction.

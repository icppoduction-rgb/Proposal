# Общая документация по анализу датасетов

## 1. Назначение документа

Документ суммирует результаты анализа файлов из `docs/ru/analysis-dataset` и описывает, как использовать эти результаты при построении pipeline для нормализации, feature extraction, обучения и проверки моделей.

В дереве анализа покрыты два домена:

- `dns`: DNS-датасеты для анализа доменов, DNS-запросов, packet capture и производных CSV-признаков.
- `host`: host telemetry, system/application logs, syscall/API traces, network flows, Windows/Sysmon-like события и packet capture.

Итоговая сводка учитывает 66 форматных отчетов и 6 README-индексов. В README проиндексировано 65 отчетов; дополнительно найден и учтен `host/train/pcap.md`.

## 2. Покрытие анализа

| Группа | Форматных отчетов | Файлов датасетов | Основной смысл |
|---|---:|---:|---|
| `dns/test` | 3 | 1 | Проверочный DNS-набор, фактически доступен только CSV |
| `dns/train` | 3 | 26 | DNS train: CSV, PCAP и `pcap.csv` |
| `dns/validation` | 2 | 8 | DNS validation: PCAP и domain-list TXT |
| `host/test` | 7 | 294589 | Большой host test набор: BSON, JSON, logs, traces, flows, WLS |
| `host/train` | 43 | 60365 | Host train: telemetry, logs, mixed JSON/JSON-lines, traces, flows, pcap |
| `host/validation` | 8 | 6686 | Host validation: metadata, JSON-lines, flows, traces, packet captures |
| **Итого** | **66** | **361675** | DNS и Host источники для feature extraction |

## 3. Статусы готовности

| Статус | Количество форматов | Смысл |
|---|---:|---|
| `READY_FOR_FEATURE_EXTRACTION` | 44 | Формат можно подключать к feature extraction после стандартной потоковой обработки и нормализации |
| `NEEDS_CUSTOM_PARSER` | 14 | Нужен специализированный parser или schema-aware слой |
| `PARTIALLY_SUPPORTED` | 6 | Формат частично пригоден, но содержит несколько под-схем или служебные файлы |
| `BROKEN_OR_EMPTY` | 2 | В подготовленном наборе нет входных файлов для анализа |

Главный вывод: большая часть источников пригодна для feature extraction, но универсальный CSV/JSON-reader не покроет весь репозиторий. Pipeline должен быть format-aware и schema-aware.

## 4. DNS-датасеты

DNS часть компактная: 8 форматных отчетов и 35 файлов. Она делится на табличные CSV, сырые packet capture и списки доменов.

### DNS TRAIN

| Формат | Файлов | Статус | Важные детали |
|---|---:|---|---|
| `csv` | 8 | `PARTIALLY_SUPPORTED` | Есть domain-list и PhishTank-like файлы, но feature CSV могут содержать неэкранированные list/dict поля с запятыми |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | Нужен parser classic pcap/pcapng с DNS protocol decoding |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | CSV-структура стабильна, заголовки присутствуют, label можно брать из имени файла |

Классы DNS TRAIN: `benign`, `malware`, `phishing`, `spam`. Для supervised learning label должен назначаться явно, чаще всего из имени файла.

### DNS TEST

| Формат | Файлов | Статус | Важные детали |
|---|---:|---|---|
| `csv` | 1 | `PARTIALLY_SUPPORTED` | Большой CSV без заголовка, нужна закрепленная 22-колоночная схема и streaming-read |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | В подготовленном `TEST.pcap` нет файлов |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | В подготовленном `TEST.pcap.csv` нет файлов |

DNS TEST нельзя считать полноценным источником packet-level проверки: доступны только CSV-данные.

### DNS VALIDATION

| Формат | Файлов | Статус | Важные детали |
|---|---:|---|---|
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | Подходит для проверки DNS amplification detection, нужен packet parser |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Domain-list: одна доменная запись на строку |

Классы DNS VALIDATION включают `attack`, `benign` для PCAP и `unknown`, `benign` для TXT. Семантику `unknown` нужно закрепить до расчета supervised metrics.

## 5. Host-датасеты

Host часть существенно крупнее DNS: 58 форматных отчетов и 361640 файлов. Источники неоднородные и требуют разных стратегий чтения.

Основные семейства данных:

- Metrics/telemetry: `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`.
- Logs: `auth.log`, `journal`, `syslog*`, `messages*`, `mainlog*`, `mail-*`, `info`, `log*`.
- Structured and semi-structured data: `csv`, `json`, `json-1`, `bson`, `xml`.
- Network/hybrid: `netflow_day`, `netflow_ids`, `pcap`, `pcapng`, `cap`.
- Behaviour traces: `txt`, `sc`, `ghc`.
- Windows/Sysmon-like events: `wls_day`, `json` validation files.

### Host TRAIN

Host TRAIN содержит 43 форматных отчета и 60365 файлов. Это основной источник для построения признаков и обучения.

Ключевые выводы:

- `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` в основном готовы к feature extraction как JSON-lines telemetry.
- `csv` пригоден для supervised learning, но содержит служебные `feature_descr.csv` и `ground_truth.csv`, поэтому parser должен различать рабочие telemetry CSV и metadata CSV.
- `cpu.log` и `diskio.log` частично готовы: внутри есть разные под-схемы, например metric rows и annotation rows.
- `auth.log`, `journal`, `journal~`, `json`, `log`, `ghc` требуют отдельных parser layers.
- Многие `log-*`, `syslog*`, `mainlog*`, `messages*`, `txt`, `xml`, `pcap` описаны как пригодные для признаков, но требуют schema-aware обработки из-за смешения сценарных JSON-документов и JSON-lines событий.

Частые поля и признаки:

- Время: `@timestamp`, `timestamp`, `time.container_ready.absolute`, packet timestamps.
- Host identity: hostname, container role, process/service identifiers.
- Labels/context: `ground_truth.csv`, `exploit`, `container.role`, `alert`, scenario-derived labels.
- Metric features: CPU load, disk I/O, filesystem usage, memory usage, network counters, process/service/socket summaries.
- Sequence features: event order, syscall/API traces, syslog/event types, authentication events.

### Host TEST

Host TEST содержит 7 форматных отчетов и 294589 файлов. Этот набор нельзя использовать для обучения, но он важен для inference/evaluation pipeline.

| Формат | Файлов | Статус | Важные детали |
|---|---:|---|---|
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | Нужен BSON parser, сопоставление descriptor/event документов по `I`, разворот `args` |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | Network/hybrid CSV, метки нужно присоединять отдельно по IP |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | Есть JSON Lines, Mongo-style `NumberLong(...)` и большие многострочные reports |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | Line-oriented sandbox runtime logs |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | Большие flow-файлы без встроенных labels |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | Syscall/API sequence traces, очень большое число файлов |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Windows security/Sysmon-like JSON Lines |

Критичная эксплуатационная деталь: `txt` и `wls_day` нужно читать потоково, без загрузки всего набора в память.

### Host VALIDATION

Host VALIDATION содержит 8 форматных отчетов и 6686 файлов.

| Формат | Файлов | Статус | Важные детали |
|---|---:|---|---|
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | Нужен pcap/cap parser или `Scapy`/`tshark` |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | Validation metadata и label/context признаки |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | JSON Lines Windows/Sysmon telemetry |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | Большие line-oriented network flows |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | Нужен packet parser |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | Нужен pcapng parser |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | Line-oriented syscall traces |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Windows/Sysmon-like events |

## 6. Labels и supervised learning

Единой схемы labels во всех данных нет.

Рекомендуемые правила:

- DNS TRAIN/VALIDATION: label назначать из имени файла или директории, если отчет явно указывает классы.
- Host TRAIN: использовать `ground_truth.csv`, scenario metadata, `exploit`, `container.role`, `alert` и другие context-поля только через явный mapping.
- Host TEST: не использовать для обучения; если нужны метки для evaluation, присоединять их внешним источником.
- TXT/domain-list с `unknown`: не смешивать с `benign`/`attack` без отдельной policy.
- Для mixed schema файлов label extraction должен быть частью schema-aware parser, а не глобальным regex.

## 7. Временные признаки

Время представлено неоднородно:

- JSON-lines telemetry чаще использует `@timestamp` или `timestamp`.
- Scenario JSON может использовать вложенные поля вроде `time.container_ready.absolute`.
- PCAP/PCAPNG/CAP требуют packet timestamp из packet parser.
- CSV и netflow могут содержать timestamp, duration или start/end fields в формате конкретной схемы.

Рекомендуемая нормализация:

1. Приводить все timestamps к UTC.
2. Сохранять исходное поле времени в audit metadata.
3. Для sequence features сортировать события внутри `host/session/file/scenario`.
4. Для sliding windows явно задавать window size, stride и grouping key.

## 8. Качество данных и риски

Главные риски:

- Смешанные схемы внутри одного расширения: особенно `json`, `log`, `syslog*`, `txt`, `xml`, `pcap` в Host TRAIN.
- Отсутствие заголовков: DNS TEST CSV и часть flow-like файлов требуют заранее закрепленной схемы.
- Очень большие источники: Host TEST `txt`, `bson`, `json`, `log`, а также `wls_day` и `netflow_day`.
- Отсутствие встроенных labels в TEST и части Host источников.
- Packet formats нельзя читать как текст: `pcap`, `pcapng`, `cap` требуют специализированных библиотек.
- BSON и Mongo-style JSON требуют отдельного decoder/parser.

## 9. Рекомендуемая архитектура обработки

Минимально безопасный pipeline:

1. File inventory: собрать `domain`, `split`, `format`, `path`, `size`, checksum.
2. Format routing: направлять файл в parser по `domain/split/format`, а не только по расширению.
3. Streaming read: для больших line-oriented источников читать батчами.
4. Schema detection: различать CSV metadata, telemetry rows, JSON document, JSON Lines, raw syslog, packet capture.
5. Normalization: приводить записи к каноническим сущностям `event`, `metric`, `flow`, `packet`, `trace`, `metadata`.
6. Label join: применять отдельный слой label mapping с сохранением происхождения метки.
7. Feature extraction: строить DNS, host, network и sequence признаки отдельно, затем объединять по ключам времени/host/session.
8. Validation: проверять schema drift, пустые файлы, parse errors, missing critical fields и дубли.

## 10. Приоритеты реализации parser layers

Высокий приоритет:

- DNS `pcap`/`pcapng`: нужен для packet-level DNS features.
- Host `bson`: нужен для TEST behaviour sequences.
- Host `json`: нужен из-за большого числа файлов и Mongo-style вариантов.
- Host `txt`: нужен потоковый parser из-за объема.
- Host `cap`/`pcap`/`pcapng`: нужен для network/hybrid validation.

Средний приоритет:

- Host `auth.log`, `journal`, `journal~`, `log`, `ghc`.
- Mixed JSON/JSON-lines parser для `syslog*`, `mainlog*`, `messages*`, `xml`, `pcap` в TRAIN.
- CSV normalizer для DNS TEST и Host TRAIN metadata/telemetry разделения.

Низкий риск, можно подключать раньше:

- JSON-lines telemetry: `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`.
- Flow-like источники: `netflow_day`, `netflow_ids`.
- Validation metadata CSV.

## 11. Итоговый вывод

Анализ показывает, что датасеты уже достаточно хорошо описаны для начала промышленного feature extraction, но обработка должна быть не универсальной, а маршрутизируемой по формату и схеме.

DNS часть меньше и проще: основной риск связан с отсутствующими TEST PCAP/PCAP.CSV и необходимостью packet parser для PCAP. Host часть крупная и неоднородная: она дает основную ценность для ML, но требует schema-aware parser layers, streaming-read и отдельной политики label mapping.

Для production-ready pipeline критично не смешивать train/test/validation, не извлекать labels неявными regex без audit trail и не читать большие файлы целиком в память.

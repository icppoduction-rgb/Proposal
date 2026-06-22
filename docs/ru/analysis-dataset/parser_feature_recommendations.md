# Рекомендации для parser pipeline и feature extraction

Документ переводит результаты анализа датасетов в требования для Stage Two parser implementations, normalized event schema и feature extraction.

## Общие требования

1. Routing должен учитывать `branch`, `role`, `source_format`, а не только расширение файла.
2. Raw files не изменяются.
3. `TRAIN`, `VALIDATION`, `TEST` обрабатываются раздельно.
4. Для больших line-oriented источников обязателен streaming/batch read.
5. Labels присоединяются отдельным label resolver layer с traceability.
6. Отсутствующий timestamp сохраняется как `timestamp=null`, `timestamp_type=missing` или `event_order`, если доступен порядок события.

## Parser priorities

### Высокий приоритет

| Parser | Форматы | Почему важно |
| --- | --- | --- |
| DNS packet parser | DNS `pcap`, DNS VALIDATION `pcap` | Нужен для packet-level DNS features и validation. |
| Host BSON parser | Host TEST `bson` | Крупный source behaviour sequences; нужен descriptor/event join по `I`. |
| Host JSON parser | Host TRAIN/TEST `json`, `json-1` | Смешанные JSON Lines, Mongo-style JSON, scenario reports. |
| Host syscall/trace parser | Host TEST/VALIDATION/TRAIN `txt`, `sc`, `ghc` | Большие sequence datasets, важны для behaviour-driven learning. |
| Host packet parser | Host VALIDATION `cap`/`pcap`/`pcapng`, Host TRAIN `pcap` | Network/hybrid validation и flow/packet features. |

### Средний приоритет

| Parser | Форматы | Задача |
| --- | --- | --- |
| Host line log parser | `auth.log`, `info`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Различать raw syslog, JSON-lines и scenario documents. |
| Host metric parser | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Metric rows, annotation rows, nested schema variants. |
| CSV normalizers | DNS TEST `csv`, Host TRAIN/VALIDATION/TEST `csv` | Headerless/fixed schema, metadata CSV, external labels. |

### Низкий риск / можно подключать раньше

| Источник | Причина |
| --- | --- |
| DNS `pcap.csv` | Стабильные headers, готов к feature extraction. |
| DNS VALIDATION `txt` | Простая domain-list структура. |
| Host filesystem/fsstat/service/socket/process summary metrics | JSON-lines/telemetry rows. |
| `netflow_day`, `netflow_ids`, `wls_day` | Line-oriented, но требуют streaming и external labels. |

## Parser contracts by format family

| Семейство | Обработка входа | Normalized output | Граничные случаи |
| --- | --- | --- | --- |
| CSV | Schema detection, header/headerless support, fixed positional schemas. | Row events, flow events, label metadata if explicit. | Service CSV files, malformed list/dict fields, label CSV joins. |
| JSON/JSONL | Distinguish JSON Lines, multi-line reports, Mongo-style wrappers. | Event/metadata records with raw payload preserved. | `NumberLong(...)`, nested timestamps, scenario docs. |
| Logs/syslog | Line parser с извлечением timestamp/user/process. | Host log events, event type, component, severity. | Mixed raw syslog и JSON-lines под одним расширением. |
| Metrics | JSON-lines or structured telemetry extraction. | Metric events/windows by host/time/component. | Annotation rows and schema variants. |
| Traces | Streaming line/token parser. | Sequence events with `event_index`. | Missing timestamps; очень большое число файлов. |
| Packet captures | Binary parser. | Packet/flow/DNS events with packet timestamp. | Поврежденные captures, различия pcap/pcapng/cap, performance. |
| BSON | BSON stream decoder. | Sandbox event sequences with descriptor/event relation. | Descriptor-event join by `I`, nested `args`, ordering. |

## Feature extraction map

| Feature group | Источники | Примеры |
| --- | --- | --- |
| `dns_features` | DNS CSV, pcap.csv, DNS packet captures, domain lists | Длина домена, entropy, qtype/rcode/ttl, query rate, unique subdomain ratio. |
| `host_syscall_features` | `txt`, `sc`, `ghc`, BSON sequence events | Syscall/API n-grams, transition probabilities, sequence length, file access indicators. |
| `host_eventlog_features` | syslog/auth/messages/mainlog/mail/info/logs, Windows/Sysmon JSON/WLS | Event type counts, auth success/failure, process chains, alert counts. |
| `host_metrics_features` | CPU/disk/filesystem/memory/network/process/service/socket metrics | Window aggregates, deltas, rates, peak values. |
| `network_flow_features` | `netflow_day`, `netflow_ids`, packet captures | Bytes/packets/duration/protocol/state/window counts. |
| `hybrid_features` | Correlated host + DNS + flow windows | Host process + network flow correlation, exfiltration windows. |
| `sequence_features` | syscall/API/log event order | LSTM/Transformer sequence inputs, n-gram vectors. |

## Readiness-to-action mapping

| Readiness | Stage Two action |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Подключить parser, если он еще не реализован; `mark-ready` можно выполнять после parser coverage check. |
| `NEEDS_CUSTOM_PARSER` | Добавить parser class и registry entry до normalization. |
| `PARTIALLY_SUPPORTED` | Добавить schema detection/sub-parser routing; не считать формат однородным. |
| `BROKEN_OR_EMPTY` | Не нормализовать; проверить Stage One sort/save-sort и source bucket. |

## Data quality checks to add

- Per-format row/event counts after normalization.
- Empty file and empty artifact checks.
- Schema drift report by branch/role/format.
- Label coverage by role/format/status.
- Покрытие timestamp и распределение `timestamp_type`.
- Метрики производительности parser для больших файлов.
- Split contamination check: no TRAIN/VALIDATION/TEST mixing.

## Implementation guardrails

- TEST labels, even if present, are evaluation-only.
- Filename labels must be disabled or heavily restricted for TEST.
- Label/source/traceability fields должны быть исключены из model-ready X.
- `unknown` labels remain unknown until explicit mapping exists.
- Packet/BSON parsers must not load huge files fully into memory.
- Parser errors should produce `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED` or `UNSUPPORTED_FORMAT`, not silent success.

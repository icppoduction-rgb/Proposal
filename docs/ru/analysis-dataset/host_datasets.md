# Host datasets

Host-ветка содержит 58 format buckets и 361640 файлов. Это основной источник host telemetry, sequence traces, runtime logs, Windows/Sysmon-like событий, network flows и packet captures.

## Host TRAIN

Host TRAIN содержит 43 format buckets и 60365 файлов. Это основной источник для обучения, но не все форматы имеют labels и не все пригодны для универсального reader.

### Сводка по семействам

| Семейство | Форматы | Статус обработки |
| --- | --- | --- |
| Metrics/telemetry | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Большинство готовы к feature extraction; `cpu.log` и `diskio.log` частично поддержаны из-за под-схем. |
| Logs | `auth.log`, `info`, `journal`, `journal~`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Требуют schema-aware routing; `journal`/`journal~` требуют отдельный toolchain. |
| Structured/semi-structured | `csv`, `json`, `json-1`, `xml` | CSV частично поддержан из-за служебных файлов; JSON требует schema-aware parser. |
| Network/hybrid | `netflow_ids`, `pcap` | `netflow_ids` готов; `pcap` требует packet/parser layer. |
| Behaviour traces | `ghc`, `sc`, `txt` | `ghc` требует custom parser; `sc`/`txt` пригодны для sequence features. |

### Ключевые Host TRAIN форматы

| Формат | Файлов | Статус | Важные факты |
| --- | ---: | --- | --- |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | Есть telemetry CSV и служебные `feature_descr.csv`/`ground_truth.csv`; labels в колонках 7/8/9 и binary label 0/1. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | Есть metric rows и annotation rows с labels `crack_passwords`, `escalate`; нужен parser split. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | Минимум две под-схемы: `system.diskio` и `host.disk.*`. |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | Смешение raw syslog и JSON-lines. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | Очень большой trace corpus; sample показывает 200 tokens на файл. |
| `journal`, `journal~` | 18 | `NEEDS_CUSTOM_PARSER` | Binary/systemd journal; нельзя читать как обычный text log. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | Смешанные схемы, scenario docs, `exploit`, `container.role`, `alert`. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | Требует packet parser. |
| `filesystem.log`, `fsstat.log` | 24 | `READY_FOR_FEATURE_EXTRACTION` | JSON-lines storage telemetry. |
| `sc`, `txt` | 3380 | `READY_FOR_FEATURE_EXTRACTION` | Syscall/API sequence traces; нужны streaming и sequence-aware features. |

## Host VALIDATION

Host VALIDATION содержит 8 format buckets и 6686 файлов.

| Формат | Файлов | Статус | Labels | Timestamp | Назначение |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Network/hybrid validation; нужен pcap/cap parser. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | частично | Validation metadata и labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON Lines Windows/Sysmon telemetry. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Большие line-oriented network flows. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Packet validation. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Packet validation, pcapng parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Line-oriented syscall traces. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon-like events. |

Validation packet/flow/traces без встроенных labels нужно связывать с validation CSV по `scenario_name`, `image_name`, filename, recording time, exploit start time и timestamp windows.

## Host TEST

Host TEST содержит 7 format buckets и 294589 файлов. Набор нельзя использовать для обучения, но он важен для inference/evaluation.

| Формат | Файлов | Статус | Labels | Timestamp | Назначение |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | нет | частично через порядок/`t`/`h` | Sandbox behaviour sequence; нужен BSON parser и сопоставление descriptor/event docs по `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | label в отдельных label CSV | да | Network/hybrid evaluation; labels join по IP или подтвержденному ключу. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | нет | да | JSON Lines, Mongo-style `NumberLong(...)`, большие reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Line-oriented sandbox runtime logs. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Большие network flow files. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Syscall/API sequence traces; очень большое число файлов. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon-like authentication/process events. |

## Host feature extraction

Приоритетные признаки:

- process/service/socket counts and transitions;
- syscall/API n-grams and sequence embeddings;
- authentication success/failure and session patterns;
- filesystem, CPU, memory, disk I/O, network telemetry aggregates;
- flow statistics, packet protocol distributions;
- Windows/Sysmon event IDs, parent-child process chains;
- alert/context fields as metadata, not X labels.

## Host quality risks

- Mixed schemas inside one extension: especially `json`, `log`, `syslog*`, `txt`, `xml`, `pcap` in TRAIN.
- Очень большие источники: TEST `txt`, `bson`, `json`, `log`, `wls_day`, `netflow_day`.
- Missing embedded labels in most Host telemetry/log/packet/sequence files.
- Packet formats require binary parsers; BSON and Mongo-style JSON require specialized decoders.

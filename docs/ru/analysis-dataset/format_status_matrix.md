# Матрица форматов и статусов

Матрица сохраняет ключевые данные из 66 старых per-format отчетов: split, format, число файлов, readiness, label availability, timestamp availability и основное ограничение. Полные старые пути перечислены в [source_inventory.md](source_inventory.md).

## Сводка по статусам

| Статус | Format buckets | Файлов |
| --- | ---: | ---: |
| `READY_FOR_FEATURE_EXTRACTION` | 42 | 288866 |
| `NEEDS_CUSTOM_PARSER` | 14 | 72666 |
| `PARTIALLY_SUPPORTED` | 6 | 138 |
| `BROKEN_OR_EMPTY` | 2 | 0 |

## DNS

| Role | Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | --- | ---: | --- | --- | --- | --- |
| `TRAIN` | `csv` | 8 | `PARTIALLY_SUPPORTED` | class hints: benign/malware/phishing/spam | частично | Нужна schema-aware normalization для feature CSV с list/dict полями. |
| `TRAIN` | `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | filename class hints | да | Нужен packet parser с DNS decoding. |
| `TRAIN` | `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | filename class hints: audio/benign/compressed/exe/image/text/video | да | Готов к DNS feature extraction после label mapping. |
| `VALIDATION` | `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | filename class hints: attack/benign | да | Нужен packet parser для validation packet features. |
| `VALIDATION` | `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | filename hints: unknown/benign | нет | Domain-list; `unknown` требует отдельной policy. |
| `TEST` | `csv` | 1 | `PARTIALLY_SUPPORTED` | partial boolean-like `label_or_flag` | да | Headerless 22-column schema; только evaluation. |
| `TEST` | `pcap` | 0 | `BROKEN_OR_EMPTY` | нет | нет | Bucket пустой. |
| `TEST` | `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | нет | нет | Bucket пустой. |

## Host TRAIN

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | нет | да | Raw syslog + JSON-lines; нужен parser с ветвлением. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | embedded/annotation labels: crack_passwords, escalate | да | Разделить metric rows и annotation rows. |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | attack categories + binary 0/1 | да | Отличать telemetry CSV от `feature_descr.csv` и `ground_truth.csv`. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | нет | да | Минимум две под-схемы: `system.diskio` и `host.disk.*`. |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON-lines storage telemetry. |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON-lines storage telemetry. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | нет | нет | Специализированный trace parser; большой объем. |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Mail/service logs; schema-aware parser. |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | нет | нет | Binary/systemd journal. |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | нет | нет | Binary/systemd journal backup. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | schema-dependent: exploit/container.role/alert | да | Смешанные schemas; нужен schema-aware parser. |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware extraction; labels только через resolver. |
| `load.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | нет/контекстно | Telemetry; timestamp может быть вложенным/контекстным. |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | context hints | да | Mixed JSON/scenario/log schemas. |
| `log-1` | 32 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `log-2` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Schema-aware parser layer. |
| `log-3` | 8 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Schema-aware parser layer. |
| `mail-info-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Mail log parser. |
| `mail-warn-1` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Mail log parser. |
| `mainlog` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-2` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-3` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `memory.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Metric telemetry; labels external only. |
| `messages` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `messages-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Flow-like source; line-oriented parser. |
| `network.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Network telemetry. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | нет | нет в extracted summary | Требуется packet parser. |
| `process.log` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Process event features. |
| `process.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Process summary features. |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Syscall/API trace parser. |
| `service.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Service telemetry. |
| `socket.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Socket summary features. |
| `syslog` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-1` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-2` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-3` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-4` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Sequence/trace parser; streaming required. |
| `uptime.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Uptime/metric features. |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | XML/schema-aware parser. |

## Host VALIDATION

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | Packet parser; labels через scenario/CSV join. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | частично | Validation labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon JSON Lines. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Большие flow files; external labels only. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | Packet parser; labels через scenario/CSV join. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | PCAPNG parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Syscall traces; streaming required. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon-like events. |

## Host TEST

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | нет | частично | BSON parser; descriptor/event join по `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | external label CSV | да | Labels только для evaluation; join по IP/ключу. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | нет | да | JSON Lines, Mongo-style `NumberLong(...)`, reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Очень большие syscall/API traces; нужен streaming. |

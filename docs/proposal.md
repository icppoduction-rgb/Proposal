# Proposal

Сводный файл, собранный из Markdown-документов `docs/ru`. Файл `docs/ru/Project Proposal.docx` исключен по условию задачи.

Дата пересборки: 2026-07-08.

## Состав

- `docs/ru/analysis-dataset/dns_datasets.md`
- `docs/ru/analysis-dataset/format_status_matrix.md`
- `docs/ru/analysis-dataset/host_datasets.md`
- `docs/ru/analysis-dataset/labels_and_readiness.md`
- `docs/ru/analysis-dataset/parser_feature_recommendations.md`
- `docs/ru/analysis-dataset/README.md`
- `docs/ru/analysis-dataset/source_inventory.md`
- `docs/ru/code-documentation/cli_and_routing.md`
- `docs/ru/code-documentation/data_leakage_prevention.md`
- `docs/ru/code-documentation/data_quality_checks.md`
- `docs/ru/code-documentation/dataset_contracts.md`
- `docs/ru/code-documentation/extension_points.md`
- `docs/ru/code-documentation/label_resolver.md`
- `docs/ru/code-documentation/normalized_event_schema.md`
- `docs/ru/code-documentation/parquet_and_duckdb.md`
- `docs/ru/code-documentation/parser_strategy.md`
- `docs/ru/code-documentation/postgresql_catalog.md`
- `docs/ru/code-documentation/README.md`
- `docs/ru/code-documentation/risks_and_technical_debt.md`
- `docs/ru/code-documentation/sqlalchemy_layer.md`
- `docs/ru/code-documentation/stage_one_handlers.md`
- `docs/ru/code-documentation/stage_three_overview.md`
- `docs/ru/code-documentation/stage_two_overview.md`
- `docs/ru/code-documentation/storage_architecture.md`
- `docs/ru/code-documentation/traceability.md`
- `docs/ru/dataset_strategy_dns_host.md`
- `docs/ru/feature_extraction_and_catalogue.md`
- `docs/ru/normalization/data_leakage_prevention.md`
- `docs/ru/normalization/data_quality_checks.md`
- `docs/ru/normalization/final_summary_template.md`
- `docs/ru/normalization/host_validation_wls_day_exclusion.md`
- `docs/ru/normalization/label_resolver.md`
- `docs/ru/normalization/normalized_event_schema.md`
- `docs/ru/normalization/parquet_duckdb_artifacts.md`
- `docs/ru/normalization/parser_development_guide.md`
- `docs/ru/normalization/parser_strategy.md`
- `docs/ru/normalization/performance_tuning.md`
- `docs/ru/normalization/postgresql_catalog_schema.md`
- `docs/ru/normalization/README.md`
- `docs/ru/normalization/runtime_resource_runbook.md`
- `docs/ru/normalization/stage_two_commands.md`
- `docs/ru/normalization/storage_architecture.md`
- `docs/ru/normalization/traceability.md`
- `docs/ru/normalization/usage_guide.md`
- `docs/ru/project_documentation_index.md`
- `docs/ru/project_overview_and_research_context.md`
- `docs/ru/README.md`
- `docs/ru/repository_analysis.md`
- `docs/ru/repository_state_qa_and_gaps.md`
- `docs/ru/stage-three/performance_tuning.md`
- `docs/ru/stage-three/README.md`
- `docs/ru/stage-three/stage_three_commands.md`
- `docs/ru/stage-three/usage_guide.md`

---

## Источник: `docs/ru/analysis-dataset/dns_datasets.md`

# DNS datasets

DNS-ветка содержит 8 format buckets и 35 файлов. Она делится на табличные CSV, packet captures и domain-list TXT. DNS `TEST` не содержит подготовленных `pcap`/`pcap.csv` файлов, поэтому TEST packet-level проверка в текущем наборе невозможна.

## DNS TRAIN

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 8 | `PARTIALLY_SUPPORTED` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | частично | Domain-list и PhishTank-like файлы читаются напрямую; feature CSV могут содержать неэкранированные list/dict поля с запятыми. |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | да, packet timestamp | Нужен packet parser с classic pcap/pcapng и DNS protocol decoding. |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | class hint из имени файла: `audio`, `benign`, `compressed`, `exe`, `image`, `text`, `video` | да | CSV-структура стабильна, заголовки присутствуют; подходит для DNS feature extraction после label mapping. |

Правило labels: filename/class hint можно использовать только как `label_source=filename`/`inferred_label`. Payload classes (`audio`, `compressed`, `exe`, `image`, `text`, `video`) нельзя автоматически считать exfiltration labels без зафиксированного target mapping.

## DNS VALIDATION

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `attack`, `benign` | да, packet timestamp | Подходит для проверки DNS amplification/detection pipeline, но требует packet parser. |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | class hint: `unknown`, `benign` | нет | Domain-list: одна доменная запись на строку. `unknown` нельзя считать benign или attack без policy. |

## DNS TEST

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 1 | `PARTIALLY_SUPPORTED` | частичное boolean-like поле `label_or_flag` в sample | да | Большой CSV без заголовка; нужна закрепленная 22-колоночная схема и streaming-read. Использовать только для evaluation. |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap` нет файлов. |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap.csv` нет файлов. |

## Выводы для DNS parsers

| Компонент Stage Two | Что требуется |
| --- | --- |
| `DnsCsvParser` | Различать TRAIN CSV под-схемы, DNS TEST headerless 22-column schema и domain-list/PhishTank-like sources. |
| `DnsPcapCsvParser` | Поддерживать стабильные CSV headers и сохранять filename class hints как label metadata. |
| `DnsTxtDomainListParser` | Читать одну доменную запись на строку, сохранять `timestamp=null`, `timestamp_type=missing` или `event_order`. |
| `DnsPacketCaptureParser` | Извлекать packet timestamp, DNS query/response fields, qtype/qclass/rcode/ttl, network tuple и packet-level metadata. |

## DNS feature extraction

Приоритетные признаки:

- длина домена, поддомена, query string;
- entropy и charset distribution;
- unique subdomain ratio;
- query rate/window counts;
- qtype/rcode/ttl distribution;
- packet size/response size;
- payload class context для pcap.csv, если mapping утвержден.

## DNS quality risks

- DNS TEST packet buckets пустые (`BROKEN_OR_EMPTY`).
- DNS TEST CSV без header требует fixed positional schema.
- `unknown` в VALIDATION TXT не является class label.
- Filename labels требуют audit trail и не должны попадать в X features.


---

## Источник: `docs/ru/analysis-dataset/format_status_matrix.md`

# Матрица форматов и статусов

Матрица сохраняет ключевые данные из 66 старых per-format отчетов: split, format, число файлов, readiness, label availability, timestamp availability и основное ограничение. Полные старые пути перечислены в [source_inventory.md](ru/analysis-dataset/source_inventory.md).

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


---

## Источник: `docs/ru/analysis-dataset/host_datasets.md`

# Host datasets

Host-ветка содержит 56 format buckets и 361635 файлов. Это основной источник host telemetry, sequence traces, runtime logs, Windows/Sysmon-like событий, network flows и packet captures.

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

Host TEST содержит 5 format buckets и 294584 файлов. Набор нельзя использовать для обучения, но он важен для inference/evaluation.

| Формат | Файлов | Статус | Labels | Timestamp | Назначение |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | нет | частично через порядок/`t`/`h` | Sandbox behaviour sequence; нужен BSON parser и сопоставление descriptor/event docs по `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | label в отдельных label CSV | да | Network/hybrid evaluation; labels join по IP или подтвержденному ключу. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | нет | да | JSON Lines, Mongo-style `NumberLong(...)`, большие reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Line-oriented sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Syscall/API sequence traces; очень большое число файлов. |

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
- Очень большие источники: TEST `txt`, `bson`, `json`, `log`.
- Missing embedded labels in most Host telemetry/log/packet/sequence files.
- Packet formats require binary parsers; BSON and Mongo-style JSON require specialized decoders.


---

## Источник: `docs/ru/analysis-dataset/labels_and_readiness.md`

# Labels и readiness

Документ объединяет сведения о label availability и parser/feature readiness из старого `dataset_labels_availability_and_recommendations.md` и per-format отчетов.

## Главные правила

1. Отсутствие label не означает benign.
2. `TEST` нельзя использовать для обучения, fit preprocessing, feature selection или threshold tuning.
3. Labels из filename, directory, scenario metadata или IDS alert должны иметь `label_source`, `label_status`, confidence и traceability.
4. Weak labels не равны ground truth.
5. Для файлов без labels сохранять `label_binary = null`, `label_source = none`, `label_status = unlabeled`.
6. Label/source fields не должны попадать в model-ready `X`.

## Canonical label fields

| Поле | Назначение |
| --- | --- |
| `label_binary` | `0=benign`, `1=malicious/attack/exfiltration`, `null=unknown`. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, unknown. |
| `label_subtype` | subtype/scenario, если доступен. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 для explicit, ниже для inferred/weak, null/0 для unlabeled. |
| `label_mapping_rule_id` | ID правила mapping. |
| `dataset_role` | TRAIN / VALIDATION / TEST. |
| `source_file` | Исходный путь/имя файла. |
| `source_event_id` | Строка/пакет/событие, если применимо. |

## Label availability summary

| Категория | Format buckets | Источники |
| --- | ---: | --- |
| Прямые labels | 5 | Host TRAIN `cpu.log`, Host TRAIN `csv`, Host TRAIN `json`, Host VALIDATION `csv`, Host TEST `csv` через label CSV. |
| Частичные labels / class hints | 6 | DNS TRAIN `csv`/`pcap`/`pcap.csv`, DNS VALIDATION `pcap`/`txt`, DNS TEST `csv`. |
| Без встроенных labels | 55 | Большинство host telemetry/log/packet/sequence formats. |

## Источники с прямыми labels

| Domain | Role | Формат | Файлов | Label field/source | Values | Как использовать |
| --- | --- | ---: | ---: | --- | --- | --- |
| Host | `TRAIN` | `cpu.log` | 13 | `labels` annotation rows | `crack_passwords`, `escalate` | Partial/weak labels; связать с metric windows по timestamp/host. |
| Host | `TRAIN` | `csv` | 101 | columns 7/8/9 | normal/attack categories + binary 0/1 | Основной supervised TRAIN источник после schema-aware normalization. |
| Host | `TRAIN` | `json` | 219 | `exploit` / `container.role` / `alert` | True/False/normal/victim/alert-derived | Schema-dependent; `exploit` inferred, `alert` weak, `container.role` context. |
| Host | `VALIDATION` | `csv` | 6 | `is_executing_exploit` | False 5813, True 187 | Основной validation label/context источник. |
| Host | `TEST` | `csv` | 3 | external label CSV | scan/attack labels | Только final evaluation; не training. |

## Источники с filename/class hints

| Domain | Role | Формат | Файлов | Hint values | Ограничение |
| --- | --- | --- | ---: | --- | --- |
| DNS | `TRAIN` | `csv` | 8 | benign, malware, phishing, spam | Использовать как inferred labels только через фиксированный mapping. |
| DNS | `TRAIN` | `pcap` | 4 | benign, malware, phishing, spam | Нужен packet parser и filename mapping. |
| DNS | `TRAIN` | `pcap.csv` | 14 | audio, benign, compressed, exe, image, text, video | Payload class не равен attack label без target policy. |
| DNS | `VALIDATION` | `pcap` | 5 | attack, benign | Filename mapping допустим для validation after audit. |
| DNS | `VALIDATION` | `txt` | 3 | unknown, benign | `unknown` не считать benign/attack автоматически. |
| DNS | `TEST` | `csv` | 1 | boolean-like `label_or_flag` | TEST только для evaluation; нужна schema policy. |

## Readiness statuses

| Статус | Что означает для Stage Two |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Можно подключать к feature extraction после корректной нормализации; не означает наличие labels. |
| `NEEDS_CUSTOM_PARSER` | Нужен специализированный parser/decoder или binary/schema-aware layer. |
| `PARTIALLY_SUPPORTED` | Формат пригоден частично; parser должен различать под-схемы, служебные файлы или fixed schema. |
| `BROKEN_OR_EMPTY` | Bucket пустой или отсутствует; feature extraction невозможен до восстановления input. |

## Правила для TRAIN / VALIDATION / TEST

| Role | Разрешено | Запрещено |
| --- | --- | --- |
| `TRAIN` | Обучение и fit preprocessing только после label-safe mapping. | Использовать weak labels как ground truth без статуса/уверенности. |
| `VALIDATION` | Проверка качества, threshold tuning только если это предусмотрено experiment design. | Смешивать с TRAIN artifacts. |
| `TEST` | Только финальная оценка/inference. | Training, fit scaler/encoder, feature selection, threshold tuning, filename heuristic label inference. |

## Минимальный LabelResolver алгоритм

1. Сохранить inventory: domain, role, format, source_file, checksum, file_size.
2. На parsing этапе извлечь timestamp, host, ip, process/session/scenario identifiers, row/event/packet id.
3. Применить правила в порядке:
   - embedded column;
   - external label file (`ground_truth.csv`, `runs.csv`, attack labels);
   - filename/class hint;
   - scenario metadata;
   - IDS alert as weak label;
   - no match -> unlabeled.
4. При конфликте выставить `conflicting_label`, а не выбирать класс произвольно.
5. Для `TEST` разрешать labels только для evaluation после завершения training pipeline.

## Связь с normalization

См. также:

- [../normalization/label_resolver.md](ru/normalization/label_resolver.md)
- [../normalization/data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md)
- [../normalization/traceability.md](ru/normalization/traceability.md)


---

## Источник: `docs/ru/analysis-dataset/parser_feature_recommendations.md`

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


---

## Источник: `docs/ru/analysis-dataset/README.md`

# Анализ датасетов

Раздел фиксирует результаты Stage One анализа DNS/Host датасетов и переводит их в удобную форму для Stage Two normalization, parser registry и feature extraction.

## Что изменено в структуре

Старые per-format отчеты были полезны как сырые заметки, но создавали дубли:

- `dns/<role>/<format>.md` и `host/<role>/<format>.md` повторяли одну и ту же структуру для 64 format buckets;
- `general_dns_*` и `general_host_*` агрегировали те же сведения повторно;
- `analysis-dataset.md` и `dataset_labels_availability_and_recommendations.md` частично пересекались с normalization/label docs.

Новая структура оставляет данные по counts/status/labels/timestamps/readiness в тематических документах:

| Документ | Назначение |
| --- | --- |
| [dns_datasets.md](ru/analysis-dataset/dns_datasets.md) | DNS TRAIN/VALIDATION/TEST: форматы, количество файлов, labels, timestamp/readiness, parser notes. |
| [host_datasets.md](ru/analysis-dataset/host_datasets.md) | Host TRAIN/VALIDATION/TEST: семейства данных, количество файлов, quality risks, parser notes. |
| [format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) | Единая таблица 64 format buckets со статусом readiness и ключевыми фактами. |
| [labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) | Label availability, canonical label rules, readiness statuses и anti-leakage правила. |
| [parser_feature_recommendations.md](ru/analysis-dataset/parser_feature_recommendations.md) | Рекомендации для Stage Two parser implementations и feature extraction. |
| [source_inventory.md](ru/analysis-dataset/source_inventory.md) | Индекс старых файлов, которые были объединены в новую структуру. |

Связанные документы:

- [../normalization/README.md](ru/normalization/README.md)
- [../normalization/parser_strategy.md](ru/normalization/parser_strategy.md)
- [../normalization/label_resolver.md](ru/normalization/label_resolver.md)
- [../normalization/normalized_event_schema.md](ru/normalization/normalized_event_schema.md)
- [../feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md)
- [../dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md)

## Покрытие анализа

| Группа | Format buckets | Файлов | Основной смысл |
| --- | ---: | ---: | --- |
| `dns/TRAIN` | 3 | 26 | DNS train: CSV, PCAP и `pcap.csv`. |
| `dns/VALIDATION` | 2 | 8 | DNS validation: PCAP и domain-list TXT. |
| `dns/TEST` | 3 | 1 | DNS test: фактически доступен только CSV. |
| `host/TRAIN` | 43 | 60365 | Host train: telemetry, logs, JSON/JSON-lines, traces, flows, pcap. |
| `host/VALIDATION` | 8 | 6686 | Host validation: metadata, JSON-lines, flows, traces, packet captures. |
| `host/TEST` | 5 | 294584 | Host test: BSON, CSV, JSON, logs, traces. |
| **Итого** | **64** | **361670** | DNS и Host источники для feature extraction. |

## Статусы готовности

| Статус | Format buckets | Файлов | Значение |
| --- | ---: | ---: | --- |
| `READY_FOR_FEATURE_EXTRACTION` | 42 | 288866 | Формат можно подключать к feature extraction после streaming/schema-aware normalization. |
| `NEEDS_CUSTOM_PARSER` | 14 | 72666 | Нужен специализированный parser или decoder. |
| `PARTIALLY_SUPPORTED` | 6 | 138 | Формат частично пригоден, но содержит под-схемы, служебные файлы или требует fixed schema. |
| `BROKEN_OR_EMPTY` | 2 | 0 | В подготовленном bucket нет входных файлов. |

## Инварианты использования

1. `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
2. `TEST` не используется для обучения, fit preprocessing, feature selection или threshold tuning.
3. Отсутствие label не означает benign.
4. Filename/class hints являются label source только при явном mapping и audit trail.
5. Raw files не изменяются; Stage Two должен сохранять traceability.
6. Для отсутствующего timestamp нельзя синтетически подставлять текущее время.

## Сводный pipeline

```mermaid
flowchart TD
    A["Stage One analyze/sort/save-sort"] --> B["analysis-dataset docs"]
    B --> C["format_status_matrix.md"]
    B --> D["labels_and_readiness.md"]
    B --> E["parser_feature_recommendations.md"]
    C --> F["Stage Two parser registry"]
    D --> G["LabelResolver and quality checks"]
    E --> H["Normalization and feature extraction"]
```

## Практический вывод

DNS-часть компактная и в основном требует DNS packet parser для PCAP/PCAPNG и fixed schema для DNS TEST CSV. Host-часть крупная и неоднородная: основная ценность для ML находится в telemetry/log/trace данных, но pipeline должен быть format-aware, streaming-friendly и label-safe.


---

## Источник: `docs/ru/analysis-dataset/source_inventory.md`

# Индекс объединенных источников

Документ фиксирует, какие старые файлы были объединены в новую тематическую структуру. Он нужен, чтобы не потерять навигацию после удаления дублей.

## Новые документы

| Новый документ | Что содержит |
| --- | --- |
| [README.md](ru/analysis-dataset/README.md) | Общая карта раздела, coverage, readiness counts, инварианты. |
| [dns_datasets.md](ru/analysis-dataset/dns_datasets.md) | Все DNS TRAIN/VALIDATION/TEST сведения. |
| [host_datasets.md](ru/analysis-dataset/host_datasets.md) | Все Host TRAIN/VALIDATION/TEST сведения. |
| [format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) | 64 format buckets: files/status/labels/timestamp/action. |
| [labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) | Label policy, readiness statuses, LabelResolver guidance. |
| [parser_feature_recommendations.md](ru/analysis-dataset/parser_feature_recommendations.md) | Parser priorities, feature groups, quality checks. |

## Старые верхнеуровневые файлы

| Старый файл | Куда перенесено содержание |
| --- | --- |
| `analysis-dataset.md` | `README.md`, `dns_datasets.md`, `host_datasets.md`, `parser_feature_recommendations.md`. |
| `dataset_labels_availability_and_recommendations.md` | `labels_and_readiness.md`, `parser_feature_recommendations.md`. |

## Старые агрегаты по split

| Старый файл | Куда перенесено содержание |
| --- | --- |
| `dns/train/general_dns_train.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/general_dns_validation.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/general_dns_test.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `host/train/general_host_train.md` | `host_datasets.md`, `format_status_matrix.md`, `parser_feature_recommendations.md`. |
| `host/validation/general_host_validation.md` | `host_datasets.md`, `format_status_matrix.md`. |
| `host/test/general_host_test.md` | `host_datasets.md`, `format_status_matrix.md`. |

## Старые per-format файлы

### DNS

| Старый каталог | Файлы | Новый документ |
| --- | --- | --- |
| `dns/train/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/` | `pcap.md`, `txt.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |

### Host TRAIN

`host/train/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `auth.log`, `cpu.log`, `csv`, `diskio.log`, `filesystem.log`, `fsstat.log`, `ghc`, `info`, `journal`, `journal~`, `json`, `json-1`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `netflow_ids`, `network.log`, `pcap`, `process.log`, `process.summary.log`, `sc`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `txt`, `uptime.log`, `xml`.

### Host VALIDATION

`host/validation/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `cap`, `csv`, `json`, `netflow_day`, `pcap`, `pcapng`, `txt`, `wls_day`.

### Host TEST

`host/test/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `bson`, `csv`, `json`, `log`, `txt`.

## Почему старые файлы удаляются

Старые документы содержали полезные исходные observations, но:

- дублировали структуру и выводы в `general_*`;
- усложняли навигацию по 80 файлам;
- мешали видеть общую readiness/label картину;
- часть сведений была уже отражена в normalization/code documentation.

Ключевые данные из них перенесены в новую тематическую структуру.


---

## Источник: `docs/ru/code-documentation/cli_and_routing.md`

# CLI и слой routing

## Точка входа

Главная точка входа: `manage.py`.

`manage.py` создает `argparse.ArgumentParser` с позиционными аргументами:

| Аргумент | Назначение |
|---|---|
| `module` | верхний routing namespace: `handlers`, `stage-two` или `stage-three` |
| `service` | service/action group внутри module |
| `action` | первый action или первый positional argument service-команды |
| `extra_args` | остаток аргументов для Stage Two команд |

Фактическая маршрутизация:

```text
manage.py
  -> stage-three shortcut: scripts.stage_three.cli.router_stage_three(service, extra_args)
  -> scripts.router_script.router_commands(module, service, action, extra_args)
     -> handlers: scripts.handlers.router_handler.router_commands_handlers(service, action)
     -> stage-two: scripts.stage_two.cli.router_stage_two(service, action, extra_args)
```

Если `module` неизвестен, печатается `config.manage_commands`.

Сверка с кодом от 2026-07-06: `config.manage_commands` является fallback-строкой для вывода в консоль. Для Stage Two используйте `scripts/stage_two/cli.py`, для Stage Three — `scripts/stage_three/cli.py`.

## Маршруты Stage One

Файл: `scripts/handlers/router_handler.py`.

| Service | Router | Actions |
|---|---|---|
| `analyze-dataset` | `scripts/handlers/analyze_dataset/router_analyze.py` | `dns-dataset-handler`, `host-dataset-handler` |
| `filter-dataset` | `scripts/handlers/filter_dataset/router_filter.py` | `filter-host-dataset-handler` |
| `sort` | `scripts/handlers/sort/router_sort.py` | `sort-dns-dataset-handler`, `sort-host-dataset-handler` |
| `save-sort` | `scripts/handlers/save_sort/router_save.py` | `save-sort-dns-dataset-handler`, `save-sort-host-dataset-handler` |
| `dns-analyze` | `scripts/handlers/dns_analyze/router_dns.py` | DNS actions по role/format content |
| `host-analyze` | `scripts/handlers/host_analyze/router_host.py` | Host actions по role/format content |

### Порядок Stage One DNS

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <action>
```

DNS content actions:

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

### Порядок Stage One Host

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <action>
```

Host content actions включают `analyze-csv-content`, `analyze-auth-log-content`, `analyze-json-content`, `analyze-validation-pcapng-content`, `analyze-test-bson-content`, `analyze-test-wls-day-content` и другие actions из `scripts/handlers/host_analyze/router_host.py`.

## Маршруты Stage Two

Файл: `scripts/stage_two/cli.py`.

| Команда | Аргументы | Назначение |
|---|---|---|
| `bootstrap-storage` | нет | создать storage tree под `PATH_DATA_STORAGE` |
| `catalog-ingest` | нет | просканировать `PATH_FOLDER_DATASETS_FILTER` и зарегистрировать файлы |
| `seed-parser-registry` | нет | зарегистрировать normalized schema и parser registry seed |
| `parser-coverage` | `[branch]` | показать coverage catalog formats vs active parsers |
| `mark-ready` | flags или fallback | перевести выбранные файлы в `READY_FOR_PARSING` |
| `normalize-format` | flags или fallback | нормализовать одну группу `branch/role/source_format` |
| `normalize-all` | flags или fallback | нормализовать все ready группы внутри branch по очереди |
| `benchmark-normalization` | flags | измерить скорость одного точного bucket `branch/role/source_format` и оценить throughput |
| `split-large-files` | flags | split line-based больших файлов |
| `normalize-dns` | `[limit]` | legacy branch-level normalization для DNS ready files |
| `normalize-host` | `[limit]` | legacy branch-level normalization для Host ready files |
| `run-duckdb-checks` | нет | создать DuckDB views и analytics report |
| `run-leakage-checks` | нет | проверить model-ready leakage и preprocessing fit role |
| `trace-artifact` | `<model_ready_id_or_artifact_path>` | вывести traceability chain |

## Маршруты Stage Three

Файл: `scripts/stage_three/cli.py`.

| Команда | Аргументы | Назначение |
|---|---|---|
| `validate-inputs` | `--branch`, `--role` | readiness gate для Stage Two normalized artifacts |
| `build-feature-catalog` | `[--feature-group]` | validate feature catalog contract |
| `probe-runtime-backend` | `--backend`, `[--profile]`, `[--skip-probe]` | выбрать CPU/GPU backend и memory guard |
| `extract-features` | `--branch`, `--role`, `--feature-group`, `[--experiment-id]`, `[--resume]` | извлечь feature artifacts из normalized Parquet |
| `align-labels` | `--branch`, `--role`, `--label-policy`, `[--experiment-id]` | применить label policy без leakage в X |
| `build-sequences` | `--branch`, `[--role]`, `[--feature-group]`, `[--experiment-id]` | собрать sequence/window artifacts |
| `build-model-ready` | `--experiment-id`, `--branch`, `--target`, `--preprocessing-profile` | собрать X/y/metadata/traceability artifacts |
| `run-quality-checks` | `--experiment-id`, optional scope flags | проверить artifacts и зарегистрировать reports |
| `run-leakage-checks` | `--experiment-id`, optional scope flags | проверить leakage и traceability |
| `trace-artifact` | `<model_ready_artifact_id>` или `--experiment-id` | восстановить lineage |
| `final-report` | `--experiment-id`, `[--branch]` | сгенерировать Task20 RU/EN final report |

### Базовый порядок Stage Three

```bash
python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three validate-inputs --branch dns --role VALIDATION
python manage.py stage-three validate-inputs --branch dns --role TEST
python manage.py stage-three build-feature-catalog
python manage.py stage-three probe-runtime-backend --backend auto
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001
```

### Базовый порядок Stage Two

```bash
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Порядок из постановки также поддержан для legacy routes:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Аргументы Stage Two

`normalize-dns` и `normalize-host` принимают не более одного optional limit. Значение должно быть неотрицательным integer.

`parser-coverage` принимает optional `branch` из `dns`, `host`, `network`, `hybrid`.

`mark-ready`:

```bash
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --retry-failed --apply
python manage.py stage-two mark-ready dry-run:dns:TRAIN:csv
```

`normalize-format`:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format json \
  --limit 100 \
  --workers 1 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume \
  --packet-mode packet-summary \
  --hash-output-artifacts
```

Fallback-формат:

```bash
python manage.py stage-two normalize-format host:TRAIN:json:100
```

`normalize-all`:

```bash
python manage.py stage-two normalize-all --branch dns --limit 100 --resume
python manage.py stage-two normalize-all dns:100
```

`split-large-files`:

```bash
python manage.py stage-two split-large-files \
  --branch dns \
  --role TEST \
  --format csv \
  --limit 1 \
  --max-part-size-gb 2 \
  --min-size-gb 1 \
  --header no \
  --apply \
  --register
```

Ограничение: split предназначен для line-based formats. Не применять к binary `cap`, `pcap`, `pcapng`, `bson`.

## Команды и выходы

| Команда | Основной input | Основной output |
|---|---|---|
| `handlers analyze-dataset dns-dataset-handler` | `PATH_DNS_DATASETS` | `PATH_TEMP_DATA/dns-path-file.json`, `dns-file.json` |
| `handlers analyze-dataset host-dataset-handler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |
| `handlers filter-dataset filter-host-dataset-handler` | Host JSON inventory | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, filter log |
| `handlers sort sort-*-dataset-handler` | path/file JSON | sorted tree в `PATH_*_DATASETS_FILTER`, sort summary JSON |
| `handlers save-sort save-sort-*-dataset-handler` | sorted tree | `sort-path-*-file.json`, summary JSON |
| `handlers dns-analyze/host-analyze` | `sort-path-*-file.json` | analysis summary JSON, docs, reports |
| `stage-two catalog-ingest` | `PATH_FOLDER_DATASETS_FILTER` | `datasets`, `ingestion_runs`, `dataset_files` |
| `stage-two seed-parser-registry` | schema JSON + seed JSON | `schema_versions`, `parser_registry` |
| `stage-two normalize-*` | `dataset_files.status=READY_FOR_PARSING` | `parser_runs`, `normalized_artifacts`, Parquet |
| `stage-two run-duckdb-checks` | Parquet layers | JSON quality report, `data_quality_reports` |
| `stage-two run-leakage-checks` | model-ready Parquet + preprocessing catalog | leakage report, `data_quality_reports` |
| `stage-three extract-features` | normalized Parquet + feature catalog | feature Parquet, `feature_artifacts`, Task07/08/09 reports |
| `stage-three build-model-ready` | feature Parquet + feature catalog | X/y/metadata/traceability Parquet, `model_ready_artifacts`, Task17 report |
| `stage-three run-quality-checks` | feature/model-ready/preprocessing artifacts | `data_quality_reports`, Task18 report |
| `stage-three run-leakage-checks` | model-ready artifacts + preprocessing catalog | leakage/traceability reports, blocking statuses |
| `stage-three final-report` | Stage Three catalog state | Task20 RU/EN report, Stage Four readiness status |

## Важные ограничения CLI

- `python manage.py stage-two` без команды печатает `unknown Stage Two command` и legacy-текст `config.manage_commands`; этот вывод не содержит все новые команды и не должен считаться полным help.
- `handlers` routes не принимают произвольные flags; `action` должен совпадать с router case.
- Stage One content analysis падает, если нужный role/format bucket отсутствует в `sort-path-*-file.json`.
- `catalog-ingest` сканирует `PATH_FOLDER_DATASETS_FILTER`, а не raw `PATH_FOLDER_DATASETS`.
- `normalize-format` и `normalize-all` обрабатывают только `READY_FOR_PARSING`.
- `benchmark-normalization` использует те же точные bucket-входы, что и `normalize-format`; actual benchmark принудительно включает resume behavior, если не указан `--dry-run`.
- `normalize-all` группирует по `role/source_format` и сохраняет порядок ролей из `ACTIVE_DATASET_ROLE_VALUES`: `TRAIN`, `VALIDATION`, `TEST`.
- Stage Two `trace-artifact` и Stage Three `trace-artifact` работают только для уже зарегистрированных `model_ready_artifacts`.
- Stage Three `final-report` может записать отчет с `NOT_READY_FOR_STAGE_FOUR`, если PostgreSQL Catalog недоступен или checks не подтверждают готовность artifacts.


---

## Источник: `docs/ru/code-documentation/data_leakage_prevention.md`

# Предотвращение data leakage

Предотвращение leakage обеспечивается документацией, контрактами, runtime validation и DuckDB checks. Полагаться только на соглашения небезопасно.

## Жесткие правила

1. `TEST` никогда не используется для training, preprocessing fit, encoder/scaler fit, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` остаются физически разделенными по role в Parquet paths.
3. Labels хранятся отдельно от X-признаков.
4. Model-ready X artifacts не должны содержать label/source/traceability leakage columns.
5. Отсутствующие labels получают статус `unlabeled`, а не benign.
6. Filename heuristic для TEST отключен.

## Контроль в коде

| Правило | Код |
|---|---|
| X forbidden columns | `scripts/stage_two/model_ready/contracts.py::validate_x_columns` |
| Исключенные колонки feature layer | `scripts/stage_two/features/contracts.py::X_EXCLUDED_COLUMNS` |
| TRAIN-only preprocessing | `validate_preprocessing_fit_role()` и DB check constraint |
| Отключение TEST filename heuristic | `LabelResolver.label_hints_allowed()` |
| Отчет leakage | `LeakageChecker` |

## Запрещенные X columns

Текущий код использует `X_EXCLUDED_COLUMNS`/`X_FORBIDDEN_COLUMNS`. Обязательный forbidden list из задачи покрыт и расширен реализацией:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

Примечание: `model_ready_v1.json` сейчас не включает `entity_type`, `entity_id`, `window_start`, `window_end`, `window_size_seconds`, `window_step_seconds`, но `features/contracts.py` включает их в `X_EXCLUDED_COLUMNS`. Для X validation нужно использовать более строгий union.

## Проверки LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Проверки:

| Проверка | Условие отказа |
|---|---|
| `x_forbidden_columns` | forbidden X columns есть в model-ready X files и содержат non-null values |
| `test_absent_from_train` | `dataset_role='TEST'` найден в TRAIN model-ready files |
| `preprocessing_fit_only_train` | preprocessing artifact имеет `fitted_on_role != 'TRAIN'` |

Severity для failed leakage report: `CRITICAL`.

`block_model_ready_if_failed()` может пометить успешный model-ready artifact как `BLOCKED`, если leakage report завершился ошибкой.

## Безопасный паттерн model-ready

Ожидаемое разделение artifacts:

```text
parquet/model_ready/tabular/{branch}/TRAIN/schema=v1/X_train.parquet
parquet/model_ready/labels/{branch}/TRAIN/schema=v1/y_train.parquet
parquet/model_ready/tabular/{branch}/VALIDATION/schema=v1/X_validation.parquet
parquet/model_ready/labels/{branch}/VALIDATION/schema=v1/y_validation.parquet
parquet/model_ready/tabular/{branch}/TEST/schema=v1/X_test.parquet
parquet/model_ready/labels/{branch}/TEST/schema=v1/y_test.parquet
```

X files содержат только model features. y files содержат labels. Traceability/source fields остаются в catalog и optional audit artifacts, а не в X.

## Небезопасные предположения

- Не выводить `benign` из отсутствующего label.
- Не использовать filename labels для TEST.
- Не выполнять threshold tuning на TEST.
- Не смешивать role partitions в одном X artifact.
- Не хранить `source_file_path`/`event_uid`/`dataset_name` в X, потому что модели могут запомнить source identity.


---

## Источник: `docs/ru/code-documentation/data_quality_checks.md`

# Проверки качества данных

Код проверок:

- `scripts/stage_two/duckdb/service.py`;
- `scripts/stage_two/quality/checks.py`;
- `scripts/stage_two/quality/checkers.py`.

## Аналитические проверки DuckDB

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Проверки:

| Проверка | Область | Условие отказа |
|---|---|---|
| `row_counts_*` | normalized/features/model-ready views | не падает; формирует counts |
| `missing_required_columns_*` | каждое view | отсутствуют required columns |
| `split_contamination` | `model_ready_all` | TEST rows присутствуют в TRAIN model-ready artifacts |
| `schema_mismatch` | все views | mismatch required columns |

Отчет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

Регистрация в catalog:

- table: `data_quality_reports`;
- `check_group='duckdb'`;
- severity `ERROR`, если есть failed checks, иначе `INFO`.

## DataQualityChecker

Класс: `DataQualityChecker`.

Проверки:

| Группа проверок | Детали |
|---|---|
| Обязательные columns | использует DuckDB `REQUIRED_COLUMNS` |
| Null counts | считает nulls в required columns, присутствующих во view |
| Duplicate keys | `event_uid` для normalized, `sample_uid` для features/model-ready |
| Role/branch domains | валидирует значения `role`, `dataset_role`, `branch` |

Выходные отчеты:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

Опциональная регистрация в catalog выполняется через `DataQualityRepository`.

Severity:

- successful checks: `INFO`;
- failed data quality checks: `ERROR`.

## LeakageChecker

Подробности leakage описаны в [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md). Checker пишет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/leakage/leakage_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/leakage/leakage_report.json
```

Severity для failed leakage report: `CRITICAL`.

## Контракт отчета

`QualityCheckResult`:

```text
check_name
status
severity
rows_total
rows_failed
details
```

`QualityReportResult`:

```text
check_group
status
severity
report_paths
checks
```

## Критические нарушения

CRITICAL считаются:

- label/source/leakage columns с non-null values в model-ready X files;
- TEST rows в TRAIN model-ready artifacts;
- preprocessing artifact с fit на role, отличной от TRAIN.

Эти нарушения должны блокировать использование model-ready artifact для training.


---

## Источник: `docs/ru/code-documentation/dataset_contracts.md`

# Dataset-specific contracts

Этот документ суммирует группы датасетов из существующих Stage One analysis docs в `docs/ru/analysis-dataset`. Количества взяты из уже созданной документации Stage One; это не новый пересчет filesystem.

## DNS TRAIN

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 8 | `PARTIALLY_SUPPORTED` | `DnsCsvParser` | filename/class hints: benign, malware, phishing, spam; non-TEST inference разрешен, но должен фиксироваться |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints; parser отдает packet summaries |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | `DnsPcapCsvParser` | filename/class hints: audio, benign, compressed, exe, image, text, video |

Ограничения:

- Labels из filename являются inferred labels, а не embedded ground truth.
- Raw files остаются неизменными.
- Role path `TRAIN` используется только для training fit.

## DNS VALIDATION

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints: attack/benign; только validation |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `DnsTxtDomainListParser` для `VALIDATION` | partial; требуется явное class assignment |

Ограничения:

- VALIDATION может использоваться для model selection/early stopping в зависимости от дизайна эксперимента, но не для fit scalers/encoders, если политика требует TRAIN-only preprocessing fit.
- Хранить отдельно от TRAIN и TEST artifacts.

## DNS TEST

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 1 | `PARTIALLY_SUPPORTED` | `DnsCsvParser`, поддержка TEST без header | sample содержит `label_or_flag`; только evaluation |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | файлов нет |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | файлов нет |

Ограничения:

- TEST нельзя использовать для training, preprocessing fit, threshold tuning или feature selection.
- Filename heuristic отключен для TEST.

## Host TRAIN

| Формат | Файлов | Статус | Parser strategy |
|---|---:|---|---|
| `csv` | 101 | `PARTIALLY_SUPPORTED` | `HostCsvParser` |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser`; registry покрывает log formats |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | `HostSyscallTraceParser` |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `log-1`, `log-2`, `log-3` | 49 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `mainlog*`, `messages*`, `syslog*`, `mail-*` | 66 | в основном `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` для TRAIN |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | `HostXmlParser` |

Labels:

- `csv` имеет embedded normal/attack categories и binary labels.
- `cpu.log` имеет partial labels.
- многие telemetry/log/trace formats не имеют direct labels и требуют external mapping/window/scenario joins.
- отсутствие label остается `unlabeled`.

## Host VALIDATION

| Формат | Файлов | Статус | Parser strategy | Labels/timestamp |
|---|---:|---|---|---|
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet header timestamp; нужны external labels/scenario |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `HostCsvParser` | `is_executing_exploit` |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` | timestamp fields; external/scenario labels |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` | time; direct labels отсутствуют |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet timestamp; external labels |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | enhanced packet timestamp; external labels |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | Time; direct labels отсутствуют |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` в текущем seed; JSON-lines semantics отмечены в analysis docs |

## Host TEST

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | `HostBsonSandboxParser` для TEST | direct labels в sample отсутствуют; external labels, если есть |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | `HostCsvParser` | отдельные label CSV maps; только TEST evaluation |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` | TEST не используется для training; external labels |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` | external labels по умолчанию отсутствуют |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | TEST не используется для training |

Ограничения:

- TEST artifacts можно нормализовать и оценивать, но нельзя использовать для любого fit/tuning.
- Filename heuristic отключен для TEST.
- Отдельные label files должны join-иться только для evaluation и должны сохранять `label_source`.

## Ограничения групп датасетов

- Counts взяты из generated docs; их нужно обновлять после изменения filters или sorted tree.
- Некоторые статусы Stage One появились до более поздней реализации parser; для текущего runnable status использовать parser coverage.
- Большие counts для Host TEST `txt` и `bson` требуют memory-safe batching/splitting strategy.


---

## Источник: `docs/ru/code-documentation/extension_points.md`

# Точки расширения

## Добавить новый handler

Где менять:

- новый module в `scripts/handlers/<group>`;
- маршрут в `scripts/handlers/router_handler.py` или group router;
- config constants в `config.py`, если нужны пути.

Контракт:

- валидировать входные пути;
- возвращать dataclass result;
- писать JSON через `JsonDataManager`;
- не изменять raw-файлы;
- сохранять разделение TRAIN/VALIDATION/TEST.

Проверка:

```bash
python -m compileall -q manage.py config.py scripts
python manage.py handlers <service> <action>
```

Обновить документацию:

- this section;
- `cli_and_routing.md`;
- relevant Stage One docs.

## Добавить action для `dns_analyze`

Где менять:

- добавить handler file в `scripts/handlers/dns_analyze`;
- экспортировать class в `scripts/handlers/dns_analyze/__init__.py`;
- добавить function в `run_action.py`;
- добавить route в `router_dns.py`.

Минимальный контракт:

- читать `sort-path-dns-file.json`;
- валидировать role/format bucket;
- анализировать ограниченную выборку файлов;
- писать summary JSON;
- писать RU/EN docs и reports;
- возвращать dataclass со status и paths.

## Добавить action для `host_analyze`

Аналогично DNS, но файлы находятся в `scripts/handlers/host_analyze`, а маршрут добавляется в `router_host.py`.

Учитывайте смешанные схемы и большие файлы. Не загружайте файлы без ограничений целиком в память.

## Добавить class парсера

Где менять:

- `scripts/stage_two/parsers/<module>.py`;
- при необходимости shared utilities в `parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py`.

Контракт:

- наследовать `BaseParser`;
- реализовать `parse()` и желательно потоковый `parse_batches()`;
- отдавать normalized events с обязательными fields;
- вызывать `self.validate_result(result)`;
- использовать `LabelResolverProtocol`;
- не синтезировать текущее время как source timestamp;
- хранить raw/source fields в `raw_fields_json` или `metadata_json`, а не в X features.

Проверки:

```bash
python -m pytest -q tests/stage_two/test_<parser>*.py
python -m pytest -q tests/stage_two/test_parser_registry_seed.py
```

## Добавить запись parser registry

Где менять: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Шаги:

1. Добавить parser group или source format.
2. Запустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
```

3. Проверить `is_active=true` в `parser_registry`.

## Добавить version схемы

Где менять:

- `schemas/normalized`;
- `schemas/features`;
- `schemas/model_ready`;
- registry code, если требуется новое поведение layer.

Контракт:

- увеличить `schema_version`;
- явно зафиксировать стратегию backward compatibility;
- обновить регистрацию `schema_versions`;
- обновить writer/validator tests.

## Добавить label mapping rule

Где менять:

- DB table `label_mapping_rules`; or
- `PATH_DATA_STORAGE/config/label_mapping_rules.json`.

Контракт:

- определить `rule_uid`;
- по возможности ограничить правило через branch/role/source_format;
- использовать явный `label_source`;
- задать `label_status` и confidence;
- не создавать TEST filename heuristic labels.

Проверяйте unit tests для `LabelResolver`.

## Добавить quality check

Где менять: `scripts/stage_two/quality/checkers.py`.

Контракт:

- возвращать `QualityCheckResult`;
- включать severity;
- включать `rows_total`, `rows_failed` и diagnostic details;
- при необходимости регистрировать aggregate через `register_quality_report`.

Если check защищает от leakage, failed severity должен быть `CRITICAL`.

## Расширить Stage Three feature/model-ready

Где менять:

- feature logic в `scripts/stage_three/extraction`;
- preprocessing logic в `scripts/stage_three/preprocessing`;
- model-ready logic в `scripts/stage_three/model_ready`;
- quality/leakage logic в `scripts/stage_three/quality`;
- CLI route в `scripts/stage_three/cli.py`, если появляется новая команда.

Контракт:

- хранить role partitions отдельно;
- сохранять traceability fields в feature layer;
- исключать forbidden columns из X;
- писать y отдельно;
- выполнять fit preprocessing только на TRAIN;
- регистрировать artifacts в catalog;
- запускать quality/leakage/traceability checks перед использованием model-ready artifacts;
- обновлять `stage-three/` docs и `stage_three_overview.md`.

Проверки:

```bash
python -m pytest -q tests/stage_three
python manage.py stage-three run-quality-checks --experiment-id <id>
python manage.py stage-three run-leakage-checks --experiment-id <id>
python manage.py stage-three final-report --experiment-id <id>
```

## Добавить Stage Four training/evaluation layer

Stage Four пока не реализован. Новый слой должен читать только artifacts, которые прошли `stage-three final-report` со статусом `READY_FOR_STAGE_FOUR`.

Минимальный контракт:

- не читать raw files как training input;
- не использовать TEST для training, preprocessing fit, threshold tuning или feature selection;
- фиксировать seeds, metrics, model configs и artifact versions;
- сохранять evaluation reports отдельно от Stage Three final report;
- запускать SHAP/XAI только после leakage checks.


---

## Источник: `docs/ru/code-documentation/label_resolver.md`

# Разрешение labels

Файл: `scripts/stage_two/labels/resolver.py`.

Цель: формировать canonical label fields для normalized events, не трактовать missing labels как benign и не разрешать filename heuristics для TEST.

## Источники

Кандидаты labels могут поступать из:

| Источник | Значение в коде | Смысл |
|---|---|---|
| Embedded columns | `embedded_column` | прямые поля вроде `label`, `target`, `is_attack`, `attack_cat` |
| External rules/config | `external_label_file`, `ground_truth_csv`, etc. | DB/config mapping rules |
| Scenario metadata | `scenario_metadata` | contextual labels из scenario/rule metadata |
| Filename | `filename` | консервативные filename tokens только для non-TEST |
| IDS alert | `ids_alert` | слабый alert-like signal |
| None | `none` | явный unlabeled result |

Приоритет источников в коде:

```text
embedded_column < ground_truth_csv/external_label_file < scenario_metadata
< filename < ids_alert < none
```

## Встроенные labels

Распознаваемые fields:

```text
label_binary, label, labels, target, class, is_attack, is_malicious,
malicious, attack, attack_cat, attack_category, attack_subcat,
is_executing_exploit, exploit
```

Для `TEST` embedded/filename/IDS hint candidates блокируются условием `label_hints_allowed(context) == False`. Это сделано намеренно, чтобы избежать TEST leakage и загрязнения evaluation через filename heuristic.

## Правила mapping

Правила могут загружаться из:

- `PATH_DATA_STORAGE/config/label_mapping_rules.json` через `LABEL_MAPPING_RULES_CONFIG`;
- PostgreSQL `label_mapping_rules` через `LabelRepository`.

Rule matching может использовать:

- branch;
- role;
- source_format;
- dataset_name_pattern;
- file_name_pattern;
- source_field;
- source_value_pattern.

Выходные fields правила:

- `label_binary`;
- `label_family`;
- `label_subtype`;
- `label_source`;
- `label_status`;
- `label_confidence`;
- `label_mapping_rule_id`.

## Labels из имени файла

Filename labels разрешены только при условии:

```python
context.dataset_role.upper() != "TEST"
```

Распознаваемые benign tokens:

```text
0, false, benign, normal, clean, legitimate
```

Распознаваемые malicious/family tokens:

```text
1, true, attack, malicious, exploit, malware, phishing, spam,
exfil, exfiltration, tunnel, tunneling, dga, nmap, hping,
masscan, zmap
```

TEST filename heuristic отключен. Его нельзя включать для evaluation datasets.

## Отсутствующие labels

Отсутствующие labels дают:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Это жесткий инвариант: отсутствие label не означает benign.

## Weak и inferred labels

| Статус | Использование |
|---|---|
| `explicit_label` | trusted direct label |
| `inferred_label` | inference по filename/scenario/rule |
| `weak_label` | weak signals, например IDS alert |
| `partial_label` | partial coverage или window/scenario labels |
| `unlabeled` | reliable label отсутствует |
| `conflicting_label` | конфликт candidates с одинаковым priority |

Weak/inferred labels должны сопровождаться `label_source`, `label_status`, `label_confidence` и желательно `label_mapping_rule_id`.

## Конфликты

Если top-priority candidates расходятся по `label_binary` или `label_family`, resolver возвращает:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_source": "<source>",
  "label_status": "conflicting_label",
  "label_confidence": 0.0
}
```

Downstream supervised training не должен неявно преобразовывать `conflicting_label` или `unlabeled` в benign.

## Канонические label fields

Normalized schema и model-ready contracts трактуют эти поля как label/leakage fields:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
```

Они могут присутствовать в normalized или y/analysis artifacts, но не в model-ready X artifacts.


---

## Источник: `docs/ru/code-documentation/normalized_event_schema.md`

# Схема normalized event

Файл схемы: `schemas/normalized/normalized_event_v1.json`.

Код регистрации: `scripts/stage_two/normalization/schema_contracts.py`.

Таблица catalog: `schema_versions`.

## Назначение

`normalized_event/v1` задает единый event-level контракт для DNS, host, network и hybrid источников. Parsers обязаны возвращать events с обязательными normalized fields. `BaseParser.validate_result()` проверяет наличие required fields, а schema JSON фиксирует полный field list и null policy.

## Обязательные поля parser-level validation

`scripts/stage_two/parsers/base.py` требует наличие:

```text
event_uid
dataset_name
dataset_role
branch
source_format
source_file_path
parser_name
parser_version
schema_name
schema_version
timestamp_type
entity_type
event_type
modality
label_source
label_status
created_at
```

Schema JSON дополнительно описывает nullable/type/allowed values для всех canonical fields.

## Поля traceability

| Field | Назначение |
|---|---|
| `event_uid` | stable event identity, обычно hash/context/index |
| `dataset_id` | FK-like catalog id, nullable для non-catalog contexts |
| `file_id` | raw dataset file id |
| `dataset_name` | dataset name из catalog/context |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| `branch` | `dns`, `host`, `network`, `hybrid` |
| `source_format` | catalog source format |
| `source_file_path` | relative или absolute path raw/sorted source |
| `source_file_hash` | SHA-256 from catalog |
| `parser_name`, `parser_version` | parser identity |
| `parser_run_id` | parser run catalog id |
| `schema_name`, `schema_version` | normalized schema identity |

Эти поля нужны для downstream traceability и audits. Они не должны попадать в model-ready X features.

## Контракт timestamp

Поля:

- `timestamp`: nullable UTC timestamp;
- `timestamp_source`: source column/header/packet header/etc.;
- `timestamp_type`: required enum;
- `event_index`: nullable индекс порядка события.

Допустимые `timestamp_type`:

| Value | Значение |
|---|---|
| `absolute` | source содержит absolute timestamp |
| `relative` | source содержит relative timestamp/delta |
| `event_order` | absolute time отсутствует, но порядок событий значим |
| `missing` | нет времени и нет надежного order timestamp |

Правила:

- `timestamp` может быть `null`.
- Отсутствующее время нельзя заменять текущим временем.
- `created_at` фиксирует время создания normalized row, но не является временем события.
- Если timestamp отсутствует, parser должен использовать `timestamp_type='missing'` или `event_order` и сохранять `event_index`.

## Поля DNS

DNS-specific fields:

- `domain`;
- `query_domain`;
- `qtype`;
- `qclass`;
- `ttl`;
- `rcode`;
- network endpoints: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`.

DNS parsers также могут хранить source-specific values в `features_json`, `raw_fields_json`, `metadata_json`.

## Поля Host

Host-specific fields:

- `host_name`;
- `user_name`;
- `process_id`;
- `process_name`;
- `parent_process_id`;
- `parent_process_name`;
- `syscall_name`;
- `event_id`;
- `command_line`;
- `file_path`;
- metrics: `metric_name`, `metric_value`.

Host parsers могут отдавать modalities вроде `host`, `host_metric`, `sandbox`, `host_network_packet`.

## Поля network/hybrid

Network/hybrid data использует:

- endpoint fields `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- DNS fields, если packet содержит DNS;
- `modality` для различения packet/flow/DNS/host events;
- `features_json` для derived flow/packet metrics.

## Поля labels

Canonical labels:

| Поле | Смысл |
|---|---|
| `label_binary` | `0`, `1` или null |
| `label_family` | high-level label family, например benign/malware/dns_exfiltration |
| `label_subtype` | lower-level label subtype |
| `label_source` | `embedded_column`, `filename`, `scenario_metadata`, `external_label_file`, `ids_alert`, `ground_truth_csv`, `none` |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| `label_confidence` | nullable confidence |
| `label_mapping_rule_id` | rule id или source marker |

Контракт unlabeled event:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Отсутствующий label не равен benign.

## Поля JSON

| Field | Назначение |
|---|---|
| `features_json` | normalized low-level source features, полезные до feature extraction |
| `raw_fields_json` | source fields/raw row fragments для audit/debug |
| `metadata_json` | parser/source metadata, warnings, schema hints, helper flags |

`ParquetArtifactWriter` сериализует columns с окончанием `_json` в детерминированные JSON strings перед PyArrow inference.

## Политика null

Schema JSON явно фиксирует:

- missing source field -> JSON null / SQL NULL / Parquet null;
- missing labels -> unlabeled fields, not benign;
- missing timestamps -> `timestamp=null`, `timestamp_type=missing`;
- ordered streams должны передавать `event_index`;
- статистики `TEST` нельзя использовать для fit/tuning/feature selection/model training.


---

## Источник: `docs/ru/code-documentation/parquet_and_duckdb.md`

# Parquet и DuckDB артефакты

## Почему Parquet

Parquet используется для больших сгенерированных таблиц:

- normalized events;
- feature artifacts;
- model-ready artifacts.

PostgreSQL catalog хранит metadata и paths, а не табличные данные строк. Это сохраняет catalog компактным и позволяет DuckDB делать SQL-проверки поверх columnar data.

## Запись Parquet

Файл: `scripts/stage_two/parquet/writer.py`.

Класс: `ParquetArtifactWriter`.

Compression по умолчанию:

```text
zstd
```

`_write_rows()`:

1. нормализует JSON suffix columns (`*_json`) в детерминированные JSON strings;
2. строит PyArrow table;
3. записывает Parquet;
4. возвращает `ParquetWriteResult`.

`ParquetWriteResult`:

| Поле | Значение |
|---|---|
| `absolute_path` | полный filesystem path |
| `relative_path` | path относительно `PATH_DATA_STORAGE` |
| `row_count` | количество записанных строк |
| `file_size_bytes` | размер Parquet file |
| `content_hash_sha256` | optional output hash, пустой если hash не включен |

## Пути артефактов

Normalized:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Features:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Model-ready:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

## Регистрация в catalog

| Метод writer | Таблица catalog |
|---|---|
| `register_normalized_artifact()` | `normalized_artifacts` |
| `register_feature_artifact()` | `feature_artifacts` |
| `register_model_ready_artifact()` | `model_ready_artifacts` |

В catalog сохраняются relative paths:

- `normalized_artifacts.normalized_path`;
- `feature_artifacts.feature_path`;
- `model_ready_artifacts.artifact_path`.

## Сервис DuckDB

Файл: `scripts/stage_two/duckdb/service.py`.

Класс: `DuckDBAnalyticsService`.

База данных по умолчанию:

```text
PATH_DATA_STORAGE/duckdb/proposal_analytics.duckdb
```

Представления:

| Представление | Pattern |
|---|---|
| `normalized_all` | `parquet/normalized/**/*.parquet` |
| `features_all` | `parquet/features/**/*.parquet` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` |

Представления создаются через:

```sql
read_parquet('<glob>', union_by_name = true, filename = true)
```

Если файлы не найдены, service создает empty view со стабильными placeholder columns.

## Проверки DuckDB

`run_checks()` выполняет:

- проверки row count с группировкой по доступным role/branch columns или filename path;
- проверки отсутствующих обязательных columns;
- проверку split contamination;
- проверку schema mismatch.

Обязательные columns:

| View | Обязательные columns |
|---|---|
| `normalized_all` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `filename` |

Путь отчета:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

`register_report()` пишет aggregate row в `data_quality_reports`.

## SQL-шаблон

`scripts/stage_two/duckdb/sql/create_views.sql` содержит прямой SQL template с placeholder `${PATH_DATA_STORAGE}`. Python service безопаснее для runtime, потому что обрабатывает empty views и escaping путей.


---

## Источник: `docs/ru/code-documentation/parser_strategy.md`

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


---

## Источник: `docs/ru/code-documentation/postgresql_catalog.md`

# PostgreSQL Catalog

PostgreSQL catalog хранит metadata, статусы, связи, пути, хеши и отчеты. Большие normalized/features/model-ready таблицы в PostgreSQL не пишутся: они хранятся в Parquet.

## Зачем нужен catalog

- регистрировать identity датасетов и файлов;
- хранить file hashes и обнаруживать изменения;
- фиксировать статусы ingestion/parser run;
- хранить parser registry и schema versions;
- связывать normalized, feature и model-ready artifacts;
- регистрировать quality/leakage reports;
- обеспечивать traceability.

## Таблицы

### `datasets`

Назначение: dataset-level metadata для raw sources и split roles.

Основные поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `description`, `dataset_version`, `source_url`, `license_name`, `is_active`, `metadata_json`.

Связи:

- `datasets.id -> dataset_files.dataset_id`;
- `datasets.id -> normalized_artifacts.dataset_id`;
- `datasets.id -> feature_artifacts.dataset_id`.

Пишут: `CatalogIngestionService` через `DatasetRepository.get_or_create_dataset`.

Читают: normalization services, traceability, repositories.

Статусы: `is_active`; `branch` в `dns, host, network, hybrid`; `role` в `TRAIN, VALIDATION, TEST, EXPERIMENTS`.

### `ingestion_runs`

Назначение: один запуск directory scanning/catalog ingestion.

Поля: `run_uid`, `root_path`, `root_path_kind`, `branch`, `role`, `started_at`, `finished_at`, `status`, counters `files_seen/new/existing/changed/failed`, `error_message`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: `IngestionRepository`.

Читают: audit/reporting, dataset file trace.

### `dataset_files`

Назначение: catalog record для raw/sorted file.

Поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `file_modified_at`, `role`, `branch`, `status`, parser/label/timestamp/encoding hints, `metadata_json`, `error_message`.

Статусы:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Пишут:

- `CatalogIngestionService`;
- `MarkReadyService`;
- `ParserResolver.resolve_or_mark_unsupported`;
- normalization services.

Читают:

- `NormalizeFormatRunner`;
- `NormalizeAllRunner`;
- normalization services;
- traceability.

### `parser_registry`

Назначение: metadata стратегии parser.

Поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `priority`, `is_active`, `supports_streaming`, `requires_external_tools`, `external_tools_json`, `config_json`.

Пишут: `ParserRegistrySeeder`.

Читают: `ParserResolver`, parser coverage, normalization.

Ограничение: parser class должен существовать и наследовать `BaseParser`; иначе seed отключает active row.

### `schema_versions`

Назначение: metadata версионированных schema contracts.

Поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`, `description`, `columns_json`.

Пишут: `NormalizedSchemaRegistry.register_contract`, `SchemaRepository`.

Читают: `ParserResolver.resolve_schema_version`, smoke checks, artifact registration.

Layers: `normalized`, `features`, `model_ready`.

### `parser_runs`

Назначение: одна попытка parsing/normalization для raw file.

Поля: `run_uid`, `file_id`, `parser_registry_id`, `parser_name`, `parser_version`, `schema_version_id`, `started_at`, `finished_at`, `status`, `rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`, `output_parquet_path`, `error_message`, `warning_count`, `metadata_json`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: DNS/Host normalization services через `ParserRepository`.

Читают: `TraceabilityService`, artifact repositories, reports.

### `normalized_artifacts`

Назначение: registry row для normalized Parquet output.

Поля: `artifact_uid`, `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, status, timestamp и label distributions, `metadata_json`.

Статусы: `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Пишут: `ParquetArtifactWriter.register_normalized_artifact`.

Читают: feature writer, traceability, DuckDB via Parquet path.

### `feature_artifacts`

Назначение: registry row для feature Parquet output.

Поля: `artifact_uid`, `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, schema name/version, row/sample/feature/entity/window counts, label distribution, excluded columns, status, metadata.

Пишут: `FeatureArtifactWriter`.

Читают: model-ready registry, preprocessing registry, traceability.

### `preprocessing_artifacts`

Назначение: metadata для scaler/encoder/imputer/preprocessing object.

Поля: `artifact_uid`, `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, schema/object versions, columns/params JSON, status.

DB constraint: `fitted_on_role = 'TRAIN'`.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact`.

Читают: `LeakageChecker._preprocessing_fit_role_check`, model-ready artifacts.

### `model_ready_artifacts`

Назначение: final metadata для model-ready X/y/sequence/split/preprocessing.

Поля: `artifact_uid`, `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, schema name/version, sample/feature counts, label distribution, excluded columns, sequence length, status, metadata.

Data types: `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`.

Пишут: `ModelReadyRegistryService`.

Читают: `LeakageChecker`, `TraceabilityService`, DuckDB views.

### `label_mapping_rules`

Назначение: explainable rules для назначения labels.

Поля: `rule_uid`, `rule_name`, `branch`, `role`, `source_format`, `dataset_name_pattern`, `file_name_pattern`, `source_field`, `source_value_pattern`, canonical label fields, `priority`, `is_active`, `description`.

Пишут: manual seed/config или repository.

Читают: `LabelResolver` через `LabelRepository.find_matching_rules`.

### `data_quality_reports`

Назначение: registry для quality/leakage/schema reports.

Поля: `report_uid`, `artifact_type`, `artifact_id`, `check_group`, `check_name`, `status`, `severity`, row counters, missing/duplicate/schema/leakage counts, label/timestamp distributions, `details_json`, `report_path`.

Значения статуса: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Severity values: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Пишут:

- `DuckDBAnalyticsService.register_report`;
- `register_quality_report`.

Читают: audit/reporting/CI gating.

## Traceability chain

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

`TraceabilityService` требует наличие каждого link. `feature_artifacts.normalized_artifact_id` и `model_ready_artifacts.feature_artifact_id` nullable в schema, поэтому production model-ready artifact должен заполнять эти поля, иначе traceability будет неполной.

## Почему не хранить большие таблицы в PostgreSQL

- normalized/events/features/model-ready rows могут быть на сотни тысяч или миллионы строк;
- PostgreSQL catalog нужен для metadata и lineage, а не для аналитического сканирования больших columnar datasets;
- Parquet + DuckDB дают columnar storage и SQL-проверки без перегрузки catalog DB;
- backups catalog metadata остаются компактными.


---

## Источник: `docs/ru/code-documentation/README.md`

# Документация по коду проекта

Этот раздел описывает кодовую базу `Proposal`: инвентаризацию и анализ Stage One, pipeline нормализации Stage Two, Stage Three feature/model-ready preparation, каталог PostgreSQL, контракты схем, стратегию парсеров, обработку меток, Parquet/DuckDB-артефакты, проверки качества/утечек и точки расширения.

Документация нужна разработчику, который подключается к проекту без предварительного чтения всего кода. Она фиксирует не только назначение файлов, но и контракты данных, порядок запуска, статусы, ограничения и зоны риска.

Последняя repo-wide сверка: 2026-07-08. В checkout найдено 334 Python-файла, 66 тестовых Python-файлов и 106 Markdown-документов в `docs/`. Сводный анализ см. в [../repository_analysis.md](ru/repository_analysis.md).

## Карта документов

| Документ | Назначение |
|---|---|
| [cli_and_routing.md](ru/code-documentation/cli_and_routing.md) | `manage.py`, слой маршрутизации, команды Stage One/Stage Two, порядок запуска |
| [stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md) | handlers Stage One: анализ, фильтрация, сортировка, экспорт путей, анализ содержимого, JSON |
| [stage_two_overview.md](ru/code-documentation/stage_two_overview.md) | pipeline Stage Two: storage, ingestion, registry, normalization, checks |
| [stage_three_overview.md](ru/code-documentation/stage_three_overview.md) | pipeline Stage Three: feature catalog, extraction, preprocessing, model-ready build, checks, final report |
| [storage_architecture.md](ru/code-documentation/storage_architecture.md) | `PATH_DATA_STORAGE`, обязательные директории, пути артефактов |
| [postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md) | таблицы PostgreSQL catalog и цепочка трассируемости |
| [sqlalchemy_layer.md](ru/code-documentation/sqlalchemy_layer.md) | config/session/models/repositories/migrations/smoke check |
| [normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md) | `normalized_event_v1`, поля, timestamp, labels, traceability |
| [parser_strategy.md](ru/code-documentation/parser_strategy.md) | parser registry, resolver, parser classes, статусы parser runs |
| [label_resolver.md](ru/code-documentation/label_resolver.md) | источники labels, ограничения TEST, конфликтные labels |
| [parquet_and_duckdb.md](ru/code-documentation/parquet_and_duckdb.md) | Parquet writer, пути, compression, DuckDB views/checks |
| [data_quality_checks.md](ru/code-documentation/data_quality_checks.md) | DataQualityChecker, DuckDB analytics, отчеты |
| [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md) | запрещенные X-колонки, инварианты TRAIN/VALIDATION/TEST |
| [traceability.md](ru/code-documentation/traceability.md) | цепочка raw -> normalized -> features -> model-ready |
| [dataset_contracts.md](ru/code-documentation/dataset_contracts.md) | DNS/Host TRAIN/VALIDATION/TEST форматы, количества, labels, потребности parser |
| [extension_points.md](ru/code-documentation/extension_points.md) | как добавлять handlers, parsers, schemas, labels, checks, stages |
| [risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md) | известные ограничения, parser gaps, риски leakage/timestamp/large files |

## Рекомендуемый порядок чтения

1. [cli_and_routing.md](ru/code-documentation/cli_and_routing.md)
2. [stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md)
3. [stage_two_overview.md](ru/code-documentation/stage_two_overview.md)
4. [stage_three_overview.md](ru/code-documentation/stage_three_overview.md)
5. [postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md)
6. [normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md)
7. [parser_strategy.md](ru/code-documentation/parser_strategy.md)
8. [label_resolver.md](ru/code-documentation/label_resolver.md)
9. [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md)
10. [dataset_contracts.md](ru/code-documentation/dataset_contracts.md)
11. [risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md)

## Stage One

Stage One анализирует файловую структуру DNS/Host датасетов, создает JSON-инвентари, фильтрует Host-источники, сортирует файлы по ролям и форматам, экспортирует карты путей sorted tree и генерирует отчеты анализа содержимого.

Фактические компоненты находятся в `scripts/handlers`:

```text
scripts/handlers/
  analyze_dataset/
  filter_dataset/
  sort/
  save_sort/
  dns_analyze/
  host_analyze/
  json_handler/
```

Stage One не регистрирует файлы в PostgreSQL и не пишет normalized/features/model-ready артефакты. Его результаты используются как filesystem/JSON-основа для дальнейшего catalog ingestion и стратегии парсеров.

## Stage Two

Stage Two создает storage-структуру, регистрирует raw-файлы в PostgreSQL catalog, seed-ит metadata схем и парсеров, выбирает parser, нормализует события в Parquet, пишет parser reports, выполняет DuckDB checks, quality/leakage checks и обеспечивает трассируемость raw -> normalized -> features -> model-ready.

Фактические компоненты находятся в `scripts/stage_two`, `scripts/db`, `schemas`.

Сверка с текущим кодом от 2026-07-08:

- `router_stage_two()` поддерживает `bootstrap-storage`, `catalog-ingest`, `seed-parser-registry`, `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization`, `split-large-files`, `normalize-dns`, `normalize-host`, `run-duckdb-checks`, `run-leakage-checks` и `trace-artifact`.
- `config.manage_commands` является только fallback-списком для вывода в консоль и не полон для новых Stage Two команд.
- `normalize-format` и `benchmark-normalization` перед запуском применяют resource profiles и format-specific runtime policy; `normalize-all` получает общие runtime options, но не применяет per-format policy на уровне CLI route.
- `python manage.py stage-two --help` не является надежным help в текущем checkout: фактический список команд находится в `router_stage_two()`.
- Stage Three feature/model-ready preparation вынесен в `scripts/stage_three` и опубликован через `python manage.py stage-three ...`. Training/evaluation pipeline через `manage.py` относится к Stage Four и пока не опубликован.

## Stage Three

Stage Three читает catalog-backed normalized artifacts, валидирует feature catalog, извлекает features, разделяет X/y/metadata/traceability, применяет preprocessing utilities, строит model-ready artifacts, выполняет checks и пишет final report.

Фактические компоненты находятся в `scripts/stage_three`.

Подробно: [stage_three_overview.md](ru/code-documentation/stage_three_overview.md).

## Ключевые инварианты

1. Raw-файлы датасетов не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются в одном model-ready artifact.
3. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или отбора признаков.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты, но не большие normalized/features/model-ready таблицы.
5. Parquet используется для normalized events, feature artifacts и model-ready artifacts.
6. DuckDB используется для аналитических SQL-проверок поверх Parquet.
7. Labels хранятся отдельно от X-признаков.
8. Leakage/source/label поля не попадают в model-ready X artifacts.
9. Все артефакты должны сохранять traceability.
10. Если label отсутствует, файл или событие нельзя считать benign по умолчанию.
11. Filename heuristic для TEST при label inference отключен в `LabelResolver`.
12. Отсутствующие timestamps нельзя синтетически заменять текущим временем.

## Основные CLI-команды

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze analyze-train-csv-content

python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze analyze-csv-content

python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two normalize-all --branch host --limit 100
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>

python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three build-feature-catalog
python manage.py stage-three probe-runtime-backend --backend auto
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
python manage.py stage-three rebalance-dns-supervised --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001
```

Подробные аргументы и порядок запуска описаны в [cli_and_routing.md](ru/code-documentation/cli_and_routing.md).


---

## Источник: `docs/ru/code-documentation/risks_and_technical_debt.md`

# Риски, ограничения и technical debt

## Известные ограничения

| Риск | Где возникает | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Fallback Host role в TEST | `HostDatasetHandler._detect_role` | файлы без role token попадут в TEST | проверить `host-path-file.json` | требовать явные role directories, добавить strict mode |
| Жестко заданный Host filter whitelist | `HostDatasetFilterHandler` | новые datasets/formats исключаются | причины в filter log | вынести rules в config с тестами |
| Статусы Stage One могут отставать от Stage Two parsers | analysis docs vs parser registry | формат помечен `NEEDS_CUSTOM_PARSER`, хотя parser уже есть | `parser-coverage` | обновлять analysis docs после parser work |
| Stage Four отсутствует | model training/evaluation layer | нельзя обучать/оценивать модели штатной командой проекта | ревью CLI routes и `docs/stage-three` final report | добавить отдельный Stage Four CLI после `READY_FOR_STAGE_FOUR` |
| Production Host/Network/Hybrid expansion неполный | Stage Three MVP path начинается с DNS | DNS MVP может быть готов раньше полного hybrid scope | `stage-three final-report`, feature group coverage | расширять Stage Three по branch/feature_group с `--resume` и checks |

## Gaps в parser layer

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Смешанные CSV schemas | DNS/Host CSV | failures при парсинге строк, partial artifacts | parser reports, `PARTIAL_SUCCESS` | schema-specific parsing, per-file schema hints |
| Смешанные JSON schemas | Host TRAIN/TEST JSON | failed rows или слабая нормализация | parser error samples | schema-aware dispatch и JSON flatten tests |
| Неоднозначность WLS/NetFlow | registry для `wls_day` использует `HostNetflowParser` | semantic mismatch, если WLS является JSON-lines | parser coverage + sample parse | выделить WLS parser или обновить registry |
| Производительность PCAP/PCAPNG | packet parser | медленная обработка, pressure на память/диск | runtime metrics, parser reports | packet sampling, `dns-only`, chunked streaming |
| Сложность BSON | sandbox BSON | descriptor/event mismatch | parser warnings | descriptor state tests, bounded raw previews |

## Риски leakage

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Labels попали в X | feature/model-ready build | model напрямую учит target | `run-leakage-checks` | `validate_x_columns`, strict excluded list |
| Source identity в X | source paths/event ids | model запоминает dataset/file | проверка forbidden columns | хранить traceability только в catalog/audit |
| TEST используется для fit/tuning | preprocessing/model code | невалидная evaluation | preprocessing fit check, review | enforcing TRAIN-only fit и CI checks |
| Filename label inference для TEST | изменения label resolver | загрязнение evaluation | unit tests | сохранять `label_hints_allowed(TEST)=False` |

## Риски labels

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Отсутствующий label трактуется как benign | downstream feature/model code | false negatives, contaminated labels | label distribution checks | сохранять `unlabeled` и фильтровать supervised samples |
| Weak labels используются как ground truth | IDS/scenario/filename | noisy training labels | проверять `label_status` | train/evaluate by label confidence/source |
| Conflicting labels игнорируются | resolver candidates | неверный target | counts по `conflicting_label` | блокировать или вручную разруливать conflicts |

## Риски timestamp

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Missing timestamp заменен текущим временем | parser implementation | invalid temporal features | review `timestamp_type`, tests | использовать `timestamp=null`, `timestamp_type=missing/event_order` |
| Relative time трактуется как absolute | syscall/BSON/logs | неверный ordering/windows | parser tests | сохранять `timestamp_type=relative` и `event_index` |
| Смешанный timezone parsing | logs/json/csv | смещенные windows | sample validation | нормализовать в UTC только известные absolute timestamps |

## Риски больших файлов

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Загрузка файла целиком | parsers/analyzers | исчерпание памяти | profiling, OOM | streaming readers, `parse_batches`, split-large-files |
| Слишком много Parquet parts | low max rows | filesystem overhead | artifact counts | настраивать `--max-output-part-rows` |
| Parallel workers на огромных файлах | `normalize-format --workers` | RAM/disk pressure | system monitoring | использовать workers=1, пока нет chunks |

## Schema drift

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Source schema изменилась | datasets | parser failures | `PARTIAL_SUCCESS`, schema mismatch | сохранять schema hints, обновлять parser tests |
| Normalized schema развивается | schema JSON + parsers | downstream mismatch | DuckDB required column checks | версионировать schemas и поддерживать migrations |
| Feature schema mismatch | feature artifacts | model-ready invalid | quality checks | валидировать feature contract до регистрации |

## Follow-up по technical debt

1. Добавить config-driven Host filter rules.
2. Добавить Stage Four CLI для training/evaluation только поверх `READY_FOR_STAGE_FOUR` artifacts.
3. Расширить Stage Three production path на Host/Network/Hybrid feature groups.
4. Добавить отдельный WLS parser, если текущий netflow mapping семантически недостаточен.
5. Уточнить schema-version lifecycle для feature/model-ready schemas в production migrations.
6. Добавить CI command для parser registry validation, Stage Three tests, leakage contract tests и docs link checks.


---

## Источник: `docs/ru/code-documentation/sqlalchemy_layer.md`

# Слой SQLAlchemy

## Расположение

```text
scripts/db/
  config.py
  session.py
  smoke_check.py
  models/
  repositories/
  migrations/
```

## Конфигурация

Файл: `scripts/db/config.py`.

`load_database_settings()` читает:

| Env | Значение по умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | обязательное | строка подключения SQLAlchemy |
| `SQLALCHEMY_ECHO_SQL` | `false` | логирование SQL |
| `SQLALCHEMY_POOL_PRE_PING` | `true` | pre-ping подключений |

Если `DATABASE_URL` не задан, функция поднимает `ValueError`.

## Управление сессиями

Файл: `scripts/db/session.py`.

`session_scope()`:

```python
@contextmanager
def session_scope(...):
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Свойства:

- commit транзакции после успешного блока;
- rollback при exception;
- close выполняется всегда;
- `expire_on_commit=False`;
- `autoflush=False`, `autocommit=False`.

Вложенные операции по отдельным файлам в normalization используют `session.begin_nested()`, чтобы failing file не обязательно ломал весь batch.

## Модели

Модели находятся в `scripts/db/models` и экспортируются через `scripts/db/models/__init__.py`.

Ключевые модели:

- `Dataset`;
- `DatasetFile`;
- `IngestionRun`;
- `ParserRegistry`;
- `SchemaVersion`;
- `ParserRun`;
- `NormalizedArtifact`;
- `FeatureArtifact`;
- `PreprocessingArtifact`;
- `ModelReadyArtifact`;
- `LabelMappingRule`;
- `DataQualityReport`.

Общие constants: `scripts/db/models/constants.py`.

Важные constants:

```text
BRANCH_VALUES = dns, host, network, hybrid
ROLE_VALUES = TRAIN, VALIDATION, TEST, EXPERIMENTS
ACTIVE_DATASET_ROLE_VALUES = TRAIN, VALIDATION, TEST
ACTIVE_CATALOG_SOURCE_GROUP = PATH_FOLDER_DATASETS_FILTER
```

## Репозитории

Repositories инкапсулируют записи/запросы и не управляют commit самостоятельно.

| Repository | Назначение |
|---|---|
| `DatasetRepository` | получение/создание datasets |
| `IngestionRepository` | start/finish/failed для ingestion runs |
| `DatasetFileRepository` | bulk upsert файлов, выбор ready files, обновление статуса |
| `ParserRepository` | parser registry rows и жизненный цикл parser run |
| `SchemaRepository` | регистрация schema version |
| `ArtifactRepository` | регистрация normalized/feature/model-ready artifacts |
| `PreprocessingRepository` | регистрация preprocessing artifacts |
| `LabelRepository` | поиск label mapping |
| `DataQualityRepository` | регистрация quality/leakage reports |

`DatasetFileRepository.bulk_upsert_files()` использует PostgreSQL `ON CONFLICT` по `(dataset_id, file_path)`. Если hash файла изменился, статус становится `CHANGED`; иначе существующий статус сохраняется.

## Миграции Alembic

Конфигурация: `scripts/db/migrations/alembic.ini`.

Миграция:

```text
scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py
```

Применение:

```bash
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Миграция создает все таблицы catalog Stage Two:

- `data_quality_reports`;
- `datasets`;
- `ingestion_runs`;
- `label_mapping_rules`;
- `parser_registry`;
- `schema_versions`;
- `dataset_files`;
- `parser_runs`;
- `normalized_artifacts`;
- `feature_artifacts`;
- `preprocessing_artifacts`;
- `model_ready_artifacts`.

## Smoke-проверка

Файл: `scripts/db/smoke_check.py`.

`run_smoke_checks()`:

- создает dataset;
- проверяет unique/check constraints;
- создает ingestion run;
- вставляет dataset file;
- создает parser registry/schema/parser run;
- регистрирует normalized, feature, preprocessing и model-ready artifacts;
- проверяет, что `PreprocessingArtifact(fitted_on_role='TEST')` падает;
- создает quality report;
- откатывает все smoke data в конце.

Рекомендуемая команда:

```bash
python - <<'PY'
from scripts.db.smoke_check import run_smoke_checks
print(run_smoke_checks())
PY
```

Требует рабочий `DATABASE_URL` и примененные migrations.

## Эксплуатационные замечания

- Методы repository ожидают session, управляемую снаружи.
- Ни один repository не должен хранить большие row tables в PostgreSQL.
- DB constraints защищают домены branch/role/status, но сами по себе не предотвращают ML leakage; нужны model-ready contracts и leakage checks.
- Для долгих запусков normalization предпочитайте `normalize-format` с ограниченным `--batch-size` и явным `--limit`.


---

## Источник: `docs/ru/code-documentation/stage_one_handlers.md`

# Handlers Stage One

Stage One отвечает за filesystem inventory, фильтрацию, сортировку и content analysis DNS/Host датасетов. Он работает с raw/sorted файлами и JSON-картами, но не пишет PostgreSQL catalog и не создает normalized Parquet.

## Общий поток

```mermaid
flowchart LR
  A["Raw datasets PATH_FOLDER_DATASETS"] --> B["analyze_dataset"]
  B --> C["path/file JSON в PATH_TEMP_DATA"]
  C --> D["filter_dataset только Host"]
  C --> E["sort DNS"]
  D --> F["sort Host"]
  E --> G["save_sort DNS"]
  F --> H["save_sort Host"]
  G --> I["dns_analyze"]
  H --> J["host_analyze"]
  I --> K["docs + reports + summary JSON"]
  J --> K
```

## `json_handler` / `JsonDataManager`

Файл: `scripts/handlers/json_handler/json_data.py`.

`JsonDataManager` предоставляет минимальный контракт:

| Метод | Поведение |
|---|---|
| `ensure_directory()` | создает parent directory |
| `exists()` | проверяет наличие JSON file |
| `create(initial_data, overwrite=False)` | создает JSON, не перезаписывает без `overwrite=True` |
| `read(default=None)` | читает JSON object; если файла нет, возвращает default или `{}` |
| `write(data)` | полностью перезаписывает JSON; принимает только `dict` |
| `update(new_data)` | top-level merge и запись |

Пограничные случаи:

- JSON должен быть object/dict. List/scalar вызывает `ValueError`.
- Запись не атомарная: при аварийном завершении возможен частично записанный файл.
- Нет file locking; параллельные writes не защищены.

## `analyze_dataset`

Файлы:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`
- `scripts/handlers/analyze_dataset/host_dataset_handler.py`
- `scripts/handlers/analyze_dataset/router_analyze.py`

Команды:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
```

Назначение: просканировать директории `PATH_DNS_DATASETS` или `PATH_HOST_DATASETS`, распределить файлы по ролям и сохранить path/name JSON.

Важно: handler проверяет наличие файла через filesystem walk, но не читает содержимое файлов.

### Выходной контракт DNS

Файлы:

- `PATH_TEMP_DATA/dns-path-file.json`
- `PATH_TEMP_DATA/dns-file.json`

Контракт:

```json
{
  "TRAIN": ["/abs/path/file1.csv"],
  "TEST": ["/abs/path/file2.csv"],
  "VALIDATION": ["/abs/path/file3.pcap"],
  "EXPERIMENTS": []
}
```

Роли определяются по токенам пути:

| Role | Keywords |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |
| `EXPERIMENTS` | fallback для DNS, если role tokens не найдены |

### Выходной контракт Host

Файлы:

- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Контракт:

```json
{
  "TRAIN": ["/abs/path/file1.log"],
  "TEST": ["/abs/path/file2.json"],
  "VALIDATION": ["/abs/path/file3.csv"]
}
```

Host fallback role в коде: `TEST`. Это риск: если путь не содержит role token, файл попадает в `TEST`. Для новых датасетов лучше не полагаться на fallback и обеспечить явные role directories.

Ошибки:

- пустой `PATH_*_DATASETS` -> `ValueError`;
- несуществующая директория -> `FileNotFoundError`;
- path не directory -> `NotADirectoryError`.

## `filter_dataset`

Файл: `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`.

Команда:

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

Фильтрация реализована только для Host datasets. DNS filter отсутствует.

Вход:

- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Выход:

- `PATH_TEMP_DATA/filter_dataset-host-path-file.json`
- `PATH_TEMP_DATA/filter_dataset-host-file.json`
- `PATH_FILTER_LOG`

Фильтр обязателен перед Host sort, потому что `HostDatasetSortHandler` читает именно `filter_dataset-host-*.json`.

В коде зашиты whitelist rules:

| Role | Разрешенные datasets |
|---|---|
| `TRAIN` | `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset` |
| `VALIDATION` | `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets` |
| `TEST` | `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset` |

Примеры разрешенных suffix:

- ADFA: `.txt`, `.ghc`, `.csv`, `.netflow_ids`, `.xml`
- LID-DS 2021: `.sc`, `.json`
- OTRF: `.json`, `.cap`, `.pcap`, `.pcapng`
- ISOT: `.csv`
- Dynamic Malware: `.txt`, `.json`, `.bson`, `.log`

Технические риски:

- Извлечение имени датасета завязано на сегмент пути `host` и позицию `host/<role>/<dataset>`.
- Новые dataset names будут исключены без изменения кода.
- Whitelist не конфигурируется через JSON/YAML.
- Фильтр не проверяет содержимое файлов.

## `sort`

Файлы:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`
- `scripts/handlers/sort/sort_host_dataset_handler.py`

Команды:

```bash
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
```

Назначение: создать sorted tree:

```text
PATH_DNS_DATASETS_FILTER/
  TRAIN/<format>/
  TEST/<format>/
  VALIDATION/<format>/

PATH_HOST_DATASETS_FILTER/
  TRAIN/<format>/
  TEST/<format>/
  VALIDATION/<format>/
```

Материализация файла:

1. сначала `os.link` hardlink;
2. при ошибке fallback на `shutil.copy2`.

Коллизии имен решаются hash suffix по исходному пути. Если destination уже тот же file, он считается skipped existing.

Summary JSON:

- `PATH_TEMP_DATA/sort-dns-format-summary.json`
- `PATH_TEMP_DATA/sort-host-format-summary.json`

Summary fields:

```json
{
  "sorted_root_path": "...",
  "created_links_count": 0,
  "copied_files_count": 0,
  "skipped_existing_count": 0,
  "missing_source_count": 0,
  "name_mismatch_count": 0,
  "files_by_role_and_format": {
    "TRAIN": {"csv": 8}
  }
}
```

Ограничение: сортировка не регистрирует файлы в PostgreSQL. Catalog ingestion делает Stage Two.

## `save_sort`

Файлы:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`
- `scripts/handlers/save_sort/save_sort_host_path_handler.py`

Команды:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
```

Назначение: обойти sorted tree и сохранить пути по `role/format`.

Выход:

- `PATH_TEMP_DATA/sort-path-dns-file.json`
- `PATH_TEMP_DATA/sort-path-dns-file-summary.json`
- `PATH_TEMP_DATA/sort-path-host-file.json`
- `PATH_TEMP_DATA/sort-path-host-file-summary.json`

Контракт:

```json
{
  "TRAIN": {
    "csv": ["/abs/sorted/TRAIN/csv/file.csv"],
    "pcap.csv": ["/abs/sorted/TRAIN/pcap.csv/file.pcap.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Эти JSON нужны для `dns_analyze` и `host_analyze`: content analyzers читают role/format bucket из `sort-path-*-file.json`.

## `dns_analyze`

Файлы:

- `scripts/handlers/dns_analyze/router_dns.py`
- `scripts/handlers/dns_analyze/run_action.py`
- `scripts/handlers/dns_analyze/analyze_dns_*_dataset_handler.py`

Actions:

| Action | Bucket |
|---|---|
| `analyze-train-csv-content` | DNS `TRAIN/csv` |
| `analyze-train-pcap-content` | DNS `TRAIN/pcap` |
| `analyze-train-pcap-csv-content` | DNS `TRAIN/pcap.csv` |
| `analyze-test-csv-content` | DNS `TEST/csv` |
| `analyze-test-pcap-content` | DNS `TEST/pcap` |
| `analyze-test-pcap-csv-content` | DNS `TEST/pcap.csv` |
| `analyze-validation-pcap-content` | DNS `VALIDATION/pcap` |
| `analyze-validation-txt-content` | DNS `VALIDATION/txt` |

Выход:

- analysis summary JSON в `PATH_TEMP_DATA`;
- RU/EN docs в `docs/{ru,en}/analysis-dataset/dns/<role>`;
- RU/EN reports в `PATH_REPORT/{ru,en}/stage-one/analysis-dataset/dns/<role>`.

## `host_analyze`

Файлы:

- `scripts/handlers/host_analyze/router_host.py`
- `scripts/handlers/host_analyze/run_action.py`
- `scripts/handlers/host_analyze/analyze_host_*_dataset_handler.py`

Actions покрывают train/validation/test buckets: `csv`, `json`, `json-1`, `log`, rotated logs, `cap`, `pcap`, `pcapng`, `bson`, `netflow_day`, `wls_day`, `txt`, `sc`, `ghc`, `xml`, Metricbeat-like logs.

Выход аналогичен DNS, но находится в `host/<role>`.

## Статусы анализа

Stage One docs используют статусы:

| Статус | Значение |
|---|---|
| `READY_FOR_FEATURE_EXTRACTION` | формат можно подключать к feature extraction после стандартной нормализации |
| `NEEDS_CUSTOM_PARSER` | нужен специализированный parser или schema-aware обработчик |
| `PARTIALLY_SUPPORTED` | часть структуры читается, но есть mixed schema/partial labels/нестабильность |
| `BROKEN_OR_EMPTY` | bucket пустой или непригоден для дальнейшего анализа |

Эти статусы не являются PostgreSQL enum для Stage Two. Они используются как input к parser strategy и ручной приоритизации.


---

## Источник: `docs/ru/code-documentation/stage_three_overview.md`

# Stage Three overview

Stage Three превращает normalized Parquet artifacts из Stage Two в feature artifacts и model-ready artifacts для Stage Four.

Граница ответственности:

```text
Stage Two:   raw -> normalized
Stage Three: normalized -> features -> model-ready
Stage Four:  model-ready -> training/evaluation/explainability
```

Stage Three не обучает RF/XGBoost/CNN/LSTM, не подбирает thresholds и не строит SHAP explanations.

## CLI

Точка входа: `python manage.py stage-three ...`.

Фактический router: `scripts/stage_three/cli.py`.

Поддержанные команды:

| Команда | Назначение |
| --- | --- |
| `validate-inputs` | Проверяет Stage Two normalized artifacts перед downstream Stage Three. |
| `build-feature-catalog` | Валидирует `feature_catalog.yml` и пишет normalized JSON snapshot. |
| `probe-runtime-backend` | Резолвит CPU/GPU backend и memory guard profile. |
| `extract-features` | Читает normalized Parquet и пишет feature artifacts. |
| `align-labels` | Фиксирует label policy без помещения labels в X. |
| `build-sequences` | Создает sequence/window artifacts для Stage Four DL branches. |
| `build-model-ready` | Собирает X/y/metadata/traceability, split index и preprocessing metadata. |
| `rebalance-dns-supervised` | Строит воспроизводимый DNS supervised 70/30 model-ready split для baseline experiment. |
| `run-quality-checks` | Проверяет feature/model-ready/preprocessing artifacts. |
| `run-leakage-checks` | Проверяет forbidden X columns, TEST leakage, fit role и traceability. |
| `trace-artifact` | Восстанавливает lineage model-ready artifact до raw source. |
| `final-report` | Пишет Task20 final report и Stage Four readiness status. |

## Модули

| Пакет | Назначение |
| --- | --- |
| `scripts/stage_three/requests.py` | Typed request dataclasses для CLI. |
| `scripts/stage_three/storage/` | Bootstrap Stage Three storage directories. |
| `scripts/stage_three/readiness/` | Stage Three input readiness gate. |
| `scripts/stage_three/feature_catalog/` | YAML/JSON feature catalog loader, validator, reports. |
| `scripts/stage_three/runtime/` | Resource profile, memory guard, CPU/GPU backend selection. |
| `scripts/stage_three/extraction/` | DNS/Host/Network extractors, artifact writer, registry integration. |
| `scripts/stage_three/labels/` | Label policies for windows/sequences. |
| `scripts/stage_three/preprocessing/` | Type casting, missing values, categorical encoding, scaling profiles, class balance. |
| `scripts/stage_three/model_ready/` | X/y separation, split index, sequence builder, model-ready registry/builder. |
| `scripts/stage_three/quality/` | Feature quality, preprocessing quality, model-ready quality, leakage, traceability. |
| `scripts/stage_three/reports/` | Report path utilities, console output helpers and final Task20 report generation. |

## Artifact lifecycle

1. `validate-inputs` confirms Stage Two artifacts are usable.
2. `build-feature-catalog` validates allowed feature groups and forbidden X columns.
3. `extract-features` creates Parquet feature artifacts and registers `feature_artifacts`.
4. `align-labels` and model-ready separation keep labels outside X.
5. `build-model-ready` writes `X`, `y`, `metadata`, `traceability`, `split_index`, `preprocessing_metadata`.
6. `rebalance-dns-supervised` может создать отдельный DNS supervised baseline experiment без физического удаления raw-файлов.
7. `run-quality-checks` registers `data_quality_reports`.
8. `run-leakage-checks` blocks unsafe artifacts with `BLOCKED_BY_LEAKAGE` or `BLOCKED_BY_QUALITY`.
9. `final-report` summarizes readiness for Stage Four.

## Readiness policy

Stage Four may start only when:

- required model-ready artifacts exist for TRAIN/VALIDATION/TEST;
- quality checks have no blocking failures;
- leakage checks pass;
- traceability chain is recoverable;
- `stage-three final-report` returns `READY_FOR_STAGE_FOUR`.

If PostgreSQL Catalog is unavailable, `final-report` still writes RU/EN reports but marks readiness as `NOT_READY_FOR_STAGE_FOUR`.

## Related docs

- [../stage-three/README.md](ru/stage-three/README.md)
- [../stage-three/usage_guide.md](ru/stage-three/usage_guide.md)
- [../stage-three/stage_three_commands.md](ru/stage-three/stage_three_commands.md)
- [traceability.md](ru/code-documentation/traceability.md)
- [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md)


---

## Источник: `docs/ru/code-documentation/stage_two_overview.md`

# Обзор Stage Two

Stage Two переводит sorted filesystem datasets в catalog-backed normalized artifacts. Цель: сохранить raw files неизменными, зарегистрировать metadata, выбрать parser, записать normalized events в Parquet и подготовить основу для feature/model-ready layers без leakage.

## Основные директории кода

```text
scripts/stage_two/
  cli.py
  storage/bootstrap.py
  ingestion/
  parser_registry/
  parsers/
  labels/
  normalization/
  parquet/
  features/
  model_ready/
  duckdb/
  quality/
  traceability/
  splitting/
  reports/
  readiness_check.py
  e2e_dry_run.py

scripts/db/
  config.py
  session.py
  models/
  repositories/
  migrations/

schemas/
  normalized/normalized_event_v1.json
  features/feature_artifact_v1.json
  model_ready/model_ready_v1.json
```

## Поток данных

```mermaid
flowchart TD
  A["PATH_FOLDER_DATASETS_FILTER"] --> B["catalog-ingest"]
  B --> C["PostgreSQL: datasets, ingestion_runs, dataset_files"]
  D["schemas + parser_registry_seed.json"] --> E["seed-parser-registry"]
  E --> F["schema_versions + parser_registry"]
  C --> G["mark-ready"]
  F --> H["ParserResolver"]
  G --> I["normalize-format / normalize-all / normalize-dns / normalize-host"]
  H --> I
  I --> J["parser_runs"]
  I --> K["Parquet normalized"]
  K --> L["normalized_artifacts"]
  K --> M["DuckDB views/checks"]
  N["feature/model-ready writers"] --> O["feature_artifacts, preprocessing_artifacts, model_ready_artifacts"]
  O --> P["LeakageChecker"]
  O --> Q["TraceabilityService"]
```

## Инициализация storage

Файл: `scripts/stage_two/storage/bootstrap.py`.

Команда:

```bash
python manage.py stage-two bootstrap-storage
```

Создает обязательную структуру в `PATH_DATA_STORAGE`, не удаляя существующие файлы. Bootstrap идемпотентный: существующие directories попадают в `existing`, новые в `created`.

## Ingestion catalog

Файлы:

- `scripts/stage_two/ingestion/catalog_ingestion_service.py`
- `scripts/stage_two/ingestion/scanner.py`
- `scripts/stage_two/ingestion/file_hash_service.py`

Команда:

```bash
python manage.py stage-two catalog-ingest
```

Вход: `PATH_FOLDER_DATASETS_FILTER`.

Записывает:

- `ingestion_runs`;
- `datasets`;
- `dataset_files`.

Scanner определяет:

| Metadata | Источник |
|---|---|
| `branch` | части path: `dns`, `host`, `network`, `hybrid`; fallback `hybrid` |
| `role` | части path: `TRAIN`, `VALIDATION`, `TEST`; файлы без active role игнорируются |
| `source_format` | sorted bucket после role или filename suffix/compound suffix |
| `dataset_name` | path segment между branch и role, fallback `<branch>_<role>_<source_format>` |
| `dataset_slug` | lowercase slug |

Catalog ingestion рассчитывает SHA-256 потоковым чтением и делает upsert файлов по `(dataset_id, file_path)`.

Назначение статусов:

- `REGISTERED` по умолчанию;
- `EMPTY_FILE` для файлов нулевого размера;
- `UNSUPPORTED_FORMAT`, если inferred format находится вне known formats.

## Seed parser registry

Файлы:

- `scripts/stage_two/parser_registry/parser_registry_seed.json`
- `scripts/stage_two/parser_registry/seed.py`
- `scripts/stage_two/parser_registry/resolver.py`
- `scripts/stage_two/normalization/schema_contracts.py`

Команда:

```bash
python manage.py stage-two seed-parser-registry
```

Действия:

1. Загружает `schemas/normalized/normalized_event_v1.json`.
2. Делает upsert row в `schema_versions` для `normalized_event/v1`.
3. Разворачивает compact parser seed groups в rows `parser_registry`.
4. Валидирует `parser_module.parser_class`.
5. Если active parser class отсутствует или не является `BaseParser`, row сохраняется с `is_active=false` и диагностикой в `config_json`.

## Разрешение parser

`ParserResolver` выбирает active parser по правилу:

```text
branch + source_format + (supported_role == role OR supported_role IS NULL)
ORDER BY priority ASC, id ASC
```

Если parser не найден, `resolve_or_mark_unsupported()` помечает `dataset_files.status='UNSUPPORTED_FORMAT'`.

## Сервисы normalization

Файлы:

- `scripts/stage_two/normalization/dns_service.py`
- `scripts/stage_two/normalization/host_service.py`
- `scripts/stage_two/normalization/runner.py`
- `scripts/stage_two/normalization/options.py`

Команды:

```bash
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two normalize-all --branch host --limit 100
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

`normalize-format` и `normalize-all` являются более контролируемыми routes: они не смешивают роли и форматы. Legacy `normalize-dns/host` выбирают ready files по branch.

Поток normalization:

1. Выбрать `dataset_files.status='READY_FOR_PARSING'`.
2. Разрешить parser metadata и schema version.
3. Создать или возобновить `parser_runs`.
4. Создать parser с `LabelResolver`.
5. Собрать `ParserContext`.
6. Потоково читать parse batches.
7. Записать normalized Parquet parts через `ParquetArtifactWriter`.
8. Зарегистрировать `normalized_artifacts`.
9. Завершить `parser_runs`.
10. Обновить `dataset_files.status`.
11. Сохранить parser run reports.

Маппинг статусов parser/file:

| Результат parser | `parser_runs.status` | `dataset_files.status` |
|---|---|---|
| все строки распарсены | `SUCCESS` | `PARSED` |
| часть строк распарсена, часть завершилась ошибкой | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| ошибка чтения или нет распарсенных строк | `FAILED` | `FAILED` |
| пустой файл | `SKIPPED` | `EMPTY_FILE` |
| unsupported format | `SKIPPED` | `UNSUPPORTED_FORMAT` |
| намеренно пропущенный helper file | `SKIPPED` | `SKIPPED` |

## Разрешение labels

Файл: `scripts/stage_two/labels/resolver.py`.

Resolver возвращает canonical label fields для каждого normalized event. Отсутствующие labels преобразуются в:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Filename и embedded label hints отключены для `TEST` через `label_hints_allowed()`.

## Запись Parquet

Файл: `scripts/stage_two/parquet/writer.py`.

Записывает:

- normalized events;
- feature rows;
- model-ready tables.

Compression по умолчанию: `zstd`.

PostgreSQL хранит только artifact metadata и paths. Большие данные остаются в Parquet.

## Сервисы feature и model-ready

Файлы:

- `scripts/stage_two/features/contracts.py`
- `scripts/stage_two/features/writer.py`
- `scripts/stage_two/model_ready/contracts.py`
- `scripts/stage_two/model_ready/registry.py`

Текущее состояние:

- feature writer может писать prepared rows и регистрировать `feature_artifacts`;
- model-ready registry может писать/регистрировать X/y/sequence/split/preprocessing artifacts;
- orchestration feature extraction пока не оформлена как полный CLI pipeline;
- contracts enforce X excluded/forbidden columns и TRAIN-only preprocessing fit.

## DuckDB и проверки

Файлы:

- `scripts/stage_two/duckdb/service.py`
- `scripts/stage_two/duckdb/sql/create_views.sql`
- `scripts/stage_two/quality/checkers.py`

Команды:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

DuckDB views:

- `normalized_all`;
- `features_all`;
- `model_ready_all`.

Проверки покрывают row counts, required columns, split contamination, schema mismatch, nulls, duplicates, role/branch domains, forbidden X columns, отсутствие TEST в TRAIN artifacts и preprocessing fit role.

## Traceability

Файл: `scripts/stage_two/traceability/service.py`.

Команда:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Traceability разрешает цепочку:

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

Если любая связь отсутствует, `TraceabilityError` объясняет недостающий link.

## Readiness и dry run

В репозитории есть `scripts/stage_two/readiness_check.py` и `scripts/stage_two/e2e_dry_run.py`. Они относятся к слоям operational validation. Основные production contracts при этом задаются CLI, ORM, schemas, parser registry и tests в `tests/stage_two`.

## Ограничения текущей реализации

- Orchestration feature extraction не полностью оформлена как end-to-end CLI stage.
- Model-ready creation есть как registry/writer service, но нет полноценной команды сборки X/y для всех branches.
- `normalize-dns/host` legacy routes менее управляемы, чем `normalize-format`.
- Некоторые Stage One docs могут иметь статус `NEEDS_CUSTOM_PARSER`, даже если Stage Two уже содержит parser class для части формата; решающим является active parser registry + parser coverage.
## Performance execution architecture

Stage Two normalization теперь имеет performance-oriented execution layer без изменения normalized event contract.

Основные файлы:

- `scripts/stage_two/execution/work_unit.py`;
- `scripts/stage_two/execution/planner.py`;
- `scripts/stage_two/execution/executor.py`;
- `scripts/stage_two/execution/runtime_settings.py`;
- `scripts/stage_two/execution/retry_policy.py`;
- `scripts/stage_two/execution/progress.py`;
- `scripts/stage_two/execution/format_policy.py`;
- `scripts/stage_two/benchmark.py`;
- `scripts/stage_two/quality/post_run_validation.py`.

Ключевое поведение:

- `WorkUnitPlanner` строит работу только для `dataset_files.status=READY_FOR_PARSING` и одного точного `branch/role/source_format`.
- `WorkUnitExecutor` использует `ProcessPoolExecutor` для CPU parsing и bounded future submission.
- Workers не делят одну SQLAlchemy session; каждый process открывает собственный DB/session context только там, где нужно.
- Resume пропускает successful normalized artifacts с подходящими parser/schema versions.
- Parser failures изолируются на уровне file/chunk и могут давать `PARTIAL_SUCCESS` для команды.
- Parsers используют `parse_batches` для streaming/batch parsing там, где возможно.
- Большие line-based files можно делить на registered chunks с parent trace metadata.
- Binary formats (`cap`, `pcap`, `pcapng`, `bson`) не делятся обычным line splitter.
- `ParquetArtifactWriter` пишет через atomic temp-file и валидирует output до artifact registration.
- `benchmark-normalization` измеряет throughput и оценивает достижимость `17 GB <= 3 hours`.
- `normalize-format` создает post-run validation report по counts, reconciliation, split separation, leakage и traceability.

Resource profiles:

| Profile | workers | batch_size | max_output_part_rows |
| --- | ---: | ---: | ---: |
| `safe` | 4 | 50000 | 100000 |
| `balanced` | 8 | 100000 | 250000 |
| `fast` | 12 | 200000 | 500000 |
| `aggressive` | 14 | 300000 | 750000 |

Format policy ограничивает рискованные форматы:

- PCAP/PCAPNG/CAP: low workers и `packet-summary` by default.
- BSON: low workers и moderate batches.
- JSON/JSONL: moderate workers.
- line-based logs/TXT/syscall traces: fast settings после benchmark validation.

Operational target:

- required throughput для 17 GB за 3 часа: около `5.67 GB/hour`;
- target на i7-14700KF / 64 GB RAM / M.2 SSD: `10-20+ GB/hour` для line-based formats;
- GPU остается extension point для feature/model-ready/training, а не default raw parser engine.

Safety invariants не меняются: raw files immutable, splits separate, `TEST` не используется для training/fit/tuning, labels не являются X features, missing labels/timestamps сохраняют explicit null/missing semantics, traceability остается полной.


---

## Источник: `docs/ru/code-documentation/storage_architecture.md`

# Архитектура storage

## Корень storage

`PATH_DATA_STORAGE` задается в `.env` и читается в `config.py`. Все generated artifacts, reports, temporary files, база DuckDB, backups и runtime config Stage Two должны находиться внутри этого корня.

Команда bootstrap:

```bash
python manage.py stage-two bootstrap-storage
```

## Обязательная структура

`StorageBootstrapper.required_relative_paths()` создает:

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
      dns/TRAIN/
      dns/VALIDATION/
      dns/TEST/
      host/TRAIN/
      host/VALIDATION/
      host/TEST/
      network/TRAIN/
      network/VALIDATION/
      network/TEST/
      hybrid/TRAIN/
      hybrid/VALIDATION/
      hybrid/TEST/
    features/
      dns_features/
      host_syscall_features/
      host_eventlog_features/
      host_metrics_features/
      network_flow_features/
      hybrid_features/
      sequence_features/
    model_ready/
      tabular/
      labels/
      sequences/
      preprocessing/
      split_index/
  duckdb/
    sql/
    exports/
  logs/stage-two/
  backups/
    postgres_catalog/
    metadata_exports/
  temp_data/
    ingestion/
    parser_runs/
    normalization/
    duckdb/
  schemas/
    normalized/
    features/
    model_ready/
  reports/
    ru/stage-two/
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
    en/stage-two/
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
  config/
```

Фактический bootstrap также создает report group directories в `reports/ru/<group>` и `reports/en/<group>` для совместимости с текущими constants.

## Пути storage для Stage One

Stage One использует:

| Config | Назначение |
|---|---|
| `PATH_FOLDER_DATASETS` | корень raw datasets |
| `PATH_DNS_DATASETS` | `PATH_FOLDER_DATASETS/dns` |
| `PATH_HOST_DATASETS` | `PATH_FOLDER_DATASETS/host` |
| `PATH_FOLDER_DATASETS_FILTER` | корень sorted/filtered datasets для Stage Two ingestion |
| `PATH_DNS_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/dns` |
| `PATH_HOST_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/host` |
| `PATH_TEMP_DATA` | JSON inventories и Stage One summaries |
| `PATH_REPORT` | корень reports Stage One и Stage Two |

Raw files в `PATH_FOLDER_DATASETS` не изменяются. `sort` создает hardlinks/copies в `PATH_FOLDER_DATASETS_FILTER`.

## Пути Parquet

Normalized:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Features:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Model-ready:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

`ParquetArtifactWriter` возвращает абсолютный и относительный path. Относительный path сохраняется в PostgreSQL artifact tables.

## Пути DuckDB

| Путь | Назначение |
|---|---|
| `duckdb/proposal_analytics.duckdb` | DuckDB database по умолчанию |
| `duckdb/sql/create_views.sql` | SQL template для views |
| `duckdb/exports/` | exports |

`DuckDBAnalyticsService` может создавать views напрямую из Parquet glob patterns. Он не копирует Parquet data в PostgreSQL.

## Отчеты

| Тип отчета | Путь |
|---|---|
| DuckDB analytics | `reports/en/stage-two/quality/duckdb_analytics_report.json` |
| Quality report | `reports/{en,ru}/stage-two/quality/quality_report.json` |
| Leakage report | `reports/{en,ru}/stage-two/leakage/leakage_report.json` |
| Parser reports | генерируются `scripts/stage_two/reports` внутри storage reports |

## Config и schemas

Исходные schemas проекта находятся в repository `schemas/`. Bootstrap также создает directories `PATH_DATA_STORAGE/schemas/...` для runtime copies/exports, если они нужны.

Текущий загрузчик схем читает:

- `schemas/normalized/normalized_event_v1.json`;
- `schemas/features/feature_artifact_v1.json`;
- `schemas/model_ready/model_ready_v1.json`.

## Эксплуатационные ограничения

- `PATH_DATA_STORAGE` должен быть непустым для bootstrap, Parquet writer и DuckDB service.
- Generated artifacts должны использовать relative paths в catalog для portability.
- Raw datasets должны оставаться вне generated Parquet/report directories.
- Backups должны включать PostgreSQL catalog metadata и schema/config snapshots, а не копии raw data, если это явно не запланировано.


---

## Источник: `docs/ru/code-documentation/traceability.md`

# Трассируемость

Traceability связывает model-ready artifact с feature artifact, normalized Parquet, parser run, raw file и dataset.

## Сервис

Файл: `scripts/stage_two/traceability/service.py`.

Команда:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Режимы поиска:

- числовой argument -> `model_ready_artifacts.id`;
- нечисловой argument -> `model_ready_artifacts.artifact_path`.

## Цепочка

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

## Возвращаемая metadata

`TraceabilityChain` возвращает dictionaries для:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Ключевые fields включают artifact paths, role, branch, data type/modality, statuses, parser counters, raw file path/hash и dataset identity.

## Обязательные связи

Сервис поднимает `TraceabilityError`, если:

- model-ready artifact не найден;
- `feature_artifact_id` равен null;
- связанный feature artifact не найден;
- `normalized_artifact_id` равен null;
- связанный normalized artifact не найден;
- связанный parser run не найден;
- связанный dataset file не найден;
- связанный dataset не найден.

## Следствия контракта

Хотя некоторые FK columns nullable для поддержки staged/incomplete artifacts, production artifacts для экспериментов должны заполнять traceability links. Иначе:

- воспроизводимость нарушена;
- leakage audits не могут атрибутировать samples;
- academic implementation description не может доказать lineage;
- model-ready artifacts должны считаться incomplete.

## Traceability в row schemas

Normalized rows включают event/file/parser fields. Feature rows должны сохранять:

```text
sample_uid
dataset_id
normalized_artifact_id
role
branch
feature_group
feature_schema_name
feature_schema_version
source_event_uid_refs
source_normalized_path
created_at
```

Эти traceability fields обязательны в feature artifacts, но исключаются из model-ready X artifacts. Они остаются в catalog и audit layers.


---

## Источник: `docs/ru/dataset_strategy_dns_host.md`

# Стратегия DNS и Host датасетов

Документ объединяет `dns_dataset_strategy.md`, `host_datasets_analysis.md`, dataset role sections из `functional_project_cheatsheet.md` и карту датасетов из `dataset_feature_extraction_map.md`. DNS и Host логика разделены явно; `TRAIN`, `VALIDATION` и `TEST` не смешиваются.

## Назначение

Стратегия датасетов нужна для трех задач:

1. Обосновать proposal-level выбор источников данных.
2. Зафиксировать role matrix для обучения, валидации и финального тестирования.
3. Подготовить Stage Two parser pipeline и feature extraction к разным типам телеметрии.

## Общие правила

- `TRAIN` используется для обучения и fit preprocessing.
- `VALIDATION` используется для настройки, контроля false positives и проверки устойчивости.
- `TEST` используется только для финальной evaluation/inference.
- DNS и Host не объединяются на raw-level.
- Hybrid integration выполняется на уровне normalized events, windows, feature artifacts и traceability.
- Экспериментальные датасеты не повышаются до `TRAIN` без отдельного решения.

## DNS strategy

Текущий DNS scope включает три активных источника. DNS `EXPERIMENTS` в исходной стратегии не используются.

| Роль | Датасет | Назначение | Источник |
| --- | --- | --- | --- |
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | Обучение attack-class behavior: DNS exfiltration / tunneling. | <https://www.unb.ca/cic/datasets/dns-exf-2021.html> |
| `TRAIN` | CIC-Bell-DNS-2021 | Benign baseline и обучение нормальному DNS-поведению. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `VALIDATION` | Split CIC-Bell-DNS-2021 | Контроль false positives и настройка threshold. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `TEST` | Mendeley DNS Exfiltration Dataset | Независимая проверка generalization и междатасетного переноса. | <https://data.mendeley.com/datasets/c4n7fckkz3/3> |

```text
DNS TRAIN:
  - CIC-Bell-DNS-EXF-2021
  - CIC-Bell-DNS-2021

DNS VALIDATION:
  - split CIC-Bell-DNS-2021

DNS TEST:
  - Mendeley DNS Exfiltration Dataset
```

### DNS supervised split policy 70/30

Для supervised DNS baseline активная policy: `dns_supervised_70_30_v1`.
Она строится не из исходного битого `TEST/csv`, а из валидных labeled DNS rows
с traceability через `dns_lexical` feature artifacts.

Итоговый split:

| Роль | normal | attack | total |
| --- | ---: | ---: | ---: |
| `TRAIN` | 6,010,841 | 2,576,074 | 8,586,915 |
| `VALIDATION` | 1,288,037 | 552,016 | 1,840,053 |
| `TEST` | 1,288,037 | 552,016 | 1,840,053 |

Правила исключения:

- `dns/TEST/csv/dataset.csv` и все его chunked downstream artifacts не используются для final test;
- `dns/VALIDATION/pcap/ens33-dns_amplification_attack.pcap` исключен полностью;
- `dns/VALIDATION/pcap/ens33-dns_amplification_attack__f291ed87a1.pcap` используется только как ограниченный attack source;
- существующие `TRAIN` attack rows (`409,076`) сохраняются в учете target distribution;
- `label_binary=NULL` не трактуется как normal и не попадает в supervised split;
- raw-файлы физически не удаляются, catalog/downstream artifacts помечаются `SKIPPED` с traceability.

Команда воспроизведения:

```powershell
python manage.py stage-three rebalance-dns-supervised --experiment-id dns_rebalanced_70_30_v1

python manage.py stage-three rebalance-dns-supervised `
  --experiment-id dns_rebalanced_70_30_v1 `
  --apply `
  --apply-catalog `
  --deactivate-existing-experiment exp001
```

Новый model-ready path:

```text
parquet/model_ready/dns_rebalanced_70_30_v1/dns/tree_unscaled/{TRAIN,VALIDATION,TEST}/
```

Вердикт готовности:

- DNS model-ready данные готовы для обучения supervised tabular моделей.
- Использовать только experiment `dns_rebalanced_70_30_v1`.
- `TRAIN` можно использовать для обучения и fit preprocessing.
- `VALIDATION` можно использовать для tuning/threshold selection.
- `TEST` использовать только для финальной evaluation.
- `run-quality-checks` для `dns_rebalanced_70_30_v1` возвращает `PASS` без `blocking_issues` и без предупреждений по timestamp.
- `run-leakage-checks` для `dns_rebalanced_70_30_v1` возвращает `PASS`.

Полные пути к model-ready данным:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\metadata.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\traceability.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\metadata.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\traceability.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\metadata.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\traceability.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\split_index.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\preprocessing_metadata.parquet
```

Полные пути к отчетам:

```text
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
```

### DNS feature purpose

| Датасет | Attack lifecycle | Основные feature groups |
| --- | --- | --- |
| CIC-Bell-DNS-EXF-2021 | Exfiltration | DNS lexical, entropy, temporal, RR/TTL, stateful/stateless DNS features. |
| CIC-Bell-DNS-2021 | Benign baseline / exfiltration contrast | Те же DNS признаки; используется для normal DNS baseline и FP-control. |
| Mendeley DNS Exfiltration Dataset | Exfiltration / generalization | DNS lexical, temporal, numeric feature table, source IP windows. |

## Host strategy

Host-side часть не должна опираться на один датасет, потому что разные источники покрывают разные уровни поведения:

- system calls;
- enterprise logs;
- authentication events;
- Windows/Sysmon telemetry;
- malware traces;
- cloud telemetry;
- host + network events.

### Host role matrix

| Роль | Датасет | Назначение | Source |
| --- | --- | --- | --- |
| `TRAIN` | ADFA IDS | Baseline HIDS training, normal/attack host traces, syscall sequences. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| `TRAIN` | LID-DS 2021 | Core sequence modelling dataset для Linux syscall behaviour. | <https://github.com/LID-DS/LID-DS> |
| `TRAIN` | Maintainable Log Dataset | Enterprise log behaviour и multi-stage attack modelling. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| `VALIDATION` | LID-DS 2019 | Cross-version validation на CVE-based attack scenarios. | <https://github.com/LID-DS/LID-DS> |
| `VALIDATION` | LANL Dataset | User-host behaviour, authentication behaviour, lateral movement patterns. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `VALIDATION` | Windows Event Log / OTRF Security Datasets | SOC-style validation на Windows/Sysmon telemetry. | <https://github.com/OTRF/Security-Datasets> |
| `TEST` | Unified Host + Network Dataset / LANL | Hybrid host+network validation, multi-source telemetry, feature-level fusion. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `TEST` | ISOT Cloud IDS Dataset | Cloud environment validation, workloads, logs/syscalls/performance metrics. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| `TEST` | Dynamic Malware Analysis Dataset | Malware-driven host behaviour и exfiltration-related activity. | <https://zenodo.org/record/1203289> |

### Host dataset details

| Датасет | Роль | Что содержит | Почему нужен | Подходящие модели | Source |
| --- | --- | --- | --- | --- | --- |
| ADFA IDS | `TRAIN` | Linux/Windows system calls, normal traces, attack traces. | Стандартный HIDS baseline и сравнимость с research. | RF, XGBoost, LSTM, CNN. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| LID-DS 2021 | `TRAIN` | System calls, attack scenarios, normal behaviour, labelled traces. | Основной источник для LSTM/sequence branch. | LSTM, GRU, CNN-LSTM, Transformers. | <https://github.com/LID-DS/LID-DS> |
| Maintainable Log Dataset | `TRAIN` | Enterprise logs, 20 log types, multi-stage attacks via state machines. | Проверяет log-level multi-stage behaviour, а не только syscalls. | RF, XGBoost, LSTM/GRU, Autoencoder. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| LID-DS 2019 | `VALIDATION` | CVE-based scenarios, syscall parameters, labelled attacks, benign traces. | Проверяет переносимость LID-DS 2021 -> 2019. | Same syscall/sequence models. | <https://github.com/LID-DS/LID-DS> |
| LANL Dataset | `VALIDATION` | Authentication logs, user-computer events, multi-day enterprise activity. | Закрывает user/auth/lateral movement поведение. | Graph/sequence/tabular auth models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| Windows Event Log / OTRF | `VALIDATION` | Windows Event Logs, Sysmon, process/security events. | SOC-oriented validation и Windows telemetry. | RF, XGBoost, sequence/event models. | <https://github.com/OTRF/Security-Datasets> |
| Unified Host + Network / LANL | `TEST` | Host events, network events, authentication activity. | Финальная проверка hybrid host+network fusion. | Hybrid/late-fusion models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| ISOT Cloud IDS | `TEST` | Cloud logs, syscalls, performance metrics. | Проверяет переносимость в cloud-like среду. | Resource/log/sequence models. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| Dynamic Malware Analysis | `TEST` | Kernel calls, user-level activity, malware traces. | Проверяет malware-driven host behaviour. | API/syscall/process models. | <https://zenodo.org/record/1203289> |

### Experiments only

| Датасет | Статус | Ограничение |
| --- | --- | --- |
| HDFS Log Dataset / LogHub | Experiments only | Не является security-focused dataset; использовать только для проверки log anomaly pipeline. |
| Synthetic syscall augmentation / extra syscall traces | Experiments only | Не использовать как основной источник ground truth без отдельной методологии. |

## Attack lifecycle coverage

| Этап | Поддерживающие источники |
| --- | --- |
| Reconnaissance | OTRF, Maintainable Log Dataset, Unified Host-Network. |
| Privilege Escalation | OTRF, LANL, Unified Host-Network. |
| Lateral Movement | LANL, OTRF, Unified Host-Network. |
| Collection | ADFA IDS, LID-DS 2021/2019, Dynamic Malware Analysis, Maintainable Log Dataset, Unified Host-Network. |
| Data Staging | ADFA IDS, LID-DS 2021/2019, Maintainable Log Dataset, Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network. |
| Exfiltration | CIC-Bell-DNS-EXF-2021, CIC-Bell-DNS-2021, Mendeley DNS, Unified Host-Network. |

## Minimal and optimal host stack

| Stack | Датасеты | Назначение |
| --- | --- | --- |
| Минимально достаточный | ADFA IDS; LID-DS 2021; Maintainable Log Dataset. | HIDS baseline, syscall sequence modelling, enterprise logs. |
| Оптимальный для proposal | ADFA IDS; LID-DS 2021; LID-DS 2019; LANL; Maintainable Log Dataset; Unified Host + Network / LANL. | Baseline + sequence + validation + user-host + enterprise + hybrid. |
| Расширенный | Windows Event Logs / OTRF; ISOT Cloud IDS; Dynamic Malware Analysis. | SOC telemetry, cloud portability, malware-driven behaviour. |

## Stage Two implications

| Компонент Stage Two | Требование из dataset strategy |
| --- | --- |
| Catalog ingestion | Хранить dataset domain, role, source, format, checksum и source path. |
| Parser registry | DNS CSV/PCAP/TXT, host syscalls, logs, JSON/BSON, packet captures и netflow требуют разных parser classes. |
| Label resolver | Не считать unlabeled источники benign; filename/scenario labels только через explicit mapping. |
| Feature extraction | Использовать одинаковые функции признаков для roles, но сохранять role-separated artifacts. |
| Leakage checks | Исключать dataset name, role, scenario, path и label/source fields из model-ready X. |

## Итоговое решение

Для proposal и дальнейшей реализации нужно поддерживать две независимые ветви:

```text
DNS branch:
  TRAIN -> CIC-Bell-DNS-EXF-2021 + CIC-Bell-DNS-2021
  VALIDATION -> split CIC-Bell-DNS-2021
  TEST -> Mendeley DNS Exfiltration Dataset

Host branch:
  TRAIN -> ADFA IDS + LID-DS 2021 + Maintainable Log Dataset
  VALIDATION -> LID-DS 2019 + LANL + Windows Event Logs / OTRF
  TEST -> Unified Host + Network / LANL + ISOT Cloud IDS + Dynamic Malware Analysis
```

Hybrid learning строится поверх feature-level fusion и late fusion. Raw logs, syscalls, packet captures и auth events не объединяются механически в один dataset.


---

## Источник: `docs/ru/feature_extraction_and_catalogue.md`

# Feature extraction map и каталог признаков

Документ объединяет `dataset_feature_extraction_map.md`, `feature_catalogue_full.md` и feature-related разделы `functional_project_cheatsheet.md`. Он задает контракт для Stage Three feature extraction, Parquet artifacts и model-ready datasets.

## Назначение

Документ отвечает на два вопроса:

1. Из каких датасетов какие группы признаков извлекаются.
2. Какие признаки и поля должны существовать в feature artifacts без нарушения traceability и anti-leakage правил.

## Текущая реализация Stage Three

Machine-readable feature catalog находится в `scripts/stage_three/feature_catalog/feature_catalog.yml`.

Stage Three CLI:

```bash
python manage.py stage-three build-feature-catalog
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001
```

Актуальные runbooks: [stage-three/usage_guide.md](ru/stage-three/usage_guide.md) и [stage-three/stage_three_commands.md](ru/stage-three/stage_three_commands.md).

## Принципы отбора признаков

1. `TRAIN`, `VALIDATION`, `TEST` не смешиваются.
2. DNS и Host не склеиваются на raw-level.
3. Labels не являются input features.
4. Leakage поля исключаются из model-ready `X`.
5. Sequence-признаки строятся отдельно от табличных aggregate features.
6. Отсутствие label не означает benign.
7. Timestamp ordering используется только при фактическом наличии timestamp или event order; текущее время не подставляется.

## Уровни расчета

| Уровень | Описание | Модели |
| --- | --- | --- |
| Event-level | Один DNS query, syscall, process event, auth event, packet или log event. | RF, XGBoost, CNN |
| Window-level | Aggregates по host/source_ip/user/domain/process за окно. | RF, XGBoost, CNN |
| Flow-level | 5-tuple / сетевой flow. | RF, XGBoost |
| Trace-level | Syscall/API/module trace как последовательность. | CNN, LSTM |
| Sequence-level | Ordered multi-source events, плановый размер 50-100 событий. | LSTM |
| Hybrid-level | Корреляция host + network/DNS по времени, host, scenario или mapping. | Late fusion, RF/XGBoost, LSTM |

## Dataset to feature map

| Датасет / источник | Роль | Основные группы признаков | Этапы атаки | Использование |
| --- | --- | --- | --- | --- |
| CIC-Bell-DNS-EXF-2021 | `TRAIN` | DNS lexical, entropy, RR/TTL, query-rate, inter-query intervals, unique subdomain ratio. | Exfiltration | Attack-class DNS source. |
| CIC-Bell-DNS-2021 | `TRAIN` + `VALIDATION` split | Те же DNS признаки, benign baseline, FP-control. | Exfiltration / benign baseline | Training normal DNS behaviour и threshold tuning. |
| Mendeley DNS Exfiltration | `TEST` | DNS lexical/temporal/numeric table, source IP windows. | Exfiltration | Финальная generalization check; не обучать. |
| ADFA IDS | `TRAIN` | Syscall frequencies, n-grams, transitions, trace length, collection syscalls. | Collection, Data Staging | HIDS/syscall benchmark. |
| LID-DS 2021 | `TRAIN` | Syscall/API sequence, syscall args, file access, inter-arrival timings. | Collection, Data Staging, Pre-exfiltration | Основной host sequence source. |
| LID-DS 2019 | `VALIDATION` | Те же syscall/sequence признаки, что LID-DS 2021. | Collection, Data Staging | Cross-version validation. |
| Maintainable Log Dataset | `TRAIN` | Log templates, event volume, multi-stage event sequences, file access/log correlation. | Reconnaissance, Collection, Data Staging | Enterprise log behaviour. |
| LANL Dataset | `VALIDATION` | Auth frequency, user-host interaction, failed login ratio, privileged account usage, lateral movement graph. | Privilege Escalation, Lateral Movement | Enterprise behaviour validation. |
| Windows Event Log / OTRF | `VALIDATION` | EventID, process tree, PowerShell/command line, logon/auth, object access, SourceAddress/DestAddress. | Reconnaissance, Privilege Escalation, Lateral Movement | SOC-oriented Windows/Sysmon validation. |
| Unified Host-Network / LANL | `TEST` | Host auth/process + netflow + correlation features. | Full lifecycle | Финальный hybrid test. |
| ISOT Cloud IDS | `TEST` | CPU/memory/I/O/log/cloud workload anomalies. | Data Staging | Cloud portability check. |
| Dynamic Malware Analysis | `TEST` | API/syscall events, command line/path/module tokens, process tree, sandbox lifecycle. | Collection, Data Staging, Pre-exfiltration | Malware-driven host behaviour check. |
| DNS VALIDATION pcap | `VALIDATION` | Amplification ratio, qname/qtype, response size, TTL, RCODE/NXDOMAIN, packet/byte counts. | DNS exfiltration/amplification | Requires DNS packet parser. |
| DNS VALIDATION txt | `VALIDATION` | Domain length, label count, TLD/SLD, entropy. | Domain validation | `unknown` не использовать как class без policy. |
| Host packet captures | `VALIDATION` / `TEST` | Packet/flow counts, protocol distribution, ports, TCP flags, DNS/LDAP/SMB/DCERPC indicators. | Reconnaissance, Lateral Movement, Exfiltration | Labels через scenario/external mapping. |
| Host TEST bson/json/txt | `TEST` | API/syscall-like frequencies, n-grams, transitions, args, process context, command/path entropy. | Collection, Data Staging | Evaluation only. |
| Host TEST csv | `TEST` | Flow duration, bytes/packets, ports, protocol, fan-in/fan-out, TCP flags. | Reconnaissance, Lateral Movement, Exfiltration | TEST-only; не обучать. |

## DNS feature catalogue

| Группа | Примеры признаков | Формула / расчет | Stage Two parser dependency |
| --- | --- | --- | --- |
| Lexical | `dns_query_length`, `dns_subdomain_length`, `dns_subdomain_depth`, `dns_label_count`, `dns_label_avg_len`, `dns_label_max_len`, `dns_digit_count`, `dns_special_char_count`. | String parsing по qname/FQDN/subdomain. | DNS CSV/TXT/PCAP parser. |
| Entropy | `dns_entropy`, `dns_rr_name_entropy`, `url_token_entropy`. | Shannon entropy по domain/query/url tokens. | DNS parser + URL/domain tokenizer. |
| N-grams | `dns_1gram_frequency`, `dns_2gram_frequency`, `dns_3gram_frequency`. | Character/token n-gram counts. | Domain tokenizer. |
| Categorical/enrichment | `dns_tld`, `dns_sld`, `domain_age_days`, `name_server_count`, `unique_asn_count`, `unique_country_count`. | Extract/enrich and encode safely. | DNS parser + optional enrichment. |
| RR/protocol | `ttl_mean`, `ttl_variance`, `unique_ttl_count`, `rr_count`, `rr_rate`, `rr_type_frequency_*`, `dns_qtype_frequency`, `dns_rcode_distribution`, `dns_nxdomain_rate`. | Aggregates по RR/query/response/window. | DNS packet/pcap.csv parser. |
| Temporal | `dns_inter_query_interval_stats`, `dns_query_rate`, `dns_queries_per_window`. | `diff(timestamp)` and count over sliding window. | Timestamp-aware DNS events. |
| Network/DNS bridge | `dns_response_size_stats`, `dns_amplification_ratio`, `dns_source_ip_query_count`, `dnsbl_provider_match`. | Packet/response/window aggregates. | DNS packet parser + source IP fields. |

## Network / flow / packet feature catalogue

| Группа | Примеры признаков | Расчет |
| --- | --- | --- |
| Volume | `packet_count`, `byte_count`, `flow_duration`, `packet_size_mean`, `packet_size_std`. | Group by flow/window. |
| Timing | `inter_arrival_time_stats`. | `diff(timestamp)` by flow/src/dst. |
| Protocol/ports | `protocol_distribution`, `src_port_frequency`, `dst_port_frequency`, TCP flag counts. | Counts/ratios over window. |
| Directionality | `outbound_byte_ratio`, `external_destination_count`, fan-in/fan-out, unique dst hosts. | Internal/external mapping + flow aggregates. |

## Host feature catalogue

| Группа | Примеры признаков | Источники |
| --- | --- | --- |
| Syscall/API sequence | `syscall_frequency`, `syscall_ngram_2_frequency`, `syscall_ngram_3_frequency`, `syscall_transition_probability`, `unique_syscall_count`, `syscall_trace_length`, `syscall_interarrival_stats`. | ADFA, LID-DS, Host txt/sc/ghc/bson/json. |
| Collection indicators | `collection_syscall_count`, `directory_enumeration_count`, `file_access_count`, `file_access_rate`, `file_access_entropy`, `unique_file_count`, `sensitive_file_extension_count`. | Syscalls, logs, Windows object access, malware traces. |
| API/sandbox/trace | `api_descriptor_frequency`, `api_category_frequency`, `api_arg_token_count`, `trace_module_frequency`, `trace_module_transition_frequency`, `trace_offset_distribution`, `trace_density`. | Dynamic Malware, Host BSON/JSON/GHC. |
| Authentication | `login_success_count`, `login_failure_count`, `failed_login_ratio`, `failed_then_success_login_indicator`, `session_opened_count`, `session_duration_stats`, `sudo_activity_count`, `sshd_activity_count`. | LANL, OTRF, auth logs, wls_day. |
| User/host graph | `user_host_interaction_count`, `source_ip_auth_frequency`, `auth_baseline_deviation`, `source_loghost_graph_degree`. | LANL, Windows logs, wls_day. |
| Windows/Sysmon/process | `event_id_frequency`, `security_event_sequence_entropy`, `logon_type_distribution`, `parent_child_process_count`, `process_name_frequency`, `command_line_length`, `command_line_entropy`, `encoded_powershell_indicator`, `rare_process_execution_score`. | OTRF, Windows Event Logs, Dynamic Malware. |
| Filesystem/resource telemetry | `filesystem_used_pct_stats`, `filesystem_pressure_ratio`, `inode_free_ratio`, `disk_read_bytes_rate`, `disk_write_bytes_rate`, `cpu_total_pct_stats`, `memory_usage_stats`, `load_average_stats`. | Host metric logs, ISOT Cloud IDS. |
| Network/resource bridge | `network_interface_bytes_rate`, `socket_count`, `source_dest_address_port_count`. | Host network telemetry, Windows events, netflow. |
| Logs/templates | `log_event_count`, `log_volume_rate`, `log_level_frequency`, `warning_error_count`, `component_frequency`, `message_template_frequency`, `event_type_frequency`, `alert_count`. | Maintainable logs, syslog/messages/mainlog, sandbox logs. |
| Staging/compression | `archive_creation_count`, `compression_process_indicator`, `process_path_entropy`, `suspicious_path_indicator`, `module_path_entropy`. | Windows/process logs, malware, command-line telemetry. |

## Hybrid and sequence catalogue

| Признак | Назначение |
| --- | --- |
| `host_network_time_delta` | Временной лаг между nearest host event и network event. |
| `process_to_network_burst_score` | Связь запуска процесса и последующего network burst. |
| `auth_to_network_correlation` | Количество network flows после auth event/window. |
| `file_to_network_correlation` | Связь file access/data staging с network outflow. |
| `cpu_io_network_correlation` | Rolling correlation CPU/disk/network spikes. |
| `cross_source_event_count` | Количество событий из разных sources в одном unified window. |
| `sequence_window_event_count` | Количество events в LSTM window. |
| `sequence_window_duration` | Длительность sequence window. |
| `sequence_event_type_entropy` | Entropy over ordered event type tokens. |
| `sequence_temporal_order_pattern` | Ordered stage/event tokens. |
| `process_file_network_sequence` | Pattern: file access -> archive/compress -> outbound network event. |
| `stage_transition_pattern` | Переходы Reconnaissance -> Privilege Escalation -> Lateral Movement -> Collection -> Data Staging -> Exfiltration. |

## Минимальный feature schema для Parquet artifacts

### Traceability fields

| Поле | Назначение | Использовать как model feature |
| --- | --- | --- |
| `event_id` | ID normalized event. | Нет |
| `source_file_id` | ID raw-файла из catalog. | Нет |
| `source_row_id` / `packet_id` | Row/packet/event index. | Нет |
| `dataset_domain` | `dns`, `host`, `network`, `hybrid`. | Нет |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`. | Нет |
| `dataset_name` | Dataset name. | Нет, кроме audit/reporting |
| `dataset_format` | csv, pcap, json, log, bson, txt, etc. | Нет, кроме parser/debug |
| `parser_name` / `parser_version` | Parser traceability. | Нет |
| `event_timestamp` | Normalized event time. | Только derived time features / ordering |
| `window_id` | Window ID. | Нет |
| `sequence_id` | Sequence-window ID. | Нет |

### Label fields

| Поле | Назначение |
| --- | --- |
| `label_binary` | 0=benign, 1=attack/exfiltration/malicious, NULL=unknown. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, collection, data_staging, unknown. |
| `label_subtype` | Specific subtype/scenario, если доступен. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 explicit; 0.7-0.9 inferred; 0.4-0.7 weak; 0 unlabeled. |
| `label_mapping_rule_id` | ID label resolver rule. |

## Что исключать из model-ready X

| Поле / группа | Почему исключать |
| --- | --- |
| `source_file`, basename, full path | Может кодировать `benign`, `malware`, `attack`, `exfiltration`. |
| `dataset_role` | TRAIN/VALIDATION/TEST leakage. |
| `dataset_name` | Модель может запомнить dataset вместо поведения. |
| `scenario_name`, `image_name` | Использовать только для label join/evaluation metadata. |
| `label_*` | Target/audit fields, не input features. |
| Raw payload/body | Проект ориентирован на metadata/behavioural detection, не payload inspection. |
| Абсолютные локальные пути | Непереносимы и создают leakage risk. |

## Приоритет реализации

| Priority | Feature groups |
| --- | --- |
| P0 | DNS lexical/entropy/temporal/protocol; host syscall/API; auth; Windows/Sysmon; network volume/ports; sequence window basics; stage transition patterns. |
| P1 | Domain enrichment; hybrid correlations; resource telemetry; archive/compression; sensitive file access; graph/baseline features. |
| P2 | Advanced command-line tokenization; template mining; long-term per-user/per-host baselines; feature stability checks. |

## Рекомендуемый порядок расширения в коде

1. Обновить `scripts/stage_three/feature_catalog/feature_catalog.yml`.
2. Добавить extractor в `scripts/stage_three/extraction`.
3. Сохранить feature artifacts через Stage Three writer/registry.
4. Проверить X/y/metadata/traceability separation.
5. Прогнать quality/leakage/traceability checks.
6. Сгенерировать `stage-three final-report` и переходить в Stage Four только при `READY_FOR_STAGE_FOUR`.

## Связь со Stage Two и Stage Three

| Stage Two layer | Требование |
| --- | --- |
| Parser pipeline | Каждый feature group зависит от конкретного parser output и normalized schema. |
| PostgreSQL Catalog | Хранит metadata, paths, statuses, hashes, reports, но не большие feature tables. |
| Parquet artifacts | Хранят normalized events, feature windows, sequence windows, model-ready X/y. |
| DuckDB checks | Проверяют Parquet counts, schema drift, split contamination, leakage columns. |
| LabelResolver | Заполняет label fields отдельно от X features. |
| Traceability | Feature/model-ready artifacts должны вести к normalized -> parser run -> raw dataset file. |
| Stage Three final report | Фиксирует готовность конкретного `experiment_id` к Stage Four. |


---

## Источник: `docs/ru/normalization/data_leakage_prevention.md`

# Предотвращение data leakage

Leakage prevention в Stage Two опирается на contract-level запреты, catalog traceability и runtime checks. Главная цель: labels, source identifiers и split metadata не должны попадать в model-ready `X`.

## Неприкосновенные правила

1. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` не смешиваются в одном model-ready artifact.
3. Labels не являются обычными input features.
4. Filename heuristic для `TEST` labels запрещен.
5. Отсутствующий label не означает benign.
6. Traceability fields сохраняются в catalog/metadata, но исключаются из `X`.

## Запрещенные X columns

Запрещенные columns берутся из feature/model-ready contracts:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

`ModelReadyRegistryService.write_table_artifact()` вызывает `validate_x_columns()` для `data_type = "X"` и отклоняет rows, если в них есть запрещенные поля.

## LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Код:

```text
scripts/stage_two/quality/checkers.py
```

Проверки:

| Проверка | Что ловит |
| --- | --- |
| `x_forbidden_columns` | Label/source/traceability columns внутри model-ready `X`. |
| `test_absent_from_train` | Использование `TEST` в training context. |
| `preprocessing_fit_only_train` | Preprocessing artifact fitted на роли, отличной от `TRAIN`. |

CRITICAL нарушения регистрируются в `data_quality_reports` и должны блокировать использование artifact.

## Labels

Label fields могут присутствовать в normalized events для audit и в model-ready `y`, но не в `X`. События без label остаются unlabeled:

```json
{
  "label_binary": null,
  "label_source": "none",
  "label_status": "unlabeled"
}
```

См. [label_resolver.md](ru/normalization/label_resolver.md).

## Traceability без leakage

Traceability chain обязателен:

```text
raw -> normalized -> features -> model-ready
```

Но traceability identifiers (`event_uid`, `sample_uid`, paths, hashes, parser IDs) не должны становиться признаками. Они должны храниться:

- в PostgreSQL Catalog;
- в artifact metadata;
- в non-X columns, исключенных из training matrix.

## DNS supervised 70/30 policy

Для DNS supervised split `dns_supervised_70_30_v1` leakage prevention включает
не только запрет label/source/path fields в `X`, но и запрет некорректных
источников:

- текущий DNS `TEST/csv` и его chunked downstream artifacts не используются в supervised evaluation;
- `ens33-dns_amplification_attack.pcap` исключен полностью;
- `ens33-dns_amplification_attack__f291ed87a1.pcap` ограничивается global target;
- `label_binary=NULL` исключается, а не конвертируется в normal;
- `split_index.parquet` проверяется на отсутствие пересечений `sample_uid` между `TRAIN`, `VALIDATION`, `TEST`;
- `traceability.parquet` сохраняет `source_role`, `normalized_artifact_id`, `source_normalized_path` и `split_policy_id`, но эти поля не попадают в `X.parquet`.

Проверочный отчет:

```text
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
```

Вердикт готовности:

- активный experiment: `dns_rebalanced_70_30_v1`;
- статус: готово для обучения supervised tabular модели;
- quality checks: `PASS`, без `blocking_issues`, без предупреждений по timestamp;
- leakage/traceability checks: `PASS`;
- `TEST` остается только для финальной evaluation.

## Типовые ошибки

| Ошибка | Последствие | Исправление |
| --- | --- | --- |
| `label_binary` попал в X | Модель обучается на ответе. | Пересобрать X после exclusion contract. |
| `source_file_path` попал в X | Модель может выучить dataset/source identity. | Удалить source fields из feature selection. |
| `TEST` использован для scaler fit | Метрики становятся завышенными. | Fit только на `TRAIN`, transform для `VALIDATION`/`TEST`. |
| Unlabeled заменен на benign | Искажение labels. | Сохранять `label_binary = null`, `label_status = unlabeled`. |
| Filename heuristic для TEST | Leakage из имени файла. | Отключить heuristic, использовать только explicit ground truth. |


---

## Источник: `docs/ru/normalization/data_quality_checks.md`

# Проверки качества данных

Stage Two использует два уровня проверок:

1. DuckDB analytics checks поверх Parquet views.
2. `DataQualityChecker`/`LeakageChecker` с регистрацией результатов в `data_quality_reports`.

## DuckDB analytics

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Runtime-защита:

- команда применяет bounded DuckDB settings: `memory_limit`, `threads`, `temp_directory`, `max_temp_directory_size`;
- значения по умолчанию: `STAGE_TWO_DUCKDB_MEMORY_LIMIT=32GB`, `STAGE_TWO_DUCKDB_THREADS=2`, `STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE=100GB`;
- spill directory по умолчанию: `PATH_DATA_STORAGE/temp_data/duckdb`;
- для больших Parquet layers команда не создает единый DuckDB view поверх всех файлов; row counts и schema checks считаются потоково по Parquet metadata, а data-level checks выполняются chunked;
- CLI показывает progress bar по подготовке слоев, проверкам, сохранению report и регистрации в catalog.

Код:

```text
scripts/stage_two/duckdb/service.py
```

Проверяет:

- созданы ли views `normalized_all`, `features_all`, `model_ready_all`;
- row counts по Parquet layers;
- наличие required columns;
- split contamination;
- schema mismatch.

Report:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

После регистрации в catalog создается запись `data_quality_reports` с `check_group` для DuckDB/quality diagnostics.

## DataQualityChecker

Код:

```text
scripts/stage_two/quality/checkers.py
```

`DataQualityChecker` читает DuckDB views и проверяет:

| Проверка | Цель |
| --- | --- |
| Required columns | Контрактные колонки присутствуют в views. |
| Null counts | Видимость пустых значений в критичных columns. |
| Duplicate keys | Дубликаты ключевых event/sample identifiers. |
| Role domain | Значения role/dataset_role ограничены `TRAIN`, `VALIDATION`, `TEST`. |
| Branch domain | Значения branch ограничены catalog constants. |

Reports пишутся в RU/EN report roots и могут регистрироваться через `DataQualityRepository`.

## Уровни severity

| Severity | Значение |
| --- | --- |
| `INFO` | Диагностическая информация. |
| `WARNING` | Нежелательное состояние, которое не всегда блокирует pipeline. |
| `ERROR` | Нарушение контракта или качества данных. |
| `CRITICAL` | Нарушение, которое может привести к leakage, смешиванию splits или недостоверному model-ready artifact. |

## Связь с leakage checks

`LeakageChecker` находится в том же модуле, но описан отдельно в [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md). Его CRITICAL results также регистрируются в `data_quality_reports`, обычно с `check_group = "leakage"`.

## Readiness check

```bash
python -m scripts.stage_two.readiness_check
```

Команда выводит progress bar в stderr и JSON result в stdout. Проверка raw file hashes выполняется потоково по колонкам `dataset_files.id/file_path/file_hash_sha256`, без загрузки ORM-объектов всей таблицы в память.

Runtime-настройки для hash scan:

- `STAGE_TWO_READINESS_DB_YIELD_PER` - сколько catalog rows получать за один streaming batch, default `1000`;
- `STAGE_TWO_READINESS_HASH_CHUNK_BYTES` - размер блока чтения raw file при SHA-256, default `1048576` bytes.

Readiness проверяет, что:

- миграции применены;
- storage paths существуют;
- catalog содержит datasets/files/parser_registry/schema_versions/artifacts/reports;
- parser coverage не имеет uncovered combinations;
- normalized artifacts есть и не failed;
- feature/model-ready artifacts связаны с upstream artifacts;
- quality/leakage reports существуют;
- traceability chain восстанавливается;
- raw file hashes совпадают с catalog.

Readiness report сохраняется в:

```text
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
reports/en/stage-two/stage_two_readiness_report.json
```

## Что считается блокирующим

Блокирующие сценарии:

- `TEST` найден в preprocessing fit/training context;
- label/source fields присутствуют в model-ready `X`;
- отсутствует обязательная traceability связь;
- raw file hash не совпадает с catalog;
- parser coverage отсутствует для files, которые должны нормализоваться;
- role contamination между `TRAIN`, `VALIDATION`, `TEST`.

Такие нарушения нужно исправлять до использования artifacts в ML experiments.


---

## Источник: `docs/ru/normalization/final_summary_template.md`

# Шаблон итоговой сводки Stage Two normalization

Используйте шаблон после изменения parser/normalization pipeline или после полного запуска Stage Two.

## Область запуска

- Branches:
- Roles:
- Source formats:
- Storage root:
- Catalog DB:
- Code revision:

## Команды

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit <N>
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Сводка catalog

| Table | Count | Notes |
| --- | ---: | --- |
| `datasets` |  |  |
| `ingestion_runs` |  |  |
| `dataset_files` |  |  |
| `parser_registry` |  |  |
| `parser_runs` |  |  |
| `normalized_artifacts` |  |  |
| `feature_artifacts` |  |  |
| `model_ready_artifacts` |  |  |
| `data_quality_reports` |  |  |

## Parser coverage

| Branch | Role | Source format | Parser | Status | Notes |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Результаты normalization

| Branch | Role | Source format | Files | Parsed | Partial | Failed | Unsupported |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |  |  |  |

## Quality и leakage

| Check group | Status | Severity | Report path | Notes |
| --- | --- | --- | --- | --- |
| DuckDB analytics |  |  |  |  |
| Data quality |  |  |  |  |
| Leakage |  |  |  |  |
| Readiness |  |  |  |  |

## Пример traceability

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

Artifact checked:

- model_ready_artifact:
- feature_artifact:
- normalized_artifact:
- parser_run:
- dataset_file:
- dataset:

## Ограничения и follow-up

- Unsupported formats:
- Parser gaps:
- Label risks:
- Timestamp risks:
- Риски больших файлов:
- Schema drift:
- Требуемые следующие действия:


---

## Источник: `docs/ru/normalization/host_validation_wls_day_exclusion.md`

# Исключение Host VALIDATION wls_day

Raw bucket `host/VALIDATION/wls_day` исключен из активной Stage Two обработки после того, как большие JSONL-файлы были разделены и зарегистрированы как chunks.

Активная обработка должна использовать только:

```text
chunked/host/VALIDATION/wls_day/...
```

Не удаляйте raw-файлы физически без отдельного решения оператора. Traceability по исходным файлам, parser runs и уже созданным artifacts должна сохраняться. Невалидные normalized artifacts, созданные из исходных больших файлов, должны оставаться зарегистрированными, но не должны иметь `SUCCESS`.

Ожидаемое состояние catalog:

- исходные raw-файлы: `dataset_files.status = SKIPPED`
- parser runs исходных файлов: `parser_runs.status = SKIPPED`
- normalized artifacts от parser runs исходных файлов: `normalized_artifacts.status = SKIPPED`
- chunked-файлы: остаются доступными как `READY_FOR_PARSING` или `PARSED`

Scanner и operational selectors не должны повторно активировать raw bucket. Роли `TRAIN`, `VALIDATION` и `TEST` не смешиваются; это исключение относится только к Host `VALIDATION` `wls_day`.


---

## Источник: `docs/ru/normalization/label_resolver.md`

# Разрешение labels

`LabelResolver` находится в:

```text
scripts/stage_two/labels/resolver.py
```

Он приводит labels из разных источников к canonical normalized fields и защищает pipeline от опасного предположения "нет label = benign".

## Canonical label fields

| Поле | Значение |
| --- | --- |
| `label_binary` | `1`, `0` или `null`. |
| `label_family` | Семейство/класс атаки, если известно. |
| `label_subtype` | Более точный subtype, если известен. |
| `label_source` | `embedded_column`, `external_file`, `scenario_metadata`, `filename`, `ids_alert`, `none` и т.п. |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label`. |
| `label_confidence` | Число confidence, если применимо. |
| `label_mapping_rule_id` | ID rule из catalog/config, если label получен правилом. |

Unlabeled output:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

## Источники labels

| Источник | Приоритет | Комментарий |
| --- | --- | --- |
| Embedded column | 0 | Поля вроде `label_binary`, `label`, `target`, `class`, `is_attack`, `malicious`, `attack_cat`. |
| External/ground truth rule | 1 | Rule из catalog/config, если он явно матчится. |
| Scenario metadata | 2 | Metadata контекст dataset/scenario. |
| Filename | 3 | Weak/inferred hint из имени файла; запрещен для `TEST`. |
| IDS alert | 4 | Alert-derived weak signal. |
| None | 99 | Нет label. |

Точные поля embedded labels перечислены в `EMBEDDED_LABEL_FIELDS` в `resolver.py`.

## Политика TEST

`LabelResolver.label_hints_allowed()` возвращает `False` для `TEST`. Это означает:

- filename heuristic нельзя использовать для label inference в `TEST`;
- embedded/IDS hints, которые являются эвристикой, не должны превращать `TEST` в training signal;
- `TEST` не используется для threshold tuning, feature selection или preprocessing fit.

Explicit external ground truth rules допустимы только если они не являются filename heuristic и явно заданы как label source. Если label отсутствует, событие остается unlabeled.

## Конфликтующие labels

Если разные источники дают несовместимые canonical labels, результат должен фиксироваться как `conflicting_label`, а не silently выбирать benign/malicious. Такой случай должен попадать в metadata/errors и далее в quality review.

## Использование в parser

Parser должен передавать raw record и context в resolver и включать результат в normalized event:

```python
labels = self.label_resolver.resolve(record, context)
event.update(labels)
```

Если parser читает source, где label отсутствует, он не должен создавать `label_binary = 0`. Правильный output - unlabeled contract выше.

## Labels и model-ready artifacts

Labels не входят в X features. Они должны храниться отдельно:

- в normalized events как label metadata;
- в feature/model-ready metadata как label distribution;
- в model-ready `y` artifact, если downstream stage создает labels table.

Для model-ready `X` поля `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id` и другие label/source columns запрещены.


---

## Источник: `docs/ru/normalization/normalized_event_schema.md`

# Схема normalized event

Normalized event schema хранится в:

```text
schemas/normalized/normalized_event_v1.json
```

Это JSON contract с `schema_name = "normalized_event"`, `schema_version = "v1"`, `layer = "normalized"` и массивом `fields`. Parser implementations должны выдавать rows, совместимые с этим контрактом.

## Обязательные поля parser output

Базовый parser contract в `scripts/stage_two/parsers/base.py` требует поля:

```text
event_uid
dataset_name
dataset_role
branch
source_format
source_file_path
parser_name
parser_version
schema_name
schema_version
timestamp_type
entity_type
event_type
modality
label_source
label_status
created_at
```

Дополнительные поля из JSON schema могут быть nullable, но parser должен сохранять traceability и label/timestamp null policy.

## Traceability поля

| Поле | Назначение |
| --- | --- |
| `event_uid` | Уникальный идентификатор normalized event. |
| `dataset_name` | Имя dataset из catalog/source context. |
| `dataset_role` | `TRAIN`, `VALIDATION` или `TEST`. |
| `branch` | `dns`, `host`, `network`, `hybrid`. |
| `source_format` | Формат raw файла. |
| `source_file_path` | Путь к исходному файлу. |
| `source_file_hash` | SHA-256 raw файла, если доступен из catalog. |
| `parser_run_id` | ID parser run, связывает event с `parser_runs`. |
| `parser_name`, `parser_version` | Parser implementation и версия. |
| `schema_name`, `schema_version` | Версия normalized schema. |
| `event_index` | Порядковый номер события внутри файла, если доступен. |

Traceability поля нельзя удалять из normalized artifacts. Для model-ready `X` они считаются leakage/source columns и должны быть исключены из признаков.

## Timestamp policy

| Поле | Правило |
| --- | --- |
| `timestamp` | Может быть `null`. |
| `timestamp_type` | Одно из `absolute`, `relative`, `event_order`, `missing`. |
| `event_index` | Используется для сохранения порядка, когда абсолютного времени нет. |

Если timestamp отсутствует, нельзя подставлять текущее время. Правильные варианты:

- `timestamp = null`, `timestamp_type = "event_order"`, если есть надежный `event_index`;
- `timestamp = null`, `timestamp_type = "missing"`, если нет времени и порядка.

`build_timestamp_fields()` в `scripts/stage_two/parsers/common.py` реализует это правило: timestamp дает `absolute`, event index без timestamp дает `event_order`, отсутствие обоих дает `missing`.

## DNS поля

DNS parsers заполняют поля, связанные с DNS/network context, если они есть в source:

- `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- `query_domain`, `qtype`, `qclass`, `rcode`, `ttl`;
- DNS-specific values внутри `features_json` или `raw_fields_json`, если исходная схема не совпадает напрямую с normalized fields.

DNS packet captures могут давать summary-level events в зависимости от `--packet-mode`.

## Host поля

Host parsers используют поля, связанные с host telemetry:

- process: `process_id`, `process_name`, parent process fields;
- file/path: `path`, file action fields;
- syscall/log: `sys_call`, `event_id`, `event_type`;
- metrics/log payload, если source формат логовый или metricbeat-like.

Для нестандартных строковых логов часть значений сохраняется в `raw_fields_json`, а normalized columns заполняются только когда значение можно извлечь без выдумывания.

## Network/hybrid поля

`network` и `hybrid` branches есть в schema/catalog constants, но текущий normalization runner поддерживает только `dns` и `host`. Network/hybrid fields могут использоваться контрактами будущих parsers, но не должны описываться как полностью реализованный normalization pipeline.

## Labels

Unlabeled event должен иметь:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Отсутствующий label не равен benign. Для `TEST` filename/embedded heuristics отключены `LabelResolver.label_hints_allowed()`, чтобы не вносить leakage через имя файла или поля, которые не являются explicit external ground truth.

## JSON поля

| Поле | Назначение |
| --- | --- |
| `features_json` | Parser-level extracted attributes, которые еще не являются model-ready X features. |
| `raw_fields_json` | Исходные поля или фрагменты raw record для audit/debug. |
| `metadata_json` | Parser/file metadata, warnings, confidence, дополнительные counters. |

`ParquetArtifactWriter` сериализует поля с суффиксом `_json` в deterministic JSON strings перед записью Parquet.

## Граничные случаи

| Сценарий | Ожидаемое поведение |
| --- | --- |
| Empty file | Parser result может привести к `EMPTY_FILE`/`SKIPPED`, artifact не обязан создаваться. |
| Частично битые строки | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, ошибки фиксируются в parser run counters/error samples. |
| Неизвестный source format | Файл получает `UNSUPPORTED_FORMAT`, если resolver не нашел parser. |
| Schema drift | Parser должен сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не расширять model-ready X без schema review. |


---

## Источник: `docs/ru/normalization/parquet_duckdb_artifacts.md`

# Parquet и DuckDB артефакты

Stage Two хранит большие таблицы в Parquet и использует DuckDB для аналитических SQL-проверок поверх этих файлов. PostgreSQL Catalog хранит только metadata: paths, row counts, hashes, schema versions, statuses и связи.

## Parquet writer

Код:

```text
scripts/stage_two/parquet/writer.py
```

`ParquetArtifactWriter`:

- пишет rows в Parquet;
- сериализует поля с суффиксом `_json` в deterministic JSON strings;
- по умолчанию использует compression `zstd`;
- считает `row_count`, `file_size_bytes`, optional `content_hash_sha256`;
- регистрирует artifacts через `ArtifactRepository`.

Hash output контролируется normalization option `--hash-output-artifacts`. Если hashing выключен, `content_hash_sha256` может быть пустой строкой.

## Пути normalized artifacts

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Пример:

```text
parquet/normalized/dns/TRAIN/dns_query/dns-train/schema=v1/part-42.parquet
```

Пишут:

- `DnsNormalizationService`;
- `HostNormalizationService`;
- `NormalizeFormatRunner`;
- legacy `normalize-dns`/`normalize-host`.

Catalog entry: `normalized_artifacts.normalized_path`.

## Пути feature artifacts

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Feature groups из contract:

```text
dns_features
host_syscall_features
host_eventlog_features
host_metrics_features
network_flow_features
hybrid_features
sequence_features
```

Catalog entry: `feature_artifacts.feature_path`.

В текущем CLI нет отдельной команды сборки feature artifacts. Реализованы contract helpers и writer service: `scripts/stage_two/features/contracts.py`, `scripts/stage_two/features/writer.py`.

## Пути model-ready artifacts

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

Поддерживаемые `data_type`:

```text
X
y
sequence
split_index
preprocessing_metadata
```

Catalog entry: `model_ready_artifacts.artifact_path`.

`ModelReadyRegistryService` проверяет:

- `data_type` входит в contract;
- `X` rows не содержат forbidden leakage columns;
- preprocessing artifacts fitted only on `TRAIN`.

## DuckDB service

Код:

```text
scripts/stage_two/duckdb/service.py
```

DuckDB создает views поверх Parquet:

| View | Path pattern | Required columns |
| --- | --- | --- |
| `normalized_all` | `parquet/normalized/**/*.parquet` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `parquet/features/**/*.parquet` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` | `filename` |

Если matching Parquet файлов нет, service создает placeholder view с required columns, чтобы checks возвращали контролируемый результат, а не падали из-за отсутствия view.

## DuckDB checks

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Проверки:

- row counts по views;
- наличие required columns;
- split contamination (`TRAIN`, `VALIDATION`, `TEST` не должны смешиваться);
- schema mismatch diagnostics.

Report сохраняется как:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

Через `register_report()` результат регистрируется в `data_quality_reports`.

## Ограничения

- DuckDB читает уже записанные Parquet files; он не заменяет PostgreSQL Catalog.
- Feature/model-ready paths появляются после Stage Three `extract-features` и `build-model-ready`; готовность для Stage Four подтверждается `stage-three final-report`.
- Перемещение Parquet files без обновления catalog ломает traceability.
- `TRAIN`, `VALIDATION`, `TEST` должны оставаться раздельными на уровне path, catalog metadata и downstream artifacts.


---

## Источник: `docs/ru/normalization/parser_development_guide.md`

# Руководство добавления parser implementation

Этот документ описывает минимальный контракт нового parser в Stage Two. Новый parser должен быть безопасен для raw data, не смешивать роли и сохранять traceability.

## Где менять код

| Задача | Файл/директория |
| --- | --- |
| Parser class | `scripts/stage_two/parsers/*.py` |
| Shared helpers | `scripts/stage_two/parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py` |
| Registry entry | `scripts/stage_two/parser_registry/parser_registry_seed.json` |
| Schema contract | `schemas/normalized/normalized_event_v1.json` или новая schema version |
| Parser tests/smoke | `scripts/stage_two/parser_smoke.py`, `parser_input_smoke.py`, project tests if present |
| Документация | `docs/ru/normalization/parser_strategy.md`, этот файл, при необходимости schema docs |

## Минимальный контракт parser

Parser class должен:

1. наследоваться от `BaseParser`;
2. принимать `ParserContext`;
3. возвращать `ParserResult`;
4. заполнять обязательные normalized fields;
5. не изменять raw файл;
6. сохранять `event_index` или другой порядок, если timestamp отсутствует;
7. использовать `LabelResolver`, а не назначать benign по умолчанию;
8. сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не терять их.

Обязательные поля перечислены в [normalized_event_schema.md](ru/normalization/normalized_event_schema.md).

## Шаблон решения

```python
from pathlib import Path

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import build_timestamp_fields
from scripts.stage_two.parsers.input_reader import UniversalInputReader


class MyParser(BaseParser):
    parser_name = "my_parser"
    parser_version = "v1"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        events: list[dict[str, object]] = []
        errors: list[str] = []

        reader = UniversalInputReader(path)
        with reader.open("json_lines") as records:
            for event_index, raw_record in enumerate(records):
                try:
                    timestamp_fields = build_timestamp_fields(
                        raw_record.get("timestamp"),
                        event_index=event_index,
                    )
                    labels = self.label_resolver.resolve(raw_record, context)
                    events.append(self.base_event(
                        context,
                        event_index=event_index,
                        **timestamp_fields,
                        **labels,
                        event_type="my_event",
                        entity_type="host",
                        modality="host_event",
                        raw_fields_json=raw_record,
                    ))
                except Exception as exc:
                    errors.append(f"event_index={event_index}: {exc}")

        return ParserResult(
            events=events,
            rows_read=len(events) + len(errors),
            rows_parsed=len(events),
            rows_failed=len(errors),
            error_samples=errors,
        )
```

В реальном parser используйте тот reader mode, который соответствует формату (`csv_rows`, `json_lines`, `lines`, `binary`, `packet_bytes`, `bson_stream`). Не добавляйте псевдополя в normalized output без обновления schema contract.

## Запись в registry

После добавления class нужно добавить или расширить parser group в:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Минимальные поля:

```json
{
  "parser_name": "my_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["my_format"],
  "supported_roles": null,
  "priority": 100,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "MyParser"
}
```

`supported_roles = null` означает все активные роли. Если parser допустим только для `TEST` или только для `TRAIN/VALIDATION`, задайте список явно. Например `HostBsonSandboxParser` ограничен `TEST`, а `HostPacketCaptureParser` - `TRAIN`/`VALIDATION`.

## Обработка labels

Parser не должен самостоятельно назначать `label_binary = 0` при отсутствии label. Используйте `LabelResolver`:

- explicit embedded/external labels дают `explicit_label` или configured status;
- weak/inferred labels должны иметь confidence/source;
- conflicting labels должны фиксироваться как `conflicting_label`;
- для `TEST` filename/embedded heuristics отключены.

См. [label_resolver.md](ru/normalization/label_resolver.md).

## Обработка timestamp

Запрещено подставлять `datetime.now()` для отсутствующего timestamp.

Используйте правила:

```text
timestamp present -> timestamp_type = absolute
timestamp missing but event_index present -> timestamp_type = event_order
timestamp missing and no ordering -> timestamp_type = missing
```

## Обработка ошибок

| Ошибка | Как фиксировать |
| --- | --- |
| Битая строка | Увеличить failed counter, добавить sample в errors, продолжить если возможно. |
| Empty file | Вернуть status override `EMPTY_FILE` или `SKIPPED`, не создавать fake benign events. |
| Unsupported subformat | Вернуть `UNSUPPORTED_FORMAT` или error metadata, если parser не может безопасно читать файл. |
| Schema drift | Сохранить raw payload в JSON fields и добавить warning. |
| Large binary file | Использовать packet summary/sample режимы; не загружать весь файл в память без необходимости. |

## Проверки после добавления parser

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --dry-run
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit 10
python manage.py stage-two run-duckdb-checks
```

Если parser влияет на labels или model-ready downstream, дополнительно:

```bash
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Документация, которую нужно обновить

- `parser_strategy.md` - список parser classes/source formats.
- `normalized_event_schema.md` - если добавлены новые normalized fields или новая schema version.
- `label_resolver.md` - если появились новые label fields/rules.
- `data_quality_checks.md` - если нужен новый quality check.
- `performance_tuning.md` - если parser требует специальных runtime limits.


---

## Источник: `docs/ru/normalization/parser_strategy.md`

# Стратегия parser registry и выбора parser

Parser strategy состоит из трех частей:

1. `parser_registry_seed.json` описывает поддерживаемые parser groups.
2. `ParserRegistrySeeder` разворачивает groups в строки `parser_registry`.
3. `ParserResolver` выбирает активный parser для конкретного `dataset_files` по `branch`, `role`, `source_format`.

## Seed registry

Файл:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Seed загружается командой:

```bash
python manage.py stage-two seed-parser-registry
```

Seeder проверяет, что `parser_module` и `parser_class` импортируются. Если класс отсутствует или не наследуется от `BaseParser`, entry может быть сохранен как inactive с diagnostic metadata в `config_json.class_validation`.

## Как выбирается parser

`ParserResolver` ищет active entries:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
supported_role == dataset_file.role OR supported_role IS NULL
is_active == true
```

Затем сортирует по `priority`, потом `id`. Role-specific entry имеет преимущество только через порядок/priority; универсальная запись с `supported_role = NULL` подходит для всех ролей.

Если parser не найден:

- `resolve_or_mark_unsupported()` переводит файл в `UNSUPPORTED_FORMAT`;
- `normalize-format` возвращает status `UNSUPPORTED_FORMAT` для выбранного bucket;
- parser run не должен имитировать успешную нормализацию.

## Реализованные parser groups

### DNS

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `DnsCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsPcapCsvParser` | `pcap.csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsTxtDomainListParser` | `txt` | `VALIDATION` | `scripts.stage_two.parsers.dns` |
| `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all active roles | `scripts.stage_two.parsers.dns` |

### Host

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `HostCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.host` |
| `HostJsonLinesParser` | `json`, `json-1` | all active roles | `scripts.stage_two.parsers.host` |
| `HostLineLogParser` | `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `info`, `journal`, `journal~`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `uptime.log` | all active roles | `scripts.stage_two.parsers.host` |
| `HostSyscallTraceParser` | `txt`, `sc`, `ghc` | all active roles | `scripts.stage_two.parsers.host` |
| `HostXmlParser` | `xml` | all active roles | `scripts.stage_two.parsers.host` |
| `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all active roles | `scripts.stage_two.parsers.host` |
| `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | `TRAIN`, `VALIDATION` | `scripts.stage_two.parsers.host` |
| `HostBsonSandboxParser` | `bson` | `TEST` | `scripts.stage_two.parsers.host` |

Metricbeat-like логи обрабатываются через существующие host parser modules/helpers; отдельной active seed group с именем `HostMetricbeatParser` в текущем registry seed нет.

## Lifecycle statuses parser

| Уровень | Status | Значение |
| --- | --- | --- |
| parser run | `SUCCESS` | Parser completed and emitted events without failed rows. |
| parser run | `PARTIAL_SUCCESS` | Parser emitted events, but some rows/records failed. |
| parser run | `FAILED` | Parser failed for the file. |
| parser run | `SKIPPED` | File intentionally skipped. |
| dataset file | `PARSED` | Файл успешно нормализован. |
| dataset file | `PARTIALLY_PARSED` | Есть normalized events, но были ошибки. |
| dataset file | `FAILED` | Нормализация не удалась. |
| dataset file | `SKIPPED` | Файл пропущен по parser/result policy. |
| dataset file | `UNSUPPORTED_FORMAT` | Для `branch/role/source_format` нет parser. |

Stage One analysis statuses вроде `READY_FOR_FEATURE_EXTRACTION`, `NEEDS_CUSTOM_PARSER`, `PARTIALLY_SUPPORTED`, `BROKEN_OR_EMPTY` используются как input guidance для parser strategy, но Stage Two catalog lifecycle использует DB statuses выше.

## Контракт ParserResult

Parser возвращает `ParserResult`:

- `events`: список normalized event rows;
- counters: rows read/parsed/failed, events emitted;
- errors/warnings/metadata;
- optional `status_override`: `EMPTY_FILE`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.

`ParserResult.status_decision` преобразует результат в parser run/file statuses. Empty output без явной причины не должен маскироваться как успешный benign dataset.

## Ошибки и граничные случаи

| Сценарий | Поведение |
| --- | --- |
| Missing parser class | Seed entry становится inactive или получает validation diagnostics. |
| Parser не найден | `dataset_files.status = UNSUPPORTED_FORMAT`. |
| Binary PCAP/PCAPNG большой | Использовать `--packet-mode packet-summary` или `sample`; учитывать performance risk. |
| TEST labels в имени файла | Filename hints отключены для `TEST`. |
| Mixed schema CSV/JSON | Parser должен сохранять неизвестные поля в JSON payload и фиксировать warnings. |
| Partially corrupt file | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, counters должны показывать failed rows. |

## Проверка покрытия

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

Проверка сравнивает зарегистрированные `dataset_files` combinations с `parser_registry`. Ее нужно запускать после `catalog-ingest` и `seed-parser-registry`.


---

## Источник: `docs/ru/normalization/performance_tuning.md`

# Настройка производительности normalization

Документ описывает только реализованные runtime options из `scripts/stage_two/normalization/options.py` и `scripts/stage_two/cli.py`.

## Опции нормализации

| CLI option | Default | Назначение |
| --- | --- | --- |
| `--workers` | `STAGE_TWO_DEFAULT_WORKERS` (`1`) | Количество parallel worker processes для `normalize-format`/`normalize-all`. |
| `--batch-size` | `STAGE_TWO_DEFAULT_BATCH_SIZE` (`50000`) | Размер batch при parser batch processing. |
| `--max-output-part-rows` | `STAGE_TWO_MAX_OUTPUT_PART_ROWS` (`50000`) | Максимум rows в output part, если service делит output. |
| `--resume` | `false` | Пропускать уже успешно нормализованные files. |
| `--hash-output-artifacts` | `false` | Считать SHA-256 для output Parquet artifacts. |
| `--packet-mode` | `packet-summary` | Режим packet parsing: `packet-summary`, `dns-only`, `sample`. |
| `--sample-size` | unset | Обязателен для `--packet-mode sample`. |
| `--resource-profile` | unset | Optional preset: `safe`, `balanced`, `fast` или `aggressive`. |
| `--engine` | `cpu` | Допустимые значения: `cpu`, `gpu`, `auto`; raw Stage Two parsers все равно работают на CPU, пока не реализован отдельный parser-specific backend. |

Порядок resolution:

1. Стартовые значения берутся из constants в `config.py`.
2. Если указан `--resource-profile`, применяются значения profile.
3. Явные CLI overrides вроде `--workers` и `--batch-size` имеют приоритет над profile.
4. Для `normalize-format` и `benchmark-normalization` затем применяется format policy к тем значениям, которые пользователь явно не переопределил.

`normalize-all` получает общие runtime options из defaults/profile/explicit flags, но текущий CLI route не применяет per-format policy к каждой группе перед вызовом runner.

Пример:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 10000 \
  --workers 4 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --resume
```

## Выбор `--workers`

`--workers > 1` включает `ProcessPoolExecutor` в normalization runner. Это полезно для независимых файлов, но увеличивает:

- количество открытых DB connections;
- конкуренцию за диск;
- memory pressure при больших parser outputs;
- сложность диагностики parser errors.

Практический порядок:

1. Начать с `--workers 1 --limit 10`.
2. Проверить parser status, Parquet output и DuckDB checks.
3. Увеличивать workers постепенно.
4. Для binary PCAP/PCAPNG не повышать workers без контроля RAM/IO.

## Packet modes

| Mode | Когда использовать |
| --- | --- |
| `packet-summary` | Default для безопасного summary parsing packet captures. |
| `dns-only` | Когда нужен DNS extraction из packet captures и parser это поддерживает. |
| `sample` | Для первичной оценки больших PCAP/PCAPNG; требует `--sample-size`. |

Если `packet-mode = sample` и `sample-size` не задан, validation options выбросит ошибку.

## Разделение больших файлов

Для больших line-based files используйте:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Splitter поддерживает text/line formats и не предназначен для `cap`, `pcap`, `pcapng`, `bson`.

Риски:

- JSON arrays/objects могут быть небезопасны для line split;
- header handling нужно проверять через `--header auto|yes|no`;
- без `--register` chunks не появятся в catalog.

## Хеширование output artifacts

`--hash-output-artifacts` повышает проверяемость, но добавляет IO cost, потому что файл нужно прочитать после записи. Для smoke/iteration можно оставить выключенным; для финальных artifacts лучше включать.

## Resume

`--resume` пропускает файлы, для которых уже есть успешный normalized artifact. Это не заменяет data quality checks: после resume все равно нужно запускать:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

## Ограничения

- Performance options не должны менять contracts и labels.
- Нельзя объединять роли ради ускорения.
- Нельзя использовать `TEST` для подбора batch/feature/preprocessing решений, если это влияет на training pipeline.
- Для mixed CSV/JSON schemas лучше уменьшить batch size и сначала прогнать `--limit`.
## Обновление performance architecture

Stage Two теперь поддерживает resource profiles, format-specific policy, bounded multiprocessing, streaming parser batches, chunk-aware large-file processing, atomic Parquet writes, benchmark reports и post-run quality gates.

### Performance target

- Цель по датасету: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Целевая скорость для текущего железа: `10-20+ GB/hour` для line-based formats при нормальном состоянии RAM, PostgreSQL, SSD и parser errors.

Текущее железо:

- CPU: Intel Core i7-14700KF.
- RAM: 64 GB DDR5.
- Storage: Samsung M.2 SSD 2 TB.
- GPU: MSI GeForce RTX 5060 Ti 16 GB.

GPU зарезервирован для feature/model-ready/training layers. Raw normalization parsers по умолчанию работают на CPU; PCAP/BSON/raw log parsing не переносится на GPU без отдельного backend и проверок корректности.

### Resource profiles

Используйте `--resource-profile safe|balanced|fast|aggressive` с `normalize-format`, `normalize-all` и `benchmark-normalization`.

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size | hash_output_artifacts |
| --- | ---: | ---: | ---: | ---: | --- |
| `safe` | 4 | 50000 | 100000 | 50000 | false |
| `balanced` | 8 | 100000 | 250000 | 50000 | false |
| `fast` | 12 | 200000 | 500000 | 50000 | false |
| `aggressive` | 14 | 300000 | 750000 | 50000 | false |

CLI arguments имеют приоритет над profile. Пример: `--resource-profile fast --workers 6` дает `workers=6`, остальные параметры берутся из `fast`.

CLI печатает `resolved_runtime_settings` перед запуском normalization. Для `aggressive` warning является эксплуатационным предупреждением: контролируйте RAM, DB connections, parser failures и SSD throttling.

### Format policy

Если пользователь явно не указал runtime параметры, `normalize-format` и `benchmark-normalization` применяют format policy после profile resolution:

- быстрые line-based formats (`txt`, `sc`, `ghc`, log/syslog/messages/mainlog, `wls_day`, metric logs): больше workers и batch size;
- CSV / `pcap.csv` / NetFlow: умеренно высокие workers и большие batches;
- JSON / JSONL (`json`, `json-1`): умеренные workers и batches;
- BSON: низкое число workers;
- PCAP / PCAPNG / CAP: низкое число workers, `packet_batch_size=50000`, default `packet_mode=packet-summary`.

Явные CLI значения не перезаписываются policy. Для `normalize-all` с mixed/risky ready groups используйте conservative explicit settings или conservative profile.

### Рекомендуемый порядок

1. Готовить к запуску один точный bucket: `branch/role/source_format`.
2. Сначала benchmark на 5-10% данных: сначала `--dry-run`, затем небольшой actual run.
3. Начинать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки DuckDB, leakage, parser errors, RAM, DB connections и SSD.
5. Использовать `aggressive` только для line-based formats после чистых проверок.
6. Full run запускать с `--resume`.
7. После run запускать DuckDB, leakage и readiness checks.

### Команды

Benchmark 5-10%:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Split большого line-based файла:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Быстрая normalization для line-based формата:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

Post-run checks:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Для post-run DuckDB checks на машине с 64 GB RAM используйте bounded defaults или задайте их явно:

```powershell
$env:STAGE_TWO_DUCKDB_MEMORY_LIMIT="32GB"
$env:STAGE_TWO_DUCKDB_THREADS="2"
$env:STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE="100GB"
python manage.py stage-two run-duckdb-checks
```

Если DuckDB снова упирается в память, снизьте `STAGE_TWO_DUCKDB_MEMORY_LIMIT` до `8GB` и `STAGE_TWO_DUCKDB_THREADS` до `1`, оставив достаточное место под `PATH_DATA_STORAGE/temp_data/duckdb`.

### Safety invariants

- Raw files не изменяются.
- `TRAIN`, `VALIDATION`, `TEST` не смешиваются в catalog, Parquet paths, features и model-ready artifacts.
- `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается control plane; большие normalized/features/model-ready данные хранятся в Parquet.
- Labels и source/path/scenario/dataset role fields не попадают в model-ready X.
- Отсутствующий label не считается benign.
- Отсутствующий timestamp не заменяется текущим временем.
- Parser errors остаются явными: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.
- Traceability сохраняется по цепочке `raw -> normalized -> features -> model-ready`.

### Troubleshooting

| Симптом | Вероятная причина | Действие |
| --- | --- | --- |
| PostgreSQL timeout | слишком много workers или медленные catalog updates | уменьшить `--workers`, использовать `safe`, проверить DB locks/pool, перезапустить с `--resume` |
| too many DB connections | workers превышают capacity БД | ограничить workers до `4-8`, не использовать `aggressive`, проверить per-worker sessions |
| memory pressure | слишком большой batch/output part, binary parser load или DuckDB scan без spill headroom | уменьшить `--batch-size` и `--max-output-part-rows`; split для line-based files; для DuckDB снизить `STAGE_TWO_DUCKDB_MEMORY_LIMIT`/`STAGE_TWO_DUCKDB_THREADS` и проверить `temp_data/duckdb` |
| SSD throttling | слишком много concurrent writes или hashing | уменьшить workers, не включать `--hash-output-artifacts` на итерациях, проверить температуру SSD |
| too many small files | overhead futures/DB/filesystem | использовать bounded executor, запускать точный format bucket, держать `--resume` |
| parser errors | malformed rows или новая schema variant | читать parser run report и error samples; failed rows не скрывать |
| empty DuckDB views | нет Parquet, неверный `PATH_DATA_STORAGE` или failed normalization | выполнить `bootstrap-storage`, проверить artifact paths, запустить `run-duckdb-checks` |
| leakage critical | forbidden X columns или TEST contamination | заблокировать artifact use, проверить `run-leakage-checks`, пересобрать features/model-ready |


---

## Источник: `docs/ru/normalization/postgresql_catalog_schema.md`

# PostgreSQL Catalog и SQLAlchemy слой

PostgreSQL Catalog хранит metadata, статусы, связи, пути, хеши и отчеты Stage Two. Большие normalized/features/model-ready таблицы не пишутся в PostgreSQL: они сохраняются как Parquet в `PATH_DATA_STORAGE`, а catalog хранит только ссылки и агрегированную metadata.

## Где находится код

| Компонент | Путь |
| --- | --- |
| DB settings | `scripts/db/config.py` |
| Engine/session | `scripts/db/session.py` |
| Models | `scripts/db/models/*` |
| Constants/status values | `scripts/db/models/constants.py` |
| Repositories | `scripts/db/repositories/*` |
| Alembic migrations | `scripts/db/migrations/*` |
| Smoke check | `scripts/db/smoke_check.py` |

`session_scope()` создает SQLAlchemy session, делает `commit()` при успешном выходе и `rollback()` при исключении.

## Миграции и smoke check

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

Smoke check создает временные записи внутри транзакции и проверяет:

- unique/check constraints;
- создание `datasets`, `ingestion_runs`, `dataset_files`;
- parser run lifecycle;
- регистрацию normalized, feature, preprocessing, model-ready artifacts;
- запрет `TEST` для preprocessing fit;
- регистрацию quality report.

## Основные constraints

| Constraint group | Значения |
| --- | --- |
| branch | `dns`, `host`, `network`, `hybrid` |
| active dataset role | `TRAIN`, `VALIDATION`, `TEST` |
| DB role values | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| file status | `DISCOVERED`, `REGISTERED`, `CHANGED`, `EMPTY_FILE`, `UNSUPPORTED_FORMAT`, `READY_FOR_PARSING`, `PARSED`, `PARTIALLY_PARSED`, `FAILED`, `SKIPPED` |
| run status | `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED` |
| parser run status | `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED` |
| schema layer | `normalized`, `features`, `model_ready` |
| label status | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| quality severity | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

Catalog scanner Stage Two активирует только `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` существует как DB value, но не должен попадать в основной normalization pipeline.

## Таблицы

### `datasets`

Назначение: логическая группа файлов одного dataset/branch/role/source group.

Пишут: `CatalogIngestionService`, DB smoke check.  
Читают: normalization services, artifact registration, readiness checks.

Ключевые поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `root_path`, timestamps/metadata.

Связи: `datasets.id -> dataset_files.dataset_id`, `normalized_artifacts.dataset_id`, `feature_artifacts.dataset_id`.

### `ingestion_runs`

Назначение: запуск сканирования input tree.

Пишут: `CatalogIngestionService`.  
Читают: diagnostics/readiness.

Ключевые поля: `id`, `root_path`, `root_path_kind`, `branch`, `role`, counters, `status`, timestamps, error fields.

### `dataset_files`

Назначение: metadata raw/input файла, включая путь, размер, hash, role, branch, source_format и lifecycle status.

Пишут: catalog ingestion, large-file splitter при `--register`, status tools.  
Читают: parser resolver, normalization runners/services, readiness raw hash check.

Ключевые поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `role`, `branch`, `status`, `error_message`, `metadata_json`.

Статусы: `REGISTERED` после ingestion, `READY_FOR_PARSING` после `mark-ready`, `PARSED`/`PARTIALLY_PARSED`/`FAILED` после normalization, `UNSUPPORTED_FORMAT` при отсутствии parser.

### `parser_registry`

Назначение: declarative registry parser implementations.

Пишут: `ParserRegistrySeeder`.  
Читают: `ParserResolver`, normalization services, parser coverage, readiness.

Ключевые поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `priority`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `is_active`, `config_json`.

Resolver выбирает active parser по `branch/source_format`, role-specific entry или `supported_role IS NULL`, сортирует по `priority` и `id`.

### `schema_versions`

Назначение: catalog registry schema contracts.

Пишут: parser registry seed, repositories/smoke.  
Читают: parser runs, readiness, normalization.

Ключевые поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`.

### `parser_runs`

Назначение: один запуск parser для одного `dataset_files.id`.

Пишут: DNS/Host normalization services.  
Читают: artifact registration, traceability, readiness.

Ключевые поля: `file_id`, `parser_registry_id`, `schema_version_id`, `parser_name`, `parser_version`, `status`, counters (`rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`), `output_parquet_path`, error samples/timestamps.

Статусы: `RUNNING`, затем `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` или `SKIPPED`.

### `normalized_artifacts`

Назначение: metadata normalized Parquet artifact.

Пишут: `ParquetArtifactWriter.register_normalized_artifact()`.  
Читают: feature writer/registry services, DuckDB/readiness, traceability.

Ключевые поля: `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, `status`.

### `feature_artifacts`

Назначение: metadata feature Parquet artifact.

Пишут: `FeatureArtifactWriter.write_and_register()`.  
Читают: model-ready registry, leakage checks, readiness, traceability.

Ключевые поля: `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, `feature_schema_name`, `feature_schema_version`, `row_count`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `status`.

В production traceability `normalized_artifact_id` должен быть заполнен. Readiness check считает artifact без этой связи ошибкой.

### `preprocessing_artifacts`

Назначение: metadata scaler/encoder/other preprocessing objects.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact()`.  
Читают: model-ready registry, leakage checks/readiness.

Ключевые поля: `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, `schema_version`, `object_version`, `columns_json`, `params_json`, `status`.

Ограничение: `fitted_on_role` должен быть `TRAIN`. Код отклоняет `TEST`.

### `model_ready_artifacts`

Назначение: metadata model-ready X/y/sequence/split/preprocessing tables or files.

Пишут: `ModelReadyRegistryService.write_table_artifact()` и `register_external_artifact()`.  
Читают: leakage checks, traceability, readiness.

Ключевые поля: `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, `schema_name`, `schema_version`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `sequence_length`, `status`.

`data_type` поддерживает `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`. Для `X` registry validates forbidden leakage columns.

### `label_mapping_rules`

Назначение: explicit/external rules для label resolver.

Пишут: `LabelRepository` или конфигурационные загрузчики, если используются в сценарии.  
Читают: `LabelResolver`.

Ключевые поля: branch/role/source_format matching, pattern/rule payload, canonical label fields, confidence/status, active flag.

Правило: отсутствие matching label rule не означает benign; событие остается unlabeled.

### `data_quality_reports`

Назначение: metadata quality/leakage/DuckDB reports.

Пишут: `DuckDBAnalyticsService.register_report()`, `DataQualityChecker`, `LeakageChecker`, smoke/e2e checks.  
Читают: readiness, audit/reporting.

Ключевые поля: `check_group`, `artifact_type`, `artifact_id`, `status`, `severity`, `report_path`, `summary_json`, `metrics_json`, `violations_json`.

`CRITICAL` используется для leakage нарушений, которые могут сделать model-ready artifact непригодным.

## Traceability chain

Полная цепочка для model-ready artifact:

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

Если любой обязательный link отсутствует, `TraceabilityService` возвращает ошибку, а readiness check помечает traceability как `FAILED`.


---

## Источник: `docs/ru/normalization/README.md`

# Stage Two / нормализация данных

Раздел описывает фактическую реализацию Stage Two: catalog ingestion, parser registry, нормализацию DNS/Host файлов в normalized events, запись Parquet artifacts, PostgreSQL Catalog, DuckDB/data quality/leakage checks и traceability. Документы предназначены для разработчика, который должен запускать pipeline, добавлять parser implementations и проверять, что данные не смешивают роли и не создают leakage.

## Границы Stage Two

Stage Two начинается после Stage One, когда исходные файлы уже разложены в sorted/filter tree. Raw-файлы не изменяются: Stage Two читает их, регистрирует metadata в PostgreSQL и создает новые артефакты в `PATH_DATA_STORAGE`.

Фактически реализованные части:

| Область | Реализация | Документ |
| --- | --- | --- |
| CLI/routing | `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py` | [usage_guide.md](ru/normalization/usage_guide.md), [stage_two_commands.md](ru/normalization/stage_two_commands.md) |
| Storage bootstrap | `scripts/stage_two/storage/bootstrap.py` | [storage_architecture.md](ru/normalization/storage_architecture.md) |
| Catalog ingestion | `scripts/stage_two/ingestion/*` | [postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) |
| Parser registry/resolver | `scripts/stage_two/parser_registry/*` | [parser_strategy.md](ru/normalization/parser_strategy.md) |
| Parser development | `scripts/stage_two/parsers/*` | [parser_development_guide.md](ru/normalization/parser_development_guide.md) |
| Label resolver | `scripts/stage_two/labels/resolver.py` | [label_resolver.md](ru/normalization/label_resolver.md) |
| Normalized schema | `schemas/normalized/normalized_event_v1.json` | [normalized_event_schema.md](ru/normalization/normalized_event_schema.md) |
| Parquet/DuckDB | `scripts/stage_two/parquet/*`, `scripts/stage_two/duckdb/*` | [parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md) |
| Quality checks | `scripts/stage_two/quality/checkers.py` | [data_quality_checks.md](ru/normalization/data_quality_checks.md) |
| Leakage prevention | feature/model-ready contracts, `LeakageChecker` | [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md) |
| Traceability | `scripts/stage_two/traceability/service.py` | [traceability.md](ru/normalization/traceability.md) |
| Performance/runbooks | normalization options, large-file split, recovery steps | [performance_tuning.md](ru/normalization/performance_tuning.md), [runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) |

Не реализовано как отдельная CLI-команда в текущем роутере: полноценный build step для feature artifacts и model-ready artifacts. Для них есть contracts, writers/registry services и e2e dry-run, но operational CLI сейчас покрывает catalog, parser readiness, normalization, DuckDB checks, leakage checks и traceability.

## Рекомендуемый порядок чтения

1. [usage_guide.md](ru/normalization/usage_guide.md) - как запустить Stage Two и какие команды реально поддерживает CLI.
2. [stage_two_commands.md](ru/normalization/stage_two_commands.md) - полный reference по командам normalization: входы, выходы, статусы, ошибки и проверки.
3. [storage_architecture.md](ru/normalization/storage_architecture.md) - что должно быть в `PATH_DATA_STORAGE`.
4. [postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) - какие metadata и связи хранятся в PostgreSQL.
5. [parser_strategy.md](ru/normalization/parser_strategy.md) и [parser_development_guide.md](ru/normalization/parser_development_guide.md) - как выбирается parser и как добавить новый.
6. [normalized_event_schema.md](ru/normalization/normalized_event_schema.md) и [label_resolver.md](ru/normalization/label_resolver.md) - контракт normalized event и правила labels.
7. [parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md), [data_quality_checks.md](ru/normalization/data_quality_checks.md), [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md), [traceability.md](ru/normalization/traceability.md) - артефакты, проверки и lineage.
8. [performance_tuning.md](ru/normalization/performance_tuning.md), [runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md), [final_summary_template.md](ru/normalization/final_summary_template.md) - эксплуатация, восстановление и итоговая отчетность.

## Основные инварианты

1. Raw-файлы датасетов не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются в одном normalized/feature/model-ready artifact.
3. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или feature selection.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты; большие normalized/features/model-ready таблицы хранятся в Parquet.
5. DuckDB используется для аналитических SQL-проверок поверх Parquet.
6. Labels хранятся отдельно от X-признаков.
7. Leakage/source/label поля не должны попадать в model-ready `X` artifacts.
8. Все артефакты должны сохранять traceability: `raw -> normalized -> features -> model-ready`.
9. Отсутствующий label не означает benign.
10. Filename heuristics для `TEST` labels отключены.
11. Отсутствующий timestamp нельзя заменять текущим временем; нужно сохранять `timestamp = null` и `timestamp_type = "missing"` либо `event_order`, если доступен порядок события.

## Основные команды

Все команды проходят через `manage.py`:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage [dns|host|network|hybrid]
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two split-large-files --branch host --role TRAIN --format csv --max-part-size-mb 512 --apply --register
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Миграции и модульные проверки запускаются отдельно:

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

## Pipeline

```mermaid
flowchart TD
    A["Stage One sorted/filter tree"] --> B["catalog-ingest"]
    B --> C["datasets, ingestion_runs, dataset_files"]
    C --> D["seed-parser-registry"]
    D --> E["parser-coverage / mark-ready"]
    E --> F["normalize-format / normalize-all / normalize-dns / normalize-host"]
    F --> G["parser_runs"]
    F --> H["parquet/normalized/..."]
    G --> I["normalized_artifacts"]
    H --> J["DuckDB views and checks"]
    I --> K["feature/model-ready contracts and registry services"]
    K --> L["feature_artifacts / model_ready_artifacts"]
    L --> M["leakage checks"]
    L --> N["trace-artifact"]
```

## Терминология

| Термин | Значение |
| --- | --- |
| branch | Модальность или ветка данных: `dns`, `host`, `network`, `hybrid`. Нормализация сейчас поддерживает `dns` и `host`. |
| role | Split датасета: `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` есть в DB constraint, но catalog scanner Stage Two активирует только `TRAIN/VALIDATION/TEST`. |
| source_format | Формат исходного файла: `csv`, `pcap`, `pcap.csv`, `json`, `txt`, `bson`, `auth.log`, `netflow_day` и т.д. |
| normalized event | Одна нормализованная запись по контракту `normalized_event/v1`. |
| parser run | Запуск parser для одного `dataset_files.id`. |
| artifact | Parquet или внешний файл, зарегистрированный в catalog metadata. |


---

## Источник: `docs/ru/normalization/runtime_resource_runbook.md`

# Runbook по runtime-ресурсам

Runbook описывает диагностику Stage Two normalization без изменения raw files.

## Быстрый чеклист статуса

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Если `readiness_check` долго идет или растет RAM на этапе raw hashes, запустите с явными streaming settings:

```powershell
$env:STAGE_TWO_READINESS_DB_YIELD_PER="1000"
$env:STAGE_TWO_READINESS_HASH_CHUNK_BYTES="1048576"
python -m scripts.stage_two.readiness_check
```

Эти настройки не увеличивают качество проверки, а ограничивают форму чтения: catalog rows идут streaming batches, raw files читаются блоками по 1 MiB.

## Если storage не готов

Симптомы:

- `PATH_DATA_STORAGE must be configured`;
- отсутствующие директории в readiness report;
- DuckDB views пустые из-за отсутствующих Parquet roots.

Действия:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
python manage.py stage-two bootstrap-storage
python -m scripts.stage_two.readiness_check
```

## Если catalog пустой

Симптомы:

- `catalog_counts.dataset_files = 0`;
- `parser-coverage` нечего проверять;
- `mark-ready` не находит files.

Действия:

```bash
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

Проверьте, что input tree содержит `TRAIN`, `VALIDATION`, `TEST`; scanner не активирует произвольные роли.

## Если parser отсутствует

Симптомы:

- `UNSUPPORTED_FORMAT`;
- `parser-coverage` показывает uncovered combination;
- `normalize-format` не создает normalized artifact.

Действия:

1. Проверить `branch/role/source_format` в `dataset_files`.
2. Проверить `parser_registry` после `seed-parser-registry`.
3. Добавить parser class или registry entry.
4. Перезапустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
```

## Если normalization падает

Действия:

```bash
python manage.py stage-two normalize-format \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --limit 10 \
  --workers 1
```

После ошибки проверить:

- `parser_runs.status`, counters, error samples;
- `dataset_files.status` и `error_message`;
- parser-specific warnings;
- schema mismatch report;
- размер файла и необходимость `split-large-files`.

Для больших line-based files:

```bash
python manage.py stage-two split-large-files \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --max-part-size-mb 512 \
  --apply \
  --register
```

## Если проверки DuckDB завершились ошибкой

Проверить:

- существуют ли Parquet files под `PATH_DATA_STORAGE/parquet`;
- совпадают ли paths в catalog и на диске;
- есть ли required columns;
- не смешаны ли roles;
- не записаны ли пустые artifacts вместо ошибок parser.

Если `run-duckdb-checks` забивает RAM или система завершает процессы:

1. Убедиться, что используется обновленная команда с bounded DuckDB settings.
2. Убедиться, что команда не застряла на `CREATE VIEW normalized_all`: обновленная реализация должна показывать `scanning normalized_all ...`, потому что большие слои проверяются через Parquet metadata, а не через единый DuckDB view.
3. Начать с консервативного лимита:

```powershell
$env:STAGE_TWO_DUCKDB_MEMORY_LIMIT="8GB"
$env:STAGE_TWO_DUCKDB_THREADS="1"
$env:STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE="150GB"
python manage.py stage-two run-duckdb-checks
```

4. Проверить свободное место в `PATH_DATA_STORAGE/temp_data/duckdb`, потому что при `memory_limit` DuckDB может spill-ить промежуточные данные на диск.
5. Если run проходит, увеличить `STAGE_TWO_DUCKDB_THREADS` до `2`; не поднимать memory limit выше безопасного headroom для ОС и PostgreSQL.

Запуск:

```bash
python manage.py stage-two run-duckdb-checks
```

## Если leakage checks завершились ошибкой

Проверить:

- model-ready `X` не содержит forbidden columns;
- preprocessing artifacts имеют `fitted_on_role = TRAIN`;
- `TEST` не используется в training context;
- unlabeled events не превращены в benign.

Запуск:

```bash
python manage.py stage-two run-leakage-checks
```

CRITICAL leakage report должен блокировать использование artifact.

## Если traceability chain разорвана

Запуск:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
python -m scripts.stage_two.readiness_check
```

Проверить links:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset
```

Если `feature_artifact_id` или `normalized_artifact_id` отсутствует, artifact нельзя считать полностью traceable.

## Несовпадение raw hash

Readiness check пересчитывает hashes для `dataset_files.file_path`. Mismatch означает, что raw file изменился после ingestion или catalog указывает не на тот файл.

Действия:

1. Не перезаписывать catalog вручную без audit.
2. Проверить source path и backup.
3. Повторить `catalog-ingest`, если raw tree официально обновлен.
4. Пересобрать downstream artifacts, потому что normalized/features/model-ready могли быть созданы из старого содержимого.
## Performance runbook для текущего железа

Целевое железо:

- Intel Core i7-14700KF.
- 64 GB DDR5 RAM.
- Samsung M.2 SSD 2 TB.
- MSI GeForce RTX 5060 Ti 16 GB.

Raw normalization ориентирована на CPU. GPU по умолчанию не используется для raw parsers; оставляйте GPU для feature/model-ready/training layers, пока нет отдельного parser backend с проверенной корректностью.

### Цель

- Full Stage Two normalization target: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Ожидаемый target для line-based formats на этом железе: `10-20+ GB/hour` после benchmark validation.

### Безопасный порядок запуска

1. Проверить parser coverage и подготовить один точный bucket.
2. Запустить `benchmark-normalization` на 5-10% файлов.
3. Начать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки parser reports, DuckDB checks, leakage checks, RAM, DB connections и SSD write behavior.
5. Использовать `aggressive` только для line-based formats после чистого `fast` run.
6. Full bucket запускать с `--resume`.
7. Запустить post-run gates:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

### Примеры команд

Benchmark:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Line-based full run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP safe run:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON safe run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

### Troubleshooting performance runs

| Проблема | Что проверить | Recovery |
| --- | --- | --- |
| PostgreSQL timeout | long transactions, locks, slow catalog writes | уменьшить `--workers`, использовать `safe`, перезапустить с `--resume` |
| too many DB connections | process workers vs DB pool size | ограничить workers до `4-8`, не использовать `aggressive`, проверить worker-local sessions |
| memory pressure | batch size, output part rows, binary formats | уменьшить `--batch-size`, уменьшить `--max-output-part-rows`, split для line-based files |
| SSD throttling | high concurrent writes, temperature, hashing | уменьшить workers, отключить output hashing на итерациях, разделить большие buckets |
| too many small files | scheduler и catalog overhead | использовать bounded execution, группировать exact format, избегать mixed all-branch runs |
| parser errors | parser run reports, error samples, malformed rows | исправить parser/schema handling; не считать malformed rows успешными silently |
| empty DuckDB views | нет Parquet roots или неверный storage path | проверить `PATH_DATA_STORAGE`, artifact paths и `run-duckdb-checks` report |
| leakage critical | forbidden X columns или TEST в training artifacts | остановить training use, проверить leakage report, пересобрать feature/model-ready artifacts |

### Safety rules

- Не изменять raw dataset files.
- Не смешивать `TRAIN`, `VALIDATION`, `TEST`.
- Не использовать `TEST` для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается catalog/control plane, Parquet хранит большие данные.
- Labels и path/source/scenario fields не попадают в model-ready X.
- Missing labels не считаются benign.
- Missing timestamps не заменяются current time.
- Traceability сохраняется от raw file до normalized, features и model-ready artifacts.


---

## Источник: `docs/ru/normalization/stage_two_commands.md`

# Команды Stage Two normalization

Документ описывает реализованные команды Stage Two normalization и операционный порядок запуска. Источники проверки: `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py`, сервисы `scripts/stage_two/*` и файл `stage_two_dns_host_normalization_commands.txt`.

Главная точка входа:

```bash
python manage.py stage-two <command> [args]
```

`manage.py` принимает `module`, `service`, `action`, `extra_args`; `scripts/router_script.py` направляет `module=stage-two` в `scripts.stage_two.cli.router_stage_two()`. Неизвестная Stage Two команда возвращает ошибку `unknown Stage Two command`.

Сверка с кодом от 2026-07-04: fallback-текст из `config.manage_commands` не является полным help по Stage Two. В нем нет части новых router-команд, включая `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization` и `split-large-files`. Источник истины по реализованным Stage Two командам - `scripts/stage_two/cli.py`.

## Полный порядок запуска

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage

# Операционный шаг: выбрать bucket и подготовить только нужный branch/role/format.
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply

# Опциональный benchmark перед полным запуском.
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run

# Основной точный запуск для production/runbook.
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100 --workers 1 --resume

# Legacy shortcuts, если нужен запуск всех ready DNS или Host файлов.
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10

python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

`TRAIN`, `VALIDATION` и `TEST` запускаются отдельными bucket-командами или через `normalize-all`, который группирует работу по `role/source_format`. `TEST` не используется для обучения, fit preprocessing, scaler/encoder fit, feature selection или threshold tuning.

## Команды и операционные шаги

| Шаг | Команда | Реализовано в CLI | Назначение |
| --- | --- | --- | --- |
| 1 | `bootstrap-storage` | Да | Создать обязательное дерево `PATH_DATA_STORAGE`. |
| 2 | `catalog-ingest` | Да | Зарегистрировать Stage One filtered/sorted files в PostgreSQL Catalog. |
| 3 | `seed-parser-registry` | Да | Загрузить schema/parser metadata из seed-файла. |
| 4 | `parser-coverage [branch]` | Да | Проверить покрытие parser registry для catalog buckets. |
| 5 | `mark-ready` | Да | Перевести выбранные файлы в `READY_FOR_PARSING`. |
| 6 | `split-large-files` | Да | Разбить большие line-based ready files на chunks. |
| 7 | `normalize-format` | Да | Нормализовать один `branch/role/source_format`. |
| 8 | `normalize-all` | Да | Нормализовать все ready buckets внутри одной ветки `dns` или `host`. |
| 9 | `benchmark-normalization` | Да | Измерить скорость одного точного bucket `branch/role/source_format` и оценить throughput. |
| 10 | `normalize-dns [limit]` | Да | Legacy shortcut для DNS files со статусом `READY_FOR_PARSING`. |
| 11 | `normalize-host [limit]` | Да | Legacy shortcut для Host files со статусом `READY_FOR_PARSING`. |
| 12 | `run-duckdb-checks` | Да | Создать DuckDB views и записать analytics report. |
| 13 | `run-leakage-checks` | Да | Проверить model-ready/feature contracts на leakage. |
| 14 | `trace-artifact` | Да | Восстановить lineage для model-ready artifact. |
| - | `readiness_check`, `e2e_dry_run` | Нет как `manage.py stage-two` | Запускаются как Python modules. |

## `bootstrap-storage`

```bash
python manage.py stage-two bootstrap-storage
```

**Что делает:** идемпотентно создает обязательные директории Stage Two в `PATH_DATA_STORAGE`: `postgres/`, `pgadmin/`, `parquet/normalized/`, `parquet/features/`, `parquet/model_ready/`, `duckdb/sql/`, `duckdb/exports/`, `logs/stage-two/`, `backups/`, `temp_data/`, `schemas/`, `reports/ru/stage-two/`, `reports/en/stage-two/`, `config/`.

**Когда запускать:** один раз при подготовке окружения и повторно после изменения storage contract. Повторный запуск не удаляет существующие файлы.

**Входные данные:** переменная `PATH_DATA_STORAGE`.

**Артефакты:** директории под storage root. Parquet и отчеты на этом шаге не создаются.

**PostgreSQL:** не читает и не пишет таблицы.

**Возможные ошибки:** `PATH_DATA_STORAGE must be configured before bootstrapping storage`, отказ доступа к директории.

**Проверка успеха:** CLI выводит `root`, `created_count`, `existing_count`; директории существуют на диске.

## `catalog-ingest`

```bash
python manage.py stage-two catalog-ingest
```

**Что делает:** сканирует `PATH_FOLDER_DATASETS_FILTER`, определяет `branch`, `role`, `source_format`, считает размер, mtime и SHA-256, затем регистрирует datasets/files в PostgreSQL Catalog. Raw-файлы не изменяются.

**Когда запускать:** после Stage One sorted/filter tree и после появления новых или измененных файлов.

**Входные данные:** `PATH_FOLDER_DATASETS_FILTER`, доступная БД, примененные Alembic migrations.

**Артефакты:** внешних Parquet artifacts не создает.

**PostgreSQL:** пишет `ingestion_runs`, `datasets`, `dataset_files`. Новые поддержанные непустые файлы получают `REGISTERED`; пустые - `EMPTY_FILE`; неподдержанные scanner-форматы - `UNSUPPORTED_FORMAT`; измененные файлы учитываются в счетчике `files_changed`.

**Возможные ошибки:** отсутствует `PATH_FOLDER_DATASETS_FILTER`, нет подключения к БД, ошибка чтения файла, ошибка hash/stat.

**Проверка успеха:** CLI выводит `run_count` и список runs со статусом `SUCCESS` или `PARTIAL_SUCCESS`; в `dataset_files` появились строки по нужным `branch/role/source_format`.

## `seed-parser-registry`

```bash
python manage.py stage-two seed-parser-registry
```

**Что делает:** загружает schema metadata и parser registry entries из `scripts/stage_two/parser_registry/parser_registry_seed.json`.

**Когда запускать:** после миграций и перед `mark-ready`/normalization. Повторный запуск обновляет существующие registry entries.

**Входные данные:** seed JSON, доступные parser classes в `scripts/stage_two/parsers/*`, подключение к БД.

**Артефакты:** файловых artifacts не создает.

**PostgreSQL:** пишет/обновляет `schema_versions` и `parser_registry`.

**Возможные ошибки:** невалидный seed, отсутствующий parser module/class, ошибка БД.

**Проверка успеха:** CLI выводит `schema_version_id`, `inserted`, `updated`; `parser-coverage` показывает `parser_active=yes` для поддержанных buckets.

## `parser-coverage`

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

**Что делает:** строит матрицу `branch/role/source_format` по catalog counts и `parser_registry`, проверяет, найден ли активный parser и доступен ли parser class.

**Когда запускать:** после `catalog-ingest` и `seed-parser-registry`, а также перед массовым `mark-ready`.

**Входные данные:** `dataset_files`, `datasets`, `parser_registry`, Stage One path JSON только для diagnostics.

**Артефакты:** parser coverage reports через `scripts.stage_two.reports.parser_reports`.

**PostgreSQL:** читает `datasets`, `dataset_files`, `parser_registry`; статусы файлов не меняет.

**Возможные ошибки:** неизвестный branch, невалидный parser class, пустой catalog, расхождение catalog и registry.

**Проверка успеха:** итоговый payload имеет `status=SUCCESS`; строки с реальными файлами имеют `parser_active=yes`. Если `catalog_gap_rows` или `missing_parser_rows` больше нуля, сначала исправить registry/parser coverage.

## Операционный шаг `READY_FOR_PARSING`

Подготовка к `READY_FOR_PARSING` реализована командой `mark-ready`. Если команда не используется, тот же переход остается ручным catalog operation и должен выполняться только после проверки parser coverage.

```bash
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --apply
```

Компактная форма:

```bash
python manage.py stage-two mark-ready dry-run:host:TRAIN:csv
python manage.py stage-two mark-ready apply:host:TRAIN:csv
```

**Что делает:** выбирает файлы активного source group по точному `branch/role/source_format`, проверяет parser resolver и переводит eligible rows в `READY_FOR_PARSING`.

**Когда запускать:** после `parser-coverage`, отдельно для каждого нужного bucket. Сначала `--dry-run`, затем `--apply`.

**Входные данные:** `--branch`, `--role`, `--format`; parser registry entry для bucket.

**Артефакты:** JSON/Markdown reports в `reports/{ru,en}/stage-two/status/`, если настроен `PATH_DATA_STORAGE`.

**PostgreSQL:** читает `datasets`, `dataset_files`, `parser_registry`; меняет `dataset_files.status` на `READY_FOR_PARSING` только для eligible files. По умолчанию eligible statuses: `REGISTERED`, `CHANGED`, `DISCOVERED`. С `--retry-failed` eligible statuses: `FAILED`, `SKIPPED`, `PARTIALLY_PARSED`.

**Возможные ошибки:** отсутствует parser (`UNSUPPORTED_FORMAT`), неверный role, одновременные `--dry-run` и `--apply`, пустой `--format`, неподходящие текущие статусы (`PARSED`, `EMPTY_FILE`, `READY_FOR_PARSING` и т.д.).

**Проверка успеха:** `dry_run=false`, `status=SUCCESS`, `updated > 0`; report показывает переходы `<previous_status> -> READY_FOR_PARSING`.

## `split-large-files`

```bash
python manage.py stage-two split-large-files \
  --branch dns \
  --role TEST \
  --format csv \
  --limit 1 \
  --max-part-size-gb 2 \
  --min-size-gb 1 \
  --header no \
  --apply \
  --register
```

**Что делает:** делит большие line-based файлы со статусом `READY_FOR_PARSING` на chunks. Поддержанные форматы включают `csv`, `pcap.csv`, `txt`, `json`, `json-1`, log formats, `ghc`, `sc`, `netflow_day`, `netflow_ids`, `wls_day` и metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) этим splitter не делятся.

**Когда запускать:** перед `normalize-format`, если один файл слишком большой для доступной RAM/времени. Для DNS TEST csv из runbook используется `--header no`.

**Входные данные:** готовые catalog rows (`READY_FOR_PARSING`), исходный файл на диске, параметры размера part.

**Артефакты:** chunk files под `PATH_FOLDER_DATASETS_FILTER/chunked/...`.

**PostgreSQL:** при `--register` регистрирует chunks в `dataset_files` со статусом `READY_FOR_PARSING`; исходный файл может быть переведен в `SKIPPED`, если не указан `--keep-source-ready`.

**Возможные ошибки:** `--register` без `--apply`, unsupported binary format, исходный файл отсутствует, output dir уже существует без `--overwrite`, неверный `--header`.

**Проверка успеха:** CLI выводит `status=SUCCESS`, `chunks_created > 0`, `registered > 0`; `normalize-format` затем выбирает chunks, а не исходный большой файл.

## `normalize-format`

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format csv \
  --limit 100 \
  --workers 1 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --packet-mode packet-summary \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-format host:TRAIN:csv:100
```

**Что делает:** выбирает `dataset_files.status=READY_FOR_PARSING` для одного `branch/role/source_format`, разрешает parser через registry, запускает DNS или Host normalization service, пишет normalized Parquet parts и регистрирует artifacts.

**Когда запускать:** основной рекомендуемый способ нормализации, особенно для runbook из `stage_two_dns_host_normalization_commands.txt`, потому что он явно фиксирует branch, role и format.

**Входные данные:** ready files, parser registry entry, normalized schema version, raw file path, storage root.

**Артефакты:** normalized Parquet:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Также создаются parser run reports в `reports/{ru,en}/stage-two/parser/`.

**PostgreSQL:** читает `dataset_files`, `datasets`, `parser_registry`, `schema_versions`; пишет `parser_runs`, `normalized_artifacts`; обновляет `dataset_files.status` на `PARSED`, `PARTIALLY_PARSED`, `FAILED` или `UNSUPPORTED_FORMAT`.

**Возможные ошибки:** нет parser, parser class не импортируется, файл отсутствует, ошибка парсинга, нехватка памяти, неверные числовые параметры, `packet_mode` не поддержан конкретным parser.

**Проверка успеха:** CLI выводит `status=SUCCESS`, `parsed + partially_parsed > 0`, `failed=0`, `unsupported=0`; Parquet files существуют; `normalized_artifacts` содержит paths; `parser_runs.status` не `FAILED`.

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch host \
  --limit 1000 \
  --workers 2 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-all host:1000
```

**Что делает:** обходит ready groups внутри одной branch и вызывает `normalize-format` по каждой группе `role/source_format`.

**Когда запускать:** когда parser coverage проверен и нужно обработать несколько ready buckets внутри `dns` или `host`.

**Входные данные:** `--branch dns|host`, ready files.

**Артефакты:** те же, что у `normalize-format`, но по нескольким группам.

**PostgreSQL:** те же таблицы, что у `normalize-format`; роли не смешиваются, потому что каждая группа запускается отдельно.

**Возможные ошибки:** частичный failure одного bucket дает общий `PARTIAL_SUCCESS`; неподдержанный parser приводит к `UNSUPPORTED_FORMAT` для соответствующей группы.

**Проверка успеха:** `groups_count > 0`, `status=SUCCESS`; каждая group summary имеет `failed=0`, `unsupported=0`.

## `normalize-dns` и `normalize-host`

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

**Что делает:** legacy shortcut. Выбирает files со статусом `READY_FOR_PARSING` для `branch=dns` или `branch=host` и запускает соответствующий normalization service. Единственный позиционный аргумент - optional non-negative integer `limit`.

**Когда запускать:** для быстрой проверки или обратной совместимости. Для воспроизводимых batch-запусков предпочтительнее `normalize-format`, потому что там явно указан `role/source_format` и доступны performance options.

**Входные данные:** ready files выбранной ветки.

**Артефакты:** normalized Parquet и catalog records как у `normalize-format`.

**PostgreSQL:** пишет `parser_runs`, `normalized_artifacts`; обновляет `dataset_files.status`.

**Возможные ошибки:** больше одного аргумента, нечисловой limit, parser/file errors.

**Проверка успеха:** CLI выводит `files_seen`, `normalized`, `skipped`; для полного контроля дополнительно проверить `parser_runs` и `normalized_artifacts`.

## `run-duckdb-checks`

```bash
python manage.py stage-two run-duckdb-checks
```

**Что делает:** выполняет analytics checks поверх Parquet: row counts, missing required columns, split contamination, schema mismatch. Для больших слоев не строит единый DuckDB view по glob pattern; row counts/schema читаются потоково из Parquet metadata, а data-level проверки запускаются chunked.

**Когда запускать:** после нормализации и после появления feature/model-ready artifacts.

**Входные данные:** `PATH_DATA_STORAGE`, Parquet layers, DuckDB package.

**Runtime limits:** команда ограничивает DuckDB через `STAGE_TWO_DUCKDB_MEMORY_LIMIT` (default `32GB`), `STAGE_TWO_DUCKDB_THREADS` (default `2`) и `STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE` (default `100GB`). Временные spill files пишутся в `PATH_DATA_STORAGE/temp_data/duckdb`.

**Артефакты:** JSON report `reports/en/stage-two/quality/duckdb_analytics_report.json`; DuckDB database path из storage config.

**PostgreSQL:** пишет aggregate report в `data_quality_reports` с `check_group=duckdb`, severity `INFO` или `ERROR`.

**Возможные ошибки:** `PATH_DATA_STORAGE` не задан, DuckDB не установлен, Parquet files отсутствуют или имеют несовместимые схемы, spill directory не имеет свободного места.

**Проверка успеха:** CLI показывает progress bar и выводит `status=SUCCESS`, `check_count`, `catalog_report_id`; report не содержит failed checks.

## `run-leakage-checks`

```bash
python manage.py stage-two run-leakage-checks
```

**Что делает:** проверяет leakage rules поверх DuckDB views и catalog context. Критичные правила включают запрет label/source/trace fields в model-ready X artifacts и запрет `TEST` rows в training artifacts.

**Когда запускать:** после сборки feature/model-ready artifacts и перед использованием данных для обучения.

**Входные данные:** Parquet `features`/`model_ready`, DuckDB views, catalog metadata. Используются те же DuckDB runtime limits, что и для `run-duckdb-checks`.

**Артефакты:** leakage reports в `reports/{ru,en}/stage-two/leakage/`.

**PostgreSQL:** пишет `data_quality_reports` с `check_group=leakage`; failed leakage checks получают severity `CRITICAL`.

**Возможные ошибки:** пустые model-ready views, forbidden X columns, `TEST` contamination, несогласованные роли в artifact paths/columns.

**Проверка успеха:** CLI показывает progress bar и выводит `status=SUCCESS`, severity не `CRITICAL`, `check_count`; report не содержит failed leakage checks.

## `trace-artifact`

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

**Что делает:** восстанавливает цепочку lineage для model-ready artifact. Числовой аргумент трактуется как `model_ready_artifacts.id`, строковый - как `model_ready_artifacts.artifact_path`.

**Когда запускать:** после создания model-ready artifacts или при расследовании качества/утечки.

**Входные данные:** id или path model-ready artifact.

**Артефакты:** файлов не создает; печатает JSON trace chain в stdout.

**PostgreSQL:** читает цепочку:

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

**Возможные ошибки:** artifact не найден, отсутствует `feature_artifact_id`, отсутствует `normalized_artifact_id`, разорванная catalog chain.

**Проверка успеха:** команда печатает JSON с dataset, source file, parser run, normalized artifact, feature artifact и model-ready artifact.

## Команды из операционного runbook

`stage_two_dns_host_normalization_commands.txt` содержит практические batch-команды для оставшихся DNS/Host форматов. Они соответствуют реализованным CLI-командам:

- `mark-ready --dry-run/--apply` для каждого `branch/role/source_format`;
- `split-large-files` для больших line-based files;
- `normalize-format` с `--workers`, `--batch-size`, `--max-output-part-rows`, `--packet-mode`, `--sample-size`, `--resume`;
- `parser-coverage`, `run-duckdb-checks`, `run-leakage-checks` как проверки после запуска.

Файл содержит Windows-specific команды `cd` и `conda activate`; они являются инструкциями окружения, а не частью CLI проекта. Команда `python -m scripts.stage_two.readiness_check` реализована как module check, но не зарегистрирована в `router_stage_two`.

## Инварианты запуска

1. Raw-файлы не изменяются; Stage Two создает metadata и новые artifacts.
2. `TRAIN`, `VALIDATION`, `TEST` обрабатываются отдельными bucket-командами.
3. `TEST` не участвует в fit/training/tuning.
4. Labels не являются X features.
5. Отсутствующий label не означает benign.
6. Отсутствующий timestamp нельзя заменять текущим временем.
7. Все artifacts должны сохранять traceability `raw -> normalized -> features -> model-ready`.
## Performance commands и profiles

Текущий CLI также включает `benchmark-normalization` и resource profiles для `normalize-format` / `normalize-all`.

### `benchmark-normalization`

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Поддерживаемые options:

- `--branch`;
- `--role`;
- `--format`;
- `--limit`;
- `--sample-ratio`;
- `--resource-profile`;
- `--workers`;
- `--batch-size`;
- `--max-output-part-rows`;
- `--resume`;
- `--dry-run`.

Report содержит `input_bytes`, `processed_bytes`, `processed_gb`, `elapsed_seconds`, `gb_per_hour`, rates по files/rows/events, failed/partial/skipped/unsupported files, Parquet output size, average parser/write time, `estimated_time_for_17gb` и `meets_3_hour_target`.

Actual benchmark run включает safe resume behavior, если не указан `--dry-run`; повторный benchmark не должен создавать дубли successful normalized artifacts.

### Resource profiles

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size |
| --- | ---: | ---: | ---: | ---: |
| `safe` | 4 | 50000 | 100000 | 50000 |
| `balanced` | 8 | 100000 | 250000 | 50000 |
| `fast` | 12 | 200000 | 500000 | 50000 |
| `aggressive` | 14 | 300000 | 750000 | 50000 |

CLI overrides имеют приоритет над profile и format policy. Пример:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --workers 6 \
  --resume
```

Итог: `workers=6`, остальные значения берутся из `fast`, если format policy не ограничит рискованный формат.

### Безопасные PCAP/BSON примеры

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume

python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

### Большие line-based files

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Не делите `cap`, `pcap`, `pcapng` или `bson` обычным line splitter.

### Обязательные gates после performance runs

`normalize-format` сохраняет post-run validation summary. После performance runs также запускайте:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Если `run-leakage-checks` возвращает CRITICAL, не используйте затронутые feature/model-ready artifacts.


---

## Источник: `docs/ru/normalization/storage_architecture.md`

# Архитектура storage Stage Two

Stage Two хранит большие данные вне PostgreSQL. Корень задается переменной `PATH_DATA_STORAGE`, а `bootstrap-storage` создает обязательную структуру директорий через `scripts/stage_two/storage/bootstrap.py`.

## Назначение `PATH_DATA_STORAGE`

`PATH_DATA_STORAGE` - отдельный storage root для Stage Two artifacts:

- Parquet normalized/features/model-ready tables;
- DuckDB SQL files, exports и локальные `.duckdb` databases;
- runtime logs;
- temp data для ingestion/parser/normalization/DuckDB;
- backups catalog metadata;
- runtime schema copies;
- reports на русском и английском.

Raw dataset files не копируются в `PATH_DATA_STORAGE` при catalog ingestion. Их путь и хеш сохраняются в PostgreSQL (`dataset_files.file_path`, `dataset_files.file_hash_sha256`).

## Базовая структура

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
    features/
    model_ready/
  duckdb/
    sql/
    exports/
  logs/
    stage-two/
  backups/
    postgres_catalog/
    metadata_exports/
  temp_data/
    ingestion/
    parser_runs/
    normalization/
    duckdb/
  schemas/
    normalized/
    features/
    model_ready/
  reports/
    ru/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
    en/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
  config/
```

`StorageBootstrapper.required_relative_paths()` также создает role-aware поддиректории для normalized/features/model-ready layers, чтобы `TRAIN`, `VALIDATION` и `TEST` не смешивались.

## Parquet layers

| Layer | Путь | Кто пишет |
| --- | --- | --- |
| normalized | `parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `ParquetArtifactWriter.write_normalized()` через DNS/Host normalization services |
| features | `parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `FeatureArtifactWriter.write_and_register()` |
| model-ready | `parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}` | `ModelReadyRegistryService.write_table_artifact()` |

Stage Two пишет normalized layer. Feature/model-ready layers теперь собираются Stage Three командами `extract-features` и `build-model-ready` из `scripts/stage_three/cli.py`; Stage Two storage bootstrap заранее создает эти директории, чтобы сохранить единый `PATH_DATA_STORAGE`.

## Reports

| Report group | Примеры файлов | Кто пишет |
| --- | --- | --- |
| parser | coverage/status reports | parser coverage/status tools |
| normalization | parser run summaries | normalization services/runners |
| quality | `duckdb_analytics_report.json`, data quality reports | `DuckDBAnalyticsService`, `DataQualityChecker` |
| leakage | leakage reports RU/EN | `LeakageChecker` |
| stage-two root | readiness/e2e reports | `readiness_check`, `e2e_dry_run` |

`DuckDBAnalyticsService` сохраняет JSON report в `reports/en/stage-two/quality/duckdb_analytics_report.json`. `DataQualityChecker` и `LeakageChecker` сохраняют отчеты в RU/EN report roots.

## Temp data

`temp_data` используется для временных результатов ingestion, parser runs, normalization и DuckDB. `e2e_dry_run` создает synthetic workspace под:

```text
temp_data/stage_two_e2e_dry_run/
```

Данные из `temp_data` нельзя считать source of truth. Source of truth для metadata - PostgreSQL Catalog, для больших таблиц - Parquet artifacts.

## Config и schemas

| Путь | Назначение |
| --- | --- |
| `config/label_mapping_rules.json` | Внешние label mapping rules, если файл создан в storage. |
| `schemas/normalized/` | Runtime schema copies для normalized layer. |
| `schemas/features/` | Runtime schema copies для feature layer. |
| `schemas/model_ready/` | Runtime schema copies для model-ready layer. |

Проектные schema contracts находятся в репозитории:

```text
schemas/normalized/normalized_event_v1.json
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

## Ограничения

- Storage bootstrap создает директории, но не запускает PostgreSQL и не применяет Alembic migrations.
- PostgreSQL хранит пути к artifacts, но не хранит большие normalized/features/model-ready таблицы.
- Удаление или перенос файлов в `PATH_DATA_STORAGE/parquet` ломает `normalized_artifacts`, `feature_artifacts`, `model_ready_artifacts` и traceability.
- `PATH_FOLDER_DATASETS_FILTER` и `PATH_DATA_STORAGE` должны быть разными зонами ответственности: первая содержит input tree, вторая - Stage Two outputs.


---

## Источник: `docs/ru/normalization/traceability.md`

# Traceability и lineage

Traceability связывает model-ready artifact с исходным raw file через PostgreSQL Catalog и Parquet metadata. Цепочка нужна для audit, воспроизводимости, поиска leakage и проверки, что raw files не изменялись.

## Реализация

Код:

```text
scripts/stage_two/traceability/service.py
```

CLI:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Числовой аргумент ищется как `model_ready_artifacts.id`, строковый - как `model_ready_artifacts.artifact_path`.

## Обязательная цепочка

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

Если link отсутствует, `TraceabilityService` выбрасывает `TraceabilityError`. Readiness check считает это `FAILED`.

## Что возвращает service

Trace chain включает metadata блоки:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Этого достаточно, чтобы ответить:

- из какого raw файла получен artifact;
- каким parser и schema version он обработан;
- где лежит normalized Parquet;
- из какого feature artifact собран model-ready artifact;
- какая role/branch использовалась на каждом уровне.

## Правила сохранения traceability

1. `normalized_artifacts.parser_run_id` должен ссылаться на реальный `parser_runs.id`.
2. `parser_runs.file_id` должен ссылаться на `dataset_files.id`.
3. `feature_artifacts.normalized_artifact_id` должен быть заполнен для production artifacts.
4. `model_ready_artifacts.feature_artifact_id` должен быть заполнен для traceable model-ready artifacts.
5. Raw file hash в `dataset_files.file_hash_sha256` должен совпадать с текущим файлом при readiness check.

## Traceability и leakage

Traceability fields нельзя удалять из catalog, но нельзя включать в model-ready `X`. Поля paths, hashes, IDs и raw metadata могут идентифицировать dataset/source и создавать leakage. Они должны оставаться в catalog/metadata или быть исключены через `x_excluded_columns`.

## Проверка

```bash
python manage.py stage-two trace-artifact 123
python -m scripts.stage_two.readiness_check
```

`readiness_check` дополнительно проверяет один последний traceable model-ready artifact и raw file hashes.


---

## Источник: `docs/ru/normalization/usage_guide.md`

# Руководство запуска Stage Two normalization

Документ фиксирует фактический CLI слой: `manage.py` принимает `module`, `service`, `action`, `extra_args`, передает `stage-two` в `scripts.stage_two.cli.router_stage_two()`, а роутер вызывает конкретные service functions.

Полный reference по каждой Stage Two normalization команде, включая входы, выходы, статусы PostgreSQL, ошибки и проверки, находится в [stage_two_commands.md](ru/normalization/stage_two_commands.md).

## Предварительные условия

Нужно настроить окружение:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database
```

`DATABASE_URL` читается через `scripts/db/config.py`. Если переменной нет в окружении, код пробует загрузить `.env` из корня проекта.

## Базовый порядок запуска

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Порядок сохраняет разделение ролей. Нормализация `TRAIN`, `VALIDATION` и `TEST` запускается отдельными командами или через `normalize-all`, который группирует файлы по `branch/role/source_format` и не объединяет роли в один output artifact.

## Команды Stage Two

| Команда | Назначение | Основной выход |
| --- | --- | --- |
| `bootstrap-storage` | Создает обязательные директории в `PATH_DATA_STORAGE`. | Storage tree, schema/report/temp/log directories. |
| `catalog-ingest` | Сканирует `PATH_FOLDER_DATASETS_FILTER`, регистрирует datasets/files. | `datasets`, `ingestion_runs`, `dataset_files`. |
| `seed-parser-registry` | Загружает `parser_registry_seed.json` в catalog. | `parser_registry`, `schema_versions`. |
| `parser-coverage [branch]` | Проверяет, есть ли parser для зарегистрированных `branch/role/source_format`. | Console report, parser coverage diagnostics. |
| `mark-ready` | Переводит файлы подходящего bucket в `READY_FOR_PARSING`. | Обновленные `dataset_files.status`. |
| `normalize-format` | Нормализует конкретный `branch/role/source_format`. | `parser_runs`, normalized Parquet, `normalized_artifacts`. |
| `normalize-all` | Нормализует все ready buckets по branch. | То же, по группам role/format. |
| `split-large-files` | Делит большие line-based files на chunks. | Chunk files, optional catalog registration. |
| `normalize-dns [limit]` | Legacy shortcut для DNS ready files. | Normalized DNS artifacts. |
| `normalize-host [limit]` | Legacy shortcut для Host ready files. | Normalized Host artifacts. |
| `run-duckdb-checks` | Создает DuckDB views поверх Parquet и запускает analytics checks. | DuckDB report, `data_quality_reports`. |
| `run-leakage-checks` | Проверяет model-ready/feature contracts на leakage. | Leakage reports, `data_quality_reports`. |
| `trace-artifact` | Восстанавливает lineage для model-ready artifact. | Console JSON trace chain. |

## `mark-ready`

Флаги:

```bash
python manage.py stage-two mark-ready \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --dry-run

python manage.py stage-two mark-ready \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --apply
```

Также поддерживается compact form:

```bash
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
```

Ограничения:

- `--dry-run` и `--apply` взаимоисключающие.
- `role` должен быть одним из `TRAIN`, `VALIDATION`, `TEST`.
- Команда работает только с metadata catalog, raw files не изменяет.

## `normalize-format`

Флаги:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 100 \
  --workers 2 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --packet-mode packet-summary \
  --resume \
  --hash-output-artifacts
```

Компактная форма:

```bash
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Поведение:

- выбирает `dataset_files` со статусом `READY_FOR_PARSING` для точного `branch/role/source_format`;
- через `ParserResolver` выбирает активный parser из `parser_registry`;
- если parser не найден, выбранные файлы помечаются `UNSUPPORTED_FORMAT`;
- пишет normalized Parquet и регистрирует `parser_runs`/`normalized_artifacts`;
- при `--workers > 1` использует `ProcessPoolExecutor`;
- при `--resume` пропускает файлы, для которых уже есть успешный normalized artifact.

`--packet-mode` поддерживает значения:

| Значение | Назначение |
| --- | --- |
| `packet-summary` | Безопасный режим для packet captures: summary-level parsing. |
| `dns-only` | Извлекать DNS-события из packet captures, где parser это поддерживает. |
| `sample` | Обрабатывать sample пакетов; требует `--sample-size`. |

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch dns \
  --limit 1000 \
  --workers 2 \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-all dns:1000
```

Команда выбирает ready groups внутри одной branch и запускает `NormalizeFormatRunner` по группам. Группировка выполняется по `role` и `source_format`; это защищает от смешивания `TRAIN`, `VALIDATION`, `TEST`.

## Legacy-команды

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

Эти команды оставлены для совместимости. Для воспроизводимых запусков предпочтительны `normalize-format` или `normalize-all`, потому что они явно задают branch/role/format и performance options.

## Разделение больших файлов

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Назначение: подготовить line-based files к нормализации, когда один файл слишком большой. Команда поддерживает `csv`, `pcap.csv`, `txt`, `json`, `json-1`, логовые форматы, `sc`, `ghc`, `netflow_day`, `netflow_ids`, `wls_day` и metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) не делятся этим splitter.

Важные правила:

- `--register` допустим только вместе с `--apply`;
- без `--apply` команда работает как dry run;
- chunks пишутся в `PATH_FOLDER_DATASETS_FILTER/chunked/...`;
- при регистрации chunks получают статус `READY_FOR_PARSING`;
- исходный файл может быть помечен `SKIPPED`, если не указан `--keep-source-ready`.

## Проверки

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

`run-duckdb-checks` строит views `normalized_all`, `features_all`, `model_ready_all` поверх Parquet и проверяет row counts, required columns, split contamination и schema mismatch. `run-leakage-checks` проверяет запретные X columns, отсутствие `TEST` в training/preprocessing fit и регистрирует CRITICAL нарушения.

## Trace artifact

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

Числовой аргумент трактуется как `model_ready_artifacts.id`, строковый путь - как `model_ready_artifacts.artifact_path`. Команда требует, чтобы у model-ready artifact был `feature_artifact_id`, а у feature artifact - `normalized_artifact_id`; иначе traceability chain считается разорванной.

## Модульные проверки

Эти проверки не зарегистрированы как `manage.py stage-two` commands, но реализованы как Python modules:

```bash
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

`readiness_check` проверяет миграции, storage paths, counts catalog tables, parser coverage, normalized/feature/model-ready registration, quality/leakage reports, traceability и raw file hashes. `e2e_dry_run` создает synthetic DNS/Host samples под `temp_data`, прогоняет ingestion, seed, normalization, feature/model-ready registry services, DuckDB/leakage checks и traceability.

## Типовые ошибки

| Симптом | Причина | Действие |
| --- | --- | --- |
| `DATABASE_URL must be configured` | Нет `DATABASE_URL` в окружении или `.env`. | Настроить `DATABASE_URL`. |
| `PATH_DATA_STORAGE must be configured` | Storage root не задан. | Задать `PATH_DATA_STORAGE`, затем `bootstrap-storage`. |
| `No parser available` / `UNSUPPORTED_FORMAT` | В `parser_registry` нет активного parser для `branch/role/source_format`. | Проверить `parser-coverage`, добавить parser или registry entry. |
| Empty DuckDB views | Parquet layer пустой или paths не созданы. | Проверить `normalized_artifacts` и storage paths. |
| Leakage CRITICAL | X artifact содержит label/source fields или TEST участвует в fit/training. | Пересобрать artifact с корректным contract. |


---

## Источник: `docs/ru/project_documentation_index.md`

# Индекс ключевой проектной документации

Этот индекс заменяет набор разрозненных документов верхнего уровня и показывает, куда перенесена ключевая информация по proposal, стратегиям датасетов, feature engineering и фактическому состоянию репозитория.

## Итоговая структура

| Документ | Назначение |
| --- | --- |
| [repository_analysis.md](ru/repository_analysis.md) | Фактический анализ текущего репозитория: entrypoints, CLI routing, Stage One/Two/Three, storage, тесты и gaps. |
| [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) | Research context, proposal-level архитектура, вопросы, цели, methodology, scope, план и ограничения. |
| [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) | Единая стратегия DNS и Host датасетов с явным разделением `TRAIN` / `VALIDATION` / `TEST`. |
| [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) | Карта feature extraction, каталог групп признаков, schema requirements, leakage exclusions и приоритеты реализации. |
| [stage-three/README.md](ru/stage-three/README.md) | Stage Three feature/model-ready preparation: usage guide, commands, performance tuning, MVP DNS path и production path. |
| [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) | Что подтверждено текущим кодом, что остается proposal/планом, QA по разделам 3.3-3.8, gaps и follow-up. |

## Объединенные старые документы

| Старый документ | Куда перенесено содержание |
| --- | --- |
| `project_proposal_analysis.md` | `project_overview_and_research_context.md`, `repository_state_qa_and_gaps.md`. |
| `functional_project_cheatsheet.md` | `project_overview_and_research_context.md`, `dataset_strategy_dns_host.md`, `feature_extraction_and_catalogue.md`. |
| `dns_dataset_strategy.md` | `dataset_strategy_dns_host.md`. |
| `host_datasets_analysis.md` | `dataset_strategy_dns_host.md`, `repository_state_qa_and_gaps.md`. |
| `dataset_feature_extraction_map.md` | `feature_extraction_and_catalogue.md`, `dataset_strategy_dns_host.md`. |
| `feature_catalogue_full.md` | `feature_extraction_and_catalogue.md`. |
| `repository_qa_section_3_8.md` | `repository_state_qa_and_gaps.md`. |

## Связанные актуальные разделы

- [analysis-dataset/README.md](ru/analysis-dataset/README.md) — фактический Stage One анализ bucket/formats/readiness.
- [normalization/README.md](ru/normalization/README.md) — Stage Two normalization guide.
- [stage-three/README.md](ru/stage-three/README.md) — Stage Three feature extraction, preprocessing и model-ready guide.
- [code-documentation/README.md](ru/code-documentation/README.md) — архитектура кода, CLI, Stage One/Stage Two, DB и parser strategy.

## Правила чтения

1. Для сверки с текущим кодом читать [repository_analysis.md](ru/repository_analysis.md), затем [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md).
2. Для research proposal читать [project_overview_and_research_context.md](ru/project_overview_and_research_context.md).
3. Для выбора датасетов читать [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md).
4. Для реализации feature engineering читать [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md).
5. Для запуска Stage Three читать [stage-three/usage_guide.md](ru/stage-three/usage_guide.md) и [stage-three/stage_three_commands.md](ru/stage-three/stage_three_commands.md).

## Архитектурные инварианты

- `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
- `TEST` не используется для training, fit preprocessing, feature selection или threshold tuning.
- DNS и Host логика разделены; объединение выполняется только на уровне normalized events, windows, features и traceability.
- Labels являются target/audit fields, а не input features.
- Отсутствие label не означает benign.
- Proposal-level идеи не считаются реализованными, пока они не подтверждены кодом, артефактами или Stage Two/Stage Three документацией.
- Stage Three artifacts считаются готовыми для Stage Four только после `final-report` со статусом `READY_FOR_STAGE_FOUR`.


---

## Источник: `docs/ru/project_overview_and_research_context.md`

# Обзор проекта и research context

Документ объединяет сведения из `project_proposal_analysis.md` и `functional_project_cheatsheet.md`. Он описывает proposal-level замысел проекта и отделяет исследовательский план от фактической реализации репозитория.

## Назначение

Проект посвящен теме **Behaviour-driven hybrid learning for data exfiltration detection**. Цель исследования — спроектировать и оценить гибридный ML/DL framework для обнаружения многоэтапной эксфильтрации данных с использованием:

- DNS и network признаков;
- host-level telemetry;
- behavioural sequence modelling;
- explainability через SHAP;
- role-separated dataset strategy для `TRAIN`, `VALIDATION`, `TEST`.

## Research gap

Исходные документы фиксируют один и тот же исследовательский разрыв:

| Ограничение существующих подходов | Последствие |
| --- | --- |
| Single-modality detection: только network или только host. | Модель видит неполный жизненный цикл атаки. |
| Event-level classification без последовательностей. | Многоэтапная эксфильтрация может быть обнаружена поздно или фрагментарно. |
| Слабая explainability. | SOC analyst не видит, какие признаки привели к решению. |
| Несовместимость публичных датасетов. | Нельзя безоговорочно выполнять raw fusion host/network логов. |

Вывод: multi-source integration должна выполняться на уровне признаков, временных окон, normalized events и traceability, а не через механическое объединение raw logs.

## Proposal-level архитектура

```mermaid
flowchart TD
    A["DNS/network datasets"] --> D["Multi-source feature integration"]
    B["Host telemetry datasets"] --> D
    C["Stage Two normalization"] --> S3["Stage Three feature/model-ready preparation"]
    S3 --> D["Multi-source feature integration"]
    D --> E["Stage Four classifiers: RF, XGBoost, CNN"]
    D --> F["Stage Four sequence modelling: LSTM"]
    E --> G["Late fusion"]
    F --> G
    G --> H["Detection decision"]
    H --> I["SHAP explanations"]
```

| Слой | Назначение | Статус |
| --- | --- | --- |
| Stage Three preparation | Feature catalog, extraction, label alignment, X/y/metadata/traceability separation, preprocessing, model-ready artifacts, checks, final report. | Реализовано как preparation layer; готовность зависит от `final-report`. |
| Multi-source integration | Нормализация host/network признаков в единое представление. | Частично покрывается Stage Three feature/model-ready layer; production Host/Network/Hybrid expansion еще требует отдельных runs. |
| Hybrid ML/DL classification | Random Forest, XGBoost, CNN для structured/local feature patterns. | Stage Four; модельный код не подтвержден. |
| Behavioural sequence modelling | LSTM по ordered event sequences. | Stage Four; Stage Three готовит sequence artifacts, но LSTM training не реализован. |
| Late fusion | Агрегация вероятностей classifier и sequence model. | Proposal; веса/формула не заданы. |
| SHAP explainability | Global/local explanations и rank-order consistency. | Proposal; SHAP variants не зафиксированы. |

## Research questions

| ID | Вопрос | Что должен дать для реализации |
| --- | --- | --- |
| RQ1 | Какие cross-domain признаки host/network характеризуют стадии эксфильтрации? | Feature catalogue и dataset-feature map. |
| RQ2 | Как объединить classical ML и DL в hybrid architecture? | Baseline classifiers, CNN branch, сравнение ablation. |
| RQ3 | Как встроить behavioural sequence modelling? | Sequence window builder, LSTM branch, event ordering. |
| RQ4 | Как XAI повышает interpretability и помогает расследованию? | SHAP reports, fold consistency, case studies. |

## Aim and objectives

Цель: разработать и оценить behaviour-driven hybrid ML framework для обнаружения data exfiltration, объединяющий host telemetry, network features, behavioural sequence modelling и explainable AI.

Задачи:

1. Определить host-level и network-level признаки для data exfiltration detection.
2. Спроектировать hybrid ML/DL detection architecture: RF, XGBoost, CNN, LSTM.
3. Реализовать behavioural sequence modelling для temporal attack patterns.
4. Интегрировать SHAP-based explainability.
5. Оценить framework на public cybersecurity benchmark datasets.

## Scope

| Входит в scope | Вне текущего scope |
| --- | --- |
| Public benchmark datasets. | Live traffic capture. |
| RF, XGBoost, CNN, LSTM. | RL components. |
| Feature-level host/network integration. | Large-scale raw multi-dataset fusion. |
| Supervised/semi-supervised sequence modelling. | Fully unsupervised sequence modelling. |
| SHAP explainability. | Полная SOC product integration. |

## Methodology

Proposal использует **Design Science Research (DSR)**:

1. Feature identification and dataset preparation.
2. Hybrid framework design.
3. Behavioural sequence modelling.
4. Explainability integration.
5. Evaluation and validation.

Плановый timeline: 12 недель, май-август 2026.

| Фаза | Key deliverable | Целевая дата |
| --- | --- | --- |
| Phase 1 | Preprocessed feature dataset with MITRE ATT&CK mappings. | May 15 |
| Phase 2 | Hybrid detection framework prototype. | June 12 |
| Phase 3 | Integrated LSTM sequence modelling component. | July 3 |
| Phase 4 | SHAP explanation module. | July 24 |
| Phase 5 | Experimental results report with comparative analysis. | August 14 |
| Report writing | Completed report and slides. | August 28 |

## Evaluation plan

| Элемент | Proposal-level решение | Gap реализации |
| --- | --- | --- |
| Metrics | Accuracy, precision, recall, F1-score, FPR, AUC. | Модельный evaluation код не подтвержден. |
| Validation | Stratified k-fold cross-validation. | Значение `k` не задано. |
| Ablation | Full hybrid vs individual components. | Ablation experiments не реализованы. |
| Baselines | RF only, XGBoost only, CNN only, LSTM only, hybrid without SHAP. | Конкретные baseline configs отсутствуют. |
| Explainability | SHAP explanations for TP/FP and fold rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны. |

## Proposal risks

| Риск | Последствие | Митигирующая мера |
| --- | --- | --- |
| Несовместимость host и network datasets. | Нельзя доказать прямую raw-level корреляцию. | Использовать feature-level integration и явно документировать ограничения. |
| Class imbalance. | Accuracy может быть вводящей в заблуждение. | Делать precision/recall/F1 основными метриками. |
| Sequence model underperformance. | LSTM может не улучшить baseline. | Добавить temporal aggregation fallback и ablation. |
| Compute constraints. | DL experiments могут быть ограничены. | Использовать Colab/Kaggle или упрощенные модели. |
| Weak explainability design. | SHAP может объяснять proxy/leakage признаки. | Исключить leakage fields и проверять SHAP stability. |

## Что является фактом, а что proposal

| Категория | Статус |
| --- | --- |
| Stage One dataset preparation, sorting, JSON path maps. | Подтверждено текущим репозиторием. |
| Stage Two normalization/catalog/parquet/parser design. | Реализовано/задокументировано в Stage Two документации; проверять готовность по checks. |
| Stage Three feature/model-ready preparation. | Реализовано/задокументировано; проверять конкретный `experiment_id` через `stage-three final-report`. |
| RF/XGBoost/CNN/LSTM training. | Proposal-level, в QA документе модельная реализация не подтверждена. |
| SHAP explanations. | Proposal-level. |
| Feature catalogue. | Machine-readable Stage Three contract в `scripts/stage_three/feature_catalog/feature_catalog.yml`. |


---

## Источник: `docs/ru/README.md`

# Документация проекта Proposal

Этот README является общей точкой входа в документацию проекта. Он помогает быстро найти материалы по исследовательскому контексту, Stage One, Stage Two normalization, Stage Three feature/model-ready preparation, архитектуре кода, датасетам, PostgreSQL Catalog, Parquet/DuckDB, labels, features и leakage checks.

Документация разделяет:

- **фактическую реализацию** - то, что подтверждено текущим кодом и CLI;
- **операционные инструкции** - как запускать и проверять pipeline;
- **исследовательские материалы и proposal** - цели, методология, dataset strategy, feature catalogue и планы;
- **gaps и follow-up** - то, что еще не реализовано или требует уточнения.

## Синхронизация с текущим кодом

Последняя сверка с кодом: 2026-07-08.

- Маршрутизация Stage Two реализована в `scripts/stage_two/cli.py`; этот файл является главным источником истины по поддержанным `stage-two` командам.
- `python manage.py stage-two --help` в текущем состоянии не является надежным help: команда попадает в fallback `config.manage_commands` и может печатать `unknown Stage Two command`. Полный список Stage Two команд нужно сверять с `scripts/stage_two/cli.py` и [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md).
- Runtime defaults без resource profile консервативные: `workers=1`, `batch_size=50000`, `max_output_part_rows=50000`. Resource profiles и format policy для `normalize-format` могут изменить итоговые значения перед запуском.
- Stage Three routing реализован в `scripts/stage_three/cli.py`; он покрывает `validate-inputs`, `build-feature-catalog`, `probe-runtime-backend`, `extract-features`, `align-labels`, `build-sequences`, `build-model-ready`, `rebalance-dns-supervised`, `run-quality-checks`, `run-leakage-checks`, `trace-artifact` и `final-report`.
- Stage Three является preparation layer: он строит feature/model-ready artifacts и проверяет quality/leakage/traceability, но не обучает RF/XGBoost/CNN/LSTM и не выполняет Stage Four evaluation.

## Быстрый старт

| Если нужно | Читать |
| --- | --- |
| Понять весь проект и исследовательский контекст | [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) |
| Увидеть фактический repo-wide анализ кода и CLI | [repository_analysis.md](ru/repository_analysis.md) |
| Увидеть карту ключевых документов | [project_documentation_index.md](ru/project_documentation_index.md) |
| Проверить, что реализовано, а что пока proposal | [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) |
| Разобраться в структуре кода и CLI | [code-documentation/README.md](ru/code-documentation/README.md) |
| Найти Stage One анализ датасетов | [analysis-dataset/README.md](ru/analysis-dataset/README.md) |
| Запустить Stage Two normalization | [normalization/README.md](ru/normalization/README.md), [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) |
| Запустить Stage Three feature/model-ready preparation | [stage-three/README.md](ru/stage-three/README.md), [stage-three/stage_three_commands.md](ru/stage-three/stage_three_commands.md) |
| Выбрать DNS/Host стратегию и split roles | [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) |
| Смотреть feature engineering и leakage exclusions | [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) |

## Основные разделы

| Раздел | Назначение | Тип |
| --- | --- | --- |
| [analysis-dataset/](ru/analysis-dataset/README.md) | Результаты Stage One анализа DNS/Host buckets, counts, formats, labels, readiness и parser recommendations. | Фактический анализ датасетов |
| [code-documentation/](ru/code-documentation/README.md) | Архитектура кода: CLI/routing, Stage One handlers, Stage Two, PostgreSQL Catalog, SQLAlchemy, schemas, parsers, labels, Parquet/DuckDB, checks, risks. | Техническая документация по коду |
| [normalization/](ru/normalization/README.md) | Operational guide по Stage Two normalization: storage, catalog ingestion, parser registry, `READY_FOR_PARSING`, normalization commands, DuckDB/leakage checks, traceability. | Фактическая реализация и runbooks |
| [stage-three/](ru/stage-three/README.md) | Operational guide по Stage Three: readiness gate, feature catalog, extraction, label alignment, preprocessing, model-ready build, checks, final report. | Фактическая реализация и runbooks |
| [repository_analysis.md](ru/repository_analysis.md) | Сводный анализ текущего репозитория: entrypoints, Stage One/Two/Three, storage, тесты, gaps. | Repo-wide анализ |
| [project_documentation_index.md](ru/project_documentation_index.md) | Индекс верхнеуровневых документов и карта переноса старых материалов. | Навигация |
| [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) | Research context, цели, methodology, proposal-level architecture и ограничения. | Research/proposal |
| [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) | DNS/Host dataset strategy с явным разделением `TRAIN`, `VALIDATION`, `TEST`. | Dataset strategy |
| [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) | Feature extraction map, feature groups, schema requirements, forbidden leakage fields, implementation priorities. | Feature engineering |
| [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) | Подтвержденная реализация, proposal-level gaps, QA и follow-up tasks. | QA/gaps |
| [Project Proposal.docx](<Project Proposal.docx>) | Русская версия проектного proposal-документа в DOCX. | Research/proposal artifact |

## Где искать по темам

### Stage One

- [code-documentation/stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md) - handlers `analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`, JSON manager.
- [analysis-dataset/README.md](ru/analysis-dataset/README.md) - итоговый индекс анализа датасетов.
- [analysis-dataset/dns_datasets.md](ru/analysis-dataset/dns_datasets.md) - DNS `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/host_datasets.md](ru/analysis-dataset/host_datasets.md) - Host `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) - readiness matrix по 64 format buckets.
- [analysis-dataset/labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) - labels, readiness statuses и anti-leakage правила.

### Stage Two / Normalization

- [normalization/README.md](ru/normalization/README.md) - границы Stage Two, основные команды, инварианты.
- [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - полный reference по Stage Two commands: входы, выходы, PostgreSQL statuses, ошибки и проверки.
- [normalization/usage_guide.md](ru/normalization/usage_guide.md) - общий порядок запуска CLI.
- [normalization/runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) - эксплуатация, recovery и large-file сценарии.
- [normalization/performance_tuning.md](ru/normalization/performance_tuning.md) - `workers`, `batch-size`, `max-output-part-rows`, packet modes.

### Stage Three / Feature and Model-ready Preparation

- [stage-three/README.md](ru/stage-three/README.md) - границы Stage Three, DNS MVP path и production expansion.
- [stage-three/usage_guide.md](ru/stage-three/usage_guide.md) - порядок запуска `validate-inputs -> feature catalog -> extraction -> model-ready -> checks -> final-report`.
- [stage-three/stage_three_commands.md](ru/stage-three/stage_three_commands.md) - CLI reference для `python manage.py stage-three ...`.
- [stage-three/performance_tuning.md](ru/stage-three/performance_tuning.md) - CPU-first/streaming-first policy, RAM/GPU profile и production tuning.
- [code-documentation/stage_three_overview.md](ru/code-documentation/stage_three_overview.md) - архитектура модулей `scripts/stage_three`.

### Архитектура кода

- [code-documentation/README.md](ru/code-documentation/README.md) - карта технической документации.
- [code-documentation/cli_and_routing.md](ru/code-documentation/cli_and_routing.md) - `manage.py`, routing layer, Stage One/Stage Two commands.
- [code-documentation/stage_two_overview.md](ru/code-documentation/stage_two_overview.md) - Stage Two pipeline.
- [code-documentation/stage_three_overview.md](ru/code-documentation/stage_three_overview.md) - Stage Three pipeline.
- [code-documentation/extension_points.md](ru/code-documentation/extension_points.md) - как расширять handlers, parsers, schemas, labels, checks и stages.
- [code-documentation/risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md) - known limitations, parser gaps, leakage/timestamp/large-file risks.

### PostgreSQL Catalog и SQLAlchemy

- [code-documentation/postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md) - catalog tables и traceability chain.
- [code-documentation/sqlalchemy_layer.md](ru/code-documentation/sqlalchemy_layer.md) - config, session, models, repositories, migrations.
- [normalization/postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) - Stage Two catalog schema с точки зрения normalization.

### Schemas, Parsers и Labels

- [code-documentation/normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md) - normalized event schema.
- [normalization/normalized_event_schema.md](ru/normalization/normalized_event_schema.md) - operational schema guide для normalization.
- [code-documentation/parser_strategy.md](ru/code-documentation/parser_strategy.md) и [normalization/parser_strategy.md](ru/normalization/parser_strategy.md) - parser registry/resolver strategy.
- [normalization/parser_development_guide.md](ru/normalization/parser_development_guide.md) - добавление нового parser implementation.
- [code-documentation/label_resolver.md](ru/code-documentation/label_resolver.md) и [normalization/label_resolver.md](ru/normalization/label_resolver.md) - label sources, `TEST` restrictions, conflicts.

### Parquet, DuckDB, Quality и Leakage

- [code-documentation/parquet_and_duckdb.md](ru/code-documentation/parquet_and_duckdb.md) - Parquet paths, writer, DuckDB views/checks.
- [normalization/parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md) - artifacts и DuckDB usage в Stage Two.
- [normalization/data_quality_checks.md](ru/normalization/data_quality_checks.md) - DataQuality/DuckDB checks.
- [normalization/data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md) - forbidden X columns и anti-leakage invariants.
- [code-documentation/traceability.md](ru/code-documentation/traceability.md) и [normalization/traceability.md](ru/normalization/traceability.md) - `raw -> normalized -> features -> model-ready`.

### Features и исследовательские материалы

- [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) - feature groups, contracts, exclusions и priorities.
- [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) - dataset roles, sources, strategy и limitations.
- [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) - research framing и proposal-level архитектура.
- [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) - где proposal расходится с текущей реализацией.

## Рекомендуемый порядок чтения

1. [project_documentation_index.md](ru/project_documentation_index.md) - общий индекс и карта объединенных документов.
2. [repository_analysis.md](ru/repository_analysis.md) - фактический анализ кода, CLI, storage и тестов.
3. [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) - граница между реализованным и proposal.
4. [analysis-dataset/README.md](ru/analysis-dataset/README.md) - фактическая структура DNS/Host данных.
5. [code-documentation/README.md](ru/code-documentation/README.md) - архитектура кода и pipeline.
6. [normalization/README.md](ru/normalization/README.md) - Stage Two implementation guide.
7. [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - точные команды запуска.
8. [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) - feature engineering и model-ready ограничения.
9. [stage-three/README.md](ru/stage-three/README.md) - практический запуск Stage Three и готовность к Stage Four.

## Основные инварианты

1. Raw-файлы не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
3. `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты; большие normalized/features/model-ready таблицы хранятся в Parquet.
5. Labels не являются input features.
6. Leakage/source/label fields не попадают в model-ready X artifacts.
7. Отсутствующий label не означает benign.
8. Отсутствующий timestamp нельзя заменять текущим временем.
9. Traceability должна сохраняться по цепочке `raw -> normalized -> features -> model-ready`.
## Stage Two performance quick start

Для текущей performance architecture используйте:

- [normalization/performance_tuning.md](ru/normalization/performance_tuning.md) - resource profiles, format policy, benchmark target и troubleshooting.
- [normalization/runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) - operational sequence для benchmark/full runs и recovery.
- [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - точный CLI reference, включая `benchmark-normalization`.
- [code-documentation/stage_two_overview.md](ru/code-documentation/stage_two_overview.md) - execution planner, bounded multiprocessing, chunking, atomic Parquet, benchmark и validation architecture.

Рекомендуемый flow:

```bash
python manage.py stage-two benchmark-normalization --branch host --role TEST --format txt --limit 10000 --sample-ratio 0.10 --resource-profile fast
python manage.py stage-two normalize-format --branch host --role TEST --format txt --resource-profile fast --resume
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Начинайте с `safe` или `balanced`; используйте `fast` или `aggressive` только после чистых benchmark reports и quality gates.


---

## Источник: `docs/ru/repository_analysis.md`

# Анализ репозитория

Дата сверки: 2026-07-08.

Документ фиксирует текущее состояние кода и документации репозитория `Proposal` после анализа entrypoints, CLI, Stage One/Two/Three модулей, тестов, схем и storage artifacts.

## Краткий вывод

Репозиторий реализует pipeline подготовки данных до model-ready artifacts:

```text
Stage One:   raw datasets -> inventories/sorted path maps/content reports
Stage Two:   raw catalog -> parser registry -> normalized Parquet -> quality/leakage/traceability
Stage Three: normalized Parquet -> feature artifacts -> model-ready X/y/metadata/traceability -> readiness report
Stage Four:  training/evaluation/explainability, пока не опубликован как CLI
```

Stage Four остается следующим этапом: обучение RF/XGBoost/CNN/LSTM, threshold tuning, SHAP/XAI и экспериментальная оценка в текущем CLI не реализованы.

## Масштаб кода и документации

Фактический срез:

| Область | Количество |
| --- | ---: |
| Python-файлы | 334 |
| Тестовые Python-файлы | 66 |
| Markdown в `docs/` | 106 |
| Markdown в `docs/ru` | 52 до добавления этого файла |
| Markdown в `docs/en` | 52 до добавления английской версии |

Основные директории:

```text
scripts/
  handlers/        # Stage One handlers
  stage_two/       # catalog, parsers, normalization, checks
  stage_three/     # feature/model-ready preparation
  db/              # SQLAlchemy models, repositories, Alembic
schemas/           # normalized/features/model_ready JSON contracts
tests/
  stage_two/
  stage_three/
docs/
  ru/
  en/
```

## Entry points и routing

Главная точка входа:

```powershell
python manage.py <module> <service> [action] [args]
```

Фактическая маршрутизация:

| Слой | Файл | Назначение |
| --- | --- | --- |
| `manage.py` | `manage.py` | тонкий CLI entrypoint; отдельно прокидывает `stage-three` в argparse-router |
| root router | `scripts/router_script.py` | отправляет команды в `handlers`, `stage_two`, `stage_three` |
| Stage One | `scripts/handlers/router_handler.py` | legacy handlers для анализа/сортировки датасетов |
| Stage Two | `scripts/stage_two/cli.py` | фактический router normalization pipeline |
| Stage Three | `scripts/stage_three/cli.py` | argparse router feature/model-ready preparation |

Важно: `python manage.py stage-two --help` в текущем состоянии не является надежным источником help. Он выводит ошибку `unknown Stage Two command` и старый fallback `config.manage_commands`. Полный фактический список Stage Two команд нужно брать из `scripts/stage_two/cli.py` и `docs/ru/normalization/stage_two_commands.md`.

## Stage One

Stage One находится в `scripts/handlers` и выполняет filesystem-level подготовку:

- анализ DNS/Host raw dataset roots;
- фильтрацию Host источников;
- сортировку по role/format;
- экспорт JSON path maps;
- content analysis reports для DNS/Host buckets.

Stage One не пишет normalized Parquet и не регистрирует артефакты в PostgreSQL catalog.

## Stage Two

Stage Two находится в `scripts/stage_two`, `scripts/db`, `schemas`.

Фактические команды router:

- `bootstrap-storage`
- `catalog-ingest`
- `seed-parser-registry`
- `parser-coverage`
- `mark-ready`
- `normalize-format`
- `normalize-all`
- `benchmark-normalization`
- `split-large-files`
- `normalize-dns`
- `normalize-host`
- `run-duckdb-checks`
- `run-leakage-checks`
- `trace-artifact`

Ключевые подсистемы:

| Подсистема | Файлы |
| --- | --- |
| storage bootstrap | `scripts/stage_two/storage/bootstrap.py` |
| catalog ingestion | `scripts/stage_two/ingestion/` |
| parser registry/resolver | `scripts/stage_two/parser_registry/` |
| parsers | `scripts/stage_two/parsers/` |
| normalization runner | `scripts/stage_two/normalization/` |
| execution policy | `scripts/stage_two/execution/` |
| Parquet writer | `scripts/stage_two/parquet/writer.py` |
| DuckDB analytics | `scripts/stage_two/duckdb/service.py` |
| quality/leakage | `scripts/stage_two/quality/` |
| traceability | `scripts/stage_two/traceability/service.py` |

Stage Two отвечает за переход `raw -> normalized` и не должен выполнять обучение моделей.

## Stage Three

Stage Three находится в `scripts/stage_three`.

Фактические команды:

- `validate-inputs`
- `build-feature-catalog`
- `probe-runtime-backend`
- `extract-features`
- `align-labels`
- `build-sequences`
- `build-model-ready`
- `rebalance-dns-supervised`
- `run-quality-checks`
- `run-leakage-checks`
- `trace-artifact`
- `final-report`

Ключевые подсистемы:

| Подсистема | Файлы |
| --- | --- |
| typed CLI requests | `scripts/stage_three/requests.py` |
| storage bootstrap | `scripts/stage_three/storage/bootstrap.py` |
| readiness gate | `scripts/stage_three/readiness/` |
| feature catalog | `scripts/stage_three/feature_catalog/feature_catalog.yml` |
| runtime profiles/backend | `scripts/stage_three/runtime/` |
| extraction | `scripts/stage_three/extraction/` |
| labels/window policies | `scripts/stage_three/labels/` |
| preprocessing | `scripts/stage_three/preprocessing/` |
| model-ready builder | `scripts/stage_three/model_ready/` |
| quality/leakage/traceability | `scripts/stage_three/quality/` |
| final reports/console output | `scripts/stage_three/reports/` |
| DNS supervised split rebuild | `scripts/stage_three/dns_rebalance.py` |

Stage Three является preparation layer. Он готовит artifacts для Stage Four, но не обучает модели.

## Feature catalog

Machine-readable catalog находится в:

```text
scripts/stage_three/feature_catalog/feature_catalog.yml
```

Он задает:

- `forbidden_X_columns`;
- feature groups для DNS, Host, Network, Hybrid и Sequence;
- source fields и output features;
- dtype/nullability/preprocessing policy.

Ключевое правило: label/source/path/parser/raw/metadata/traceability поля не должны попадать в model-ready X.

## Storage

Фактический storage root:

```text
C:\Users\Public\PythonProjects\storage
```

Основные зоны:

- `parquet/normalized`
- `parquet/features`
- `parquet/model_ready`
- `duckdb/proposal_analytics.duckdb`
- `reports/{ru,en}/stage-one`
- `reports/{ru,en}/stage-two`
- `reports/{ru,en}/stage-three`
- `temp_data`
- `schemas`
- `config`
- `logs`
- `backups`

Подробно см. `docs/storage.md`.

## Тесты

Тесты разделены по этапам:

- `tests/stage_two/` - parsers, catalog ingestion, normalization, Parquet writer, DuckDB, leakage, parser reports, status tools.
- `tests/stage_three/` - CLI routing, runtime, feature catalog, extraction, label alignment, preprocessing, model-ready builder, quality/leakage, final report, console output.

Минимальная проверка документационных правок:

```powershell
git diff --check -- docs
```

Целевые тесты после изменения Stage Two/Three кода:

```powershell
pytest tests/stage_two
pytest tests/stage_three
```

## Инварианты

1. Raw datasets не изменяются.
2. `TRAIN`, `VALIDATION`, `TEST` не смешиваются.
3. `TEST` не используется для training, preprocessing fit, feature selection или threshold tuning.
4. Labels не являются input features.
5. Отсутствующий label не означает benign.
6. Отсутствующий timestamp нельзя заменять текущим временем.
7. Большие таблицы хранятся в Parquet; PostgreSQL хранит metadata/status/lineage.
8. `temp_data` не является source of truth.
9. Переход к Stage Four допустим только после Stage Three `final-report` со статусом `READY_FOR_STAGE_FOUR`.

## Gaps

| Область | Статус |
| --- | --- |
| Stage Four training/evaluation | Не опубликован как CLI |
| RF/XGBoost configs | Proposal-level |
| CNN/LSTM architecture | Proposal-level |
| SHAP/XAI | Proposal-level |
| Late fusion | Proposal-level |
| CV folds/statistical tests/seeds | Требуют отдельного experiment config |
| Production Host/Network/Hybrid readiness | Требует проверки по конкретным `branch`, `role`, `feature_group`, `experiment_id` |


---

## Источник: `docs/ru/repository_state_qa_and_gaps.md`

# Фактическое состояние репозитория, QA и gaps

Документ объединяет `repository_qa_section_3_8.md`, QA-блоки из `project_proposal_analysis.md` и ограничения из `functional_project_cheatsheet.md`. Его задача — отделить реализованное состояние репозитория от proposal-level планов.

## Scope анализа

Последняя repo-wide сверка: 2026-07-08. Подробный текущий срез entrypoints, CLI, Stage One/Two/Three, storage и тестов вынесен в [repository_analysis.md](ru/repository_analysis.md).

Исходный QA документ фиксировал просмотр репозитория (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, конфиги). Ключевой вывод сохраняется:

> В текущем репозитории подтверждены этапы подготовки датасетов, Stage Two normalization и Stage Three feature/model-ready preparation. Обучение и оценка моделей остаются Stage Four.

## Что подтверждено текущей реализацией

| Область | Подтверждено |
| --- | --- |
| Stage One dataset preparation | Сканирование датасетов, назначение ролей, фильтрация host, сортировка по форматам, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS и Host обрабатываются отдельными ветками. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 в старом QA, 361670 total files по актуальной analysis-dataset сводке с 64 buckets. |
| Stage Two normalization | Реализованные CLI routes покрывают storage bootstrap, catalog ingestion, parser registry seed, parser coverage, mark-ready, normalization точного bucket, benchmark runs, splitting больших line-based files, DuckDB checks, leakage checks и traceability. |
| Stage Three feature/model-ready preparation | Реализован CLI `python manage.py stage-three ...` для readiness gate, feature catalog, runtime backend probe, feature extraction, label alignment, sequence build, model-ready build, quality checks, leakage/traceability checks и final report. |
| Stage Three reports | Task01-Task20 reports пишутся в `PATH_DATA_STORAGE/reports/{ru,en}/stage-three`; `final-report` явно сообщает `READY_FOR_STAGE_FOUR` или `NOT_READY_FOR_STAGE_FOUR`. |
| Current docs | Stage One/Stage Two/Stage Three architecture, normalization, parser strategy, labels, leakage, performance controls и traceability задокументированы в `analysis-dataset/`, `normalization/`, `stage-three/`, `code-documentation/`. |

## Что является proposal/планом, а не подтвержденной реализацией

| Область | Proposal-level утверждение | Gap |
| --- | --- | --- |
| Physical resampling strategy | SMOTE/undersampling как production default. | Stage Three поддерживает class balance reporting и TRAIN-only balancing constraints; SMOTE не должен быть default до отдельной проверки. |
| Random Forest / XGBoost | Baseline classifiers. | Параметры, training code и tuning не зафиксированы. |
| CNN | Deep learning branch for local feature patterns. | Архитектура не указана. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Stage Three может готовить sequence artifacts; модель LSTM, training config и evaluation остаются Stage Four. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Формула/веса/threshold не заданы. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны и не реализованы. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | Значение `k`, statistical tests, seeds и reports не зафиксированы. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware, Python/lib versions для ML stack не указаны; `requirements.txt` содержит только `python-dotenv` и `rich` без версий. |

## Текущие замечания по реализации

Сверено с кодом 2026-07-08:

- Stage Two routing находится в `scripts/stage_two/cli.py`; `config.manage_commands` является старым печатным списком команд и не полон для текущего Stage Two.
- `python manage.py stage-two --help` в текущем состоянии попадает в fallback и не должен использоваться как source of truth по командам.
- `normalize-format` и `benchmark-normalization` перед запуском применяют resource profiles и format-specific runtime policy. `normalize-all` получает общие runtime options, но не применяет per-format policy на уровне CLI route.
- Реализованные quality gates: parser reports, post-run validation для `normalize-format`, DuckDB checks, leakage checks и traceability lookup. Это проверки вокруг normalized/features/model-ready artifacts, а не полный ML experiment pipeline.
- Репозиторий подтверждает Stage Three CLI для feature extraction, DNS supervised rebalance, model-ready build, checks и final report. RF/XGBoost/CNN/LSTM training, SHAP analysis и evaluation reports остаются не реализованными в Stage Four.

## QA по разделам proposal 3.3-3.8

### Dataset Selection

| Вопрос | Ответ |
| --- | --- |
| Какие датасеты использовались? | DNS и Host datasets перечислены в [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md). |
| Есть ли total samples / class split / feature count? | Для большинства источников нет подтвержденных чисел. Для `CIC-Bell-DNS-2021` указано около 1,000,000 доменов и около 99% benign как утверждение документации. |
| Network и Host — отдельные датасеты? | Да, отдельные datasets и отдельные pipelines. |
| Host features симулировались из network? | В коде такой реализации не найдено; в proposal это только возможная feature-level simulation при отсутствии paired данных. |

### Data Preprocessing

| Вопрос | Ответ |
| --- | --- |
| Missing values | Реализованы Stage Three preprocessing utilities и reports; production readiness зависит от конкретного `experiment_id` и финальных checks. |
| Normalization/scaling | Scaling profiles и preprocessing metadata реализованы как Stage Three preparation layer. |
| Categorical encoding | Реализованы Stage Three encoding utilities; TEST не используется для fit. |
| Train/test split | Числовой split не задан; есть role-based strategy и плановая stratified k-fold CV. |

### Class Imbalance

Stage Three формирует class balance reports и class-weight metadata; physical resampling разрешается только для TRAIN и не является default для MVP DNS path.

### Model Architecture

| Модель | Состояние |
| --- | --- |
| Random Forest | Proposal-level; параметры/tuning не указаны. |
| XGBoost | Proposal-level; параметры/tuning не указаны. |
| CNN | Proposal-level; архитектура не указана. |
| LSTM | Proposal-level; есть только идея sequence-level binary classification. |

### Sequence Construction

| Вопрос | Состояние |
| --- | --- |
| Sequence length | Stage Three содержит sequence/window builder; production policy должна фиксироваться в experiment metadata. |
| Window step / overlap | Должны быть заданы в Stage Three sequence policy перед Stage Four training. |
| Multi-modal time alignment | Hybrid alignment остается production expansion area. |
| Labels for sequence windows | Stage Three поддерживает label policies; конкретная политика должна быть зафиксирована для experiment_id. |

### Decision Fusion

Proposal говорит о **late fusion** через агрегацию вероятностей classification и sequence components. Веса, формула и threshold policy не указаны.

### SHAP

Упоминается SHAP-based feature attribution. Не указано:

- TreeSHAP для RF/XGBoost;
- DeepSHAP для CNN/LSTM;
- KernelSHAP fallback;
- способ explainability для sequence windows.

### Experimental Environment

| Параметр | Состояние |
| --- | --- |
| Number of CV folds | Не указан. |
| Statistical tests | Не указаны. |
| Hardware | Не указан. |
| Software versions | ML stack не зафиксирован. |
| Random seed | Не указан. |

## Риски и рекомендации

| Риск | Где возникает | Последствие | Рекомендация |
| --- | --- | --- | --- |
| Host/network dataset incompatibility | Dataset strategy / hybrid architecture. | Нельзя доказать raw-level correlation. | Использовать feature-level integration, явно документировать assumptions. |
| TEST leakage | Feature extraction / model-ready artifacts. | Завышенная оценка качества. | Запретить TEST для training, fit preprocessing, feature selection, threshold tuning. |
| Label leakage | Filename/scenario/path fields. | Модель учит источник, а не поведение. | Исключать label/source/path/scenario fields из X. |
| Weak labels | Filename, IDS alert, scenario metadata. | Неверная supervised target разметка. | Использовать `label_status`, confidence и mapping rules. |
| Missing timestamps | TXT/trace/binary sources. | Неверные temporal features. | Использовать `timestamp=null`, `timestamp_type=missing` или event order; не подставлять current time. |
| Large files | PCAP, BSON, JSON, netflow, txt traces. | Memory/performance failures. | Streaming parsers, batch writes, DuckDB/Parquet checks. |
| Schema drift | Mixed CSV/JSON/log schemas. | Broken normalization/features. | Schema-aware parsers и per-format quality reports. |
| Explainability over proxy fields | SHAP / model-ready X. | Объяснения будут misleading. | Leakage checks перед SHAP, separate audit fields. |

## Follow-up tasks

1. Для каждого `experiment_id` прогонять `stage-three final-report` и не переходить в Stage Four без `READY_FOR_STAGE_FOUR`.
2. Расширить production Stage Three path на Host/Network/Hybrid feature groups после DNS MVP.
3. Зафиксировать production sequence window policy: length, step, overlap, label assignment, time alignment.
4. Добавить model configs для RF/XGBoost/CNN/LSTM в Stage Four.
5. Описать late fusion formula и threshold policy.
6. Выбрать SHAP variants по model family.
7. Добавить experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
8. Добавить Stage Four training/evaluation reports.

## Связанные документы

- [project_overview_and_research_context.md](ru/project_overview_and_research_context.md)
- [repository_analysis.md](ru/repository_analysis.md)
- [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](ru/analysis-dataset/README.md)
- [normalization/README.md](ru/normalization/README.md)
- [stage-three/README.md](ru/stage-three/README.md)
- [code-documentation/README.md](ru/code-documentation/README.md)


---

## Источник: `docs/ru/stage-three/performance_tuning.md`

# Stage Three Performance Tuning

## Default policy

Stage Three должен быть CPU-first и streaming-first:

- не загружать крупные datasets целиком в pandas/DataFrame memory;
- использовать Parquet column projection и predicate pushdown;
- держать PostgreSQL как metadata/catalog layer;
- хранить крупные feature/model-ready данные в Parquet;
- использовать GPU только после runtime probe и проверки корректности.

## Рекомендуемый профиль для текущего ПК

```text
STAGE_THREE_DEFAULT_PROFILE=balanced
STAGE_THREE_ACCELERATION_BACKEND=auto
STAGE_THREE_RESERVED_RAM_GB=8
STAGE_THREE_SOFT_RAM_LIMIT_GB=48
STAGE_THREE_HARD_RAM_LIMIT_GB=56
STAGE_THREE_DEFAULT_WORKERS=8
STAGE_THREE_MAX_WORKERS=12
STAGE_THREE_DB_WORKERS=4
STAGE_THREE_BATCH_ROWS=250000
STAGE_THREE_PARQUET_ROW_GROUP_SIZE=250000
STAGE_THREE_GPU_MEMORY_SOFT_LIMIT_GB=12
STAGE_THREE_GPU_MEMORY_HARD_LIMIT_GB=14
```

## CPU path

CPU path является обязательным production fallback. Предпочтительные инструменты:

- `pyarrow.dataset` для streaming/batch Parquet scans;
- `duckdb` для out-of-core SQL checks;
- `polars` lazy для тяжелых transforms, если он уже используется в реализации;
- bounded worker pools вместо запуска всех CPU threads.

## GPU path

GPU optional. На native Windows нельзя делать RAPIDS/cuDF обязательной зависимостью. В `auto` mode GPU можно использовать только если:

- dependency доступна;
- small correctness probe совпал с CPU output в допустимом tolerance;
- VRAM/RAM остаются в лимитах;
- CPU fallback остается рабочим.

## Workers and memory

Не стартовать сразу все 28 CPU threads. Практический порядок:

1. Начать с `STAGE_THREE_DEFAULT_WORKERS=8`.
2. Проверить runtime report и RAM usage.
3. Повышать workers только если storage, DB и memory остаются стабильными.
4. При memory pressure уменьшить `STAGE_THREE_BATCH_ROWS` и workers.

## MVP DNS path

Для первого результата держать scope узким:

- branch: `dns`;
- profile: `tree_unscaled`;
- target: `label_binary`;
- feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`;
- no SMOTE/resampling;
- class imbalance обрабатывать на Stage Four через `class_weight` или `scale_pos_weight`.

## Production path

Для production expansion:

- разделить jobs по branch/role/feature_group;
- использовать `--resume`;
- запускать checks после каждого крупного batch;
- не смешивать output разных experiment_id;
- писать final report для каждого production experiment_id.


---

## Источник: `docs/ru/stage-three/README.md`

# Stage Three

Stage Three преобразует результаты Stage Two из normalized Parquet в split-safe, leakage-safe и traceable model-ready artifacts для Stage Four.

Основная линия данных:

```text
raw -> normalized -> features -> model-ready -> training/evaluation
```

Stage Three закрывает только участок:

```text
normalized -> features -> model-ready
```

Обучение RF/XGBoost/CNN/LSTM, подбор гиперпараметров, threshold tuning, SHAP/XAI и итоговая экспериментальная оценка относятся к Stage Four.

## Документы

- [usage_guide.md](ru/stage-three/usage_guide.md) - порядок запуска Stage Three.
- [stage_three_commands.md](ru/stage-three/stage_three_commands.md) - справочник CLI-команд.
- [performance_tuning.md](ru/stage-three/performance_tuning.md) - runtime-профиль, RAM/GPU policy и безопасные настройки производительности.

## Минимальный DNS MVP path

1. Проверить готовность Stage Two для DNS TRAIN/VALIDATION/TEST.
2. Собрать и проверить feature catalog.
3. Извлечь DNS feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`.
4. Собрать `tree_unscaled` model-ready artifacts для `label_binary`.
5. При необходимости построить воспроизводимый DNS supervised 70/30 split через `rebalance-dns-supervised`.
6. Запустить quality checks.
7. Запустить leakage/traceability checks.
8. Сгенерировать final report.
9. Переходить к Stage Four только если final report показывает `READY_FOR_STAGE_FOUR`.

## Production path

После DNS MVP расширить Stage Three на Host/Network/Hybrid:

- добавить и прогнать Host/Network feature groups;
- включить sequence artifacts, если нужны CNN/LSTM/LSTM-like модели;
- использовать отдельные preprocessing profiles для tree/DL/linear моделей;
- прогнать quality/leakage/traceability checks для каждого production `experiment_id`;
- не смешивать TRAIN, VALIDATION и TEST;
- не fit-ить imputer/scaler/encoder на VALIDATION или TEST.

## Итоговый отчет

Команда:

```powershell
python manage.py stage-three final-report --experiment-id <id>
```

Отчеты пишутся в:

- `C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task20-stage-three-final-report-and-documentation.md`
- `C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task20-stage-three-final-report-and-documentation.md`


---

## Источник: `docs/ru/stage-three/stage_three_commands.md`

# Stage Three Command Reference

Все команды запускаются из корня проекта `C:\Users\Public\PythonProjects\Proposal`.

## Help

```powershell
python manage.py stage-three --help
```

## validate-inputs

```powershell
python manage.py stage-three validate-inputs --branch <dns|host|network|hybrid> --role <TRAIN|VALIDATION|TEST>
```

Проверяет, можно ли использовать normalized artifacts из Stage Two как вход Stage Three.

## build-feature-catalog

```powershell
python manage.py stage-three build-feature-catalog [--feature-group <name>]
```

Валидирует machine-readable feature catalog и пишет отчеты Task05.

## probe-runtime-backend

```powershell
python manage.py stage-three probe-runtime-backend --backend <auto|cpu|gpu> [--profile safe|balanced|fast|aggressive] [--batch-rows <rows>] [--reserved-ram-gb <gb>] [--soft-ram-limit-gb <gb>] [--hard-ram-limit-gb <gb>] [--skip-probe]
```

Резолвит runtime backend и memory guard settings.

## extract-features

```powershell
python manage.py stage-three extract-features --branch <branch> --role <role> --feature-group <name> [--experiment-id <id>] [--resume] [--profile safe|balanced|fast|aggressive] [--batch-rows <rows>] [--reserved-ram-gb <gb>] [--soft-ram-limit-gb <gb>] [--hard-ram-limit-gb <gb>] [--workers <count>]
```

Читает normalized Parquet, создает feature artifacts и регистрирует их в catalog.

## align-labels

```powershell
python manage.py stage-three align-labels --branch <branch> --role <role> --label-policy explicit_only [--experiment-id <id>] [--resume]
```

Поддерживаемые policies:

- `explicit_only`
- `any_attack_in_window`
- `majority_label`
- `last_event_label`
- `weak_allowed_with_confidence`

## build-sequences

```powershell
python manage.py stage-three build-sequences --branch <branch> [--role <role>] [--feature-group <name>] [--experiment-id <id>] [--resume]
```

Создает sequence/window artifacts для downstream DL-моделей, если production path требует sequence branch.

## build-model-ready

```powershell
python manage.py stage-three build-model-ready --experiment-id <id> --branch <branch> --target label_binary --preprocessing-profile tree_unscaled [--role <role>] [--feature-group <name>] [--include-sequences] [--resume]
```

Собирает X/y/metadata/traceability, split index и preprocessing metadata.

## rebalance-dns-supervised

```powershell
python manage.py stage-three rebalance-dns-supervised [--experiment-id dns_rebalanced_70_30_v1] [--feature-group dns_lexical] [--target label_binary] [--preprocessing-profile tree_unscaled] [--overwrite] [--apply] [--apply-catalog] [--deactivate-existing-experiment <id>] [--dry-run]
```

Готовит воспроизводимый DNS supervised 70/30 model-ready split. Без `--apply` команда работает как audit/dry-run. `--apply-catalog` используется только вместе с осознанным применением результата к catalog metadata.

## run-quality-checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Проверяет schema, empty artifacts, dtype consistency, class balance, label coverage и model-ready contracts.

## run-leakage-checks

```powershell
python manage.py stage-three run-leakage-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Проверяет forbidden X columns, TEST leakage, preprocessing fit role, balancing policy и traceability chain.

## trace-artifact

```powershell
python manage.py stage-three trace-artifact <model_ready_artifact_id>
python manage.py stage-three trace-artifact --experiment-id <id>
```

Восстанавливает lineage:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset -> raw source
```

## final-report

```powershell
python manage.py stage-three final-report --experiment-id <id> [--branch <branch>]
```

Пишет RU/EN final report Task20 и выводит Stage Four readiness status.


---

## Источник: `docs/ru/stage-three/usage_guide.md`

# Stage Three Usage Guide

## Предусловия

Перед Stage Three должны быть готовы Stage Two artifacts:

- normalized Parquet artifacts зарегистрированы в PostgreSQL Catalog;
- parser runs завершены без blocking failures для нужных branch/role;
- Stage Two quality/leakage/traceability checks пройдены;
- `PATH_DATA_STORAGE` и `DATABASE_URL` заданы в `.env`.

Рабочее окружение:

```powershell
cmd /c "C:\ProgramData\Anaconda3\condabin\conda.bat activate C:\Users\fmark\.conda\envs\proposal && python manage.py stage-three --help"
```

## Последовательность запуска

### 1. Validate Stage Two inputs

```powershell
python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three validate-inputs --branch dns --role VALIDATION
python manage.py stage-three validate-inputs --branch dns --role TEST
```

Если команда возвращает `FAIL`, downstream-команды Stage Three для этой ветки запускать нельзя.

### 2. Build feature catalog

```powershell
python manage.py stage-three build-feature-catalog
```

Команда валидирует `scripts/stage_three/feature_catalog/feature_catalog.yml` и пишет normalized JSON snapshot.

### 3. Probe runtime backend

```powershell
python manage.py stage-three probe-runtime-backend --backend auto
```

Default policy: CPU-first, streaming-first. GPU используется только после capability/correctness checks.

### 4. Extract DNS MVP features

```powershell
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_entropy --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_temporal --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role VALIDATION --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TEST --feature-group dns_lexical --experiment-id exp001 --resume
```

Для production повторить extraction для всех нужных feature groups и roles.

### 5. Optional Host feature extraction

Host path шире DNS MVP и должен запускаться только после отдельного `validate-inputs` для каждой роли:

```powershell
python manage.py stage-three validate-inputs --branch host --role TRAIN
python manage.py stage-three validate-inputs --branch host --role VALIDATION
python manage.py stage-three validate-inputs --branch host --role TEST
```

Если любая Host role возвращает `FAIL`, extraction/model-ready шаги для этой роли запускать нельзя. `WARN` допустим только после явного принятия parser/schema/label рисков из отчета.

Текущие поддержанные Host feature groups:

- `host_syscall`
- `host_process`
- `host_auth`
- `host_file_access`
- `host_metrics`
- `host_logs`

Минимальный Host extraction запуск:

```powershell
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_process --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_auth --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_file_access --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_metrics --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_logs --experiment-id exp001-host --resume
```

```powershell
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_syscall --experiment-id exp001-host --resume `
  --profile aggressive --batch-rows 1000000 --reserved-ram-gb 10 --soft-ram-limit-gb 50 --hard-ram-limit-gb 54
```

Для полноценного Host experiment повторить нужные feature groups для `VALIDATION` и `TEST`:

```powershell
python manage.py stage-three extract-features --branch host --role VALIDATION --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TEST --feature-group host_syscall --experiment-id exp001-host --resume
```

Sequence artifacts нужны только если downstream Stage Four будет использовать sequence/DL-модели:

```powershell
python manage.py stage-three build-sequences --branch host --role TRAIN --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three build-sequences --branch host --role VALIDATION --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three build-sequences --branch host --role TEST --feature-group host_syscall --experiment-id exp001-host --resume
```

Host ограничения:

- Host `TEST` используется только для final evaluation/inference.
- Большинство Host источников не имеют embedded labels; missing labels должны оставаться `unlabeled`.
- Mixed schemas и большие `txt`/`json`/`bson`/`log` inputs требуют проверки Stage Two parser reports до Stage Three.
- Hybrid/Host-Network correlation не является частью минимального Host path и должен идти отдельным experiment_id.

### 6. Align labels

```powershell
python manage.py stage-three align-labels --branch dns --role TRAIN --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role VALIDATION --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role TEST --label-policy explicit_only --experiment-id exp001 --resume
```

Для Host использовать отдельный experiment_id:

```powershell
python manage.py stage-three align-labels --branch host --role TRAIN --label-policy explicit_only --experiment-id exp001-host --resume
python manage.py stage-three align-labels --branch host --role VALIDATION --label-policy explicit_only --experiment-id exp001-host --resume
python manage.py stage-three align-labels --branch host --role TEST --label-policy explicit_only --experiment-id exp001-host --resume
```

Labels не должны попадать в model-ready X. Missing labels остаются `unlabeled`, а не превращаются в benign.

### 7. Build model-ready artifacts

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
```

Host model-ready artifacts собираются отдельно:

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001-host --branch host --target label_binary --preprocessing-profile tree_unscaled --resume
```

Ожидаемые outputs:

- `X.parquet`
- `y.parquet`
- `metadata.parquet`
- `traceability.parquet`
- `split_index.parquet`
- `preprocessing_metadata.parquet`

### 7.1. DNS supervised 70/30 rebalanced split

Для DNS supervised baseline используется отдельный воспроизводимый split policy
`dns_supervised_70_30_v1`. Он не удаляет raw-файлы физически, сначала выполняет
dry-run audit, затем при `--apply` пишет новый model-ready experiment:

```powershell
python manage.py stage-three rebalance-dns-supervised --experiment-id dns_rebalanced_70_30_v1

python manage.py stage-three rebalance-dns-supervised `
  --experiment-id dns_rebalanced_70_30_v1 `
  --apply `
  --apply-catalog `
  --deactivate-existing-experiment exp001
```

Политика:

- итоговый supervised total: `12,267,021`;
- `TRAIN`: `6,010,841` normal / `2,576,074` attack;
- `VALIDATION`: `1,288,037` normal / `552,016` attack;
- `TEST`: `1,288,037` normal / `552,016` attack;
- текущий битый DNS `TEST/csv` и его chunked downstream artifacts исключаются;
- `VALIDATION/pcap/ens33-dns_amplification_attack.pcap` исключается полностью;
- `VALIDATION/pcap/ens33-dns_amplification_attack__f291ed87a1.pcap` используется только в пределах global target;
- `label_binary=NULL` не включается в supervised split;
- `X.parquet` содержит только DNS lexical feature columns, без labels/source/path/role fields.

Отчет:

```text
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
```

Вердикт: DNS model-ready данные готовы для обучения supervised tabular модели.
Использовать только experiment `dns_rebalanced_70_30_v1`.

Полный model-ready root:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled
```

Ключевые файлы:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\split_index.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\preprocessing_metadata.parquet
```

Проверочные отчеты:

```text
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
```

Важно: если сохранять уже существующие `TRAIN` attack rows (`409,076`) и одновременно
держать global target `attack=3,680,106`, из ограничиваемого attack-source в итоговый
supervised split входит `3,271,030` rows. Значение `3,680,106` остается верхней
границей для source, но не количеством, которое можно дополнительно добавить без
нарушения global 70/30 target.

### 8. Run checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three run-quality-checks --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-leakage-checks --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-quality-checks --experiment-id exp001-host
python manage.py stage-three run-leakage-checks --experiment-id exp001-host
```

Blocking failures должны быть исправлены до Stage Four.
Для `dns_rebalanced_70_30_v1` `run-quality-checks` должен возвращать `PASS`
без `blocking_issues` и без предупреждений по timestamp. `run-leakage-checks` для этого
experiment должен возвращать `PASS`.

### 9. Generate final report

```powershell
python manage.py stage-three final-report --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001-host
```

Final report сообщает `READY_FOR_STAGE_FOUR` или `NOT_READY_FOR_STAGE_FOUR` и перечисляет explicit gaps.

## Правила безопасности данных

- TEST нельзя использовать для training, fit preprocessing, feature selection или threshold tuning.
- VALIDATION/TEST нельзя балансировать через resampling.
- `label_*`, source/path/parser/raw/metadata/traceability поля нельзя включать в X.
- Stage Three не должен читать raw files как основной источник.
- PostgreSQL используется как catalog/metadata layer; крупные данные остаются в Parquet.

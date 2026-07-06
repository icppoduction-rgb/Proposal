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

Актуальные runbooks: [stage-three/usage_guide.md](stage-three/usage_guide.md) и [stage-three/stage_three_commands.md](stage-three/stage_three_commands.md).

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

# Feature extraction map and feature catalogue

This document merges `dataset_feature_extraction_map.md`, `feature_catalogue_full.md`, and feature-related sections from `functional_project_cheatsheet.md`. It defines the contract for Stage Three feature extraction, Parquet artifacts, and model-ready datasets.

## Current Stage Three Implementation

The machine-readable feature catalog lives at `scripts/stage_three/feature_catalog/feature_catalog.yml`.

Stage Three CLI:

```bash
python manage.py stage-three build-feature-catalog
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001
```

Current runbooks: [stage-three/usage_guide.md](stage-three/usage_guide.md) and [stage-three/stage_three_commands.md](stage-three/stage_three_commands.md).

## Principles

1. `TRAIN`, `VALIDATION`, and `TEST` are not mixed.
2. DNS and Host are not joined at raw level.
3. Labels are not input features.
4. Leakage fields are excluded from model-ready `X`.
5. Sequence features are built separately from tabular aggregate features.
6. A missing label does not mean benign.
7. Timestamp ordering is used only when a timestamp or event order exists; current time is not inserted.

## Calculation levels

| Level | Description | Models |
| --- | --- | --- |
| Event-level | One DNS query, syscall, process event, auth event, packet, or log event. | RF, XGBoost, CNN |
| Window-level | Aggregates by host/source_ip/user/domain/process over a time window. | RF, XGBoost, CNN |
| Flow-level | 5-tuple / network flow. | RF, XGBoost |
| Trace-level | Syscall/API/module trace as a sequence. | CNN, LSTM |
| Sequence-level | Ordered multi-source events, planned size 50-100 events. | LSTM |
| Hybrid-level | Host + network/DNS correlation by time, host, scenario, or mapping. | Late fusion, RF/XGBoost, LSTM |

## Dataset to feature map

| Dataset / source | Role | Main feature groups | Attack stages | Use |
| --- | --- | --- | --- | --- |
| CIC-Bell-DNS-EXF-2021 | `TRAIN` | DNS lexical, entropy, RR/TTL, query-rate, inter-query intervals, unique subdomain ratio. | Exfiltration | Attack-class DNS source. |
| CIC-Bell-DNS-2021 | `TRAIN` + `VALIDATION` split | Same DNS features, benign baseline, FP-control. | Exfiltration / benign baseline | Training normal DNS behaviour and threshold tuning. |
| Mendeley DNS Exfiltration | `TEST` | DNS lexical/temporal/numeric table, source IP windows. | Exfiltration | Final generalization check; not training. |
| ADFA IDS | `TRAIN` | Syscall frequencies, n-grams, transitions, trace length, collection syscalls. | Collection, Data Staging | HIDS/syscall benchmark. |
| LID-DS 2021 | `TRAIN` | Syscall/API sequence, syscall args, file access, inter-arrival timings. | Collection, Data Staging, Pre-exfiltration | Main host sequence source. |
| LID-DS 2019 | `VALIDATION` | Same syscall/sequence features as LID-DS 2021. | Collection, Data Staging | Cross-version validation. |
| Maintainable Log Dataset | `TRAIN` | Log templates, event volume, multi-stage event sequences, file access/log correlation. | Reconnaissance, Collection, Data Staging | Enterprise log behaviour. |
| LANL Dataset | `VALIDATION` | Auth frequency, user-host interaction, failed login ratio, privileged account usage, lateral movement graph. | Privilege Escalation, Lateral Movement | Enterprise behaviour validation. |
| Windows Event Log / OTRF | `VALIDATION` | EventID, process tree, PowerShell/command line, logon/auth, object access, SourceAddress/DestAddress. | Reconnaissance, Privilege Escalation, Lateral Movement | SOC-oriented Windows/Sysmon validation. |
| Unified Host-Network / LANL | `TEST` | Host auth/process + netflow + correlation features. | Full lifecycle | Final hybrid test. |
| ISOT Cloud IDS | `TEST` | CPU/memory/I/O/log/cloud workload anomalies. | Data Staging | Cloud portability check. |
| Dynamic Malware Analysis | `TEST` | API/syscall events, command line/path/module tokens, process tree, sandbox lifecycle. | Collection, Data Staging, Pre-exfiltration | Malware-driven host behaviour check. |

## DNS feature catalogue

| Group | Example features | Calculation | Parser dependency |
| --- | --- | --- | --- |
| Lexical | `dns_query_length`, `dns_subdomain_length`, `dns_subdomain_depth`, `dns_label_count`, `dns_digit_count`, `dns_special_char_count`. | String parsing by qname/FQDN/subdomain. | DNS CSV/TXT/PCAP parser. |
| Entropy | `dns_entropy`, `dns_rr_name_entropy`, `url_token_entropy`. | Shannon entropy over domain/query/url tokens. | DNS parser + URL/domain tokenizer. |
| N-grams | `dns_1gram_frequency`, `dns_2gram_frequency`, `dns_3gram_frequency`. | Character/token n-gram counts. | Domain tokenizer. |
| Categorical/enrichment | `dns_tld`, `dns_sld`, `domain_age_days`, `name_server_count`, `unique_asn_count`, `unique_country_count`. | Extract/enrich and encode safely. | DNS parser + optional enrichment. |
| RR/protocol | `ttl_mean`, `ttl_variance`, `rr_count`, `rr_rate`, `rr_type_frequency_*`, `dns_qtype_frequency`, `dns_rcode_distribution`, `dns_nxdomain_rate`. | Aggregates by RR/query/response/window. | DNS packet/pcap.csv parser. |
| Temporal | `dns_inter_query_interval_stats`, `dns_query_rate`, `dns_queries_per_window`. | `diff(timestamp)` and count over sliding window. | Timestamp-aware DNS events. |

## Host and network feature catalogue

| Group | Example features | Sources |
| --- | --- | --- |
| Network/flow | `packet_count`, `byte_count`, `flow_duration`, `packet_size_mean`, `packet_size_std`, `protocol_distribution`, `src_port_frequency`, `dst_port_frequency`. | DNS pcap, Host cap/pcap/pcapng, netflow. |
| Syscall/API sequence | `syscall_frequency`, `syscall_ngram_2_frequency`, `syscall_ngram_3_frequency`, `syscall_transition_probability`, `unique_syscall_count`, `syscall_trace_length`. | ADFA, LID-DS, Host txt/sc/ghc/bson/json. |
| Collection indicators | `collection_syscall_count`, `directory_enumeration_count`, `file_access_count`, `file_access_rate`, `file_access_entropy`, `unique_file_count`, `sensitive_file_extension_count`. | Syscalls, logs, Windows object access, malware traces. |
| API/sandbox/trace | `api_descriptor_frequency`, `api_category_frequency`, `api_arg_token_count`, `trace_module_frequency`, `trace_module_transition_frequency`, `trace_density`. | Dynamic Malware, Host BSON/JSON/GHC. |
| Authentication | `login_success_count`, `login_failure_count`, `failed_login_ratio`, `failed_then_success_login_indicator`, `session_opened_count`, `session_duration_stats`, `sudo_activity_count`. | LANL, OTRF, auth logs, wls_day. |
| Windows/Sysmon/process | `event_id_frequency`, `security_event_sequence_entropy`, `logon_type_distribution`, `parent_child_process_count`, `process_name_frequency`, `command_line_entropy`, `encoded_powershell_indicator`, `rare_process_execution_score`. | OTRF, Windows Event Logs, Dynamic Malware. |
| Resource telemetry | `filesystem_used_pct_stats`, `disk_read_bytes_rate`, `disk_write_bytes_rate`, `cpu_total_pct_stats`, `memory_usage_stats`, `load_average_stats`. | Host metric logs, ISOT Cloud IDS. |
| Logs/templates | `log_event_count`, `log_volume_rate`, `log_level_frequency`, `warning_error_count`, `component_frequency`, `message_template_frequency`, `event_type_frequency`, `alert_count`. | Maintainable logs, syslog/messages/mainlog, sandbox logs. |
| Staging/compression | `archive_creation_count`, `compression_process_indicator`, `process_path_entropy`, `suspicious_path_indicator`, `module_path_entropy`. | Windows/process logs, malware, command-line telemetry. |

## Hybrid and sequence catalogue

| Feature | Purpose |
| --- | --- |
| `host_network_time_delta` | Time lag between the nearest host event and network event. |
| `process_to_network_burst_score` | Process start followed by a network burst. |
| `auth_to_network_correlation` | Network flows after auth events/windows. |
| `file_to_network_correlation` | File access/data staging followed by network outflow. |
| `cpu_io_network_correlation` | Rolling correlation of CPU/disk/network spikes. |
| `cross_source_event_count` | Events from different sources in one unified window. |
| `sequence_window_event_count` | Number of events in an LSTM window. |
| `sequence_event_type_entropy` | Entropy over ordered event type tokens. |
| `process_file_network_sequence` | Pattern: file access -> archive/compress -> outbound network event. |
| `stage_transition_pattern` | Transitions across Reconnaissance, Privilege Escalation, Lateral Movement, Collection, Data Staging, Exfiltration. |

## Minimum feature schema for Parquet artifacts

### Traceability fields

| Field | Purpose | Use as model feature |
| --- | --- | --- |
| `event_id` | Normalized event ID. | No |
| `source_file_id` | Raw file ID from catalog. | No |
| `source_row_id` / `packet_id` | Row/packet/event index. | No |
| `dataset_domain` | `dns`, `host`, `network`, `hybrid`. | No |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`. | No |
| `dataset_name` | Dataset name. | No, audit/reporting only |
| `dataset_format` | csv, pcap, json, log, bson, txt, etc. | No, parser/debug only |
| `parser_name` / `parser_version` | Parser traceability. | No |
| `event_timestamp` | Normalized event time. | Derived time features / ordering only |
| `window_id` | Window ID. | No |
| `sequence_id` | Sequence-window ID. | No |

### Label fields

| Field | Purpose |
| --- | --- |
| `label_binary` | 0=benign, 1=attack/exfiltration/malicious, NULL=unknown. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, collection, data_staging, unknown. |
| `label_subtype` | Specific subtype/scenario, if available. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 explicit; 0.7-0.9 inferred; 0.4-0.7 weak; 0 unlabeled. |
| `label_mapping_rule_id` | Label resolver rule ID. |

## Exclude from model-ready X

| Field / group | Reason |
| --- | --- |
| `source_file`, basename, full path | May encode `benign`, `malware`, `attack`, `exfiltration`. |
| `dataset_role` | TRAIN/VALIDATION/TEST leakage. |
| `dataset_name` | Model may memorize dataset instead of behaviour. |
| `scenario_name`, `image_name` | Label join/evaluation metadata only. |
| `label_*` | Target/audit fields, not input features. |
| Raw payload/body | Project scope is metadata/behavioural detection, not payload inspection. |
| Absolute local paths | Not portable and leakage-prone. |

## Implementation priority

| Priority | Feature groups |
| --- | --- |
| P0 | DNS lexical/entropy/temporal/protocol; host syscall/API; auth; Windows/Sysmon; network volume/ports; sequence window basics; stage transition patterns. |
| P1 | Domain enrichment; hybrid correlations; resource telemetry; archive/compression; sensitive file access; graph/baseline features. |
| P2 | Advanced command-line tokenization; template mining; long-term per-user/per-host baselines; feature stability checks. |

## Stage Two and Stage Three Link

| Stage Two layer | Requirement |
| --- | --- |
| Parser pipeline | Each feature group depends on a specific parser output and normalized schema. |
| PostgreSQL Catalog | Stores metadata, paths, statuses, hashes, reports, not large feature tables. |
| Parquet artifacts | Store normalized events, feature windows, sequence windows, model-ready X/y. |
| DuckDB checks | Validate Parquet counts, schema drift, split contamination, leakage columns. |
| LabelResolver | Fills label fields separately from X features. |
| Traceability | Feature/model-ready artifacts must link back to normalized -> parser run -> raw dataset file. |
| Stage Three final report | Records whether a concrete `experiment_id` is ready for Stage Four. |

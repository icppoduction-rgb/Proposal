# Labeling in DNS/Host Datasets

**Document for analyzing label availability and label mapping recommendations**

---

## Metadata

| Field | Value |
|---|---|
| Preparation date | 2026-06-12 |
| Sources | `general_host_train.md, general_host_validation.md, general_host_test.md, general_dns_train.md, general_dns_validation.md, general_dns_test.md` |

## Table of Contents

- [1. Document Purpose](#1-document-purpose)
- [2. Core Rules](#2-core-rules)
- [3. Recommended Canonical Label Schema](#3-recommended-canonical-label-schema)
- [4. Summary by Label Category](#4-summary-by-label-category)
- [5. Detailed Action Table by Source](#5-detailed-action-table-by-source)
- [6. Practical Rules for Adding Labels to Files Without Labels](#6-practical-rules-for-adding-labels-to-files-without-labels)
- [7. Recommended Label Resolver Algorithm](#7-recommended-label-resolver-algorithm)
- [8. Recommended `label_status` Values](#8-recommended-label_status-values)
- [9. Minimum Implementation Tasks](#9-minimum-implementation-tasks)
- [10. Final Decision](#10-final-decision)

---

## 1. Document Purpose

This document records which dataset formats/files already contain labels, where labels are missing, and where labels can only be obtained partially. It also explains how to correctly add labels for files without embedded annotations so that supervised training/evaluation is not compromised and data leakage is avoided.

## 2. Core Rules

1. Absence of a label does not mean benign.
2. TEST data must not be used for training, even when labels are present.
3. Labels obtained from a filename, directory, scenario metadata, or IDS alert must have `label_source` and `label_status`.
4. Weak labels are not equivalent to ground truth. Final metrics must separate `explicit_label` from `inferred_label` / `weak_label`.
5. For files without labels, store `label_binary=NULL`, `label_family=unknown`, and `label_status=unlabeled` until a reliable label mapping is found.
6. Every label join must preserve traceability: `raw_file -> normalized_event -> feature/window/sequence -> model_ready_sample`.

## 3. Recommended Canonical Label Schema

Minimum fields to add to normalized artifacts / Parquet / model-ready datasets:

| Поле | Назначение |
|---|---|
| `label_binary` | 0=benign, 1=malicious/attack/exfiltration, NULL=unknown |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, unknown |
| `label_subtype` | Specific subtype/scenario, if available |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label |
| `label_confidence` | 1.0 for explicit, 0.7-0.9 for inferred, 0.4-0.7 for weak, 0 for unlabeled |
| `label_mapping_rule_id` | Mapping rule ID |
| `dataset_domain` | dns / host |
| `dataset_role` | TRAIN / VALIDATION / TEST |
| `dataset_format` | csv, pcap, pcap.csv, json, log, bson, ... |
| `source_file` | Original path/file name |
| `source_row_id/event_id` | Row/packet/event, if applicable |

## 4. Summary by Label Category

| Category | Count |
|---|---:|
| Total analyzed format buckets | 66 |
| With direct labels (`Label found = yes`) | 5 |
| With partial labels / class hints | 6 |
| Without embedded labels | 55 |

### 4.1. Formats Where Labels Are Found Directly or as Embedded Fields

| Source | Domain | Role | Format | Files | Label field | Values | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_host_train.md | Host | TRAIN | cpu.log | 13 | labels | crack_passwords, escalate | partially |
| general_host_train.md | Host | TRAIN | csv | 101 | columns 7, 8, 9 | normal/attack categories + binary label (0/1) | yes |
| general_host_train.md | Host | TRAIN | json | 219 | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | partially |
| general_host_validation.md | Host | VALIDATION | csv | 6 | is_executing_exploit | False: 5813, True: 187 | yes, as validation labels |
| general_host_test.md | Host | TEST | csv | 3 | label in separate label CSV files; `attack_dataset.csv` does not contain labels | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 | partially; requires join by IP and TEST must not be used for training |

### 4.2. Formats Where Labels Are Partial or Inferred Through `filename` / `class_hint`

| Source | Domain | Role | Format | Files | Field/source | Values | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_dns_train.md | DNS | TRAIN | csv | 8 | filename / class_hint | benign, malware, phishing, spam | yes, after assigning the label from the filename |
| general_dns_train.md | DNS | TRAIN | pcap | 4 | filename | benign, malware, phishing, spam | yes, after assigning the label from the filename |
| general_dns_train.md | DNS | TRAIN | pcap.csv | 14 | filename / class_hint | audio, benign, compressed, exe, image, text, video | yes, after assigning the label from the filename |
| general_dns_validation.md | DNS | VALIDATION | pcap | 5 | filename | attack, benign | yes, after assigning the label from the filename |
| general_dns_validation.md | DNS | VALIDATION | txt | 3 | filename / class_hint | unknown, benign | partially, only after explicit class assignment |
| general_dns_test.md | DNS | TEST | csv | 1 | `label_or_flag` | boolean-like flag в sample | no, this is the TEST role; use only for evaluation |

### 4.3. Formats Where Labels Were Not Found

| Source | Domain | Role | Format | Files | Timestamp | Time field | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_host_train.md | Host | TRAIN | auth.log | 23 | yes | @timestamp, message(syslog prefix) | partially |
| general_host_train.md | Host | TRAIN | diskio.log | 12 | yes | @timestamp | no |
| general_host_train.md | Host | TRAIN | filesystem.log | 12 | yes | @timestamp | no |
| general_host_train.md | Host | TRAIN | fsstat.log | 12 | yes | @timestamp | no |
| general_host_train.md | Host | TRAIN | ghc | 56158 | no | - | partially |
| general_host_train.md | Host | TRAIN | info | 3 | yes | @timestamp, message(syslog prefix) | partially |
| general_host_train.md | Host | TRAIN | journal | 17 | no | - | no |
| general_host_train.md | Host | TRAIN | journal~ | 1 | no | - | no |
| general_host_train.md | Host | TRAIN | json-1 | 1 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | load.log | 12 | no | time.container_ready.absolute, timestamp | no |
| general_host_train.md | Host | TRAIN | log | 98 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-1 | 32 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-2 | 9 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-3 | 8 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mail-info-1 | 3 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mail-warn-1 | 2 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog | 3 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-1 | 3 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-2 | 3 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-3 | 3 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | memory.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | messages | 3 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | messages-1 | 3 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | netflow_ids | 50 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | network.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | pcap | 15 | no | - | no |
| general_host_train.md | Host | TRAIN | process.log | 2 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | process.summary.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | sc | 210 | yes | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | service.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | socket.summary.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog | 9 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-1 | 10 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-2 | 10 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-3 | 10 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-4 | 1 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | txt | 3170 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | uptime.log | 12 | no | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | xml | 40 | no | time.container_ready.absolute, timestamp | partially |
| general_host_validation.md | Host | VALIDATION | cap | 44 | yes | packet header ts_sec/ts_usec | partially; only with external labeling / scenario inferred from filename |
| general_host_validation.md | Host | VALIDATION | json | 130 | yes | TimeCreated, @timestamp | частично, при внешней разметке из scenario/file name |
| general_host_validation.md | Host | VALIDATION | netflow_day | 2 | yes | time | no without external labels |
| general_host_validation.md | Host | VALIDATION | pcap | 1 | yes | packet header ts_sec/ts_usec | partially; only with external labeling / scenario inferred from filename |
| general_host_validation.md | Host | VALIDATION | pcapng | 5 | yes | Enhanced Packet Block timestamp_high/timestamp_low | partially; only with external labeling / scenario inferred from filename |
| general_host_validation.md | Host | VALIDATION | txt | 6495 | yes | Time | нет без внешней разметки |
| general_host_validation.md | Host | VALIDATION | wls_day | 3 | yes | Time | no without external labels |
| general_host_test.md | Host | TEST | bson | 9005 | partially | порядок BSON-документов, числовые `t`/`h` в event-записях | no for TEST; external labels are required if they exist |
| general_host_test.md | Host | TEST | json | 7071 | yes | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` | нет для TEST; нужны внешние метки |
| general_host_test.md | Host | TEST | log | 4086 | yes | timestamp | no without external labels |
| general_host_test.md | Host | TEST | netflow_day | 2 | yes | time | no without external labels |
| general_host_test.md | Host | TEST | txt | 274419 | yes | Time | no without external labels |
| general_host_test.md | Host | TEST | wls_day | 3 | yes | Time | no without external labels |
| general_dns_test.md | DNS | TEST | pcap | 0 | no | - | no |
| general_dns_test.md | DNS | TEST | pcap.csv | 0 | no | - | no |

## 5. Detailed Action Table by Source

### 5.1. general_host_train.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | TRAIN | auth.log | 23 | NEEDS_CUSTOM_PARSER | no | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | cpu.log | 13 | PARTIALLY_SUPPORTED | yes | labels | crack_passwords, escalate | Использовать как частичные annotation labels: отделить metric rows от label/annotation rows, связать labels/rules с временными окнами по @timestamp/host, пометить label_status=weak_or_partial_label. Для финальных метрик желательно подтверждать через ground_truth/scenario mapping. |
| Host | TRAIN | csv | 101 | PARTIALLY_SUPPORTED | yes | columns 7, 8, 9 | normal/attack categories + binary label (0/1) | Использовать напрямую для supervised TRAIN/VALIDATION после нормализации: label_binary, label_family, label_subtype, label_source=embedded_column. |
| Host | TRAIN | diskio.log | 12 | PARTIALLY_SUPPORTED | no | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | filesystem.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | fsstat.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | ghc | 56158 | NEEDS_CUSTOM_PARSER | no | - | - | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | info | 3 | READY_FOR_FEATURE_EXTRACTION | no | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | journal | 17 | NEEDS_CUSTOM_PARSER | no | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | journal~ | 1 | NEEDS_CUSTOM_PARSER | no | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | json | 219 | NEEDS_CUSTOM_PARSER | yes | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Использовать только через schema-aware resolver: exploit=true/false может быть inferred label для scenario/window; container.role хранить как context, но не считать attack; alert использовать как weak label, а не ground truth. |
| Host | TRAIN | json-1 | 1 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | TRAIN | load.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | log | 98 | NEEDS_CUSTOM_PARSER | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-1 | 32 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-2 | 9 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-3 | 8 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mail-info-1 | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mail-warn-1 | 2 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-1 | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-2 | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-3 | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | memory.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | messages | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | messages-1 | 3 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | netflow_ids | 50 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | network.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | pcap | 15 | NEEDS_CUSTOM_PARSER | no | - | - | Встроенного label нет. Извлекать packet/flow признаки, затем искать внешний label по scenario/file name, timestamp, host/IP или ground_truth.csv. Не считать отсутствие label benign; при отсутствии связи — unlabeled/inference-only. |
| Host | TRAIN | process.log | 2 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | process.summary.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | sc | 210 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | service.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | socket.summary.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | syslog | 9 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-1 | 10 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-2 | 10 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-3 | 10 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-4 | 1 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | txt | 3170 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | uptime.log | 12 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | xml | 40 | READY_FOR_FEATURE_EXTRACTION | no | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |

### 5.2. general_host_validation.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | VALIDATION | cap | 44 | NEEDS_CUSTOM_PARSER | no | absent | not found inside the file | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | csv | 6 | READY_FOR_FEATURE_EXTRACTION | yes | is_executing_exploit | False: 5813, True: 187 | Использовать напрямую для supervised TRAIN/VALIDATION после нормализации: label_binary, label_family, label_subtype, label_source=embedded_column. |
| Host | VALIDATION | json | 130 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | VALIDATION | netflow_day | 2 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | VALIDATION | pcap | 1 | NEEDS_CUSTOM_PARSER | no | absent | not found inside the file | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | pcapng | 5 | NEEDS_CUSTOM_PARSER | no | absent | not found inside the file | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | txt | 6495 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | VALIDATION | wls_day | 3 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |

### 5.3. general_host_test.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | TEST | bson | 9005 | NEEDS_CUSTOM_PARSER | no | absent | not found | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | csv | 3 | PARTIALLY_SUPPORTED | yes | label in separate label CSV files; `attack_dataset.csv` does not contain labels | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 | Labels есть, но это TEST. Использовать только для финальной оценки; для строк без label выполнить join с label-файлами по стабильному ключу (например, IP / sample id), сохранив label_source=external_label_file. |
| Host | TEST | json | 7071 | NEEDS_CUSTOM_PARSER | no | absent in sample | not found | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | TEST | log | 4086 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TEST | netflow_day | 2 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | txt | 274419 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | wls_day | 3 | READY_FOR_FEATURE_EXTRACTION | no | absent | not found | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |

### 5.4. general_dns_train.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | TRAIN | csv | 8 | PARTIALLY_SUPPORTED | partially | filename / class_hint | benign, malware, phishing, spam | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | TRAIN | pcap | 4 | NEEDS_CUSTOM_PARSER | partially | filename | benign, malware, phishing, spam | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | TRAIN | pcap.csv | 14 | READY_FOR_FEATURE_EXTRACTION | partially | filename / class_hint | audio, benign, compressed, exe, image, text, video | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |

### 5.5. general_dns_validation.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | VALIDATION | pcap | 5 | NEEDS_CUSTOM_PARSER | partially | filename | attack, benign | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | VALIDATION | txt | 3 | READY_FOR_FEATURE_EXTRACTION | partially | filename / class_hint | unknown, benign | Реализовать filename/class_hint resolver. Значение unknown не считать malicious/benign автоматически: закрепить семантику через документацию датасета или исключить unknown из supervised evaluation. |

### 5.6. general_dns_test.md

| Domain | Role | Format | Files | Status | Label found | Label field | Label values | Decision / recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | TEST | csv | 1 | PARTIALLY_SUPPORTED | partially | `label_or_flag` | boolean-like flag в sample | The `label_or_flag` field exists, but this is TEST data. Before evaluation, fix the positional schema and the semantics of the boolean flag; use it only for evaluation, not for training. |
| DNS | TEST | pcap | 0 | BROKEN_OR_EMPTY | no | - | - | There are effectively no files, or the bucket is empty. Labels cannot be added until the input files are restored; check the ingestion/sort-path JSON and the presence of the original bucket. |
| DNS | TEST | pcap.csv | 0 | BROKEN_OR_EMPTY | no | - | - | There are effectively no files, or the bucket is empty. Labels cannot be added until the input files are restored; check the ingestion/sort-path JSON and the presence of the original bucket. |

## 6. Practical Rules for Adding Labels to Files Without Labels

### 6.1. DNS

**DNS TRAIN:**
- `csv`, `pcap.csv`, and `pcap` receive labels from the filename or `class_hint`.
- For benign: `label_binary=0`, `label_family=benign`.
- For malware/phishing/spam: `label_binary=1`, but `label_family` must preserve the original class. These records must not be automatically called `dns_exfiltration` unless this is confirmed by the documentation of the specific dataset.
- For audio/compressed/exe/image/text/video in `pcap.csv`, the meaning must be explicitly defined: either an exfiltrated payload type or a traffic class. If it is a DNS exfiltration class, mapping can be `label_binary=1`, `label_family=dns_exfiltration`, `label_subtype=<payload_type>`. If it is only a traffic type without attack semantics, use it as `class_hint`/context, not as the target.

**DNS VALIDATION:**
- `pcap`: labels can be taken from the filename (`attack` / `benign`).
- `txt`: `benign_domains.txt` can be considered benign only after fixing the mapping; `domains.txt` / `domains__*.txt` have `class_hint=unknown`, so they must not be automatically used as attack or benign.

**DNS TEST:**
- `csv`: `label_or_flag` is partially present; the positional schema and the meaning of the boolean flag must be fixed. Use only for evaluation.
- `pcap` and `pcap.csv`: there are no files; labels cannot be added until the bucket is restored.

### 6.2. Host

**Host TRAIN:**
- `csv`: use embedded `attack_cat`, `attack_subcat`, and `label` as the main supervised source.
- `cpu.log`: `labels`/`rules` exist only in annotation rows; use them as partial/weak labels after linking them to metric rows by `@timestamp`/host.
- `auth.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `journal`, `journal~`, `pcap`, and other telemetry/log formats without labels: add labels only through external mapping: `ground_truth.csv`, scenario metadata, filename scenario, host + timestamp window. If no mapping is found, keep them unlabeled.
- Formats with schema-dependent fields `exploit` / `container.role` / `alert`: `exploit` can be used as an inferred label for a scenario/window; `alert` only as a weak label; `container.role` should be stored as context.

**Host VALIDATION:**
- `csv` / `runs*.csv` contains `is_executing_exploit` and should be the main source of validation labels.
- `cap` / `pcap` / `pcapng` / `json` / `netflow_day` / `txt` / `wls_day` do not contain embedded labels. They must be linked to the validation CSV by `scenario_name`, `image_name`, filename, `recording_time` / `exploit_start_time`, and timestamp.

**Host TEST:**
- `csv` contains labels in separate label CSV files; `attack_dataset.csv` must be joined with `attack_labels.csv` / `attack_labels_sbseg.csv` by IP or another confirmed key. TEST must not be used for training.
- `bson` / `json` / `log` / `netflow_day` / `txt` / `wls_day` do not have labels. External labels are required from sandbox report metadata, sample ID, malware family, attack label files, or dataset documentation. If external labels are unavailable, use only inference-only/anomaly analysis.

## 7. Recommended Label Resolver Algorithm

1. At the inventory stage, store: domain, role, format, source_file, checksum, file_size.
2. At the parsing stage, extract: timestamp, host, IP, process/session/scenario identifiers, row/event/packet ID.
3. Apply label rules in strict order:
   - `embedded_column` — label/attack_cat/attack_subcat/is_executing_exploit;
   - `external_label_file` — attack_labels.csv, ground_truth.csv, runs.csv;
   - `filename` / `class_hint` — benign, attack, malware, phishing, spam, payload type;
   - `scenario_metadata` — exploit, scenario_name, exploit_start_time;
   - `ids_alert` — weak_label only;
   - `no_match` — unlabeled.
4. If labels conflict, do not choose arbitrarily: set `label_status=conflicting_label` and send the record to the quality report.
5. Use TEST labels only after model training is complete, for final evaluation.

## 8. Recommended `label_status` Values

- `explicit_label` — the label is present directly in a column or in an official label file.
- `inferred_label` — the label is obtained from a filename, directory, or scenario metadata, and the rule is fixed.
- `weak_label` — the label is obtained from an alert/rule/heuristic and is not ground truth.
- `partial_label` — the label exists only for some rows/windows.
- `unlabeled` — no reliable label is available.
- `conflicting_label` — different label sources produce different classes.

## 9. Minimum Implementation Tasks

- **Task 1.** Create `label_mapping.yml` with rules for DNS/Host TRAIN/VALIDATION/TEST.
- **Task 2.** Implement `LabelResolver`, which returns `label_binary`, `label_family`, `label_source`, `label_status`, and `label_confidence`.
- **Task 3.** Implement joins for Host TRAIN `csv` / `ground_truth` and Host VALIDATION `runs.csv`.
- **Task 4.** Implement a filename label parser for DNS TRAIN/VALIDATION.
- **Task 5.** Add a TEST guard: labels are allowed only for evaluation, not for training.
- **Task 6.** Generate a label coverage report: explicit/partial/inferred/weak/unlabeled/conflicting for each dataset role and format.

## 10. Final Decision

Labels already exist or can be reliably inferred for part of DNS TRAIN, DNS VALIDATION `pcap`, Host TRAIN `csv`, Host TRAIN `cpu.log` as partial annotations, Host VALIDATION `csv`, and Host TEST `csv` through separate label CSV files. Most Host telemetry/log/packet/sequence files do not contain embedded labels. They should be preserved and normalized, but they must not be used as supervised samples without label mapping. The main implementation should not be manual labeling of all files, but a separate label mapping / label resolver layer with traceability, label provenance, and data leakage control.

---

## Usage Note

This document is intended for designing `LabelResolver`, `label_mapping.yml`, normalized artifacts, and label coverage reports. The main rule is: files without reliable labeling are preserved and normalized, but they are not used as supervised samples until successful label mapping is completed.

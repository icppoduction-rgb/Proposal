# Разметка labels в датасетах dns/host

**Документ по анализу наличия labels и рекомендациям по label mapping**

---

## Метаданные

| Поле | Значение |
|---|---|
| Дата подготовки | 2026-06-12 |
| Источники | `general_host_train.md, general_host_validation.md, general_host_test.md, general_dns_train.md, general_dns_validation.md, general_dns_test.md` |

## Оглавление

- [1. Цель документа](#1-цель-документа)
- [2. Главные правила](#2-главные-правила)
- [3. Рекомендуемая canonical label schema](#3-рекомендуемая-canonical-label-schema)
- [4. Сводка по категориям labels](#4-сводка-по-категориям-labels)
- [5. Детальная таблица действий по каждому источнику](#5-детальная-таблица-действий-по-каждому-источнику)
- [6. Практические правила добавления labels для файлов без labels](#6-практические-правила-добавления-labels-для-файлов-без-labels)
- [7. Рекомендуемый алгоритм label resolver](#7-рекомендуемый-алгоритм-label-resolver)
- [8. Рекомендуемые label_status значения](#8-рекомендуемые-label_status-значения)
- [9. Минимальные задачи для реализации](#9-минимальные-задачи-для-реализации)
- [10. Итоговое решение](#10-итоговое-решение)

---

## 1. Цель документа

Документ фиксирует, в каких форматах/файлах датасетов уже есть labels, где labels отсутствуют, а где labels можно получить только частично. Также указано, как корректно добавлять labels для файлов без встроенной разметки, чтобы не нарушить supervised training/evaluation и не создать data leakage.

## 2. Главные правила

1. Отсутствие label не означает benign.
2. TEST-данные нельзя использовать для обучения, даже если labels присутствуют.
3. Labels из имени файла, директории, scenario metadata или IDS alert должны иметь label_source и label_status.
4. Weak labels не равны ground truth. Для финальных метрик нужно отделять explicit_label от inferred_label/weak_label.
5. Для файлов без labels нужно сохранять label_binary=NULL, label_family=unknown, label_status=unlabeled, пока не найден надежный label mapping.
6. Любой label join должен сохранять traceability: raw_file -> normalized_event -> feature/window/sequence -> model_ready_sample.

## 3. Рекомендуемая canonical label schema

Минимальные поля, которые нужно добавить в normalized artifacts / Parquet / model-ready datasets:

| Поле | Назначение |
|---|---|
| `label_binary` | 0=benign, 1=malicious/attack/exfiltration, NULL=unknown |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, unknown |
| `label_subtype` | конкретный subtype/scenario, если доступен |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label |
| `label_confidence` | 1.0 для explicit, 0.7-0.9 для inferred, 0.4-0.7 для weak, 0 для unlabeled |
| `label_mapping_rule_id` | ID правила mapping |
| `dataset_domain` | dns / host |
| `dataset_role` | TRAIN / VALIDATION / TEST |
| `dataset_format` | csv, pcap, pcap.csv, json, log, bson, ... |
| `source_file` | исходный путь/имя файла |
| `source_row_id/event_id` | строка/пакет/событие, если применимо |

## 4. Сводка по категориям labels

| Категория | Количество |
|---|---:|
| Всего проанализировано format buckets | 66 |
| С прямыми labels (Label найден = да) | 5 |
| С частичными labels / class hints | 6 |
| Без встроенных labels | 55 |

### 4.1. Форматы, где labels найдены напрямую или как встроенное поле

| Источник | Домен | Роль | Формат | Файлов | Поле label | Значения | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_host_train.md | Host | TRAIN | cpu.log | 13 | labels | crack_passwords, escalate | partially |
| general_host_train.md | Host | TRAIN | csv | 101 | колонка(и) 7, 8, 9 | нормальные/атакующие категории + бинарный label (0/1) | да |
| general_host_train.md | Host | TRAIN | json | 219 | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | partially |
| general_host_validation.md | Host | VALIDATION | csv | 6 | is_executing_exploit | False: 5813, True: 187 | да, как validation labels |
| general_host_test.md | Host | TEST | csv | 3 | label в отдельных label CSV; `attack_dataset.csv` label не содержит | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 | частично; нужен join по IP и TEST нельзя применять для обучения |

### 4.2. Форматы, где labels частичные или выводятся через filename/class_hint

| Источник | Домен | Роль | Формат | Файлов | Поле/источник | Значения | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_dns_train.md | DNS | TRAIN | csv | 8 | имя файла / class_hint | benign, malware, phishing, spam | да, после присвоения label из имени файла |
| general_dns_train.md | DNS | TRAIN | pcap | 4 | имя файла | benign, malware, phishing, spam | да, после присвоения label из имени файла |
| general_dns_train.md | DNS | TRAIN | pcap.csv | 14 | имя файла / class_hint | audio, benign, compressed, exe, image, text, video | да, после присвоения label из имени файла |
| general_dns_validation.md | DNS | VALIDATION | pcap | 5 | имя файла | attack, benign | да, после присвоения label из имени файла |
| general_dns_validation.md | DNS | VALIDATION | txt | 3 | имя файла / class_hint | unknown, benign | частично, только после явного назначения класса |
| general_dns_test.md | DNS | TEST | csv | 1 | `label_or_flag` | boolean-like flag в sample | нет, это TEST-роль; использовать только для оценки |

### 4.3. Форматы, где labels не найдены

| Источник | Домен | Роль | Формат | Файлов | Timestamp | Поле времени | Supervised |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general_host_train.md | Host | TRAIN | auth.log | 23 | да | @timestamp, message(syslog prefix) | partially |
| general_host_train.md | Host | TRAIN | diskio.log | 12 | да | @timestamp | no |
| general_host_train.md | Host | TRAIN | filesystem.log | 12 | да | @timestamp | no |
| general_host_train.md | Host | TRAIN | fsstat.log | 12 | да | @timestamp | no |
| general_host_train.md | Host | TRAIN | ghc | 56158 | нет | - | partially |
| general_host_train.md | Host | TRAIN | info | 3 | да | @timestamp, message(syslog prefix) | partially |
| general_host_train.md | Host | TRAIN | journal | 17 | нет | - | no |
| general_host_train.md | Host | TRAIN | journal~ | 1 | нет | - | no |
| general_host_train.md | Host | TRAIN | json-1 | 1 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | load.log | 12 | нет | time.container_ready.absolute, timestamp | no |
| general_host_train.md | Host | TRAIN | log | 98 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-1 | 32 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-2 | 9 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | log-3 | 8 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mail-info-1 | 3 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mail-warn-1 | 2 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog | 3 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-1 | 3 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-2 | 3 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | mainlog-3 | 3 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | memory.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | messages | 3 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | messages-1 | 3 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | netflow_ids | 50 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | network.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | pcap | 15 | нет | - | no |
| general_host_train.md | Host | TRAIN | process.log | 2 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | process.summary.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | sc | 210 | да | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | service.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | socket.summary.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog | 9 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-1 | 10 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-2 | 10 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-3 | 10 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog-4 | 1 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | syslog.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | txt | 3170 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | uptime.log | 12 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_train.md | Host | TRAIN | xml | 40 | нет | time.container_ready.absolute, timestamp | partially |
| general_host_validation.md | Host | VALIDATION | cap | 44 | да | packet header ts_sec/ts_usec | частично; только при внешней разметке/сценарии из имени файла |
| general_host_validation.md | Host | VALIDATION | json | 130 | да | TimeCreated, @timestamp | частично, при внешней разметке из scenario/file name |
| general_host_validation.md | Host | VALIDATION | netflow_day | 2 | да | time | нет без внешних меток |
| general_host_validation.md | Host | VALIDATION | pcap | 1 | да | packet header ts_sec/ts_usec | частично; только при внешней разметке/сценарии из имени файла |
| general_host_validation.md | Host | VALIDATION | pcapng | 5 | да | Enhanced Packet Block timestamp_high/timestamp_low | частично; только при внешней разметке/сценарии из имени файла |
| general_host_validation.md | Host | VALIDATION | txt | 6495 | да | Time | нет без внешней разметки |
| general_host_validation.md | Host | VALIDATION | wls_day | 3 | да | Time | нет без внешних меток |
| general_host_test.md | Host | TEST | bson | 9005 | частично | порядок BSON-документов, числовые `t`/`h` в event-записях | нет для TEST; нужны внешние метки, если они существуют |
| general_host_test.md | Host | TEST | json | 7071 | да | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` | нет для TEST; нужны внешние метки |
| general_host_test.md | Host | TEST | log | 4086 | да | timestamp | нет без внешних меток |
| general_host_test.md | Host | TEST | netflow_day | 2 | да | time | нет без внешних меток |
| general_host_test.md | Host | TEST | txt | 274419 | да | Time | нет без внешних меток |
| general_host_test.md | Host | TEST | wls_day | 3 | да | Time | нет без внешних меток |
| general_dns_test.md | DNS | TEST | pcap | 0 | нет | - | нет |
| general_dns_test.md | DNS | TEST | pcap.csv | 0 | нет | - | нет |

## 5. Детальная таблица действий по каждому источнику

### 5.1. general_host_train.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | TRAIN | auth.log | 23 | NEEDS_CUSTOM_PARSER | нет | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | cpu.log | 13 | PARTIALLY_SUPPORTED | да | labels | crack_passwords, escalate | Использовать как частичные annotation labels: отделить metric rows от label/annotation rows, связать labels/rules с временными окнами по @timestamp/host, пометить label_status=weak_or_partial_label. Для финальных метрик желательно подтверждать через ground_truth/scenario mapping. |
| Host | TRAIN | csv | 101 | PARTIALLY_SUPPORTED | да | колонка(и) 7, 8, 9 | нормальные/атакующие категории + бинарный label (0/1) | Использовать напрямую для supervised TRAIN/VALIDATION после нормализации: label_binary, label_family, label_subtype, label_source=embedded_column. |
| Host | TRAIN | diskio.log | 12 | PARTIALLY_SUPPORTED | нет | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | filesystem.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | fsstat.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | ghc | 56158 | NEEDS_CUSTOM_PARSER | нет | - | - | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | info | 3 | READY_FOR_FEATURE_EXTRACTION | нет | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | journal | 17 | NEEDS_CUSTOM_PARSER | нет | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | journal~ | 1 | NEEDS_CUSTOM_PARSER | нет | - | - | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TRAIN | json | 219 | NEEDS_CUSTOM_PARSER | да | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Использовать только через schema-aware resolver: exploit=true/false может быть inferred label для scenario/window; container.role хранить как context, но не считать attack; alert использовать как weak label, а не ground truth. |
| Host | TRAIN | json-1 | 1 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | TRAIN | load.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | - | - | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | log | 98 | NEEDS_CUSTOM_PARSER | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-1 | 32 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-2 | 9 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | log-3 | 8 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mail-info-1 | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mail-warn-1 | 2 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-1 | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-2 | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | mainlog-3 | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | memory.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | messages | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | messages-1 | 3 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | netflow_ids | 50 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | network.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | pcap | 15 | NEEDS_CUSTOM_PARSER | нет | - | - | Встроенного label нет. Извлекать packet/flow признаки, затем искать внешний label по scenario/file name, timestamp, host/IP или ground_truth.csv. Не считать отсутствие label benign; при отсутствии связи — unlabeled/inference-only. |
| Host | TRAIN | process.log | 2 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | process.summary.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | sc | 210 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | service.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | socket.summary.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | syslog | 9 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-1 | 10 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-2 | 10 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-3 | 10 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog-4 | 1 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | syslog.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Проверить наличие scenario JSON / event_type=alert / exploit / container.role. exploit может дать inferred label на уровне scenario/window; alert — только weak label; container.role — context. При отсутствии подтверждения label_status=unlabeled. |
| Host | TRAIN | txt | 3170 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | TRAIN | uptime.log | 12 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Это telemetry/metric источник без target. Добавлять label только через временное окно: join по host.name + timestamp с размеченным scenario/ground_truth. Если окно не попало в размеченный интервал — оставить unlabeled, не использовать как supervised sample. |
| Host | TRAIN | xml | 40 | READY_FOR_FEATURE_EXTRACTION | нет | exploit / container.role / alert (schema-dependent) | True, False, normal, victim, alert-derived | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |

### 5.2. general_host_validation.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | VALIDATION | cap | 44 | NEEDS_CUSTOM_PARSER | нет | отсутствует | не обнаружены внутри файла | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | csv | 6 | READY_FOR_FEATURE_EXTRACTION | да | is_executing_exploit | False: 5813, True: 187 | Использовать напрямую для supervised TRAIN/VALIDATION после нормализации: label_binary, label_family, label_subtype, label_source=embedded_column. |
| Host | VALIDATION | json | 130 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | VALIDATION | netflow_day | 2 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | VALIDATION | pcap | 1 | NEEDS_CUSTOM_PARSER | нет | отсутствует | не обнаружены внутри файла | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | pcapng | 5 | NEEDS_CUSTOM_PARSER | нет | отсутствует | не обнаружены внутри файла | Встроенного label нет. Использовать scenario/file-name mapping и metadata из Host VALIDATION csv: scenario_name, image_name, is_executing_exploit, exploit_start_time. Затем присвоить label окнам packet/flow по scenario + timestamp; без join оставить unlabeled. |
| Host | VALIDATION | txt | 6495 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |
| Host | VALIDATION | wls_day | 3 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | Добавлять label только через внешний mapping: filename/scenario metadata, отдельный label CSV, ground_truth, timestamp-window join или dataset documentation. Если надежного источника нет — label_binary=NULL, label_status=unlabeled. |

### 5.3. general_host_test.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host | TEST | bson | 9005 | NEEDS_CUSTOM_PARSER | нет | отсутствует | не обнаружены | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | csv | 3 | PARTIALLY_SUPPORTED | да | label в отдельных label CSV; `attack_dataset.csv` label не содержит | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 | Labels есть, но это TEST. Использовать только для финальной оценки; для строк без label выполнить join с label-файлами по стабильному ключу (например, IP / sample id), сохранив label_source=external_label_file. |
| Host | TEST | json | 7071 | NEEDS_CUSTOM_PARSER | нет | отсутствует в sample | не обнаружены | Проверить schema-aware поля exploit/container.role/alert. Использовать exploit как inferred scenario label при подтвержденной связи; alert как weak label; container.role как context. Иначе оставить unlabeled. |
| Host | TEST | log | 4086 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | Лог без встроенной разметки. Делать label join по времени, host, process/user/session, scenario metadata или ground_truth. Не размечать вручную как benign. |
| Host | TEST | netflow_day | 2 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | txt | 274419 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |
| Host | TEST | wls_day | 3 | READY_FOR_FEATURE_EXTRACTION | нет | отсутствует | не обнаружены | TEST без labels. Не использовать для обучения. Для оценки нужны внешние labels: sample id, report metadata, attack_labels, scenario mapping или документация датасета. Если внешней связи нет — inference-only/anomaly analysis. |

### 5.4. general_dns_train.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | TRAIN | csv | 8 | PARTIALLY_SUPPORTED | частично | имя файла / class_hint | benign, malware, phishing, spam | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | TRAIN | pcap | 4 | NEEDS_CUSTOM_PARSER | частично | имя файла | benign, malware, phishing, spam | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | TRAIN | pcap.csv | 14 | READY_FOR_FEATURE_EXTRACTION | частично | имя файла / class_hint | audio, benign, compressed, exe, image, text, video | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |

### 5.5. general_dns_validation.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | VALIDATION | pcap | 5 | NEEDS_CUSTOM_PARSER | частично | имя файла | attack, benign | Реализовать filename-based label resolver: извлекать class_hint из имени файла, валидировать mapping, сохранять label_source=filename. Для DNS exfiltration отделить benign от attack/exfiltration и не смешивать вспомогательные классы без явного target_task. |
| DNS | VALIDATION | txt | 3 | READY_FOR_FEATURE_EXTRACTION | частично | имя файла / class_hint | unknown, benign | Реализовать filename/class_hint resolver. Значение unknown не считать malicious/benign автоматически: закрепить семантику через документацию датасета или исключить unknown из supervised evaluation. |

### 5.6. general_dns_test.md

| Домен | Роль | Формат | Файлов | Статус | Label найден | Label field | Label values | Решение / рекомендация |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | TEST | csv | 1 | PARTIALLY_SUPPORTED | частично | `label_or_flag` | boolean-like flag в sample | Поле label_or_flag есть, но это TEST. Перед оценкой закрепить positional schema и семантику boolean flag; использовать только для evaluation, не для обучения. |
| DNS | TEST | pcap | 0 | BROKEN_OR_EMPTY | нет | - | - | Файлов фактически нет или bucket пустой. Labels добавить невозможно до восстановления входных файлов; проверить ingestion/sort-path JSON и наличие исходного bucket. |
| DNS | TEST | pcap.csv | 0 | BROKEN_OR_EMPTY | нет | - | - | Файлов фактически нет или bucket пустой. Labels добавить невозможно до восстановления входных файлов; проверить ingestion/sort-path JSON и наличие исходного bucket. |

## 6. Практические правила добавления labels для файлов без labels

### 6.1. DNS

**DNS TRAIN:**
- csv, pcap.csv, pcap получают labels из имени файла или class_hint.
- Для benign -> label_binary=0, label_family=benign.
- Для malware/phishing/spam -> label_binary=1, но label_family должен сохранять исходный класс. Их нельзя автоматически называть dns_exfiltration, если это не подтверждено документацией конкретного датасета.
- Для audio/compressed/exe/image/text/video в pcap.csv нужно явно определить смысл: это тип эксфильтрируемого payload или traffic class. Если это DNS exfiltration class, можно mapping -> label_binary=1, label_family=dns_exfiltration, label_subtype=<payload_type>. Если это просто тип трафика без attack semantics, использовать как class_hint/context, не как target.

**DNS VALIDATION:**
- pcap: labels можно брать из имени файла attack/benign.
- txt: benign_domains.txt можно считать benign только после фиксации mapping; domains.txt/domains__*.txt имеют class_hint=unknown, поэтому их нельзя автоматически использовать как attack или benign.

**DNS TEST:**
- csv: label_or_flag присутствует частично; нужно закрепить positional schema и смысл boolean flag. Использовать только для evaluation.
- pcap и pcap.csv: файлов нет; labels добавить невозможно, пока не восстановлен bucket.

### 6.2. Host

**Host TRAIN:**
- csv: использовать встроенные attack_cat, attack_subcat и label как основной supervised источник.
- cpu.log: labels/rules есть только в annotation rows; использовать как partial/weak labels, связав с metric rows по @timestamp/host.
- auth.log, diskio.log, filesystem.log, fsstat.log, load.log, journal, journal~, pcap и другие telemetry/log форматы без labels: добавлять labels только через внешний mapping: ground_truth.csv, scenario metadata, filename scenario, host + timestamp window. Если mapping не найден, оставить unlabeled.
- Форматы со schema-dependent полями exploit/container.role/alert: exploit может использоваться как inferred label для scenario/window; alert только как weak label; container.role хранить как контекст.

**Host VALIDATION:**
- csv/runs*.csv содержит is_executing_exploit и должен быть основным источником validation labels.
- cap/pcap/pcapng/json/netflow_day/txt/wls_day не содержат встроенных labels. Их нужно связывать с validation csv по scenario_name, image_name, имени файла, recording_time/exploit_start_time и timestamp.

**Host TEST:**
- csv содержит label в отдельных label CSV; attack_dataset.csv нужно join-ить с attack_labels.csv/attack_labels_sbseg.csv по IP или другому подтвержденному ключу. TEST не использовать для обучения.
- bson/json/log/netflow_day/txt/wls_day не имеют labels. Нужны внешние labels из sandbox report metadata, sample id, malware family, attack label files или документации датасета. Если внешних labels нет, использовать только inference-only/anomaly analysis.

## 7. Рекомендуемый алгоритм label resolver

1. На этапе inventory сохранить: domain, role, format, source_file, checksum, file_size.
2. На этапе parsing извлечь: timestamp, host, ip, process/session/scenario identifiers, row/event/packet id.
3. Применить label rules в строгом порядке:
   - `embedded_column` — label/attack_cat/attack_subcat/is_executing_exploit;
   - `external_label_file` — attack_labels.csv, ground_truth.csv, runs.csv;
c. filename/class_hint: benign, attack, malware, phishing, spam, payload type;
   - `scenario_metadata` — exploit, scenario_name, exploit_start_time;
   - `ids_alert` — только weak_label;
   - `no_match` — unlabeled.
4. При конфликте labels не выбирать произвольно: label_status=conflicting_label, запись отправить в quality report.
5. TEST labels использовать только после завершения model training, для финальной оценки.

## 8. Рекомендуемые label_status значения

- `explicit_label` — label есть прямо в колонке или в официальном label-файле.
- `inferred_label` — label получен из имени файла, директории или scenario metadata и правило зафиксировано.
- `weak_label` — label получен из alert/rule/heuristic, не является ground truth.
- `partial_label` — label есть только для части строк/окон.
- `unlabeled` — надежного label нет.
- `conflicting_label` — разные источники labels дают разные классы.

## 9. Минимальные задачи для реализации

- **Task 1.** Создать label_mapping.yml с правилами для DNS/Host TRAIN/VALIDATION/TEST.
- **Task 2.** Реализовать LabelResolver, который возвращает label_binary, label_family, label_source, label_status, label_confidence.
- **Task 3.** Реализовать join для Host TRAIN csv/ground_truth и Host VALIDATION runs.csv.
- **Task 4.** Реализовать filename label parser для DNS TRAIN/VALIDATION.
- **Task 5.** Для TEST включить guard: labels разрешены только для evaluation, не для training.
- **Task 6.** Генерировать label coverage report: explicit/partial/inferred/weak/unlabeled/conflicting по каждому dataset role и format.

## 10. Итоговое решение

Labels уже есть или надежно выводятся для части DNS TRAIN, DNS VALIDATION pcap, Host TRAIN csv, Host TRAIN cpu.log как partial annotations, Host VALIDATION csv и Host TEST csv через отдельные label CSV. Большинство Host telemetry/log/packet/sequence файлов не содержит встроенных labels. Их нужно сохранять и нормализовать, но не использовать как supervised samples без label mapping. Основная реализация должна быть не ручной разметкой всех файлов, а отдельным label mapping / label resolver layer с traceability, label provenance и data leakage control.

---

## Примечание по использованию

Документ предназначен для проектирования `LabelResolver`, `label_mapping.yml`, normalized artifacts и отчетов по покрытию labels. Основное правило: файлы без надежной разметки сохраняются и нормализуются, но не используются как supervised samples до успешного label mapping.

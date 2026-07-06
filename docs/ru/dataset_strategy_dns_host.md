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

# Индекс объединенных источников

Документ фиксирует, какие старые файлы были объединены в новую тематическую структуру. Он нужен, чтобы не потерять навигацию после удаления дублей.

## Новые документы

| Новый документ | Что содержит |
| --- | --- |
| [README.md](README.md) | Общая карта раздела, coverage, readiness counts, инварианты. |
| [dns_datasets.md](dns_datasets.md) | Все DNS TRAIN/VALIDATION/TEST сведения. |
| [host_datasets.md](host_datasets.md) | Все Host TRAIN/VALIDATION/TEST сведения. |
| [format_status_matrix.md](format_status_matrix.md) | 64 format buckets: files/status/labels/timestamp/action. |
| [labels_and_readiness.md](labels_and_readiness.md) | Label policy, readiness statuses, LabelResolver guidance. |
| [parser_feature_recommendations.md](parser_feature_recommendations.md) | Parser priorities, feature groups, quality checks. |

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

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

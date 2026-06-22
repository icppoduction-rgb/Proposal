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

- [../normalization/label_resolver.md](../normalization/label_resolver.md)
- [../normalization/data_leakage_prevention.md](../normalization/data_leakage_prevention.md)
- [../normalization/traceability.md](../normalization/traceability.md)

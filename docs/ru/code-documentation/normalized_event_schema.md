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

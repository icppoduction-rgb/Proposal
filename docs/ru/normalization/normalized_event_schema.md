# Normalized event schema

Контракт normalized events хранится в `schemas/normalized/normalized_event_v1.json`. Парсеры Stage Two должны выдавать строки, совместимые с этим контрактом.

## Базовые поля traceability

Обязательные для трассировки поля:

- `event_uid`
- `dataset_id`
- `file_id`
- `dataset_name`
- `dataset_role`
- `branch`
- `source_format`
- `source_file_path`
- `source_file_hash`
- `parser_name`
- `parser_version`
- `parser_run_id`
- `schema_name`
- `schema_version`
- `created_at`

## Временная модель

- `timestamp` может быть null.
- `timestamp_type` принимает `absolute`, `relative`, `event_order` или `missing`.
- Если абсолютного времени нет, ordered streams должны сохранять `event_index`.
- Отсутствующее время не должно синтетически заполняться текущим временем.

## Entity и modality

Схема покрывает DNS, host, network и hybrid события. Общие поля:

- `entity_type`, `entity_id`
- `event_type`, `raw_event_name`, `modality`
- host fields: `host_name`, `user_name`, `process_id`, `process_name`, `file_path`, `command_line`
- network/DNS fields: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `domain`, `query_domain`, `qtype`, `qclass`, `ttl`, `rcode`
- metric fields: `metric_name`, `metric_value`

## Labels

Labels представлены полями:

- `label_binary`: `0`, `1` или null
- `label_family`
- `label_subtype`
- `label_source`
- `label_status`
- `label_confidence`
- `label_mapping_rule_id`

Если label отсутствует, используется:

```text
label_binary = null
label_source = none
label_status = unlabeled
```

TEST filename heuristic отключен: TEST не получает label из имени файла без явного безопасного источника.

## Raw и extra metadata

Для исходных полей и дополнительных parser-specific данных используются:

- `features_json`
- `raw_fields_json`
- `metadata_json`

Отсутствующие поля сохраняются как null.

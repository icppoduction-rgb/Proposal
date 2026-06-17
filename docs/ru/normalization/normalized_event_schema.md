# Normalized event schema

Canonical normalized event schema:

```text
schemas/normalized/normalized_event_v1.json
```

Регистрируется в PostgreSQL `schema_versions` командой:

```powershell
python manage.py stage-two seed-parser-registry
```

## Field groups

| Group | Representative fields | Purpose |
| --- | --- | --- |
| Traceability | `event_uid`, `dataset_id`, `file_id`, `dataset_name`, `dataset_role`, `branch`, `source_format`, `source_file_path`, `source_file_hash`, `parser_name`, `parser_version`, `parser_run_id`, `schema_name`, `schema_version` | Связать normalized row с raw file и parser run. |
| Time/order | `timestamp`, `timestamp_source`, `timestamp_type`, `event_index` | Сохранить absolute timestamps, relative timestamps или stream order. |
| Event identity | `entity_type`, `entity_id`, `event_type`, `raw_event_name`, `modality` | Описать event domain и normalized type. |
| Host | `host_name`, `user_name`, `process_id`, `process_name`, `parent_process_id`, `parent_process_name`, `syscall_name`, `event_id`, `command_line`, `file_path` | Host/syscall/log/sandbox fields. |
| Network/DNS | `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `domain`, `query_domain`, `qtype`, `qclass`, `ttl`, `rcode` | DNS, packet и flow fields. |
| Metrics | `metric_name`, `metric_value` | Host metricbeat/system metrics. |
| Labels | `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id` | Canonical label metadata, не X features. |
| Flexible JSON | `features_json`, `raw_fields_json`, `metadata_json` | Non-canonical source fields, parser metadata, bounded previews, parser-safe derived features. |

## Timestamp policy

| `timestamp_type` | Meaning |
| --- | --- |
| `absolute` | Source содержит absolute timestamp. |
| `relative` | Source содержит relative time/counter. |
| `event_order` | Нет absolute time; `event_index` сохраняет порядок. |
| `missing` | Нет usable time и ordered context. |

Parsers не должны silently inject current year/timezone, если source не дает достаточно контекста.

## Null policy

- Missing values сохраняются как JSON null, SQL NULL или Parquet null.
- Missing labels не считаются benign.
- Unlabeled events используют `label_binary=None`, `label_source="none"`, `label_status="unlabeled"`.
- Unknown source fields сохраняются в JSON fields, а не silently drop.

## Required parser behavior

Каждый emitted event должен содержать required normalized fields из `scripts/stage_two/parsers/base.py`. Parser smoke tests проверяют это через `REQUIRED_NORMALIZED_FIELDS`.

Recommended event creation:

1. Построить traceability fields helpers из `scripts/stage_two/parsers/common.py`.
2. Добавить timestamp/order fields.
3. Resolve labels через `LabelResolver`.
4. Merge canonical fields, `raw_fields_json`, `features_json`, `metadata_json`.
5. Вернуть `ParserResult` с counters и status.

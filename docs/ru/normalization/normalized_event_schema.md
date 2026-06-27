# Схема normalized event

Normalized event schema хранится в:

```text
schemas/normalized/normalized_event_v1.json
```

Это JSON contract с `schema_name = "normalized_event"`, `schema_version = "v1"`, `layer = "normalized"` и массивом `fields`. Parser implementations должны выдавать rows, совместимые с этим контрактом.

## Обязательные поля parser output

Базовый parser contract в `scripts/stage_two/parsers/base.py` требует поля:

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

Дополнительные поля из JSON schema могут быть nullable, но parser должен сохранять traceability и label/timestamp null policy.

## Traceability поля

| Поле | Назначение |
| --- | --- |
| `event_uid` | Уникальный идентификатор normalized event. |
| `dataset_name` | Имя dataset из catalog/source context. |
| `dataset_role` | `TRAIN`, `VALIDATION` или `TEST`. |
| `branch` | `dns`, `host`, `network`, `hybrid`. |
| `source_format` | Формат raw файла. |
| `source_file_path` | Путь к исходному файлу. |
| `source_file_hash` | SHA-256 raw файла, если доступен из catalog. |
| `parser_run_id` | ID parser run, связывает event с `parser_runs`. |
| `parser_name`, `parser_version` | Parser implementation и версия. |
| `schema_name`, `schema_version` | Версия normalized schema. |
| `event_index` | Порядковый номер события внутри файла, если доступен. |

Traceability поля нельзя удалять из normalized artifacts. Для model-ready `X` они считаются leakage/source columns и должны быть исключены из признаков.

## Timestamp policy

| Поле | Правило |
| --- | --- |
| `timestamp` | Может быть `null`. |
| `timestamp_type` | Одно из `absolute`, `relative`, `event_order`, `missing`. |
| `event_index` | Используется для сохранения порядка, когда абсолютного времени нет. |

Если timestamp отсутствует, нельзя подставлять текущее время. Правильные варианты:

- `timestamp = null`, `timestamp_type = "event_order"`, если есть надежный `event_index`;
- `timestamp = null`, `timestamp_type = "missing"`, если нет времени и порядка.

`build_timestamp_fields()` в `scripts/stage_two/parsers/common.py` реализует это правило: timestamp дает `absolute`, event index без timestamp дает `event_order`, отсутствие обоих дает `missing`.

## DNS поля

DNS parsers заполняют поля, связанные с DNS/network context, если они есть в source:

- `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- `query_domain`, `qtype`, `qclass`, `rcode`, `ttl`;
- DNS-specific values внутри `features_json` или `raw_fields_json`, если исходная схема не совпадает напрямую с normalized fields.

DNS packet captures могут давать summary-level events в зависимости от `--packet-mode`.

## Host поля

Host parsers используют поля, связанные с host telemetry:

- process: `process_id`, `process_name`, parent process fields;
- file/path: `path`, file action fields;
- syscall/log: `sys_call`, `event_id`, `event_type`;
- metrics/log payload, если source формат логовый или metricbeat-like.

Для нестандартных строковых логов часть значений сохраняется в `raw_fields_json`, а normalized columns заполняются только когда значение можно извлечь без выдумывания.

## Network/hybrid поля

`network` и `hybrid` branches есть в schema/catalog constants, но текущий normalization runner поддерживает только `dns` и `host`. Network/hybrid fields могут использоваться контрактами будущих parsers, но не должны описываться как полностью реализованный normalization pipeline.

## Labels

Unlabeled event должен иметь:

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

Отсутствующий label не равен benign. Для `TEST` filename/embedded heuristics отключены `LabelResolver.label_hints_allowed()`, чтобы не вносить leakage через имя файла или поля, которые не являются explicit external ground truth.

## JSON поля

| Поле | Назначение |
| --- | --- |
| `features_json` | Parser-level extracted attributes, которые еще не являются model-ready X features. |
| `raw_fields_json` | Исходные поля или фрагменты raw record для audit/debug. |
| `metadata_json` | Parser/file metadata, warnings, confidence, дополнительные counters. |

`ParquetArtifactWriter` сериализует поля с суффиксом `_json` в deterministic JSON strings перед записью Parquet.

## Граничные случаи

| Сценарий | Ожидаемое поведение |
| --- | --- |
| Empty file | Parser result может привести к `EMPTY_FILE`/`SKIPPED`, artifact не обязан создаваться. |
| Частично битые строки | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, ошибки фиксируются в parser run counters/error samples. |
| Неизвестный source format | Файл получает `UNSUPPORTED_FORMAT`, если resolver не нашел parser. |
| Schema drift | Parser должен сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не расширять model-ready X без schema review. |

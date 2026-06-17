# Parser development guide

Это руководство описывает поддерживаемый способ добавления или изменения Stage Two parser implementations.

## Parser contract

Каждый parser наследуется от `BaseParser` из `scripts/stage_two/parsers/base.py` и возвращает `ParserResult`.

Core classes:

| Class | Назначение |
| --- | --- |
| `ParserContext` | Traceability input: dataset/file ids, role, branch, source format, source path/hash, parser run id, metadata. |
| `ParsedEvent` | Typed event wrapper для parser helpers. |
| `ParserResult` | Parser output: events, counters, warnings, error samples, parser/file statuses. |
| `BaseParser` | Abstract parser base с parser name/version/schema metadata. |

Required normalized fields определены в `REQUIRED_NORMALIZED_FIELDS` в `base.py` и в `schemas/normalized/normalized_event_v1.json`.

## Используйте shared helpers

| Utility | File | Use |
| --- | --- | --- |
| `UniversalInputReader` | `scripts/stage_two/parsers/input_reader.py` | Streaming text/CSV/JSON-lines, binary streams, encoding, compression, safe base64. |
| Event builder helpers | `scripts/stage_two/parsers/common.py` | Stable event UID, traceability fields, labels, timestamps, metadata merge. |
| CSV helpers | `scripts/stage_two/parsers/csv_utils.py` | Headered/headerless CSV rows. |
| JSON helpers | `scripts/stage_two/parsers/json_utils.py` | JSON-line/array/object handling and flattening. |
| Log helpers | `scripts/stage_two/parsers/logs.py` | Syslog/auth/mail/journal line parsing. |
| `LabelResolver` | `scripts/stage_two/labels/resolver.py` | Safe label extraction и label mapping rules. |

## Implementation steps

1. Добавить или изменить parser class в подходящем module:

| Format family | Preferred module |
| --- | --- |
| DNS CSV/TXT/pcap.csv | `scripts/stage_two/parsers/dns.py` |
| Host CSV/JSON/log/syscall wrappers | `scripts/stage_two/parsers/host.py` |
| Metricbeat/system metrics | `scripts/stage_two/parsers/metrics.py` |
| NetFlow/WLS | `scripts/stage_two/parsers/netflow.py` |
| Packet captures | `scripts/stage_two/parsers/packet.py` |
| BSON sandbox telemetry | `scripts/stage_two/parsers/bson.py` |
| XML | `scripts/stage_two/parsers/xml.py` |

2. Export parser из `scripts/stage_two/parsers/__init__.py`, если он нужен tests или registry validation.
3. Добавить/обновить registry entry в `scripts/stage_two/parser_registry/parser_registry_seed.json`.
4. Убедиться, что scanner inference знает format в `scripts/stage_two/ingestion/scanner.py`.
5. Добавить direct parser smoke в `scripts/stage_two/parser_smoke.py` или focused tests в `tests/stage_two/`.
6. Добавить encoded/compressed smoke в `scripts/stage_two/parser_input_smoke.py`, если format это поддерживает.
7. Если меняется catalog behavior, обновить `scripts/stage_two/parser_catalog_smoke.py`.
8. Запустить validation commands.

## Registry rules

Пример registry group:

```json
{
  "parser_name": "host_netflow_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["netflow_day", "netflow_ids", "wls_day"],
  "supported_roles": null,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "HostNetflowParser",
  "priority": 50,
  "supports_streaming": true,
  "requires_external_tools": false
}
```

Не активируйте registry row для class, который не импортируется. `ParserResolver` и parser coverage покажут missing classes.

## Status rules

| Condition | Parser run status | Dataset file status |
| --- | --- | --- |
| Parsed rows and no failures | `SUCCESS` | `PARSED` |
| Parsed rows and row failures | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| No usable content | `EMPTY_FILE` | `EMPTY_FILE` |
| Parser cannot safely read file | `FAILED` | `FAILED` |
| Helper/context file intentionally skipped | `SKIPPED` | `SKIPPED` |
| No active parser exists | `UNSUPPORTED_FORMAT` | `UNSUPPORTED_FORMAT` |

Unknown rows нельзя silent drop. Увеличивайте `rows_failed` и сохраняйте bounded `error_samples`.

## Label rules

- Используйте `LabelResolver`; не пишите ad hoc label logic внутри parsers.
- Embedded labels разрешены только role-safe.
- TEST filename heuristics отключены.
- Missing labels остаются `label_binary=None`, `label_source="none"`, `label_status="unlabeled"`.
- Label fields и traceability fields не должны стать model input features.

## Raw data and payload safety

- Никогда не изменять raw files.
- Не использовать `eval`, `pickle` или subprocess на decoded content.
- Не извлекать ZIP members в filesystem paths.
- Не хранить full packet payloads, BSON streams или full raw logs в `metadata_json` или PostgreSQL.
- Ограничивать previews через `STAGE_TWO_MAX_RAW_PREVIEW_BYTES`.
- Ограничивать base64 decoded bytes через `STAGE_TWO_MAX_BASE64_DECODE_BYTES`.

## Validation commands

```powershell
python -m compileall manage.py config.py scripts tests
git diff --check
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

Для DB/catalog changes:

```powershell
python -m scripts.db.smoke_check
python -m alembic -c scripts/db/migrations/alembic.ini current
python -m scripts.stage_two.cli_operational_smoke
```

## Common mistakes

| Mistake | Consequence | Correct approach |
| --- | --- | --- |
| Hardcoded storage paths in parser code | Ломает portability и config control. | Использовать `config.py` и existing writer/services. |
| Binary files parsed as text | Corrupt packet/BSON handling. | Использовать binary reader modes. |
| Labels treated as raw model features | Leakage risk. | Держать labels только в canonical label fields. |
| Registry entry without class validation | Coverage gaps and runtime failures. | Implement/export class before activation. |
| Marking all files ready without coverage review | Large failed batches. | Сначала `parser-coverage`. |

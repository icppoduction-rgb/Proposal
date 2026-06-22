# Руководство добавления parser implementation

Этот документ описывает минимальный контракт нового parser в Stage Two. Новый parser должен быть безопасен для raw data, не смешивать роли и сохранять traceability.

## Где менять код

| Задача | Файл/директория |
| --- | --- |
| Parser class | `scripts/stage_two/parsers/*.py` |
| Shared helpers | `scripts/stage_two/parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py` |
| Registry entry | `scripts/stage_two/parser_registry/parser_registry_seed.json` |
| Schema contract | `schemas/normalized/normalized_event_v1.json` или новая schema version |
| Parser tests/smoke | `scripts/stage_two/parser_smoke.py`, `parser_input_smoke.py`, project tests if present |
| Документация | `docs/ru/normalization/parser_strategy.md`, этот файл, при необходимости schema docs |

## Минимальный контракт parser

Parser class должен:

1. наследоваться от `BaseParser`;
2. принимать `ParserContext`;
3. возвращать `ParserResult`;
4. заполнять обязательные normalized fields;
5. не изменять raw файл;
6. сохранять `event_index` или другой порядок, если timestamp отсутствует;
7. использовать `LabelResolver`, а не назначать benign по умолчанию;
8. сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не терять их.

Обязательные поля перечислены в [normalized_event_schema.md](normalized_event_schema.md).

## Шаблон решения

```python
from pathlib import Path

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import build_timestamp_fields
from scripts.stage_two.parsers.input_reader import UniversalInputReader


class MyParser(BaseParser):
    parser_name = "my_parser"
    parser_version = "v1"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        events: list[dict[str, object]] = []
        errors: list[str] = []

        reader = UniversalInputReader(path)
        with reader.open("json_lines") as records:
            for event_index, raw_record in enumerate(records):
                try:
                    timestamp_fields = build_timestamp_fields(
                        raw_record.get("timestamp"),
                        event_index=event_index,
                    )
                    labels = self.label_resolver.resolve(raw_record, context)
                    events.append(self.base_event(
                        context,
                        event_index=event_index,
                        **timestamp_fields,
                        **labels,
                        event_type="my_event",
                        entity_type="host",
                        modality="host_event",
                        raw_fields_json=raw_record,
                    ))
                except Exception as exc:
                    errors.append(f"event_index={event_index}: {exc}")

        return ParserResult(
            events=events,
            rows_read=len(events) + len(errors),
            rows_parsed=len(events),
            rows_failed=len(errors),
            error_samples=errors,
        )
```

В реальном parser используйте тот reader mode, который соответствует формату (`csv_rows`, `json_lines`, `lines`, `binary`, `packet_bytes`, `bson_stream`). Не добавляйте псевдополя в normalized output без обновления schema contract.

## Запись в registry

После добавления class нужно добавить или расширить parser group в:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Минимальные поля:

```json
{
  "parser_name": "my_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["my_format"],
  "supported_roles": null,
  "priority": 100,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "MyParser"
}
```

`supported_roles = null` означает все активные роли. Если parser допустим только для `TEST` или только для `TRAIN/VALIDATION`, задайте список явно. Например `HostBsonSandboxParser` ограничен `TEST`, а `HostPacketCaptureParser` - `TRAIN`/`VALIDATION`.

## Обработка labels

Parser не должен самостоятельно назначать `label_binary = 0` при отсутствии label. Используйте `LabelResolver`:

- explicit embedded/external labels дают `explicit_label` или configured status;
- weak/inferred labels должны иметь confidence/source;
- conflicting labels должны фиксироваться как `conflicting_label`;
- для `TEST` filename/embedded heuristics отключены.

См. [label_resolver.md](label_resolver.md).

## Обработка timestamp

Запрещено подставлять `datetime.now()` для отсутствующего timestamp.

Используйте правила:

```text
timestamp present -> timestamp_type = absolute
timestamp missing but event_index present -> timestamp_type = event_order
timestamp missing and no ordering -> timestamp_type = missing
```

## Обработка ошибок

| Ошибка | Как фиксировать |
| --- | --- |
| Битая строка | Увеличить failed counter, добавить sample в errors, продолжить если возможно. |
| Empty file | Вернуть status override `EMPTY_FILE` или `SKIPPED`, не создавать fake benign events. |
| Unsupported subformat | Вернуть `UNSUPPORTED_FORMAT` или error metadata, если parser не может безопасно читать файл. |
| Schema drift | Сохранить raw payload в JSON fields и добавить warning. |
| Large binary file | Использовать packet summary/sample режимы; не загружать весь файл в память без необходимости. |

## Проверки после добавления parser

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --dry-run
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit 10
python manage.py stage-two run-duckdb-checks
```

Если parser влияет на labels или model-ready downstream, дополнительно:

```bash
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Документация, которую нужно обновить

- `parser_strategy.md` - список parser classes/source formats.
- `normalized_event_schema.md` - если добавлены новые normalized fields или новая schema version.
- `label_resolver.md` - если появились новые label fields/rules.
- `data_quality_checks.md` - если нужен новый quality check.
- `performance_tuning.md` - если parser требует специальных runtime limits.

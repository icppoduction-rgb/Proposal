# Точки расширения, ограничения и технический долг

## Добавление нового parser implementation

Минимальный безопасный flow:

1. Добавить parser class в подходящий модуль `scripts/stage_two/parsers/*` или создать новый модуль.
2. Использовать `UniversalInputReader`, если формат text/csv/json-lines/base64/compression sensitive.
3. Строить events через shared helpers из `scripts/stage_two/parsers/common.py`.
4. Возвращать корректный `ParseResult` со status/counters/warnings/errors.
5. Добавить class export в `scripts/stage_two/parsers/__init__.py`.
6. Добавить/обновить `parser_registry_seed.json`.
7. Проверить `ParserResolver` и `parser-coverage`.
8. Добавить direct smoke и, если формат catalog-dependent, catalog smoke.
9. Запустить `compileall`, `git diff --check` и targeted CLI smoke.

Нельзя активировать registry entry, если parser class отсутствует или не импортируется.

## Расширение scanner/source_format inference

`scripts/stage_two/ingestion/scanner.py` должен сохранять точные bucket names. Для compound форматов bucket/source name важнее extension:

```text
pcap.csv
process.summary.log
socket.summary.log
netflow_day
netflow_ids
wls_day
journal~
syslog-1
```

Если новый dataset уже отсортирован в role/format bucket, scanner должен использовать bucket name. Extension heuristic применяется только для raw root без bucket context.

## Расширение CLI

Новые Stage Two команды добавляются в `scripts/stage_two/cli.py`. Требования:

- сохранять `manage.py module/service/action` interface;
- использовать `extra_args` для flags;
- поддерживать explicit errors для unknown command;
- не ломать legacy aliases `normalize-dns` и `normalize-host`;
- для destructive/status-changing operations использовать dry-run по умолчанию и явный `--apply`.

## Расширение catalog

Изменения DB schema должны идти через Alembic migration и repository layer:

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini revision -m "..."
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

Repository методы не должны делать скрытый commit, если операция управляется service/session_scope на уровне выше.

## Расширение quality/leakage checks

При добавлении feature/model-ready этапов нужно обновить:

- `scripts/stage_two/quality/checkers.py`;
- `scripts/stage_two/quality/checks.py`;
- `scripts/stage_two/duckdb/service.py`;
- `scripts/stage_two/readiness_check.py`;
- документацию `docs/*/normalization/data_leakage_prevention.md`.

Запрещенные model input признаки должны оставаться вне features:

- `source_file_path`;
- `dataset_role`;
- `source_file_hash`;
- parser metadata;
- filename/scenario hints;
- raw label columns.

## Основные риски

| Риск | Почему важен | Контроль |
| --- | --- | --- |
| Registry указывает на несуществующий class | Batch упадет на runtime import. | Resolver class availability validation + parser coverage. |
| `source_format` схлопывается до extension | Compound buckets получают неправильный parser. | Scanner bucket-first inference и tests. |
| TEST label leakage | Модель может обучиться на сплитовых/filename hints. | LabelResolver guards и leakage checks. |
| Full payload в DB/report | Рост БД и утечка данных. | Store Parquet path/hash/counters, raw preview only. |
| Роль смешивается в batch | Train/validation/test contamination. | `normalize-format` scoped by branch/role/source_format; `normalize-all` groups by role/format. |
| Raw file mutation | Нарушение reproducibility/hash. | Parser read-only behavior и hash checks. |
| Feature/model-ready assumptions | Таблицы есть, но общий production CLI не реализован. | Документировать как limitation, не заявлять full pipeline success без проверки. |

## Технический долг

| Область | Состояние |
| --- | --- |
| Stage One docs filenames | `hadlers_*` - историческая опечатка в именах документов. |
| `config.manage_commands` | Может отставать от фактического Stage Two CLI; source of truth - `scripts/stage_two/cli.py`. |
| Feature/model-ready CLI | Контракты и writers есть, но нужен отдельный production workflow. |
| Full-corpus validation | Требует доступной PostgreSQL DB и полного набора raw datasets. |
| Parser specialization | Некоторые форматы покрыты robust generic parser group; при появлении новых schema variants может потребоваться отдельный parser class. |

## Minimum review checklist

Перед merge parser/normalization изменений:

```powershell
python -m compileall manage.py config.py scripts
git diff --check
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
```

DB/full workflow проверки дополнительно:

```powershell
python -m scripts.db.smoke_check
python -m scripts.stage_two.parser_catalog_smoke
python -m scripts.stage_two.cli_operational_smoke
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

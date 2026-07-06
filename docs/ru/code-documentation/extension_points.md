# Точки расширения

## Добавить новый handler

Где менять:

- новый module в `scripts/handlers/<group>`;
- маршрут в `scripts/handlers/router_handler.py` или group router;
- config constants в `config.py`, если нужны пути.

Контракт:

- валидировать входные пути;
- возвращать dataclass result;
- писать JSON через `JsonDataManager`;
- не изменять raw-файлы;
- сохранять разделение TRAIN/VALIDATION/TEST.

Проверка:

```bash
python -m compileall -q manage.py config.py scripts
python manage.py handlers <service> <action>
```

Обновить документацию:

- this section;
- `cli_and_routing.md`;
- relevant Stage One docs.

## Добавить action для `dns_analyze`

Где менять:

- добавить handler file в `scripts/handlers/dns_analyze`;
- экспортировать class в `scripts/handlers/dns_analyze/__init__.py`;
- добавить function в `run_action.py`;
- добавить route в `router_dns.py`.

Минимальный контракт:

- читать `sort-path-dns-file.json`;
- валидировать role/format bucket;
- анализировать ограниченную выборку файлов;
- писать summary JSON;
- писать RU/EN docs и reports;
- возвращать dataclass со status и paths.

## Добавить action для `host_analyze`

Аналогично DNS, но файлы находятся в `scripts/handlers/host_analyze`, а маршрут добавляется в `router_host.py`.

Учитывайте смешанные схемы и большие файлы. Не загружайте файлы без ограничений целиком в память.

## Добавить class парсера

Где менять:

- `scripts/stage_two/parsers/<module>.py`;
- при необходимости shared utilities в `parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py`.

Контракт:

- наследовать `BaseParser`;
- реализовать `parse()` и желательно потоковый `parse_batches()`;
- отдавать normalized events с обязательными fields;
- вызывать `self.validate_result(result)`;
- использовать `LabelResolverProtocol`;
- не синтезировать текущее время как source timestamp;
- хранить raw/source fields в `raw_fields_json` или `metadata_json`, а не в X features.

Проверки:

```bash
python -m pytest -q tests/stage_two/test_<parser>*.py
python -m pytest -q tests/stage_two/test_parser_registry_seed.py
```

## Добавить запись parser registry

Где менять: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Шаги:

1. Добавить parser group или source format.
2. Запустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
```

3. Проверить `is_active=true` в `parser_registry`.

## Добавить version схемы

Где менять:

- `schemas/normalized`;
- `schemas/features`;
- `schemas/model_ready`;
- registry code, если требуется новое поведение layer.

Контракт:

- увеличить `schema_version`;
- явно зафиксировать стратегию backward compatibility;
- обновить регистрацию `schema_versions`;
- обновить writer/validator tests.

## Добавить label mapping rule

Где менять:

- DB table `label_mapping_rules`; or
- `PATH_DATA_STORAGE/config/label_mapping_rules.json`.

Контракт:

- определить `rule_uid`;
- по возможности ограничить правило через branch/role/source_format;
- использовать явный `label_source`;
- задать `label_status` и confidence;
- не создавать TEST filename heuristic labels.

Проверяйте unit tests для `LabelResolver`.

## Добавить quality check

Где менять: `scripts/stage_two/quality/checkers.py`.

Контракт:

- возвращать `QualityCheckResult`;
- включать severity;
- включать `rows_total`, `rows_failed` и diagnostic details;
- при необходимости регистрировать aggregate через `register_quality_report`.

Если check защищает от leakage, failed severity должен быть `CRITICAL`.

## Расширить Stage Three feature/model-ready

Где менять:

- feature logic в `scripts/stage_three/extraction`;
- preprocessing logic в `scripts/stage_three/preprocessing`;
- model-ready logic в `scripts/stage_three/model_ready`;
- quality/leakage logic в `scripts/stage_three/quality`;
- CLI route в `scripts/stage_three/cli.py`, если появляется новая команда.

Контракт:

- хранить role partitions отдельно;
- сохранять traceability fields в feature layer;
- исключать forbidden columns из X;
- писать y отдельно;
- выполнять fit preprocessing только на TRAIN;
- регистрировать artifacts в catalog;
- запускать quality/leakage/traceability checks перед использованием model-ready artifacts;
- обновлять `stage-three/` docs и `stage_three_overview.md`.

Проверки:

```bash
python -m pytest -q tests/stage_three
python manage.py stage-three run-quality-checks --experiment-id <id>
python manage.py stage-three run-leakage-checks --experiment-id <id>
python manage.py stage-three final-report --experiment-id <id>
```

## Добавить Stage Four training/evaluation layer

Stage Four пока не реализован. Новый слой должен читать только artifacts, которые прошли `stage-three final-report` со статусом `READY_FOR_STAGE_FOUR`.

Минимальный контракт:

- не читать raw files как training input;
- не использовать TEST для training, preprocessing fit, threshold tuning или feature selection;
- фиксировать seeds, metrics, model configs и artifact versions;
- сохранять evaluation reports отдельно от Stage Three final report;
- запускать SHAP/XAI только после leakage checks.

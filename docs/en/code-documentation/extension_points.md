# Extension Points

## Add a New Handler

Where to change:

- new module under `scripts/handlers/<group>`;
- route in `scripts/handlers/router_handler.py` or group router;
- config constants in `config.py` if paths are needed.

Contract:

- validate input paths;
- return dataclass result;
- write JSON through `JsonDataManager`;
- do not mutate raw files;
- preserve TRAIN/VALIDATION/TEST separation.

Check:

```bash
python -m compileall -q manage.py config.py scripts
python manage.py handlers <service> <action>
```

Update docs:

- this section;
- `cli_and_routing.md`;
- relevant Stage One docs.

## Add a `dns_analyze` Action

Where to change:

- add handler file in `scripts/handlers/dns_analyze`;
- export class in `scripts/handlers/dns_analyze/__init__.py`;
- add function in `run_action.py`;
- add route in `router_dns.py`.

Minimal contract:

- read `sort-path-dns-file.json`;
- validate role/format bucket;
- sample a bounded number of files;
- write summary JSON;
- write RU/EN docs and reports;
- return dataclass with status and paths.

## Add a `host_analyze` Action

Same as DNS, but files live under `scripts/handlers/host_analyze`, and the route is added to `router_host.py`.

Pay attention to mixed schemas and large files. Do not load unbounded files fully into memory.

## Add a Parser Class

Where to change:

- `scripts/stage_two/parsers/<module>.py`;
- optionally shared utilities under `parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py`.

Contract:

- inherit `BaseParser`;
- implement `parse()` and preferably streaming `parse_batches()`;
- emit normalized events with required fields;
- call `self.validate_result(result)`;
- use `LabelResolverProtocol`;
- do not synthesize current time as source timestamp;
- keep raw/source fields in `raw_fields_json` or `metadata_json`, not X features.

Tests:

```bash
python -m pytest -q tests/stage_two/test_<parser>*.py
python -m pytest -q tests/stage_two/test_parser_registry_seed.py
```

## Add a Parser Registry Entry

Where to change: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Steps:

1. Add parser group or source format.
2. Run:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
```

3. Verify `is_active=true` in `parser_registry`.

## Add a Schema Version

Where to change:

- `schemas/normalized`;
- `schemas/features`;
- `schemas/model_ready`;
- registry code if new layer behavior is required.

Contract:

- increment `schema_version`;
- define backward compatibility strategy;
- update `schema_versions` registration;
- update writer/validator tests.

## Add a Label Mapping Rule

Where to change:

- DB table `label_mapping_rules`; or
- `PATH_DATA_STORAGE/config/label_mapping_rules.json`.

Contract:

- define `rule_uid`;
- restrict by branch/role/source_format where possible;
- use explicit `label_source`;
- set `label_status` and confidence;
- do not create TEST filename heuristic labels.

Check unit tests for `LabelResolver`.

## Add a Quality Check

Where to change: `scripts/stage_two/quality/checkers.py`.

Contract:

- return `QualityCheckResult`;
- include severity;
- include `rows_total`, `rows_failed`, diagnostic details;
- register aggregate via `register_quality_report` if needed.

If the check protects against leakage, failed severity should be `CRITICAL`.

## Extend Stage Three Feature/Model-ready Logic

Where to change:

- feature logic under `scripts/stage_three/extraction`;
- preprocessing logic under `scripts/stage_three/preprocessing`;
- model-ready logic under `scripts/stage_three/model_ready`;
- quality/leakage logic under `scripts/stage_three/quality`;
- CLI route in `scripts/stage_three/cli.py` if a new command is needed.

Contract:

- keep role partitions separate;
- preserve traceability fields in the feature layer;
- exclude forbidden columns from X;
- write y separately;
- fit preprocessing only on TRAIN;
- register artifacts in catalog;
- run quality/leakage/traceability checks before using model-ready artifacts;
- update `stage-three/` docs and `stage_three_overview.md`.

Tests:

```bash
python -m pytest -q tests/stage_three
python manage.py stage-three run-quality-checks --experiment-id <id>
python manage.py stage-three run-leakage-checks --experiment-id <id>
python manage.py stage-three final-report --experiment-id <id>
```

## Add a Stage Four Training/Evaluation Layer

Stage Four is not implemented yet. The new layer must read only artifacts whose `stage-three final-report` status is `READY_FOR_STAGE_FOUR`.

Minimal contract:

- do not read raw files as training input;
- do not use TEST for training, preprocessing fit, threshold tuning, or feature selection;
- fix seeds, metrics, model configs, and artifact versions;
- store evaluation reports separately from the Stage Three final report;
- run SHAP/XAI only after leakage checks.

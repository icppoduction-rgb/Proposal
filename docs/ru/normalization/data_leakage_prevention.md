# Data leakage prevention

Stage Two рассматривает leakage prevention как data contract. Labels, split identity, source file metadata, parser metadata и traceability fields не являются model input features.

## Commands

```powershell
python manage.py stage-two run-leakage-checks
```

Expected successful output:

```text
"service": "stage-two run-leakage-checks"
"status": "SUCCESS"
"severity": "INFO"
```

## Label resolution

Implementation:

```text
scripts/stage_two/labels/resolver.py
```

`LabelResolver` sources:

| Source | Allowed behavior |
| --- | --- |
| Embedded source fields | Разрешены, когда role-safe, например TRAIN labels в реальных columns. |
| DB/config `label_mapping_rules` | Разрешены, когда rule matches branch/role/source format/context. |
| Filename hints | Conservative и disabled for TEST. |
| IDS alert fields | Weak label only when role-safe. |
| Missing labels | Explicit `unlabeled`, никогда benign by default. |

Canonical label fields:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
```

## TEST safety

- TEST filename heuristics отключены.
- TEST statistics не используются для fit scalers, imputers, encoders, thresholds, feature selectors или models.
- TEST rows могут transform только через TRAIN-fitted preprocessing artifacts.

## Forbidden X columns

Forbidden model input columns определены в:

```text
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

Они включают:

- labels и target aliases;
- dataset role/split identifiers;
- source paths и source hashes;
- parser metadata и schema metadata;
- traceability ids;
- raw/metadata JSON fields;
- scenario names и context-only fields.

## Leakage checker

Implementation:

```text
scripts/stage_two/quality/checkers.py
```

Checker использует DuckDB views и catalog metadata для reports по critical leakage issues. Reports:

```text
reports/en/stage-two/leakage/leakage_report.json
reports/ru/stage-two/leakage/leakage_report.json
```

## Parser development rules

- Не копировать raw label columns в `features_json` как model-ready features.
- Не infer TEST labels из filenames.
- `dataset_role`, `branch`, `source_format`, `source_file_path`, `source_file_hash`, `parser_name`, `parser_version` остаются traceability/context only.
- Unknown fields сохранять в `raw_fields_json` или `metadata_json`, не в X feature columns.
- Missing labels сохранять как `label_binary=None`.

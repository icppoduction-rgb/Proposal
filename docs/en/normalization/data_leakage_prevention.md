# Data Leakage Prevention

Stage Two treats leakage prevention as a data contract. Labels, split identity, source file metadata, parser metadata, and traceability fields are not model input features.

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

## Label Resolution

Implementation:

```text
scripts/stage_two/labels/resolver.py
```

`LabelResolver` sources:

| Source | Allowed behavior |
| --- | --- |
| Embedded source fields | Allowed when role-safe, e.g. TRAIN labels in real columns. |
| DB/config `label_mapping_rules` | Allowed when rule matches branch/role/source format/context. |
| Filename hints | Conservative and disabled for TEST. |
| IDS alert fields | Weak label only when role-safe. |
| Missing labels | Explicit `unlabeled`, never benign by default. |

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

## TEST Safety

- TEST filename heuristics are disabled.
- TEST statistics must not fit scalers, imputers, encoders, thresholds, feature selectors, or models.
- TEST rows may be transformed only with TRAIN-fitted preprocessing artifacts.

## Forbidden X Columns

Forbidden model input columns are defined in:

```text
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

They include:

- labels and target aliases;
- dataset role/split identifiers;
- source paths and source hashes;
- parser metadata and schema metadata;
- traceability ids;
- raw/metadata JSON fields;
- scenario names and other context-only fields.

## Leakage Checker

Implementation:

```text
scripts/stage_two/quality/checkers.py
```

The checker uses DuckDB views and catalog metadata to report critical leakage issues. Reports are written to:

```text
reports/en/stage-two/leakage/leakage_report.json
reports/ru/stage-two/leakage/leakage_report.json
```

## Parser Development Rules

- Do not copy raw label columns into `features_json` as model-ready features.
- Do not infer TEST labels from filenames.
- Keep `dataset_role`, `branch`, `source_format`, `source_file_path`, `source_file_hash`, `parser_name`, and `parser_version` as traceability/context only.
- Preserve unknown fields in `raw_fields_json` or `metadata_json`, not in X feature columns.
- Treat missing labels as `label_binary=None`.

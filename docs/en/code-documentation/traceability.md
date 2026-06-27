# Traceability

Traceability links a model-ready artifact to feature artifact, normalized Parquet, parser run, raw file, and dataset.

## Service

File: `scripts/stage_two/traceability/service.py`.

Command:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Lookup modes:

- numeric argument -> `model_ready_artifacts.id`;
- non-numeric argument -> `model_ready_artifacts.artifact_path`.

## Chain

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

## Returned Metadata

`TraceabilityChain` returns dictionaries for:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Key fields include artifact paths, role, branch, data type/modality, statuses, parser counters, raw file path/hash, and dataset identity.

## Required Links

The service raises `TraceabilityError` if:

- model-ready artifact is not found;
- `feature_artifact_id` is null;
- linked feature artifact is not found;
- `normalized_artifact_id` is null;
- linked normalized artifact is not found;
- linked parser run is not found;
- linked dataset file is not found;
- linked dataset is not found.

## Contract Implications

Some FK columns are nullable to support staged/incomplete artifacts, but production artifacts used for experiments must populate traceability links. Otherwise:

- reproducibility is broken;
- leakage audits cannot attribute samples;
- academic implementation description cannot prove lineage;
- model-ready artifacts should be treated as incomplete.

## Traceability in Row Schemas

Normalized rows include event/file/parser fields. Feature rows should preserve:

```text
sample_uid
dataset_id
normalized_artifact_id
role
branch
feature_group
feature_schema_name
feature_schema_version
source_event_uid_refs
source_normalized_path
created_at
```

These traceability fields are required in feature artifacts but excluded from model-ready X artifacts. They remain in catalog and audit layers.

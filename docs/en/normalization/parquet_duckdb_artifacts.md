# Parquet and DuckDB Artifacts

Stage Two stores large tables in Parquet and uses DuckDB for analytical SQL checks over those files. PostgreSQL Catalog stores metadata only: paths, row counts, hashes, schema versions, statuses, and relationships.

## Parquet Writer

Code:

```text
scripts/stage_two/parquet/writer.py
```

`ParquetArtifactWriter`:

- writes rows to Parquet;
- serializes fields ending in `_json` to deterministic JSON strings;
- uses `zstd` compression by default;
- computes `row_count`, `file_size_bytes`, and optional `content_hash_sha256`;
- registers artifacts through `ArtifactRepository`.

Output hashing is controlled by the normalization option `--hash-output-artifacts`. If hashing is disabled, `content_hash_sha256` may be an empty string.

## Normalized Artifact Paths

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Example:

```text
parquet/normalized/dns/TRAIN/dns_query/dns-train/schema=v1/part-42.parquet
```

Writers:

- `DnsNormalizationService`;
- `HostNormalizationService`;
- `NormalizeFormatRunner`;
- legacy `normalize-dns`/`normalize-host`.

Catalog entry: `normalized_artifacts.normalized_path`.

## Feature Artifact Paths

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Feature groups from the contract:

```text
dns_features
host_syscall_features
host_eventlog_features
host_metrics_features
network_flow_features
hybrid_features
sequence_features
```

Catalog entry: `feature_artifacts.feature_path`.

The current CLI does not provide a dedicated feature artifact build command. Contract helpers and the writer service are implemented in `scripts/stage_two/features/contracts.py` and `scripts/stage_two/features/writer.py`.

## Model-Ready Artifact Paths

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

Supported `data_type` values:

```text
X
y
sequence
split_index
preprocessing_metadata
```

Catalog entry: `model_ready_artifacts.artifact_path`.

`ModelReadyRegistryService` verifies:

- `data_type` is part of the contract;
- `X` rows do not contain forbidden leakage columns;
- preprocessing artifacts are fitted only on `TRAIN`.

## DuckDB Service

Code:

```text
scripts/stage_two/duckdb/service.py
```

DuckDB creates views over Parquet:

| View | Path pattern | Required columns |
| --- | --- | --- |
| `normalized_all` | `parquet/normalized/**/*.parquet` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `parquet/features/**/*.parquet` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` | `filename` |

If no matching Parquet files exist, the service creates a placeholder view with required columns so checks return controlled results instead of failing because the view is missing.

## DuckDB Checks

Command:

```bash
python manage.py stage-two run-duckdb-checks
```

Checks:

- row counts by view;
- required columns;
- split contamination (`TRAIN`, `VALIDATION`, and `TEST` must not mix);
- schema mismatch diagnostics.

Report path:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

Through `register_report()`, the result is registered in `data_quality_reports`.

## Limitations

- DuckDB reads already written Parquet files; it does not replace PostgreSQL Catalog.
- Feature/model-ready paths exist only after the corresponding writer/registry services are called; there is no CLI build step for them yet.
- Moving Parquet files without updating the catalog breaks traceability.
- `TRAIN`, `VALIDATION`, and `TEST` must remain separated in paths, catalog metadata, and downstream artifacts.

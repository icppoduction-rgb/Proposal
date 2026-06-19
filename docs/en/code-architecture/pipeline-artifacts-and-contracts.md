# Pipeline Artifacts And Contracts

This document maps pipeline stages to input/output artifacts.

## Stage One Artifacts

| Artifact | Config/path | Producer |
| --- | --- | --- |
| DNS file summary | `DNS_FILE` | `handlers analyze-dataset dns-dataset-handler` |
| Host file summary | `HOST_FILE` | `handlers analyze-dataset host-dataset-handler` |
| DNS path summary | `DNS_PATH_FILE` | Stage One handlers |
| Host path summary | `HOST_PATH_FILE` | Stage One handlers |
| DNS format summary | `SORT_DNS_FORMAT_SUMMARY` | `handlers sort sort-dns-dataset-handler` |
| Host format summary | `SORT_HOST_FORMAT_SUMMARY` | `handlers sort sort-host-dataset-handler` |
| DNS sorted paths | `SORT_PATH_DNS_FILE` | `handlers save-sort save-sort-dns-dataset-handler` |
| Host sorted paths | `SORT_PATH_HOST_FILE` | `handlers save-sort save-sort-host-dataset-handler` |

Stage One artifacts are JSON diagnostics. Stage Two may read sorted path JSON for coverage diagnostics only; `PATH_FOLDER_DATASETS_FILTER` plus PostgreSQL catalog ingestion remains the production input.

## Stage Two Catalog Artifacts

| Artifact | Table |
| --- | --- |
| Dataset metadata | `datasets` |
| File metadata/status | `dataset_files` |
| Parser metadata | `parser_registry` |
| Parser execution | `parser_runs` |
| Schema version | `schema_versions` |
| Normalized output metadata | `normalized_artifacts` |
| Feature output metadata | `feature_artifacts` |
| Model-ready output metadata | `model_ready_artifacts` |
| Quality/leakage/readiness report metadata | `data_quality_reports` |

## Schema Contracts

| Contract | File | Status |
| --- | --- | --- |
| Normalized event | `schemas/normalized/normalized_event_v1.json` | Used by parser registry and normalized Parquet. |
| Feature artifact | `schemas/features/feature_artifact_v1.json` | Contract exists; full production CLI not implemented. |
| Model-ready artifact | `schemas/model_ready/model_ready_v1.json` | Contract exists; full production CLI not implemented. |

## Parquet Artifacts

| Layer | Path template |
| --- | --- |
| Normalized | `parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` |
| Features | `parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` |
| Model-ready tabular | `parquet/model_ready/tabular/{branch}/{role}/schema=v1/*.parquet` |
| Model-ready labels | `parquet/model_ready/labels/{branch}/{role}/schema=v1/*.parquet` |
| Model-ready sequences | `parquet/model_ready/sequences/{branch}/{role}/schema=v1/*.npz` |
| Preprocessing metadata | `parquet/model_ready/preprocessing/{branch}/schema=v1/*` |

Only the normalized Parquet production writer is exercised by current parser normalization commands.

## Report Artifacts

| Report | Path |
| --- | --- |
| Parser coverage | `reports/{en,ru}/stage-two/parser/parser_coverage_matrix.{json,md}` |
| Parser run diagnostics | `reports/{en,ru}/stage-two/parser/` |
| Normalization diagnostics | `reports/{en,ru}/stage-two/normalization/` |
| DuckDB quality | `reports/en/stage-two/quality/duckdb_analytics_report.json` |
| Leakage | `reports/{en,ru}/stage-two/leakage/leakage_report.json` |
| Readiness | `reports/{en,ru}/stage-two/stage_two_readiness_report.md` and EN JSON |

## Traceability Contract

The intended lineage is:

```text
filtered source file
  -> dataset_files
  -> parser_runs
  -> normalized_artifacts
  -> feature_artifacts
  -> model_ready_artifacts
```

Use:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

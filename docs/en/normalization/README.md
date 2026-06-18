# Stage Two: Data Normalization

Stage Two is the data normalization and catalog control plane for the project. It reads immutable raw dataset files, registers them in PostgreSQL, resolves a parser through the parser registry, writes normalized event data to Parquet, and keeps traceability in catalog tables.

Current implemented CLI scope:

```text
raw datasets -> catalog ingestion -> parser registry -> parser run -> normalized Parquet -> catalog artifact registration -> quality/leakage/readiness checks
```

Feature and model-ready schemas, catalog tables, and artifact contracts exist in `schemas/features/feature_artifact_v1.json`, `schemas/model_ready/model_ready_v1.json`, `scripts/stage_two/features/`, and `scripts/stage_two/model_ready/`. A production CLI that builds every feature/model-ready artifact for the full corpus is not part of the current parser workflow.

## Main Commands

```powershell
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two seed-parser-registry
python manage.py stage-two catalog-ingest
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Stage Two smoke scripts are supported only in module form, for example `python -m scripts.stage_two.parser_smoke`. Do not run them as file paths such as `python scripts/stage_two/parser_smoke.py`, because that execution mode can break package imports.

Backward-compatible normalization aliases remain available:

```powershell
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

## Documentation Map

- [Stage Two usage guide](usage_guide.md): operational runbook from raw files to normalized artifacts.
- [Parser strategy](parser_strategy.md): source formats, parser classes, statuses, and registry behavior.
- [Parser development guide](parser_development_guide.md): how to add a new parser safely.
- [PostgreSQL catalog schema](postgresql_catalog_schema.md): catalog tables and relationships.
- [Normalized event schema](normalized_event_schema.md): canonical normalized event contract.
- [Storage architecture](storage_architecture.md): storage roots and generated artifact paths.
- [Parquet and DuckDB artifacts](parquet_duckdb_artifacts.md): Parquet writer and DuckDB checks.
- [Data quality checks](data_quality_checks.md): quality/readiness checks and reports.
- [Data leakage prevention](data_leakage_prevention.md): label and split safety rules.
- [Final Codex summary template](final_summary_template.md): final task summary format and staged validation commands.

## Core Invariants

- Raw datasets are never modified by Stage Two.
- PostgreSQL stores metadata, statuses, relationships, parser runs, and artifact records; large normalized data is stored in Parquet.
- TRAIN, VALIDATION, TEST, and EXPERIMENTS remain logically separated in catalog rows and physically separated in Parquet paths.
- `catalog-ingest` does not automatically mark files as `READY_FOR_PARSING`; `mark-ready` is the explicit operational gate.
- `normalize-format` processes exactly one `branch`/`role`/`source_format` slice.
- `normalize-all` processes one branch in role/source_format groups, not one uncontrolled mixed transaction.
- Missing source values are represented as `None`/SQL `NULL`/Parquet null.
- Unknown source fields are preserved in `raw_fields_json`, `features_json`, or `metadata_json`.
- Labels must not enter X/model input columns. TEST filename heuristics are disabled.
- Parser failures must be visible through `parser_runs`, `dataset_files.status`, reports, and counters.

## Current Parser Groups

| Branch | Parser class | Source formats |
| --- | --- | --- |
| dns | `DnsCsvParser` | `csv` |
| dns | `DnsPcapCsvParser` | `pcap.csv` |
| dns | `DnsTxtDomainListParser` | `txt` for DNS VALIDATION |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` |
| host | `HostCsvParser` | `csv` |
| host | `HostJsonLinesParser` | `json`, `json-1` |
| host | `HostLineLogParser` | host line-log formats and metric log buckets |
| host | `HostMetricbeatParser` | metric formats delegated from `HostLineLogParser` |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` |
| host | `HostBsonSandboxParser` | `bson` for host TEST |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` |
| host | `HostXmlParser` | `xml` |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` for host TRAIN/VALIDATION |

Run the authoritative coverage command before large normalization batches:

```powershell
python manage.py stage-two parser-coverage
```

The report is written under:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md
PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md
```

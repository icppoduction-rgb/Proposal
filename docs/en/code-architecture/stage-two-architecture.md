# Stage Two Architecture

Stage Two is implemented under `scripts/stage_two/`. Its authoritative dataset input is `PATH_FOLDER_DATASETS_FILTER`. The raw root `PATH_FOLDER_DATASETS` is retained for immutable source storage, Stage One discovery, and audit/backtracking; it is not scanned by default catalog ingestion.

## Pipeline

```text
bootstrap-storage
  -> alembic upgrade
  -> seed-parser-registry
  -> catalog-ingest
  -> parser-coverage
  -> mark-ready
  -> normalize-format / normalize-all
  -> run-duckdb-checks
  -> run-leakage-checks
  -> readiness_check
```

## Modules

| Module | Responsibility |
| --- | --- |
| `storage/bootstrap.py` | Idempotent directory creation under `PATH_DATA_STORAGE`. |
| `ingestion/scanner.py` | Branch/role/source_format inference. |
| `ingestion/catalog_ingestion_service.py` | Filtered dataset catalog ingestion and status assignment. |
| `ingestion/file_hash_service.py` | Raw file SHA-256 hashing. |
| `parser_registry/seed.py` | Registry/schema seeding and parser class validation. |
| `parser_registry/resolver.py` | Parser selection, class loading, schema version resolution. |
| `parsers/` | Parser implementations and shared parser utilities. |
| `labels/resolver.py` | Canonical label resolution and leakage guards. |
| `normalization/dns_service.py` | DNS file normalization into Parquet/catalog artifacts. |
| `normalization/host_service.py` | Host file normalization into Parquet/catalog artifacts. |
| `normalization/runner.py` | `normalize-format` and `normalize-all` batch runners. |
| `parquet/writer.py` | Parquet writing and artifact registration support. |
| `reports/parser_reports.py` | Parser coverage and parser run reports. |
| `duckdb/service.py` | DuckDB views and quality report registration. |
| `quality/checkers.py` | Leakage checks. |
| `traceability/service.py` | Artifact lineage lookup. |
| `readiness_check.py` | Final operational readiness report. |

## Parser Registry

Registry seed maps `branch` and `source_format` to parser module/class. Active parser groups cover DNS CSV/TXT/PCAP, Host CSV/JSON/log/metrics/syscall/BSON/NetFlow/XML/packet formats.

Coverage is checked with:

```powershell
python manage.py stage-two parser-coverage
```

Implemented parser groups:

| Branch | Source formats | Parser classes |
| --- | --- | --- |
| DNS | `csv` | `DnsCsvParser` |
| DNS | `pcap.csv` | `DnsPcapCsvParser` |
| DNS | `txt` | `DnsTxtDomainListParser` |
| DNS | `pcap`, `pcapng`, `cap` | `DnsPacketCaptureParser` |
| Host | `csv` | `HostCsvParser` |
| Host | `json`, `json-1` | `HostJsonLinesParser` |
| Host | line logs such as `auth.log`, `syslog*`, `messages*`, `mainlog*`, `journal*`, `mail-*`, `log-*`, `info` | `HostLineLogParser` |
| Host | metric logs such as `cpu.log`, `diskio.log`, `filesystem.log`, `process.summary.log`, `socket.summary.log` | `HostMetricbeatParser` |
| Host | `ghc`, `sc`, `txt` | `HostSyscallTraceParser` |
| Host | `bson` | `HostBsonSandboxParser` |
| Host | `netflow_day`, `netflow_ids`, `wls_day` | `HostNetflowParser` |
| Host | `xml` | `HostXmlParser` |
| Host | `pcap`, `pcapng`, `cap` | `HostPacketCaptureParser` |

## Normalization Services

DNS and Host services follow the same pattern:

1. Resolve parser metadata with `ParserResolver`.
2. Resolve `schema_version_id` from `schema_versions`.
3. Create `parser_runs` row.
4. Build `ParserContext`.
5. Run parser class.
6. Write normalized rows to Parquet if events exist.
7. Register `normalized_artifacts`.
8. Update parser run/file statuses.
9. Save parser reports in RU/EN paths.

Large-file execution adds these constraints:

- parser output is consumed through `parse_batches`;
- Parquet output is split into bounded parts controlled by `max_output_part_rows`;
- packet captures use streaming PCAP/PCAPNG readers and do not concatenate packet bytes into memory;
- output artifact hashing is disabled by default because rereading multi-GB Parquet parts is a separate bottleneck;
- per-file performance metrics are stored in `parser_runs.metadata_json.performance`;
- normalized part metadata stores `part_index`, `batch_index`, row counts, and checkpoint counters.

`--workers` uses `ProcessPoolExecutor` at file granularity. Each worker opens its own database session, normalizes one cataloged file, and commits independently. This avoids threads for CPU-bound parsing and preserves branch/role/source_format scoping.

`--resume` reuses the latest non-success parser run for the same file/parser/schema, then skips normalized artifact parts whose `metadata_json.part_index` is already registered. Existing parts remain linked to the same parser run, so traceability is preserved.

## Batch Runners

`NormalizeFormatRunner`:

- filters only `READY_FOR_PARSING` files;
- limits to one `branch`/`role`/`source_format`;
- selects catalog rows from `PATH_FOLDER_DATASETS_FILTER` unless exact file ids are supplied;
- wraps each file in a nested transaction;
- continues on file-level errors.
- can process files in parallel with `--workers`.

`NormalizeAllRunner`:

- works for one branch only;
- groups by role/source_format;
- uses only active roles: TRAIN, VALIDATION, TEST;
- respects an overall limit;
- delegates each group to `NormalizeFormatRunner`.
- forwards `--workers`, `--batch-size`, `--max-output-part-rows`, `--resume`, and packet parsing options to each group.

## Reports

| Report | Command/source |
| --- | --- |
| Parser coverage matrix | `parser-coverage` |
| Parser run diagnostics | normalization services |
| DuckDB analytics report | `run-duckdb-checks` |
| Leakage report | `run-leakage-checks` |
| Readiness report | `scripts.stage_two.readiness_check` |

Reports are written under `PATH_DATA_STORAGE/reports/en/stage-two/` and `PATH_DATA_STORAGE/reports/ru/stage-two/`.

Parser and normalization reports include branch, role, source format, dataset/file IDs, source path/hash, parser name/version, counters, status, warning samples, error samples, and reader hints. They must not store full raw packet payloads, BSON streams, or full raw log content.

## Current Limitations

- Full production feature/model-ready build CLI is not implemented in this parser workflow.
- Host packet capture registry is active for TRAIN and VALIDATION, not TEST.
- BSON parser registry is active for host TEST.
- Full packet payloads and full raw logs are intentionally not stored.

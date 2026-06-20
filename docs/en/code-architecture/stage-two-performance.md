# Stage Two Performance Architecture

Stage Two normalization uses file-level process parallelism and bounded output parts.

## Execution Model

- `NormalizeFormatRunner` selects files for exactly one `branch/role/source_format`.
- With `--workers > 1`, files are sent to a `ProcessPoolExecutor`.
- Each worker opens its own PostgreSQL session, resolves the catalog row by `file_id`, runs DNS or Host normalization, commits, and returns a compact `NormalizeFileResult`.
- CPU-bound packet parsing is not executed in threads.

## Memory Model

- Services consume parser output through `parse_batches`.
- Packet parsers stream PCAP/PCAPNG/CAP records instead of loading the capture into memory.
- Output rows are written in Parquet parts capped by `max_output_part_rows`.
- Output artifact hashing is disabled by default to avoid rereading large Parquet files. Use `--hash-output-artifacts` only when that integrity check is required.

## Resume Model

`--resume` reuses the latest non-success `parser_run` for the same file/parser/schema. Already registered normalized artifacts with `metadata_json.part_index` are skipped, and missing parts are appended under the same parser run. This preserves raw-to-normalized lineage without a schema migration.

## Metrics

`parser_runs.metadata_json.performance` stores input size, parse/write/catalog timings, throughput, peak memory, and part counts. Normalized artifacts store per-part checkpoint metadata.

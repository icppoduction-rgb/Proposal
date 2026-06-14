# CLI and Command Routing Architecture

## Entry Point: `manage.py`

`manage.py` creates an `argparse.ArgumentParser` and accepts three positional arguments:

| Argument | Purpose |
|---|---|
| `module` | Top-level area: `handlers` or `stage-two`. |
| `service` | Service inside the module, for example `analyze-dataset`, `normalize-dns`. |
| `action` | Optional action. Stage Two uses it as a `limit` or trace artifact ID/path. |

The code calls `parse_known_args()`, so unknown extra arguments do not fail argparse and are effectively ignored. Parsed values are passed to `scripts.router_script.router_commands(args.module, args.service, args.action)`.

## Top-Level Router

`router_commands()` in `scripts/router_script.py` supports two modules:

| module | Router | Purpose |
|---|---|---|
| `handlers` | `scripts.handlers.router_handler.router_commands_handlers` | Stage One file preparation and content analysis. |
| `stage-two` | `scripts.stage_two.cli.router_stage_two` | Stage Two catalog/normalization/quality/traceability. |
| other/empty | prints `manage_commands` | No exception and no non-zero exit code. |

## Handlers Router

`router_commands_handlers(service, action)` routes services as follows:

| service | Router | Purpose |
|---|---|---|
| `analyze-dataset` | `router_analyze(action)` | Initial scan of DNS/host source directories. |
| `filter-dataset` | `router_filter(action)` | Host file filtering using whitelist rules. |
| `sort` | `router_sort(action)` | Copy files into a sorted role/format tree. |
| `save-sort` | `router_save(action)` | Export paths from a sorted tree. |
| `dns-analyze` | `router_dns(action)` | Analyze DNS bucket contents. |
| `host-analyze` | `router_host(action)` | Analyze host bucket contents. |

## Stage Two Router

`router_stage_two(service, action)` supports:

| Command | `action` | Purpose |
|---|---|---|
| `bootstrap-storage` | unused | Create Stage Two storage structure. |
| `catalog-ingest` | unused | Scan configured roots and register raw files in PostgreSQL Catalog. |
| `seed-parser-registry` | unused | Register `schema_versions` and parser registry entries. |
| `normalize-dns` | optional integer limit | Normalize DNS files with status `READY_FOR_PARSING`. |
| `normalize-host` | optional integer limit | Normalize host files with status `READY_FOR_PARSING`. |
| `run-duckdb-checks` | unused | Run DuckDB analytical checks and register a report. |
| `run-leakage-checks` | unused | Run leakage checks and register a report. |
| `trace-artifact` | model-ready ID or path | Print the traceability chain. |

`normalize-*` validates `action`: when provided, it must be a non-negative integer. `ValueError` is caught and printed as a JSON-like dict.

## Example Commands

```powershell
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 100
python manage.py stage-two trace-artifact 1
```

## Routing Constraints

| Constraint | Consequence |
|---|---|
| `manage.py` accepts only `module service action`. | Multiple named CLI options require CLI changes. |
| `parse_known_args()` ignores extra args. | Typos in extra arguments are not treated as failures. |
| Unknown module/service/action prints help. | Shell exit code may remain successful, which matters for CI. |
| Routing uses `if/elif` and dict routes. | New commands must be explicitly registered in router files. |

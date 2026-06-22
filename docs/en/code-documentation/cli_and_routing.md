# CLI and Routing Layer

## Entry Point

Main entry point: `manage.py`.

`manage.py` creates an `argparse.ArgumentParser` with positional arguments:

| Argument | Meaning |
|---|---|
| `module` | top-level namespace: `handlers` or `stage-two` |
| `service` | service/action group inside the module |
| `action` | first action or first positional argument for a service command |
| `extra_args` | remaining arguments for Stage Two commands |

Actual routing:

```text
manage.py
  -> scripts.router_script.router_commands(module, service, action, extra_args)
     -> handlers: scripts.handlers.router_handler.router_commands_handlers(service, action)
     -> stage-two: scripts.stage_two.cli.router_stage_two(service, action, extra_args)
```

Unknown modules print `config.manage_commands`.

## Stage One Routes

File: `scripts/handlers/router_handler.py`.

| Service | Router | Actions |
|---|---|---|
| `analyze-dataset` | `scripts/handlers/analyze_dataset/router_analyze.py` | `dns-dataset-handler`, `host-dataset-handler` |
| `filter-dataset` | `scripts/handlers/filter_dataset/router_filter.py` | `filter-host-dataset-handler` |
| `sort` | `scripts/handlers/sort/router_sort.py` | `sort-dns-dataset-handler`, `sort-host-dataset-handler` |
| `save-sort` | `scripts/handlers/save_sort/router_save.py` | `save-sort-dns-dataset-handler`, `save-sort-host-dataset-handler` |
| `dns-analyze` | `scripts/handlers/dns_analyze/router_dns.py` | DNS content actions by role/format |
| `host-analyze` | `scripts/handlers/host_analyze/router_host.py` | Host content actions by role/format |

### Stage One DNS Order

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <action>
```

DNS content actions include:

```bash
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py handlers dns-analyze analyze-train-pcap-content
python manage.py handlers dns-analyze analyze-train-pcap-csv-content
python manage.py handlers dns-analyze analyze-test-csv-content
python manage.py handlers dns-analyze analyze-test-pcap-content
python manage.py handlers dns-analyze analyze-test-pcap-csv-content
python manage.py handlers dns-analyze analyze-validation-pcap-content
python manage.py handlers dns-analyze analyze-validation-txt-content
```

### Stage One Host Order

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <action>
```

Host content actions include `analyze-csv-content`, `analyze-auth-log-content`, `analyze-json-content`, `analyze-validation-pcapng-content`, `analyze-test-bson-content`, `analyze-test-wls-day-content`, and other actions from `scripts/handlers/host_analyze/router_host.py`.

## Stage Two Routes

File: `scripts/stage_two/cli.py`.

| Command | Arguments | Purpose |
|---|---|---|
| `bootstrap-storage` | none | create the storage tree under `PATH_DATA_STORAGE` |
| `catalog-ingest` | none | scan `PATH_FOLDER_DATASETS_FILTER` and register files |
| `seed-parser-registry` | none | register normalized schema and parser registry seed |
| `parser-coverage` | `[branch]` | compare catalog formats with active parsers |
| `mark-ready` | flags or fallback | move selected files to `READY_FOR_PARSING` |
| `normalize-format` | flags or fallback | normalize one `branch/role/source_format` group |
| `normalize-all` | flags or fallback | normalize all ready groups inside a branch |
| `split-large-files` | flags | split large line-based files |
| `normalize-dns` | `[limit]` | legacy branch-level normalization for DNS ready files |
| `normalize-host` | `[limit]` | legacy branch-level normalization for Host ready files |
| `run-duckdb-checks` | none | create DuckDB views and analytics report |
| `run-leakage-checks` | none | check model-ready leakage and preprocessing fit role |
| `trace-artifact` | `<model_ready_id_or_artifact_path>` | print traceability chain |

### Baseline Stage Two Order

```bash
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

The legacy order from the task is also supported:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Important CLI Constraints

- Stage One content analysis requires the corresponding role/format bucket in `sort-path-*-file.json`.
- `catalog-ingest` reads sorted/filtered files from `PATH_FOLDER_DATASETS_FILTER`.
- `mark-ready` should be run with `--dry-run` before `--apply`.
- `normalize-format` is safer than legacy `normalize-dns`/`normalize-host` because it keeps role and format selection explicit.
- `normalize-all` groups by `role/source_format` and preserves role order from `ACTIVE_DATASET_ROLE_VALUES`: `TRAIN`, `VALIDATION`, `TEST`.
- `split-large-files` is intended for line-based formats. Do not use it for binary `cap`, `pcap`, `pcapng`, or `bson`.
- TEST must never be used for training, preprocessing fit, threshold tuning, or feature selection.

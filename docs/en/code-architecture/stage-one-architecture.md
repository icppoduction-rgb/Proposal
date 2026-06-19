# Stage One Architecture

Stage One is the dataset discovery, analysis, sorting, and report generation layer. It operates primarily on the filesystem and JSON summaries.

## CLI Entry Points

Stage One commands are routed through:

```text
manage.py -> scripts/router_script.py -> scripts/handlers/router_handler.py
```

Common command groups:

```powershell
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers host-analyze analyze-auth-log-content
python manage.py handlers dns-analyze analyze-train-csv-content
```

## Handler Areas

| Directory | Responsibility |
| --- | --- |
| `scripts/handlers/analyze_dataset/` | Walk DNS/Host dataset roots and capture initial structure. |
| `scripts/handlers/sort/` | Sort dataset files by role and format. |
| `scripts/handlers/save_sort/` | Save sorted file path maps. |
| `scripts/handlers/filter_dataset/` | Filter Host datasets. |
| `scripts/handlers/dns_analyze/` | DNS role/format content analysis reports. |
| `scripts/handlers/host_analyze/` | Host role/format content analysis reports. |
| `scripts/handlers/json_handler/` | JSON helper utilities. |

## Stage One Outputs

Important config paths:

| Config variable | Purpose |
| --- | --- |
| `DNS_FILE`, `HOST_FILE` | Initial file summaries. |
| `DNS_PATH_FILE`, `HOST_PATH_FILE` | Path summaries. |
| `SORT_DNS_FORMAT_SUMMARY`, `SORT_HOST_FORMAT_SUMMARY` | Format count summaries. |
| `SORT_PATH_DNS_FILE`, `SORT_PATH_HOST_FILE` | Sorted path JSON used as diagnostics by Stage Two coverage. |
| `ANALYSIS_*_SUMMARY` | Role/format analysis summaries under temp data. |

Stage One JSON outputs are diagnostics and analysis artifacts. Stage Two production ingestion uses the filtered tree configured by `PATH_FOLDER_DATASETS_FILTER` and PostgreSQL catalog rows, not Stage One JSON as the primary source of truth.

## Relationship To Stage Two

Stage One helps answer:

- What files exist?
- Which formats are present?
- Which paths belong to each role/format bucket?
- What content structures are likely?

Stage Two owns:

- immutable catalog rows;
- parser registry and parser resolution;
- normalized Parquet output;
- parser run and artifact traceability;
- quality/leakage/readiness reports.

## Extension Rules

- Keep Stage One handlers filesystem/JSON focused.
- Do not write normalized events from Stage One.
- Do not store raw dataset payloads in PostgreSQL from Stage One.
- Keep path constants in `config.py`.
- If a new format is discovered in Stage One, update Stage Two scanner, registry, parser, and docs separately.

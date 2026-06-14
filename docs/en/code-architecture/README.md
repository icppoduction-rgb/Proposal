# Code Architecture

This section documents the actual implementation of `manage.py`, `scripts/*`, the PostgreSQL Catalog, and Stage Two based on the current project code.

## Documents

| Document | Purpose |
|---|---|
| [general-architecture.md](general-architecture.md) | Overall architecture, major layers, and the end-to-end pipeline. |
| [router-architecture.md](router-architecture.md) | `manage.py` entry point, command routing, and supported CLI commands. |
| [hadlers_analyze_dataset_architecture.md](hadlers_analyze_dataset_architecture.md) | Initial DNS/host dataset discovery and discovery JSON contracts. |
| [hadlers_filter_dataset_architecture.md](hadlers_filter_dataset_architecture.md) | Host filtering before sorting. |
| [hadlers_sort_architecture.md](hadlers_sort_architecture.md) | File sorting by role and format. |
| [hadlers_save_sort_architecture.md](hadlers_save_sort_architecture.md) | Path export from sorted trees. |
| [hadlers_dns_analyze_architecture.md](hadlers_dns_analyze_architecture.md) | DNS content-analysis handlers. |
| [hadlers_host_analyze_architecture.md](hadlers_host_analyze_architecture.md) | Host content-analysis handlers. |
| [hadlers_json_handler_architecture.md](hadlers_json_handler_architecture.md) | Shared JSON helper. |
| [db-architecture.md](db-architecture.md) | SQLAlchemy models, repositories, and PostgreSQL Catalog table purposes. |
| [stage-two-architecture.md](stage-two-architecture.md) | Stage Two: storage bootstrap, catalog ingestion, parser registry, normalization, quality, traceability. |
| [pipeline-artifacts-and-contracts.md](pipeline-artifacts-and-contracts.md) | Component call order, input/output artifacts, and JSON/Parquet/DB contracts. |
| [extension-points-and-risks.md](extension-points-and-risks.md) | Extension points, constraints, risks, and technical debt. |

Note: `hadlers_*` file names are preserved from the existing documentation structure. The typo is in the documentation file names only, not in the Python package name.

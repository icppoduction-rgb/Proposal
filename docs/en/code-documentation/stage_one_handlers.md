# Stage One Handlers

Stage One is a filesystem-oriented layer. It inventories raw datasets, filters Host datasets, creates sorted role/format trees, exports path maps, and analyzes bucket content. It does not write PostgreSQL records and does not create normalized Parquet artifacts.

## `json_handler` / `JsonDataManager`

Location: `scripts/handlers/json_handler`.

Purpose:

- read/write Stage One JSON inventories;
- keep path maps and file maps in deterministic JSON files;
- provide common JSON helpers to handlers.

Operational constraints:

- writes are not protected by file locking;
- concurrent writes to the same JSON path are unsafe;
- JSON contracts are filesystem metadata contracts, not database contracts.

## `analyze_dataset`

Locations:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`
- `scripts/handlers/analyze_dataset/host_dataset_handler.py`
- `scripts/handlers/analyze_dataset/router_analyze.py`

Commands:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
```

Purpose: scan raw dataset directories and create JSON inventories. This step scans paths and file metadata; it does not parse file contents.

Outputs:

- `PATH_TEMP_DATA/dns-path-file.json`
- `PATH_TEMP_DATA/dns-file.json`
- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Contract shape:

```json
{
  "TRAIN": {
    "Dataset Name": {
      "csv": ["/absolute/path/file.csv"]
    }
  },
  "VALIDATION": {},
  "TEST": {}
}
```

Roles are inferred from path segments such as `TRAIN`, `VALIDATION`, and `TEST`. DNS has an `EXPERIMENTS` fallback when role tokens are not found. Host fallback role in current code is `TEST`, which is a risk for new paths without explicit role directories.

## `filter_dataset`

Location: `scripts/handlers/filter_dataset`.

Command:

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

Purpose: filter Host datasets before sorting. This step is implemented for Host datasets and is required before Host sort because `HostDatasetSortHandler` reads `filter_dataset-host-*.json`.

Inputs:

- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Outputs:

- `PATH_TEMP_DATA/filter_dataset-host-path-file.json`
- `PATH_TEMP_DATA/filter_dataset-host-file.json`
- `PATH_FILTER_LOG`

The whitelist is hardcoded in Python. Current allowed groups:

| Role | Allowed datasets |
|---|---|
| `TRAIN` | `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset` |
| `VALIDATION` | `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets` |
| `TEST` | `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset` |

Risks:

- dataset name extraction depends on the `host/<role>/<dataset>` path shape;
- new dataset names are excluded until the code is changed;
- whitelist rules are not JSON/YAML-configured;
- file contents are not validated.

## `sort`

Locations:

- `scripts/handlers/sort/dns_dataset_sort_handler.py`
- `scripts/handlers/sort/host_dataset_sort_handler.py`

Commands:

```bash
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
```

Purpose: copy or hardlink files into a sorted tree by role and format.

Canonical tree:

```text
PATH_*_DATASETS_FILTER/
  dns/
    TRAIN/<format>/
    VALIDATION/<format>/
    TEST/<format>/
  host/
    TRAIN/<format>/
    VALIDATION/<format>/
    TEST/<format>/
```

Inputs:

- DNS sort reads `dns-path-file.json` / `dns-file.json`.
- Host sort reads `filter_dataset-host-path-file.json` / `filter_dataset-host-file.json`.

Outputs:

- sorted filesystem tree;
- sort summary JSON under `PATH_TEMP_DATA`.

Important: sorting does not register files in PostgreSQL. Catalog registration happens later in Stage Two `catalog-ingest`.

## `save_sort`

Locations:

- `scripts/handlers/save_sort/save_sort_dns_dataset_handler.py`
- `scripts/handlers/save_sort/save_sort_host_dataset_handler.py`

Commands:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
```

Purpose: traverse the sorted tree and create role/format path maps for content analyzers.

Outputs:

- `PATH_TEMP_DATA/sort-path-dns-file.json`
- `PATH_TEMP_DATA/sort-path-host-file.json`

These JSON files are required by `dns_analyze` and `host_analyze`.

## `dns_analyze`

Location: `scripts/handlers/dns_analyze`.

Command:

```bash
python manage.py handlers dns-analyze <action>
```

Supported buckets include DNS `TRAIN/csv`, `TRAIN/pcap`, `TRAIN/pcap.csv`, `TEST/csv`, `TEST/pcap`, `TEST/pcap.csv`, `VALIDATION/pcap`, and `VALIDATION/txt`.

Outputs:

- analysis summary JSON in `PATH_TEMP_DATA`;
- RU/EN docs in `docs/{ru,en}/analysis-dataset/dns/<role>`;
- RU/EN reports in `PATH_REPORT/{ru,en}/stage-one/analysis-dataset/dns/<role>`.

## `host_analyze`

Location: `scripts/handlers/host_analyze`.

Command:

```bash
python manage.py handlers host-analyze <action>
```

Actions cover train/validation/test buckets: `csv`, `json`, `json-1`, `log`, rotated logs, `cap`, `pcap`, `pcapng`, `bson`, `netflow_day`, `wls_day`, `txt`, `sc`, `ghc`, `xml`, and Metricbeat-like logs.

Outputs are analogous to DNS and are grouped under `host/<role>`.

## Analysis Statuses

Stage One analysis docs use these planning statuses:

| Status | Meaning |
|---|---|
| `READY_FOR_FEATURE_EXTRACTION` | format can be connected to feature extraction after standard normalization |
| `NEEDS_CUSTOM_PARSER` | specialized parser or schema-aware handling is required |
| `PARTIALLY_SUPPORTED` | part of the structure is readable, but mixed schemas, partial labels, or instability remain |
| `BROKEN_OR_EMPTY` | bucket is empty or unsuitable for further processing |

These are not PostgreSQL enums. They are used for parser strategy planning and prioritization.

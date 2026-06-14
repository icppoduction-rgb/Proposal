# Handler: `filter_dataset`

## Purpose

`filter_dataset` is implemented only for host datasets. It reads the JSON produced by `analyze_dataset`, applies whitelist rules for known host dataset groups, and creates filtered JSON for sorting.

## CLI

```powershell
python manage.py handlers filter-dataset filter-host-dataset-handler
```

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/filter_dataset/router_filter.py` | Creates `HostDatasetFilterHandler(PATH_TEMP_DATA, PATH_FILTER_LOG)` and calls `filter_and_save()`. |
| `scripts/handlers/filter_dataset/filter_host_dataset_handler.py` | Implements whitelist filtering and result writing. |

## Inputs

| Artifact | Created by | Purpose |
|---|---|---|
| `PATH_TEMP_DATA/host-path-file.json` | `HostDatasetHandler` | Host file paths by role. |
| `PATH_TEMP_DATA/host-file.json` | `HostDatasetHandler` | Host file names by role. |

## Outputs

| Artifact | Purpose |
|---|---|
| `PATH_TEMP_DATA/filter_dataset-host-path-file.json` | Filtered host file paths by role. |
| `PATH_TEMP_DATA/filter_dataset-host-file.json` | Filtered host file names by role. |
| filter log | Log of keep/drop reasons, path configured by `PATH_FILTER_LOG`. |

## Filtering Rules

The code contains allowlist suffix sets for known groups, including LID-DS, OTRF, and Dynamic Malware Analysis. Files that do not pass the rules or are missing from `host-file.json` are excluded from downstream sorting.

## Pipeline Position

```text
host analyze_dataset -> filter_dataset -> sort-host-dataset-handler
```

`HostDatasetSortHandler` expects `filter_dataset-host-path-file.json` and `filter_dataset-host-file.json`. Skipping this step leaves host sort without its inputs.

## Constraints and Risk

- In `config.py`, `PATH_FILTER_LOG` is defined with a trailing comma and can therefore be a tuple. The router passes it directly to the handler.
- DNS filtering is not implemented.
- Filtering rules are hard-coded; there is no external allowlist configuration file.

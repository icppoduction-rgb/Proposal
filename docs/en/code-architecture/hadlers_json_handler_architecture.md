# Handlers Architecture: json_handler

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Place in the Overall Flow](#3-place-in-the-overall-flow)
- [4. JsonDataManager](#4-jsondatamanager)
- [5. Call Chains](#5-call-chains)
- [6. Data Contract](#6-data-contract)
- [7. Errors and Limitations](#7-errors-and-limitations)

## 1. Purpose

`scripts/handlers/json_handler` provides the shared JSON file layer. Almost every service handler uses `JsonDataManager` to read and write intermediate artifacts in `PATH_TEMP_DATA`.

The package is not launched directly through `manage.py`. It is an infrastructure dependency for other handlers.

## 2. Package Files

| File | Purpose |
|---|---|
| `json_data.py` | Main `JsonDataManager` implementation. |
| `json-data.py` | Compatibility wrapper that re-exports `JsonDataManager`. |
| `__init__.py` | Package marker. |

## 3. Place in the Overall Flow

Typical call:

```text
service handler
-> JsonDataManager(path)
-> read(default={}) | write(data) | update(data)
-> JSON file on disk
```

Consumers include:

- `DNSDatasetHandler` writes `dns-path-file.json`;
- `HostDatasetFilterHandler` reads `host-path-file.json`;
- `DNSDatasetSortHandler` writes `sort-dns-format-summary.json`;
- content-analysis handlers write `analysis-*-summary.json`.

## 4. JsonDataManager

File:

- `scripts/handlers/json_handler/json_data.py`

### Methods

| Method | Purpose |
|---|---|
| `__init__(file_path)` | Stores the JSON file path as `Path`. |
| `ensure_directory()` | Creates the parent directory for the file. |
| `exists()` | Checks whether the JSON file exists. |
| `create(initial_data=None, overwrite=False, indent=2)` | Creates a JSON file without overwriting an existing one unless `overwrite=True`. |
| `read(default=None)` | Reads JSON and returns a dict. If the file is missing, returns `default` or `{}`. |
| `write(data, indent=2)` | Fully overwrites the JSON file with a dict. |
| `update(new_data, indent=2)` | Reads current JSON, updates top-level keys, and writes it back. |

## 5. Call Chains

### JSON Write

```text
handler method
-> JsonDataManager(output_path)
-> write(payload)
-> ensure_directory()
-> json.dump(payload, ensure_ascii=False, indent=2)
```

### JSON Read

```text
handler method
-> JsonDataManager(input_path)
-> read(default={})
-> file_path.open("r", encoding="utf-8")
-> json.load(...)
-> isinstance(data, dict) validation
```

### JSON Update

```text
handler method
-> JsonDataManager(path).update(new_data)
-> read(default={})
-> current_data.update(new_data)
-> write(current_data)
```

## 6. Data Contract

`JsonDataManager` expects the JSON top level to be a Python `dict`.

Valid example:

```json
{
  "TRAIN": [],
  "TEST": []
}
```

Invalid example:

```json
[
  "file1",
  "file2"
]
```

If `read()` receives a JSON array or any other non-object top-level value, it raises `ValueError`.

## 7. Errors and Limitations

- `write()` accepts only `dict`; other types raise `TypeError`.
- `read()` validates only the top-level structure, not nested fields.
- `update()` performs a top-level update, not a deep merge.
- Atomic writes through temporary files are not used. If writing fails midway, JSON may be corrupted.
- `json-data.py` exists only for filename compatibility; the main implementation is in `json_data.py`.

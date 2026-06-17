# Router Architecture

The CLI entrypoint is `manage.py`.

## Argument Shape

```text
python manage.py <module> <service> [action] [extra args...]
```

`manage.py` defines:

```python
module
service
action
extra_args = argparse.REMAINDER
```

It calls:

```text
scripts.router_script.router_commands(module, service, action, extra_args)
```

## Top-Level Router

`scripts/router_script.py` supports:

| Module | Destination |
| --- | --- |
| `handlers` | `scripts.handlers.router_handler.router_commands_handlers(service, action)` |
| `stage-two` | `scripts.stage_two.cli.router_stage_two(service, action, extra_args=extra_args)` |

Unknown modules print `config.manage_commands`.

## Stage One Routing

Stage One uses `service` and `action` only. Extra args are not forwarded to handler routers.

Examples:

```powershell
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers host-analyze analyze-auth-log-content
```

## Stage Two Routing

Stage Two supports extra args and named flags.

Implemented services:

| Service | Example |
| --- | --- |
| `bootstrap-storage` | `python manage.py stage-two bootstrap-storage` |
| `catalog-ingest` | `python manage.py stage-two catalog-ingest` |
| `seed-parser-registry` | `python manage.py stage-two seed-parser-registry` |
| `parser-coverage` | `python manage.py stage-two parser-coverage host` |
| `mark-ready` | `python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run` |
| `normalize-format` | `python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100` |
| `normalize-all` | `python manage.py stage-two normalize-all --branch host --limit 1000` |
| `normalize-dns` | `python manage.py stage-two normalize-dns 10` |
| `normalize-host` | `python manage.py stage-two normalize-host 10` |
| `run-duckdb-checks` | `python manage.py stage-two run-duckdb-checks` |
| `run-leakage-checks` | `python manage.py stage-two run-leakage-checks` |
| `trace-artifact` | `python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>` |

Fallback syntaxes:

```powershell
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
python manage.py stage-two normalize-all host:1000
```

Unknown Stage Two services return a structured error and print command help.

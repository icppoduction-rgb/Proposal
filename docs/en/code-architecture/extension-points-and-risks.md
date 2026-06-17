# Extension Points And Risks

## Safe Extension Points

| Extension | Files to change | Required validation |
| --- | --- | --- |
| New parser for existing format | Parser module, tests/smokes if behavior changes | `parser_smoke`, `parser_input_smoke`, `parser-coverage` |
| New source format | `scanner.py`, parser class, parser registry seed, docs, tests | scanner tests, registry seed tests, parser coverage |
| New label mapping | DB/config label rules | label resolver tests, leakage checks |
| New normalized field | schema JSON, parser helpers, Parquet/DuckDB checks, docs | schema tests, DuckDB checks, readiness |
| New artifact writer | `scripts/stage_two/parquet` or feature/model-ready modules | artifact registration tests, readiness |
| New CLI command | `scripts/stage_two/cli.py`, docs, operational smoke | CLI smoke, backward compatibility checks |

## Parser Extension Checklist

1. Use `UniversalInputReader`.
2. Emit canonical normalized fields.
3. Use `LabelResolver`.
4. Preserve unknown fields in JSON fields.
5. Add registry entry only when the class imports.
6. Add direct smoke and input smoke coverage.
7. Run catalog/CLI rollback smokes for DB behavior.

## Scanner Extension Rules

`scripts/stage_two/ingestion/scanner.py` must keep exact bucket/source names. For sorted trees, the role/format bucket name has priority over extension heuristics.

Examples that must not collapse to generic extensions:

```text
pcap.csv
process.summary.log
socket.summary.log
netflow_day
netflow_ids
wls_day
journal~
syslog-1
```

## CLI Extension Rules

New Stage Two commands belong in `scripts/stage_two/cli.py`.

Requirements:

- preserve the `manage.py module/service/action` interface;
- parse command-specific flags through `extra_args`;
- report unknown commands explicitly;
- keep `normalize-dns` and `normalize-host` aliases working;
- use dry-run by default for status-changing or destructive operations.

## Known Technical Debt

| Area | Current state | Risk |
| --- | --- | --- |
| Stage One handler docs | Some handler-specific filenames use `hadlers_*`. | Naming inconsistency, kept for compatibility. |
| Feature/model-ready production build | Contracts and tables exist, full CLI is not implemented in parser workflow. | Downstream users must not assume full training matrix generation. |
| Stage One JSON vs Stage Two catalog | Stage One JSON is diagnostic; Stage Two catalog is production truth. | Confusing these can create stale normalization inputs. |
| `manage_commands` in `config.py` | Help text is static and older than full Stage Two CLI. | Unknown-command help may omit newer commands unless updated. |
| Host packet capture TEST role | Registry active for TRAIN/VALIDATION only. | TEST packet captures need explicit label/leakage policy decision before activation. |

## Operational Risks

| Risk | Mitigation |
| --- | --- |
| Marking too many files ready | Run `parser-coverage`; use `mark-ready --dry-run` first. |
| Full batch failures | Start with `normalize-format --limit 10`. |
| Raw file drift | Use catalog hashes and readiness raw file checks. |
| Data leakage | Run `run-leakage-checks`; keep labels/source metadata out of X. |
| Parser class mismatch | Run `seed-parser-registry` and `parser-coverage`. |
| Storage path misconfiguration | Run `bootstrap-storage` and readiness check. |

## Non-Goals For Current Parser Workflow

- Training ML/DL models.
- Hyperparameter tuning.
- SHAP or final evaluation reports.
- Storing all normalized rows in PostgreSQL.
- Modifying raw datasets.
- Full production feature/model-ready build for the entire corpus.

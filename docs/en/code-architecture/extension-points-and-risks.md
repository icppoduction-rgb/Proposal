# Extension Points, Constraints, and Technical Debt

## Stage One Extension Points

| Extension | Where to change | Requirements |
|---|---|---|
| New top-level handler service | `scripts/handlers/router_handler.py` | Add route and update help/docs. |
| New DNS analysis action | `scripts/handlers/dns_analyze/router_dns.py`, new `analyze_dns_*_dataset_handler.py` | Handler must read `sort-path-dns-file.json` and return a result compatible with `run_action.py`. |
| New host analysis action | `scripts/handlers/host_analyze/router_host.py`, new `analyze_host_*_dataset_handler.py` | Handler must read `sort-path-host-file.json` and save summary/report output. |
| New host filtering logic | `filter_host_dataset_handler.py` | Preserve `filter_dataset-host-path-file.json` and `filter_dataset-host-file.json` contracts. |
| New sorter format bucket | `sort_dns_dataset_handler.py` or `sort_host_dataset_handler.py` | Bucket name must match save/analyze handler expectations and Stage Two scanner behavior. |

## Stage Two Parser Pipeline Extension Points

| Extension | Where to change | Minimal contract |
|---|---|---|
| New parser class | `scripts/stage_two/parsers/*` | Follow existing parser contracts and return `ParseResult` with normalized events/counters. |
| New parser registry entry | seed data used by `parser_registry/seed.py` | Provide parser name/version/module/class, branch, source_format, role, schema name/version, `is_active`. |
| New normalized schema | `schemas/normalized/*.json`, `normalization/schema_contracts.py` when needed | Register it in `schema_versions`; parser registry must reference it. |
| New label rule | `label_mapping_rules` or config `label_mapping_rules.json` | Do not mix roles; rule must be reproducible. |
| New quality checks | `scripts/stage_two/quality/*` or `duckdb/service.py` | Write a report to `data_quality_reports`. |
| Feature/model-ready stage | `features/*`, `model_ready/*` | Register catalog artifacts and preserve traceability to normalized/raw. |

## Rules for Adding a New Stage Two Parser

1. Study the Stage One analysis summary for the required role/format bucket.
2. Ensure `catalog-ingest` correctly infers `branch`, `role`, and `source_format` for the files.
3. Implement the parser class and cover edge cases: empty file, corrupt row, unknown encoding/format, missing label/timestamp information.
4. Add or update the schema contract and register it in `schema_versions` through seed.
5. Add a parser registry entry. Do not set `is_active=true` until the parser class is implemented and verified.
6. Verify resolver behavior: it must select the parser only for the supported branch/source_format/role.
7. Run normalization with a small `limit` and confirm `parser_runs`, `normalized_artifacts`, and Parquet are created.
8. Run readiness/quality checks when the environment is available.

## Differences Between Old Docs and Current Code

| Difference | Actual implementation |
|---|---|
| Old docs described only the `handlers` module. | `router_script.py` also supports `stage-two`. |
| Old docs did not describe `scripts/db`. | The DB layer is mandatory for Stage Two. |
| Old docs did not describe Stage Two CLI. | `scripts/stage_two/cli.py` contains production-facing commands. |
| Old docs did not mark `schema_versions` as mandatory. | Seed must register normalized schema metadata. |
| Old docs did not separate planned parsers from active parsers. | Planned/unsupported parser entries must be inactive. |
| Some old RU docs had broken encoding. | Documentation has been rewritten as UTF-8. |

## Current Constraints and Risks

| Risk | Impact | Practical action |
|---|---|---|
| `manage.py` uses `parse_known_args()`. | Extra CLI arguments are ignored. | Add explicit parse/validation layer for strict CI. |
| Unknown commands print help without explicit failure. | Automation may treat a wrong command as successful. | Return non-zero exit code for unknown commands. |
| `PATH_FILTER_LOG` in `config.py` may be a tuple due to a trailing comma. | Potential path handling bug in host filter. | Fix config and add a regression test. |
| Stage Two has no public mark-ready command. | `normalize-*` may process 0 files after ingestion. | Add an explicit review/mark-ready workflow. |
| Feature/model-ready pipeline is incomplete as CLI. | Traceability to model-ready is available only through APIs/dry-run. | Implement dedicated Stage Two tasks for feature/model-ready assembly. |
| Host netflow/wls parser entries are inactive. | These formats are not normalized by Stage Two. | Implement parser or keep documented inactive. |
| Stage One temporary JSON has no shared schema validation. | Different handlers may diverge in summary fields. | Add JSON Schema for temporary artifacts if they become stable contracts. |
| `readiness_check` may hash catalog files. | On the full corpus, the check may be expensive. | Add sampling/incremental mode if needed. |
| Stage One and Stage Two ingestion are independent. | Changes in the sorted tree are not automatically reflected in the catalog. | Run `catalog-ingest` after changing files. |

## What Not To Do

- Do not declare a parser active if its class is missing or does not support the format.
- Do not create normalized/features/model-ready files without catalog registration.
- Do not use TEST for fitted preprocessing or parameter selection.
- Do not treat Stage One summary as the source of truth for the Stage Two catalog; Stage Two builds its catalog through its own scanner.

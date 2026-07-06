# Risks, Limitations, and Technical Debt

## Known Limitations

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Host role fallback to TEST | `HostDatasetHandler._detect_role` | files without role token land in TEST | inspect `host-path-file.json` | require explicit role directories, add strict mode |
| Hardcoded Host filter whitelist | `HostDatasetFilterHandler` | new datasets/formats are excluded | filter log reasons | move rules to config with tests |
| Stage One statuses can lag Stage Two parsers | analysis docs vs parser registry | format may show `NEEDS_CUSTOM_PARSER` though parser exists | `parser-coverage` | update analysis docs after parser work |
| Stage Four is missing | model training/evaluation layer | models cannot be trained/evaluated through a project command | review CLI routes and `docs/stage-three` final report | add a separate Stage Four CLI after `READY_FOR_STAGE_FOUR` |
| Production Host/Network/Hybrid expansion is incomplete | Stage Three MVP path starts with DNS | DNS MVP can be ready before the full hybrid scope | `stage-three final-report`, feature group coverage | expand Stage Three by branch/feature_group with `--resume` and checks |

## Parser Layer Gaps

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Mixed CSV schemas | DNS/Host CSV | row parse failures, partial artifacts | parser reports, `PARTIAL_SUCCESS` | schema-specific parsing, per-file schema hints |
| Mixed JSON schemas | Host TRAIN/TEST JSON | failed rows or weak normalization | parser error samples | schema-aware dispatch and JSON flatten tests |
| WLS/NetFlow ambiguity | registry maps `wls_day` to `HostNetflowParser` | semantic mismatch if WLS is JSON-lines | parser coverage + sample parse | add WLS parser or update registry |
| PCAP/PCAPNG performance | packet parser | slow processing, memory/disk pressure | runtime metrics, parser reports | packet sampling, `dns-only`, chunked streaming |
| BSON complexity | sandbox BSON | descriptor/event mismatch | parser warnings | descriptor state tests, bounded raw previews |

## Leakage Risks

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Labels in X | feature/model-ready build | model directly learns target | `run-leakage-checks` | `validate_x_columns`, strict excluded list |
| Source identity in X | source paths/event ids | model memorizes dataset/file | forbidden column check | keep traceability only in catalog/audit |
| TEST used for fit/tuning | preprocessing/model code | invalid evaluation | preprocessing fit check, review | enforce TRAIN-only fit and CI checks |
| Filename label inference for TEST | label resolver changes | evaluation contamination | unit tests | keep `label_hints_allowed(TEST)=False` |

## Label Risks

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Missing label treated as benign | downstream feature/model code | false negatives, contaminated labels | label distribution checks | keep `unlabeled` and filter supervised samples |
| Weak labels used as ground truth | IDS/scenario/filename | noisy training labels | inspect `label_status` | train/evaluate by label confidence/source |
| Conflicting labels ignored | resolver candidates | wrong target | counts by `conflicting_label` | block or manually resolve conflicts |

## Timestamp Risks

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Missing timestamp replaced by current time | parser implementation | invalid temporal features | review `timestamp_type`, tests | use `timestamp=null`, `timestamp_type=missing/event_order` |
| Relative time treated as absolute | syscall/BSON/logs | wrong ordering/windows | parser tests | keep `timestamp_type=relative` and `event_index` |
| Mixed timezone parsing | logs/json/csv | shifted windows | sample validation | normalize to UTC only known absolute timestamps |

## Large File Risks

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Loading whole file | parsers/analyzers | memory exhaustion | profiling, OOM | streaming readers, `parse_batches`, split-large-files |
| Too many Parquet parts | low max rows | filesystem overhead | artifact counts | tune `--max-output-part-rows` |
| Parallel workers on huge files | `normalize-format --workers` | RAM/disk pressure | system monitoring | use workers=1 until chunking is implemented |

## Schema Drift

| Risk | Where | Consequences | Detection | Mitigation |
|---|---|---|---|---|
| Source schema changes | datasets | parser failures | `PARTIAL_SUCCESS`, schema mismatch | store schema hints, update parser tests |
| Normalized schema evolves | schema JSON + parsers | downstream mismatch | DuckDB required column checks | version schemas and maintain migrations |
| Feature schema mismatch | feature artifacts | invalid model-ready data | quality checks | validate feature contract before registration |

## Technical Debt Follow-up

1. Add config-driven Host filter rules.
2. Add a Stage Four CLI for training/evaluation only on `READY_FOR_STAGE_FOUR` artifacts.
3. Expand the Stage Three production path to Host/Network/Hybrid feature groups.
4. Add a dedicated WLS parser if current netflow mapping is semantically insufficient.
5. Clarify feature/model-ready schema-version lifecycle in production migrations.
6. Add a CI command that runs parser registry validation, Stage Three tests, leakage contract tests, and docs link checks.

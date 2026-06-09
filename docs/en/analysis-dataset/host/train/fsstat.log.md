# Format Analysis: fsstat.log

## 1. Purpose
`fsstat.log` in `TRAIN` contains host fsstat aggregate statistics telemetry (Metricbeat `system.fsstat`) for disk utilization monitoring, capacity pressure analysis, and storage degradation detection.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | fsstat.log |
| Extension variants | `.log` (grouped as `fsstat.log`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-13-system.fsstat.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-13-system.fsstat__2a7b781935.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-14-system.fsstat.log
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | none (JSON-lines) |
| Encoding | utf-8 (12) |
| Nested structure | yes (nested JSON objects) |
| Sampled files | 12 |
| Sampled lines | 4451 |
| JSON lines | 4451 |
| Metric rows | 4451 |

## 5. Semantic structure
Primary flow: `system.fsstat` records with fields:
- `count`, `total_files`, `total_size.used/free/total`;
- `metricset.period`, `event.duration`;
- `agent.version`, `host.name`, `event.dataset`.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:34.543Z` |
| host.name | string | host identifier | `internal-share` |
| event.dataset | string | telemetry dataset type | `system.fsstat` |
| system.fsstat.count | float | number of mounted filesystems | `3` |
| system.fsstat.total_files | float | total file/inode count | `6451200` |
| system.fsstat.total_size.used | float | used bytes across all filesystems | `3170240512` |
| system.fsstat.total_size.free | float | free bytes across all filesystems | `48787542016` |
| system.fsstat.total_size.total | float | total bytes across all filesystems | `51957782528` |
| metricset.period | float | metric collection period (ms) | `60000` |
| event.duration | float | event processing duration (ns) | `182471` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | no |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | @timestamp |
| Timestamp format | ISO-8601 |
| Timezone | UTC (suffix Z), event ingestion timezone |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- rolling statistics on `total_size.used`, `total_size.free`, and `total_size.total`;
- utilization ratio `total_size.used / total_size.total`;
- dynamics of `count` and `total_files`;
- trend-based features from `event.duration` and `metricset.period`.

### Network / hybrid features
- correlation of fsstat pressure with network/auth/process activity on the same host.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | missing usage rows: 0 |
| Unstable structure | no | unknown/non-json rows present |
| Mixed schemas | no | unknown json rows: 0 |
| Duplicate rows | no | duplicates in sample: 0 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Needs dedicated parser | no |
| Processing priority | medium |

## 12. Conclusion
`TRAIN/fsstat.log` has a stable JSON-lines structure and is suitable for host storage feature extraction.
`total_size.used` stats (sample): min=2805981184.0, max=4335140864.0, avg=3768959051.920018.

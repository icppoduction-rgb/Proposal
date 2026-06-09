# Format Analysis: filesystem.log

## 1. Purpose
`filesystem.log` in `TRAIN` contains host filesystem telemetry (Metricbeat `system.filesystem`) for disk utilization monitoring, capacity pressure analysis, and storage degradation detection.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | filesystem.log |
| Extension variants | `.log` (grouped as `filesystem.log`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-13-system.filesystem.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-13-system.filesystem__ce51cdb62b.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-14-system.filesystem.log
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
| Sampled lines | 9833 |
| JSON lines | 9833 |
| Metric rows | 9833 |

## 5. Semantic structure
Primary flow: `system.filesystem` records with fields:
- `mount_point`, `type`, `device_name`;
- `used.pct`, `used.bytes`;
- `total`, `free`, `available`, `files`, `free_files`.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:34.543Z` |
| host.name | string | host identifier | `internal-share` |
| event.dataset | string | telemetry dataset type | `system.filesystem` |
| system.filesystem.mount_point | string | mount point | `/` |
| system.filesystem.type | string | filesystem type | `ext4` |
| system.filesystem.device_name | string | underlying device | `/dev/vda1` |
| system.filesystem.used.pct | float | utilization ratio | `0.061` |
| system.filesystem.used.bytes | float | used bytes | `3163922432` |
| system.filesystem.total | float | total capacity | `51848359936` |
| system.filesystem.available | float | available bytes | `48667660288` |

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
- rolling statistics on `used.pct` and `used.bytes`;
- pressure features from `available/total`;
- per-device baseline deviation;
- inode pressure signals using `free_files`.

### Network / hybrid features
- correlation of filesystem pressure with network/auth/process activity on the same host.

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
`TRAIN/filesystem.log` has a stable JSON-lines structure and is suitable for host storage feature extraction.
`used.pct` stats (sample): min=0.0, max=0.0835, avg=0.04468810129156921.

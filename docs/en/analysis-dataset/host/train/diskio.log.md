# Format Analysis: diskio.log

## 1. Purpose
`diskio.log` in `TRAIN` contains host disk I/O telemetry (Metricbeat `system.diskio`) for load analysis, I/O anomaly detection, and disk subsystem health monitoring.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | diskio.log |
| Extension variants | `.log` (grouped as `diskio.log`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio__6ab638e312.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-14-system.diskio.log
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
| Sampled lines | 12000 |
| JSON lines | 12000 |
| `system.diskio` rows | 10501 |
| `host.disk.*` rows | 1499 |

## 5. Semantic structure
Primary flow: `system.diskio` records with per-device metrics (`system.diskio.name`) and counters:
- `system.diskio.read.bytes`, `system.diskio.write.bytes`;
- `system.diskio.io.ops`, `system.diskio.io.time`;
- nested `system.diskio.iostat.*` block.

A second schema is also present: aggregated rows with `host.disk.read.bytes` and `host.disk.write.bytes` without the `system` object.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:43.135Z` |
| host.name | string | host identifier | `internal-share` |
| event.dataset | string | telemetry dataset type | `system.diskio` |
| system.diskio.name | string | disk device name | `vda15` |
| system.diskio.read.bytes | float | read-bytes counter | `9526272` |
| system.diskio.write.bytes | float | write-bytes counter | `5120` |
| system.diskio.io.ops | float | I/O operations counter | `0` |
| host.disk.read.bytes | float | host-level read bytes (alternate schema) | `1572864` |
| host.disk.write.bytes | float | host-level write bytes (alternate schema) | `432029696` |

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
- rolling statistics over `system.diskio.read.bytes` / `system.diskio.write.bytes`;
- read/write ratio and burst indicators;
- I/O saturation features from `system.diskio.io.ops` and `system.diskio.iostat.busy`;
- device-level baseline deviation;
- cross-checking device-level telemetry with host-level `host.disk.*` aggregates.

### Network / hybrid features
- correlation of I/O spikes with network flow and authentication events on the same host.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | missing system bytes rows: 0 |
| Unstable structure | yes | `system.diskio` + `host.disk.*` mix |
| Mixed schemas | yes | unknown json rows: 0 |
| Duplicate rows | no | none detected in sample |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/diskio.log` is suitable for host I/O feature extraction, but at least two active sub-schemas exist under the same extension (`system.diskio` and `host.disk.*`). A production parser should explicitly branch by row shape.

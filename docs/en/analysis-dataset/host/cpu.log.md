# Format Analysis: cpu.log

## 1. Purpose
`cpu.log` in `TRAIN` contains host CPU telemetry suitable for extracting load/time-based features (CPU utilization, idle/user/system/iowait shares).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | cpu.log |
| Extension variants | `.log` (grouped as `cpu.log`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 13 |

## 3. Example files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu__e874294b43.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-14-system.cpu.log
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | none (JSON-lines) |
| Encoding | utf-8 (13) |
| Nested structure | yes (nested JSON objects) |
| Sampled files | 13 |
| Sampled lines | 10479 |
| JSON lines | 10479 |
| Metric rows | 10435 |
| Label rows | 44 |

## 5. Semantic structure
Primary flow: `system.cpu` Metricbeat records with fields:
- `@timestamp`
- `host.name`, `host.cpu.pct`
- `system.cpu.total.norm.pct`, `system.cpu.user.norm.pct`, `system.cpu.system.norm.pct`, `system.cpu.idle.norm.pct`
- `event.dataset=system.cpu`, `metricset.name=cpu`.

Additional annotation-like lines (`line`, `labels`, `rules`) are present in part of the files.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:34.512Z` |
| host.name | string | host identifier | `internal-share` |
| host.cpu.pct | float | aggregated host CPU utilization | `0.1183` |
| system.cpu.total.norm.pct | float | normalized total CPU fraction | `0.1183` |
| system.cpu.user.norm.pct | float | user CPU fraction | `0.0578` |
| system.cpu.system.norm.pct | float | kernel/system CPU fraction | `0.0246` |
| system.cpu.idle.norm.pct | float | idle CPU fraction | `0.873` |
| labels[] | array[string] | attack/annotation labels (sparse) | `["escalate","crack_passwords"]` |
| rules | object | rule references for labels | `{"escalate":["attacker.escalate.wpcrack"]}` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | labels |
| Label values | crack_passwords, escalate |
| Suitable for supervised learning | partially |

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
- rolling statistics on `host.cpu.pct` and `system.cpu.total.norm.pct`;
- user/system/iowait/idle ratio features;
- burst/anomaly features from temporal CPU deltas;
- host baseline deviation features;
- sparse weak labels from `labels/rules` for semi-supervised evaluation.

### Network / hybrid features
- correlate CPU spikes with network flow load and auth/session events.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | missing cpu pct rows: 0 |
| Unstable structure | yes | metric rows + label/annotation rows |
| Mixed schemas | yes | unknown json rows: 0 |
| Duplicate rows | no | none detected in sample |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/cpu.log` is mostly ready for CPU metric feature extraction, but the format includes sparse label/annotation rows with a different schema. A parser with branching (`metric row` vs `annotation row`) is recommended.

CPU stats (sample):
- `host.cpu.pct`: min=0.0, max=1.0, avg=0.07404315285098227
- `system.cpu.total.norm.pct`: min=0.0, max=1.0, avg=0.07404315285098227

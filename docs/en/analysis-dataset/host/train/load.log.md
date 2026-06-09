# Format Analysis: load.log

## 1. Purpose
`load.log` in `TRAIN` contains Metricbeat system load telemetry in JSON-lines format.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | load.log |
| Extension variants | `.log` (JSON-lines content) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-13-system.load.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-13-system.load__5fb44b3774.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-14-system.load.log
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | JSON object / JSON-lines |
| Encoding | utf-8 |
| Nested structure | yes |
| JSON document | 0 |
| JSON-lines | 12 |
| Unparsed | 0 |

## 5. Semantic structure
The sampled files are JSON-lines Metricbeat records with nested keys like `system.load`, `event`, and `metricset`.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| system.load.1 | float | 1-minute load average | `0.26` |
| system.load.5 | float | 5-minute load average | `0.11` |
| system.load.15 | float | 15-minute load average | `0.03` |
| @timestamp | string | event timestamp | `2022-01-13T14:31:34.512Z` |
| host.name | string | source host | `internal-share` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values |  |
| Suitable for supervised learning | no |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | no |
| Field name | time.container_ready.absolute, timestamp |
| Timestamp format | Unix epoch float + ISO-8601 |
| Timezone | UTC(+0000) for JSON-lines; scenario JSON timezone implicit |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- load averages (`system.load.1/5/15`);
- normalized load (`system.load.norm.*`);
- load trend and volatility by time windows.

### Network / hybrid features
- correlation of host load spikes with network flow anomalies from other datasets.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | no critical gaps in sampled data |
| Unstable structure | no | should stay stable as Metricbeat JSON-lines |
| Mixed schemas | no | schema branching is not expected here |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Needs dedicated parser | no |
| Processing priority | medium |

## 12. Conclusion
`TRAIN/load.log` is ready for feature extraction as a consistent JSON-lines telemetry source.

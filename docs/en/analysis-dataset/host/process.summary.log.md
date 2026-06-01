# Format Analysis: process.summary.log

## 1. Purpose
Mixed `process.summary.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | process.summary.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary__27dcbaf600.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-14-system.process.summary.log
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
| Raw text | 0 |
| Unparsed | 0 |

## 5. Semantic structure
Two schemas are present: scenario documents (`container`, `exploit`, `time`) and JSON-lines events (`timestamp`, `event_type`, `alert`, `dns`).

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| exploit | bool | scenario indicator | `false` |
| container.role | string | container role | `normal`, `victim` |
| time.container_ready.absolute | float | readiness timestamp | `1631222503.73` |
| timestamp | string | event timestamp | `2022-01-13T14:37:36.251509+0000` |
| event_type | string | event type | `stats`, `dns`, `alert` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | exploit / container.role / alert (schema-dependent) |
| Label values | True, False, normal, victim, alert-derived |
| Suitable for supervised learning | partially |

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
- frequency of `event_type=dns`;
- diversity of DNS-related events.

### Host features
- `exploit`, container roles, `recording_time`;
- temporal sequences of `event_type`.

### Network / hybrid features
- `src_ip`, `dest_ip`, `src_port`, `dest_port`, `proto`;
- correlation of alerts with host scenario context.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | no critical gaps in sampled data |
| Unstable structure | no | mixed JSON document and JSON-lines |
| Mixed schemas | no | schema-aware parser is required |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Needs dedicated parser | no |
| Processing priority | medium |

## 12. Conclusion
`TRAIN/process.summary.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

# Format Analysis: auth.log

## 1. Purpose
`auth.log` files in `TRAIN` contain authentication/session events (sudo/cron/systemd/useradd/sshd) suitable for host behavioral feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | auth.log |
| Extension variants | `.log` (grouped as `auth.log`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 23 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth__0c52d9c83a.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-14-system.auth.log
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | none (line-oriented logs / JSON-lines) |
| Encoding | utf-8 (23) |
| Nested structure | yes (JSON-lines with nested objects) |
| Sampled files | 23 |
| Sampled lines | 5263 |
| JSON lines | 2827 |
| Raw syslog lines | 2436 |

## 5. Semantic structure
Two event substructures are present in `TRAIN/auth.log`:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- Filebeat/ECS JSON-lines wrapper with keys like `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Example activities:
- `session_opened`: 2187
- `session_closed`: 2168

Example process sources:
- `sudo`: 1468
- `systemd-logind[1011]`: 37
- `systemd-logind[987]`: 36
- `systemd`: 25
- `useradd[952]`: 24
- `useradd[877]`: 24
- `auth`: 24
- `useradd[25248]`: 18

## 6. Detected fields / columns
| Field | Type | Purpose | Example |
|---|---|---|---|
| message | string | auth/syslog event payload | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | ingest timestamp (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | event category in wrapper | `system.auth` |
| host.name | string | source host | `internal-share` |
| log.file.path | string | original log path | `/var/log/auth.log` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | partially |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | @timestamp, message(syslog prefix) |
| Timestamp format | ISO-8601 (@timestamp) + syslog time without year |
| Timezone | event.timezone (+00:00) for JSON lines; implicit for raw lines |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- `session_opened/session_closed` frequencies;
- action/process frequencies (`sudo`, `cron`, `systemd`, `sshd`);
- user-level login/session features;
- source IP frequency/anomaly features;
- temporal sequences of auth events.

### Network / hybrid features
- correlate source IPs from auth events with network flow features.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | read errors: 0 |
| Missing values | yes | missing `message`: 12 |
| Unstable structure | yes | raw syslog and JSON-lines are mixed |
| Mixed schemas | yes | json_only=13, raw_only=10 |
| Duplicate rows | no | duplicate lines in sample: 0 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/auth.log` provides useful authentication telemetry for feature extraction, but the extension includes two different internal representations (raw syslog and JSON-lines). A dedicated parser with structure-aware branching is required for reliable production processing.

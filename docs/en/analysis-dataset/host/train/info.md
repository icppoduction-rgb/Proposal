# Format Analysis: info

## 1. Purpose
`info` files in `TRAIN` contain mail login/logout events (dovecot imap-login/imap) suitable for host behavioral feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | info |
| Extension variants | `.log` (grouped as `info`) |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail.info
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__b37332a09e.info
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__f74e14508c.info
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | none (line-oriented logs / JSON-lines) |
| Encoding | utf-8 (3) |
| Nested structure | yes (JSON-lines with nested objects) |
| Sampled files | 3 |
| Sampled lines | 3000 |
| JSON lines | 0 |
| Raw syslog lines | 3000 |

## 5. Semantic structure
Two event substructures are present in `TRAIN/info`:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- Filebeat/ECS JSON-lines wrapper with keys like `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Example activities:
- `login`: 1503
- `logged_out`: 1497
- `disconnected`: 6
- `auth_failed`: 6

Example process sources:
- `dovecot`: 3000

## 6. Detected fields / columns
| Field | Type | Purpose | Example |
|---|---|---|---|
| message | string | auth/syslog event payload | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | ingest timestamp (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | event category in wrapper | `mail.info/dovecot` |
| host.name | string | source host | `internal-share` |
| log.file.path | string | original log path | `/var/log/info` |

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
- `login/logged_out/disconnected` frequencies;
- action/process frequencies (`sudo`, `cron`, `systemd`, `sshd`);
- user-level login/session features;
- source IP frequency/anomaly features;
- temporal sequences of mail info events.

### Network / hybrid features
- correlate source IPs from mail info events with network flow features.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | read errors: 0 |
| Missing values | no | missing `message`: 0 |
| Unstable structure | no | raw text lines and optional JSON wrappers may coexist |
| Mixed schemas | no | json_only=0, raw_only=3 |
| Duplicate rows | yes | duplicate lines in sample: 3 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Needs dedicated parser | no |
| Processing priority | medium |

## 12. Conclusion
`TRAIN/info` provides useful mail service telemetry for feature extraction, but the extension includes two different internal representations (raw syslog and JSON-lines). A dedicated parser with structure-aware branching is required for reliable production processing.

# General Host Train Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/host/train`.

## Source documents

- `README.md`
- `auth.log.md`
- `cpu.log.md`
- `csv.md`
- `diskio.log.md`
- `filesystem.log.md`
- `fsstat.log.md`
- `ghc.md`
- `info.md`
- `journal.md`
- `journal~.md`
- `json-1.md`
- `json.md`
- `load.log.md`
- `log-1.md`
- `log-2.md`
- `log-3.md`
- `log.md`
- `mail-info-1.md`
- `mail-warn-1.md`
- `mainlog-1.md`
- `mainlog-2.md`
- `mainlog-3.md`
- `mainlog.md`
- `memory.log.md`
- `messages-1.md`
- `messages.md`
- `netflow_ids.md`
- `network.log.md`
- `pcap.md`
- `process.log.md`
- `process.summary.log.md`
- `sc.md`
- `service.log.md`
- `socket.summary.log.md`
- `syslog-1.md`
- `syslog-2.md`
- `syslog-3.md`
- `syslog-4.md`
- `syslog.log.md`
- `syslog.md`
- `txt.md`
- `uptime.log.md`
- `xml.md`

---

## Source: `README.md`

# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | 101 | no | yes | PARTIALLY_SUPPORTED | csv.md |
| auth.log | 23 | no | yes | NEEDS_CUSTOM_PARSER | auth.log.md |
| cpu.log | 13 | no | yes | PARTIALLY_SUPPORTED | cpu.log.md |
| diskio.log | 12 | no | yes | PARTIALLY_SUPPORTED | diskio.log.md |
| filesystem.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | filesystem.log.md |
| fsstat.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | fsstat.log.md |
| ghc | 56158 | no | yes | NEEDS_CUSTOM_PARSER | ghc.md |
| info | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | info.md |
| journal | 17 | no | yes | NEEDS_CUSTOM_PARSER | journal.md |
| journal~ | 1 | no | yes | NEEDS_CUSTOM_PARSER | journal~.md |
| json | 219 | no | yes | NEEDS_CUSTOM_PARSER | json.md |
| json-1 | 1 | no | yes | READY_FOR_FEATURE_EXTRACTION | json-1.md |
| load.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | load.log.md |
| log | 98 | no | yes | NEEDS_CUSTOM_PARSER | log.md |
| log-1 | 32 | no | yes | READY_FOR_FEATURE_EXTRACTION | log-1.md |
| log-2 | 9 | no | yes | READY_FOR_FEATURE_EXTRACTION | log-2.md |
| log-3 | 8 | no | yes | READY_FOR_FEATURE_EXTRACTION | log-3.md |
| mail-info-1 | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | mail-info-1.md |
| mail-warn-1 | 2 | no | yes | READY_FOR_FEATURE_EXTRACTION | mail-warn-1.md |
| mainlog | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | mainlog.md |
| mainlog-1 | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | mainlog-1.md |
| mainlog-2 | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | mainlog-2.md |
| mainlog-3 | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | mainlog-3.md |
| memory.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | memory.log.md |
| messages | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | messages.md |
| messages-1 | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | messages-1.md |
| netflow_ids | 50 | no | yes | READY_FOR_FEATURE_EXTRACTION | netflow_ids.md |
| network.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | network.log.md |
| process.log | 2 | no | yes | READY_FOR_FEATURE_EXTRACTION | process.log.md |
| process.summary.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | process.summary.log.md |
| sc | 210 | no | yes | READY_FOR_FEATURE_EXTRACTION | sc.md |
| service.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | service.log.md |
| socket.summary.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | socket.summary.log.md |
| syslog | 9 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog.md |
| syslog-1 | 10 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog-1.md |
| syslog-2 | 10 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog-2.md |
| syslog-3 | 10 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog-3.md |
| syslog-4 | 1 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog-4.md |
| syslog.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | syslog.log.md |
| txt | 3170 | no | yes | READY_FOR_FEATURE_EXTRACTION | txt.md |
| uptime.log | 12 | no | yes | READY_FOR_FEATURE_EXTRACTION | uptime.log.md |
| xml | 40 | no | yes | READY_FOR_FEATURE_EXTRACTION | xml.md |

---

## Source: `auth.log.md`

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

---

## Source: `cpu.log.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu__e874294b43.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-14-system.cpu.log
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

---

## Source: `csv.md`

# Format Analysis: csv

## 1. Purpose
Host TRAIN CSV files are used as the main source of system telemetry (date/time, process, syscall/event, attack labels) for downstream feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 101 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\1.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\10.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\11.csv
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | yes |
| Header | not always (utility files with header are present) |
| Delimiter | , (30) |
| Encoding | cp1252 (1), utf-8-sig (29) |
| Nested structure | no |
| Sampled files | 30 |
| Sampled rows | 29027 |

## 5. Semantic structure
The primary CSV block (numbered files `1.csv`..`99.csv`) contains host telemetry: event date/time, process identifier, process path, syscall/event field, and attack label fields.
Additional utility CSV files are present:
- `feature_descr.csv` - feature dictionary;
- `ground_truth.csv` - attack scenario ground-truth details.

## 6. Detected fields / columns
| Column | Inferred name | Type | Example value |
|---|---|---|---|
| 1 | date | date | 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016 |
| 2 | time | time | 2:45:01, 2:45:06, 2:45:06, 2:45:35, 2:45:44 |
| 3 | process_id | integer | 1830, 1804, 2133, 4528, 1847 |
| 4 | path | string | /sbin/upstart-dbus-bridge, /bin/dbus-daemon, /usr/lib/i386-linux-gnu/gconf/gconfd-2, /usr/bin/python3.4, /usr/bin/ibus-daemon |
| 5 | sys_call | integer | 142, 256, 168, 3, 102 |
| 6 | event_id | integer | 45354, 45352, 45372, 39459, 37263 |
| 7 | category_7 | string | normal, normal, normal, normal, normal |
| 8 | category_8 | string | normal, normal, normal, normal, normal |
| 9 | label | integer | 0, 0, 0, 0, 0 |

### Extra mapping from feature_descr.csv
| Feature No | Feature Name | Type |
|---|---|---|
| 1 | date | date |
| 2 | time | time |
| 3 | pro_id | number |
| 4 | path | nominal |
| 5 | sys_call | number |
| 6 | event_id | number |
| 7 | attack_cat | nominal |
| 8 | attack_subcat | nominal |
| 9 | label | binary |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | column(s) 7, 8, 9 |
| Label values | normal/attack categories plus binary label (0/1) |
| Suitable for supervised learning | yes |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | date + time (separate columns) |
| Timestamp format | date + time in separate columns (dd/mm/yyyy and HH:MM:SS) |
| Timezone | not specified |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable for this format scope.

### Host features
- `sys_call`/`event_id` frequency features;
- syscall n-grams and transition features;
- process-centric sequence features (`process_id` + `path`);
- attack category/subcategory distributions;
- binary target from label (0/1).

### Network / hybrid features
- `ground_truth.csv` can provide additional context indicators (attack campaign and IP pair metadata) for host+network correlation.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted/unreadable files | no | encoding/read errors: 0 |
| Missing values | yes | found in sample: 66 |
| Unstable structure | yes | observed 9/7/5-column schemas |
| Mixed schemas | yes | special schema files: 2 |
| Duplicate rows | yes | found in sample: 13 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/csv` is suitable for host-side feature extraction and supervised learning. The main data flow has a stable 9-column schema, but utility files (`feature_descr.csv`, `ground_truth.csv`) use separate schemas, so partial parser branching is required for full-format coverage.

---

## Source: `diskio.log.md`

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

---

## Source: `filesystem.log.md`

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

---

## Source: `fsstat.log.md`

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

---

## Source: `ghc.md`

# Format Analysis: ghc

## 1. Purpose
`ghc` in `TRAIN` contains text trace sequences in `<module>+0x<offset>` form for host process behavior analysis.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | ghc |
| Extension variants | `.ghc`, `.GHC` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 56158 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-0.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-1.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-10.GHC
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | space |
| Encoding | utf-8 (30) |
| Nested structure | no |
| Sampled files | 30 |
| Sampled lines | 30 |
| Token count | 6000 |
| Valid trace tokens | 6000 |

## 5. Semantic structure
Data is represented as trace-like token sequences containing:
- module name (`kernel32.dll`);
- hexadecimal offset (`0xb50b`);
- token order in a line as behavioral sequence.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| trace.token | string | raw trace token | `kernel32.dll+0xb50b` |
| trace.module | string | module/library name | `kernel32.dll` |
| trace.offset_hex | string | hexadecimal offset | `0xb50b` |
| filename.scenario_tag | string | filename scenario prefix | `S1-1-Full` |

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
| Timestamp found | no |
| Field name | - |
| Timestamp format | not present |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- module frequency counts (`top_modules_detected`);
- trace token n-grams;
- transitions between modules;
- trace sequence length;
- per-module offset distributions.

### Network / hybrid features
- correlate trace sequences with process/network activity by host and external timestamps.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | invalid tokens: 0 |
| Unstable structure | no | non-trace tokens exist |
| Mixed schemas | no | includes tokens outside `<module>+0x<hex>` |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/ghc` is usable for feature extraction only through a dedicated specialized parser.
Token-per-file stats (sample): min=200.0, max=200.0, avg=200.0.

---

## Source: `info.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail.info
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__b37332a09e.info
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__f74e14508c.info
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

---

## Source: `journal.md`

# Format Analysis: journal

## 1. Purpose
`journal` in `TRAIN` is a binary systemd journal container and requires a dedicated parser to extract events.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | journal |
| Extension variants | `.journal` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 17 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__1451ab8d6a.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__53b42cbacc.journal
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | binary signature present |
| Delimiter | none |
| Encoding | unknown (container bytes) |
| Nested structure | yes |
| Sampled files | 17 |
| Files with `LPKSHHRH` signature | 17 |

## 5. Semantic structure
The format matches a systemd journal-like binary container. Direct text parsing is not reliable.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| header_signature_hex | string | first 8-byte signature | `4c504b5348485248` |
| size_bytes | integer | file size | `16777216` |
| printable_ratio | float | printable bytes ratio in sampled header | `0.12` |

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
| Timestamp found | no |
| Field name | - |
| Timestamp format | not directly readable |
| Sequence-ready | no |
| Sliding-window-ready | no |

## 9. Potential feature extraction signals
### DNS features
- not applicable at raw binary stage.

### Host features
- journal size and growth pace;
- entry count and event families after `journalctl` parsing.

### Network / hybrid features
- correlation of extracted journal events with network/process logs after normalization.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse/read errors: 0 |
| Missing values | no | binary container format |
| Unstable structure | no | binary and text-like files mixed |
| Mixed schemas | no | binary_like=17, text_like=0 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/journal` should not be handled as a plain text log. A dedicated parser/toolchain for systemd journal is required for reliable feature extraction.

---

## Source: `journal~.md`

# Format Analysis: journal~

## 1. Purpose
`journal~` in `TRAIN` is a binary systemd journal container and requires a dedicated parser to extract events.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | journal~ |
| Extension variants | `.journal~` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 1 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal~\system@0005d5746689b192-0aaa58de307081cb.journal~
-
-
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | binary signature present |
| Delimiter | none |
| Encoding | unknown (container bytes) |
| Nested structure | yes |
| Sampled files | 1 |
| Files with `LPKSHHRH` signature | 1 |

## 5. Semantic structure
The format matches a systemd journal-like binary container. Direct text parsing is not reliable.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| header_signature_hex | string | first 8-byte signature | `4c504b5348485248` |
| size_bytes | integer | file size | `16777216` |
| printable_ratio | float | printable bytes ratio in sampled header | `0.12` |

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
| Timestamp found | no |
| Field name | - |
| Timestamp format | not directly readable |
| Sequence-ready | no |
| Sliding-window-ready | no |

## 9. Potential feature extraction signals
### DNS features
- not applicable at raw binary stage.

### Host features
- journal size and growth pace;
- entry count and event families after `journalctl` parsing.

### Network / hybrid features
- correlation of extracted journal events with network/process logs after normalization.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse/read errors: 0 |
| Missing values | no | binary container format |
| Unstable structure | no | binary and text-like files mixed |
| Mixed schemas | no | binary_like=1, text_like=0 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/journal~` should not be handled as a plain text log. A dedicated parser/toolchain for systemd journal is required for reliable feature extraction.

---

## Source: `json-1.md`

# Format Analysis: json-1-1

## 1. Purpose
Mixed `json-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | json-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 1 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json-1\eve.json.1
-
-
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
| JSON-lines | 1 |
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
| Timestamp found | yes |
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
`TRAIN/json-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `json.md`

# Format Analysis: json

## 1. Purpose
Mixed `json` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 219 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_buck_7911.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_jang_1984.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_moser_1096.json
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
| JSON document | 29 |
| JSON-lines | 1 |
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
| Label found | yes |
| Field name | exploit / container.role / alert (schema-dependent) |
| Label values | True, False, normal, victim, alert-derived |
| Suitable for supervised learning | partially |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | yes |
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
| Unstable structure | yes | mixed JSON document and JSON-lines |
| Mixed schemas | yes | schema-aware parser is required |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/json` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `load.log.md`

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

---

## Source: `log-1.md`

# Format Analysis: log-1

## 1. Purpose
Mixed `log-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | log-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 32 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log__2c25d4bfe3.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log__5869f86552.1
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
| JSON-lines | 0 |
| Raw text | 30 |
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
| Timestamp found | yes |
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
`TRAIN/log-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `log-2.md`

# Format Analysis: log-2

## 1. Purpose
Mixed `log-2` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | log-2 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 9 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\cloud.smith.santos.com-access.log.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\error.log.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\error.log__4546271eaa.2
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
| JSON-lines | 0 |
| Raw text | 9 |
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
`TRAIN/log-2` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `log-3.md`

# Format Analysis: log-3

## 1. Purpose
Mixed `log-3` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | log-3 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 8 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\cloud.smith.santos.com-access.log.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\error.log.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\error.log__37add883a7.3
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
| JSON-lines | 0 |
| Raw text | 8 |
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
`TRAIN/log-3` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `log.md`

# Format Analysis: log

## 1. Purpose
Mixed `log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 98 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\attacks.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\audit.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\audit__102e01617c.log
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
| JSON-lines | 7 |
| Raw text | 23 |
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
| Timestamp found | yes |
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
| Unstable structure | yes | mixed JSON document and JSON-lines |
| Mixed schemas | yes | schema-aware parser is required |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mail-info-1.md`

# Format Analysis: mail-info-1

## 1. Purpose
Mixed `mail-info-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mail-info-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info__19c6dd9286.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info__e9f0904d0f.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/mail-info-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mail-warn-1.md`

# Format Analysis: mail-warn-1

## 1. Purpose
Mixed `mail-warn-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mail-warn-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 2 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-warn-1\mail.warn.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-warn-1\mail.warn__3fed34c246.1
-
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
| JSON-lines | 0 |
| Raw text | 2 |
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
`TRAIN/mail-warn-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mainlog-1.md`

# Format Analysis: mainlog-1

## 1. Purpose
Mixed `mainlog-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mainlog-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog__10ce3c1dea.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog__30704dbbbe.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp found | yes |
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
`TRAIN/mainlog-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mainlog-2.md`

# Format Analysis: mainlog-2

## 1. Purpose
Mixed `mainlog-2` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mainlog-2 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog__240133fe49.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog__cd47151943.2
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp found | yes |
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
`TRAIN/mainlog-2` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mainlog-3.md`

# Format Analysis: mainlog-3

## 1. Purpose
Mixed `mainlog-3` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mainlog-3 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog__74d65a7798.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog__eb89245528.3
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp found | yes |
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
`TRAIN/mainlog-3` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `mainlog.md`

# Format Analysis: mainlog

## 1. Purpose
Mixed `mainlog` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | mainlog |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog__0c75e068e4
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog__220033d95b
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp found | yes |
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
`TRAIN/mainlog` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `memory.log.md`

# Format Analysis: memory.log

## 1. Purpose
Mixed `memory.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | memory.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-13-system.memory.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-13-system.memory__c01f1006f7.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-14-system.memory.log
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
`TRAIN/memory.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `messages-1.md`

# Format Analysis: messages-1

## 1. Purpose
Mixed `messages-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | messages-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages__4260d24d73.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages__4e26791260.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/messages-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `messages.md`

# Format Analysis: messages

## 1. Purpose
Mixed `messages` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | messages |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages__0f8a1d8071
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages__de412018b2
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/messages` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `netflow_ids.md`

# Format Analysis: netflow_ids

## 1. Purpose
Mixed `netflow_ids` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | netflow_ids |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 50 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_fri.netflow_ids
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_fri__dd3db04938.netflow_ids
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_mon.netflow_ids
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/netflow_ids` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `network.log.md`

# Format Analysis: network.log

## 1. Purpose
Mixed `network.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | network.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-13-system.network.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-13-system.network__3342ea8eb0.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-14-system.network.log
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
`TRAIN/network.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `pcap.md`

# Format Analysis: pcap

## 1. Purpose
`pcap` in `TRAIN` stores packet capture binaries and requires specialized parser libraries.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | `.pcap` / `.pcapng` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 15 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084616
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084634
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084645
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | unknown |
| Nested structure | no |
| JSON document | 0 |
| JSON-lines | 0 |
| Raw text | 15 |
| Unparsed | 0 |

## 5. Semantic structure
PCAP stores packet frames in binary form. Event-level fields require dedicated packet parsing tools/libraries.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| magic | hex | pcap signature | `d4c3b2a1` |
| version_major | int | format major version | `2` |
| version_minor | int | format minor version | `4` |
| snaplen | int | max packet bytes captured | `65535` |
| network | int | link-layer type | `1` |

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
| Field name |  |
| Timestamp format | requires PCAP parser |
| Timezone | unknown |
| Sequence-ready | no |
| Sliding-window-ready | no |

## 9. Potential feature extraction signals
### DNS features
- DNS features are available only after packet parsing.

### Host features
- packet rate over time windows;
- protocol distribution per capture.

### Network / hybrid features
- flow duration, bytes, packets, protocol, TCP flags;
- DNS/TCP/UDP/ICMP counts after parsing.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | no critical gaps in sampled data |
| Unstable structure | no | binary capture requires dedicated parser |
| Mixed schemas | no | parser/toolchain required for packet decoding |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/pcap` requires a dedicated PCAP parsing layer before feature extraction.

---

## Source: `process.log.md`

# Format Analysis: process.log

## 1. Purpose
Mixed `process.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | process.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 2 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.log\2022-01-13-system.process.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.log\2022-01-13-system.process__1b19d2a0f4.log
-
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
| JSON-lines | 2 |
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
`TRAIN/process.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `process.summary.log.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary__27dcbaf600.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-14-system.process.summary.log
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

---

## Source: `sc.md`

# Format Analysis: sc

## 1. Purpose
Mixed `sc` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | sc |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 210 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_buck_7911.sc
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_jang_1984.sc
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_moser_1096.sc
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
| JSON-lines | 0 |
| Raw text | 30 |
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
| Timestamp found | yes |
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
`TRAIN/sc` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `service.log.md`

# Format Analysis: service.log

## 1. Purpose
Mixed `service.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | service.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-13-system.service.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-13-system.service__ea8ef3f753.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-14-system.service.log
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
`TRAIN/service.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `socket.summary.log.md`

# Format Analysis: socket.summary.log

## 1. Purpose
Mixed `socket.summary.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | socket.summary.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-13-system.socket.summary.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-13-system.socket.summary__ee3c7fe60e.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-14-system.socket.summary.log
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
`TRAIN/socket.summary.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog-1.md`

# Format Analysis: syslog-1

## 1. Purpose
Mixed `syslog-1` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog-1 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 10 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog__2b89be2198.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog__31309f5830.1
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-1` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog-2.md`

# Format Analysis: syslog-2

## 1. Purpose
Mixed `syslog-2` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog-2 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 10 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog__03421c5fb5.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog__060eb57e99.2
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-2` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog-3.md`

# Format Analysis: syslog-3

## 1. Purpose
Mixed `syslog-3` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog-3 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 10 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog__08b69a348f.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog__1ff252de29.3
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-3` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog-4.md`

# Format Analysis: syslog-4

## 1. Purpose
Mixed `syslog-4` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog-4 |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 1 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-4\syslog.4
-
-
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
| JSON-lines | 0 |
| Raw text | 1 |
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
`TRAIN/syslog-4` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog.log.md`

# Format Analysis: syslog.log

## 1. Purpose
Mixed `syslog.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog__66beef41ca.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-14-system.syslog.log
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
`TRAIN/syslog.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `syslog.md`

# Format Analysis: syslog

## 1. Purpose
Mixed `syslog` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | syslog |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 9 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog__072490aa2f
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog__07c7f78139
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
| JSON-lines | 0 |
| Raw text | 9 |
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
`TRAIN/syslog` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `txt.md`

# Format Analysis: txt

## 1. Purpose
Mixed `txt` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 3170 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\ADFA-LD+Syscall+List.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\fox_alerts.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\harrison_alerts.txt
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/txt` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `uptime.log.md`

# Format Analysis: uptime.log

## 1. Purpose
Mixed `uptime.log` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | uptime.log |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 12 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-13-system.uptime.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-13-system.uptime__bb8fbe0154.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-14-system.uptime.log
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
`TRAIN/uptime.log` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

---

## Source: `xml.md`

# Format Analysis: xml

## 1. Purpose
Mixed `xml` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | xml |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 40 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-1.XML
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-10.XML
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-2.XML
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/xml` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.

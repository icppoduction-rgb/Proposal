# Format and status matrix

This matrix preserves the key facts from the previous 66 per-format reports: split, format, file count, readiness, label availability, timestamp availability, and the main limitation/action. The old source paths are listed in [source_inventory.md](source_inventory.md).

## Status summary

| Status | Format buckets | Files |
| --- | ---: | ---: |
| `READY_FOR_FEATURE_EXTRACTION` | 42 | 288866 |
| `NEEDS_CUSTOM_PARSER` | 14 | 72666 |
| `PARTIALLY_SUPPORTED` | 6 | 138 |
| `BROKEN_OR_EMPTY` | 2 | 0 |

## DNS

| Role | Format | Files | Status | Labels | Timestamp | Limitation / action |
| --- | --- | ---: | --- | --- | --- | --- |
| `TRAIN` | `csv` | 8 | `PARTIALLY_SUPPORTED` | class hints: benign/malware/phishing/spam | partial | Requires schema-aware normalization for feature CSV files with list/dict fields. |
| `TRAIN` | `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | filename class hints | yes | Requires a packet parser with DNS decoding. |
| `TRAIN` | `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | filename class hints: audio/benign/compressed/exe/image/text/video | yes | Ready for DNS feature extraction after label mapping. |
| `VALIDATION` | `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | filename class hints: attack/benign | yes | Requires a packet parser for validation packet features. |
| `VALIDATION` | `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | filename hints: unknown/benign | no | Domain-list; `unknown` requires a separate policy. |
| `TEST` | `csv` | 1 | `PARTIALLY_SUPPORTED` | partial boolean-like `label_or_flag` | yes | Headerless 22-column schema; evaluation only. |
| `TEST` | `pcap` | 0 | `BROKEN_OR_EMPTY` | none | no | Bucket is empty. |
| `TEST` | `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | none | no | Bucket is empty. |

## Host TRAIN

| Format | Files | Status | Labels | Timestamp | Limitation / action |
| --- | ---: | --- | --- | --- | --- |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | none | yes | Raw syslog + JSON Lines; requires branching parser logic. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | embedded/annotation labels: crack_passwords, escalate | yes | Split metric rows and annotation rows. |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | attack categories + binary 0/1 | yes | Distinguish telemetry CSV from `feature_descr.csv` and `ground_truth.csv`. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | none | yes | At least two sub-schemas: `system.diskio` and `host.disk.*`. |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | JSON Lines storage telemetry. |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | JSON Lines storage telemetry. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | none | no | Specialized trace parser; large volume. |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Mail/service logs; schema-aware parser. |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | none | no | Binary/systemd journal. |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | none | no | Binary/systemd journal backup. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | schema-dependent: exploit/container.role/alert | yes | Mixed schemas; requires a schema-aware parser. |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware extraction; labels only through the resolver. |
| `load.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | none | none/contextual | Telemetry; timestamp may be nested/contextual. |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | context hints | yes | Mixed JSON/scenario/log schemas. |
| `log-1` | 32 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware parser layer. |
| `log-2` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Schema-aware parser layer. |
| `log-3` | 8 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Schema-aware parser layer. |
| `mail-info-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Mail log parser. |
| `mail-warn-1` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Mail log parser. |
| `mainlog` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware parser layer. |
| `mainlog-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware parser layer. |
| `mainlog-2` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware parser layer. |
| `mainlog-3` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Schema-aware parser layer. |
| `memory.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Metric telemetry; external labels only. |
| `messages` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `messages-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Flow-like source; line-oriented parser. |
| `network.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Network telemetry. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | none | no in extracted summary | Requires a packet parser. |
| `process.log` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Process event features. |
| `process.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Process summary features. |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | context hints | yes | Syscall/API trace parser. |
| `service.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Service telemetry. |
| `socket.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Socket summary features. |
| `syslog` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `syslog-1` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `syslog-2` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `syslog-3` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `syslog-4` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `syslog.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Syslog-like parser. |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Sequence/trace parser; streaming required. |
| `uptime.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | Uptime/metric features. |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | context hints | no | XML/schema-aware parser. |

## Host VALIDATION

| Format | Files | Status | Labels | Timestamp | Limitation / action |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | none inside file | yes | Packet parser; labels through scenario/CSV join. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | partial | Validation labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Windows/Sysmon JSON Lines. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Large flow files; external labels only. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | none inside file | yes | Packet parser; labels through scenario/CSV join. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | none inside file | yes | PCAPNG parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Syscall traces; streaming required. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Windows/Sysmon-like events. |

## Host TEST

| Format | Files | Status | Labels | Timestamp | Limitation / action |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | none | partial | BSON parser; descriptor/event join by `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | external label CSV | yes | Labels for evaluation only; join by IP/key. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | none | yes | JSON Lines, Mongo-style `NumberLong(...)`, reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Very large syscall/API traces; requires streaming. |

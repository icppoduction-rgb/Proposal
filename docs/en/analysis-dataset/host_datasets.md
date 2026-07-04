# Host datasets

The Host branch contains 56 format buckets and 361635 files. It is the main source for host telemetry, sequence traces, runtime logs, Windows/Sysmon-like events, network flows, and packet captures.

## Host TRAIN

Host TRAIN contains 43 format buckets and 60365 files. It is the main training source, but not every format has labels and not every format is suitable for a generic reader.

### Family summary

| Family | Formats | Processing status |
| --- | --- | --- |
| Metrics/telemetry | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Most are ready for feature extraction; `cpu.log` and `diskio.log` are partially supported because of sub-schemas. |
| Logs | `auth.log`, `info`, `journal`, `journal~`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Require schema-aware routing; `journal`/`journal~` require a dedicated toolchain. |
| Structured/semi-structured | `csv`, `json`, `json-1`, `xml` | CSV is partially supported because of service files; JSON requires a schema-aware parser. |
| Network/hybrid | `netflow_ids`, `pcap` | `netflow_ids` is ready; `pcap` requires a packet/parser layer. |
| Behaviour traces | `ghc`, `sc`, `txt` | `ghc` requires a custom parser; `sc`/`txt` are suitable for sequence features. |

### Key Host TRAIN formats

| Format | Files | Status | Key facts |
| --- | ---: | --- | --- |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | Contains telemetry CSV plus service files such as `feature_descr.csv` and `ground_truth.csv`; labels are in columns 7/8/9 and binary label 0/1. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | Contains metric rows and annotation rows with labels `crack_passwords`, `escalate`; parser split is required. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | At least two sub-schemas: `system.diskio` and `host.disk.*`. |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | Mixes raw syslog and JSON Lines. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | Very large trace corpus; sample shows 200 tokens per file. |
| `journal`, `journal~` | 18 | `NEEDS_CUSTOM_PARSER` | Binary/systemd journal; must not be read as a regular text log. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | Mixed schemas, scenario docs, `exploit`, `container.role`, `alert`. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | Requires a packet parser. |
| `filesystem.log`, `fsstat.log` | 24 | `READY_FOR_FEATURE_EXTRACTION` | JSON Lines storage telemetry. |
| `sc`, `txt` | 3380 | `READY_FOR_FEATURE_EXTRACTION` | Syscall/API sequence traces; require streaming and sequence-aware features. |

## Host VALIDATION

Host VALIDATION contains 8 format buckets and 6686 files.

| Format | Files | Status | Labels | Timestamp | Purpose |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | none inside file | packet timestamp | Network/hybrid validation; requires a pcap/cap parser. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | partial | Validation metadata and labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | JSON Lines Windows/Sysmon telemetry. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Large line-oriented network flows. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | none inside file | packet timestamp | Packet validation. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | none inside file | packet timestamp | Packet validation, pcapng parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Line-oriented syscall traces. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Windows/Sysmon-like events. |

Validation packet/flow/trace files without embedded labels must be linked to validation CSV by `scenario_name`, `image_name`, filename, recording time, exploit start time, and timestamp windows.

## Host TEST

Host TEST contains 5 format buckets and 294584 files. This set must not be used for training, but it is important for inference/evaluation.

| Format | Files | Status | Labels | Timestamp | Purpose |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | none | partial via order/`t`/`h` | Sandbox behaviour sequence; requires a BSON parser and descriptor/event matching by `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | label in separate label CSV | yes | Network/hybrid evaluation; labels join by IP or another confirmed key. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | none | yes | JSON Lines, Mongo-style `NumberLong(...)`, large reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Line-oriented sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | none | yes | Syscall/API sequence traces; very large number of files. |

## Host feature extraction

Priority features:

- process/service/socket counts and transitions;
- syscall/API n-grams and sequence embeddings;
- authentication success/failure and session patterns;
- filesystem, CPU, memory, disk I/O, and network telemetry aggregates;
- flow statistics and packet protocol distributions;
- Windows/Sysmon event IDs and parent-child process chains;
- alert/context fields as metadata, not X labels.

## Host quality risks

- Mixed schemas inside one extension, especially `json`, `log`, `syslog*`, `txt`, `xml`, `pcap` in TRAIN.
- Very large sources: TEST `txt`, `bson`, `json`, `log`.
- Missing embedded labels in most Host telemetry/log/packet/sequence files.
- Packet formats require binary parsers; BSON and Mongo-style JSON require specialized decoders.

# Parser pipeline and feature extraction recommendations

This document translates the dataset analysis results into requirements for Stage Two parser implementations, the normalized event schema, and feature extraction.

## General requirements

1. Routing must use `branch`, `role`, and `source_format`, not only the file extension.
2. Raw files are not modified.
3. `TRAIN`, `VALIDATION`, and `TEST` are processed separately.
4. Large line-oriented sources require streaming/batch reads.
5. Labels are attached by a separate label resolver layer with traceability.
6. A missing timestamp is stored as `timestamp=null`, `timestamp_type=missing`, or `event_order` if event order is available.

## Parser priorities

### High priority

| Parser | Formats | Why it matters |
| --- | --- | --- |
| DNS packet parser | DNS `pcap`, DNS VALIDATION `pcap` | Required for packet-level DNS features and validation. |
| Host BSON parser | Host TEST `bson` | Large source of behaviour sequences; requires descriptor/event join by `I`. |
| Host JSON parser | Host TRAIN/TEST `json`, `json-1` | Mixed JSON Lines, Mongo-style JSON, scenario reports. |
| Host syscall/trace parser | Host TEST/VALIDATION/TRAIN `txt`, `sc`, `ghc` | Large sequence datasets, important for behaviour-driven learning. |
| Host packet parser | Host VALIDATION `cap`/`pcap`/`pcapng`, Host TRAIN `pcap` | Network/hybrid validation and flow/packet features. |

### Medium priority

| Parser | Formats | Task |
| --- | --- | --- |
| Host line log parser | `auth.log`, `info`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Distinguish raw syslog, JSON Lines, and scenario documents. |
| Host metric parser | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Metric rows, annotation rows, nested schema variants. |
| CSV normalizers | DNS TEST `csv`, Host TRAIN/VALIDATION/TEST `csv` | Headerless/fixed schema, metadata CSV, external labels. |

### Low risk / can be connected earlier

| Source | Reason |
| --- | --- |
| DNS `pcap.csv` | Stable headers, ready for feature extraction. |
| DNS VALIDATION `txt` | Simple domain-list structure. |
| Host filesystem/fsstat/service/socket/process summary metrics | JSON Lines/telemetry rows. |
| `netflow_day`, `netflow_ids`, `wls_day` | Line-oriented, but require streaming and external labels. |

## Parser contracts by format family

| Family | Input processing | Normalized output | Edge cases |
| --- | --- | --- | --- |
| CSV | Schema detection, header/headerless support, fixed positional schemas. | Row events, flow events, label metadata if explicit. | Service CSV files, malformed list/dict fields, label CSV joins. |
| JSON/JSONL | Distinguish JSON Lines, multi-line reports, Mongo-style wrappers. | Event/metadata records with raw payload preserved. | `NumberLong(...)`, nested timestamps, scenario docs. |
| Logs/syslog | Line parser with timestamp/user/process extraction. | Host log events, event type, component, severity. | Mixed raw syslog and JSON Lines under one extension. |
| Metrics | JSON Lines or structured telemetry extraction. | Metric events/windows by host/time/component. | Annotation rows and schema variants. |
| Traces | Streaming line/token parser. | Sequence events with `event_index`. | Missing timestamps; very large number of files. |
| Packet captures | Binary parser. | Packet/flow/DNS events with packet timestamp. | Corrupted captures, pcap/pcapng/cap differences, performance. |
| BSON | BSON stream decoder. | Sandbox event sequences with descriptor/event relation. | Descriptor-event join by `I`, nested `args`, ordering. |

## Feature extraction map

| Feature group | Sources | Examples |
| --- | --- | --- |
| `dns_features` | DNS CSV, pcap.csv, DNS packet captures, domain lists | Domain length, entropy, qtype/rcode/ttl, query rate, unique subdomain ratio. |
| `host_syscall_features` | `txt`, `sc`, `ghc`, BSON sequence events | Syscall/API n-grams, transition probabilities, sequence length, file access indicators. |
| `host_eventlog_features` | syslog/auth/messages/mainlog/mail/info/logs, Windows/Sysmon JSON/WLS | Event type counts, auth success/failure, process chains, alert counts. |
| `host_metrics_features` | CPU/disk/filesystem/memory/network/process/service/socket metrics | Window aggregates, deltas, rates, peak values. |
| `network_flow_features` | `netflow_day`, `netflow_ids`, packet captures | Bytes/packets/duration/protocol/state/window counts. |
| `hybrid_features` | Correlated host + DNS + flow windows | Host process + network flow correlation, exfiltration windows. |
| `sequence_features` | syscall/API/log event order | LSTM/Transformer sequence inputs, n-gram vectors. |

## Readiness-to-action mapping

| Readiness | Stage Two action |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Connect a parser if it is not implemented yet; `mark-ready` is safe only after parser coverage check. |
| `NEEDS_CUSTOM_PARSER` | Add parser class and registry entry before normalization. |
| `PARTIALLY_SUPPORTED` | Add schema detection/sub-parser routing; do not treat the format as homogeneous. |
| `BROKEN_OR_EMPTY` | Do not normalize; check Stage One sort/save-sort and source bucket. |

## Data quality checks to add

- Per-format row/event counts after normalization.
- Empty file and empty artifact checks.
- Schema drift report by branch/role/format.
- Label coverage by role/format/status.
- Timestamp coverage and `timestamp_type` distribution.
- Parser performance metrics for large files.
- Split contamination check: no TRAIN/VALIDATION/TEST mixing.

## Implementation guardrails

- TEST labels, even if present, are evaluation-only.
- Filename labels must be disabled or heavily restricted for TEST.
- Label/source/traceability fields must be excluded from model-ready X.
- `unknown` labels remain unknown until an explicit mapping exists.
- Packet/BSON parsers must not load huge files fully into memory.
- Parser errors should produce `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, or `UNSUPPORTED_FORMAT`, not silent success.

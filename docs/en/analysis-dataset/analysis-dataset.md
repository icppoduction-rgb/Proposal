# General Dataset Analysis Documentation

## 1. Purpose

This document summarizes the analysis files under `docs/en/analysis-dataset` and `docs/ru/analysis-dataset`. It explains how the analyzed dataset formats should be used for normalization, feature extraction, model training, and validation.

The analyzed tree covers two domains:

- `dns`: DNS datasets for domain lists, DNS queries, packet captures, and derived CSV features.
- `host`: host telemetry, system/application logs, syscall/API traces, network flows, Windows/Sysmon-like events, and packet captures.

The summary covers 66 format reports and 6 README indexes. The README files index 65 reports; `host/train/pcap.md` is present as an additional report and is included in this summary.

## 2. Coverage

| Group | Format reports | Dataset files | Main meaning |
|---|---:|---:|---|
| `dns/test` | 3 | 1 | DNS test set, effectively only CSV is available |
| `dns/train` | 3 | 26 | DNS train: CSV, PCAP, and `pcap.csv` |
| `dns/validation` | 2 | 8 | DNS validation: PCAP and domain-list TXT |
| `host/test` | 7 | 294589 | Large host test set: BSON, JSON, logs, traces, flows, WLS |
| `host/train` | 43 | 60365 | Host train: telemetry, logs, mixed JSON/JSON-lines, traces, flows, pcap |
| `host/validation` | 8 | 6686 | Host validation: metadata, JSON-lines, flows, traces, packet captures |
| **Total** | **66** | **361675** | DNS and Host sources for feature extraction |

## 3. Readiness Statuses

| Status | Format count | Meaning |
|---|---:|---|
| `READY_FOR_FEATURE_EXTRACTION` | 44 | The format can be connected to feature extraction after standard streaming and normalization |
| `NEEDS_CUSTOM_PARSER` | 14 | A specialized parser or schema-aware layer is required |
| `PARTIALLY_SUPPORTED` | 6 | The format is partially usable but contains several sub-schemas or service files |
| `BROKEN_OR_EMPTY` | 2 | The prepared dataset does not contain input files for this format |

Main conclusion: most sources are usable for feature extraction, but a universal CSV/JSON reader is not enough. The pipeline must be format-aware and schema-aware.

## 4. DNS Datasets

The DNS part is compact: 8 format reports and 35 files. It consists of tabular CSV, raw packet captures, and domain lists.

### DNS TRAIN

| Format | Files | Status | Important details |
|---|---:|---|---|
| `csv` | 8 | `PARTIALLY_SUPPORTED` | Contains domain-list and PhishTank-like files, while feature CSV files may contain unescaped list/dict fields with commas |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | Requires a classic pcap/pcapng parser with DNS protocol decoding |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | Stable CSV structure with headers; label can be assigned from the file name |

DNS TRAIN classes: `benign`, `malware`, `phishing`, `spam`. For supervised learning, labels must be assigned explicitly, usually from file names.

### DNS TEST

| Format | Files | Status | Important details |
|---|---:|---|---|
| `csv` | 1 | `PARTIALLY_SUPPORTED` | Large headerless CSV, requires a fixed 22-column schema and streaming read |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | No files are present in prepared `TEST.pcap` |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | No files are present in prepared `TEST.pcap.csv` |

DNS TEST should not be treated as a full packet-level test source: only CSV data is available.

### DNS VALIDATION

| Format | Files | Status | Important details |
|---|---:|---|---|
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | Useful for DNS amplification detection validation, requires a packet parser |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Domain-list format: one domain record per line |

DNS VALIDATION classes include `attack`, `benign` for PCAP and `unknown`, `benign` for TXT. The meaning of `unknown` must be fixed before computing supervised metrics.

## 5. Host Datasets

The Host part is much larger than DNS: 58 format reports and 361640 files. Sources are heterogeneous and require different reading strategies.

Main data families:

- Metrics/telemetry: `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`.
- Logs: `auth.log`, `journal`, `syslog*`, `messages*`, `mainlog*`, `mail-*`, `info`, `log*`.
- Structured and semi-structured data: `csv`, `json`, `json-1`, `bson`, `xml`.
- Network/hybrid: `netflow_day`, `netflow_ids`, `pcap`, `pcapng`, `cap`.
- Behaviour traces: `txt`, `sc`, `ghc`.
- Windows/Sysmon-like events: `wls_day`, validation `json` files.

### Host TRAIN

Host TRAIN contains 43 format reports and 60365 files. It is the main source for feature generation and model training.

Key findings:

- `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, and `uptime.log` are mostly ready for feature extraction as JSON-lines telemetry.
- `csv` is usable for supervised learning, but it also contains service files such as `feature_descr.csv` and `ground_truth.csv`; the parser must distinguish telemetry CSV from metadata CSV.
- `cpu.log` and `diskio.log` are partially ready: they contain multiple sub-schemas, for example metric rows and annotation rows.
- `auth.log`, `journal`, `journal~`, `json`, `log`, and `ghc` require dedicated parser layers.
- Many `log-*`, `syslog*`, `mainlog*`, `messages*`, `txt`, `xml`, and `pcap` reports are suitable for feature extraction but require schema-aware handling because scenario JSON documents and JSON-lines events are mixed.

Common fields and feature groups:

- Time: `@timestamp`, `timestamp`, `time.container_ready.absolute`, packet timestamps.
- Host identity: hostname, container role, process/service identifiers.
- Labels/context: `ground_truth.csv`, `exploit`, `container.role`, `alert`, scenario-derived labels.
- Metric features: CPU load, disk I/O, filesystem usage, memory usage, network counters, process/service/socket summaries.
- Sequence features: event order, syscall/API traces, syslog/event types, authentication events.

### Host TEST

Host TEST contains 7 format reports and 294589 files. It should not be used for training, but it is important for inference and evaluation pipelines.

| Format | Files | Status | Important details |
|---|---:|---|---|
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | Requires BSON parser, descriptor/event matching by `I`, and `args` expansion |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | Network/hybrid CSV, labels must be joined separately by IP |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | Contains JSON Lines, Mongo-style `NumberLong(...)`, and large multi-line reports |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | Line-oriented sandbox runtime logs |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | Large flow files without embedded labels |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | Syscall/API sequence traces, very large file count |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Windows security/Sysmon-like JSON Lines |

Operationally important detail: `txt` and `wls_day` must be read in streaming mode, without loading the full dataset into memory.

### Host VALIDATION

Host VALIDATION contains 8 format reports and 6686 files.

| Format | Files | Status | Important details |
|---|---:|---|---|
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | Requires a pcap/cap parser or `Scapy`/`tshark` |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | Validation metadata and label/context features |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | JSON Lines Windows/Sysmon telemetry |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | Large line-oriented network flows |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | Requires a packet parser |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | Requires a pcapng parser |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | Line-oriented syscall traces |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | Windows/Sysmon-like events |

## 6. Labels and Supervised Learning

There is no single label schema across all datasets.

Recommended rules:

- DNS TRAIN/VALIDATION: assign labels from file names or directories when reports explicitly define classes.
- Host TRAIN: use `ground_truth.csv`, scenario metadata, `exploit`, `container.role`, `alert`, and other context fields only through an explicit mapping.
- Host TEST: do not use for training; if evaluation labels are needed, join them from an external source.
- TXT/domain-list files with `unknown`: do not mix them with `benign`/`attack` without a separate policy.
- For mixed-schema files, label extraction must be part of the schema-aware parser, not a global regex.

## 7. Time Features

Time is represented inconsistently:

- JSON-lines telemetry usually uses `@timestamp` or `timestamp`.
- Scenario JSON may use nested fields such as `time.container_ready.absolute`.
- PCAP/PCAPNG/CAP require packet timestamps from a packet parser.
- CSV and netflow files may contain timestamp, duration, or start/end fields depending on the specific schema.

Recommended normalization:

1. Convert all timestamps to UTC.
2. Preserve the original time field in audit metadata.
3. Sort events inside `host/session/file/scenario` before building sequence features.
4. Define window size, stride, and grouping key explicitly for sliding windows.

## 8. Data Quality and Risks

Main risks:

- Mixed schemas inside one extension: especially Host TRAIN `json`, `log`, `syslog*`, `txt`, `xml`, `pcap`.
- Missing headers: DNS TEST CSV and some flow-like files require a fixed schema.
- Very large sources: Host TEST `txt`, `bson`, `json`, `log`, plus `wls_day` and `netflow_day`.
- Missing embedded labels in TEST and some Host sources.
- Packet formats must not be parsed as text: `pcap`, `pcapng`, and `cap` require specialized libraries.
- BSON and Mongo-style JSON require separate decoder/parser logic.

## 9. Recommended Processing Architecture

Minimum safe pipeline:

1. File inventory: collect `domain`, `split`, `format`, `path`, `size`, checksum.
2. Format routing: route files by `domain/split/format`, not only by extension.
3. Streaming read: process large line-oriented sources in batches.
4. Schema detection: distinguish CSV metadata, telemetry rows, JSON document, JSON Lines, raw syslog, and packet capture.
5. Normalization: map records into canonical entities: `event`, `metric`, `flow`, `packet`, `trace`, `metadata`.
6. Label join: apply a separate label mapping layer and preserve label provenance.
7. Feature extraction: build DNS, host, network, and sequence features separately, then join by time/host/session keys.
8. Validation: check schema drift, empty files, parse errors, missing critical fields, and duplicates.

## 10. Parser Layer Priorities

High priority:

- DNS `pcap`/`pcapng`: required for packet-level DNS features.
- Host `bson`: required for TEST behaviour sequences.
- Host `json`: important because of file volume and Mongo-style variants.
- Host `txt`: requires a streaming parser due to volume.
- Host `cap`/`pcap`/`pcapng`: required for network/hybrid validation.

Medium priority:

- Host `auth.log`, `journal`, `journal~`, `log`, `ghc`.
- Mixed JSON/JSON-lines parser for TRAIN `syslog*`, `mainlog*`, `messages*`, `xml`, `pcap`.
- CSV normalizer for DNS TEST and Host TRAIN metadata/telemetry separation.

Lower risk, can be connected earlier:

- JSON-lines telemetry: `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`.
- Flow-like sources: `netflow_day`, `netflow_ids`.
- Validation metadata CSV.

## 11. Final Conclusion

The analyzed datasets are sufficiently documented to start production-grade feature extraction, but processing must be routed by format and schema rather than implemented as a universal reader.

The DNS part is smaller and simpler: the main risks are missing TEST PCAP/PCAP.CSV inputs and the need for packet parsers. The Host part is larger and more heterogeneous: it provides most of the ML value, but requires schema-aware parser layers, streaming reads, and a separate label mapping policy.

For a production-ready pipeline, it is critical not to mix train/test/validation, not to infer labels through unaudited global regex rules, and not to load large files fully into memory.

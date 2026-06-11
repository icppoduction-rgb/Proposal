# General Host Test Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/host/test`.

## Source documents

- `README.md`
- `bson.md`
- `csv.md`
- `json.md`
- `log.md`
- `netflow_day.md`
- `txt.md`
- `wls_day.md`

---

## Source: `README.md`

# Dataset File Content Analysis (Host TEST)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| bson | 9005 | no | yes | NEEDS_CUSTOM_PARSER | bson.md |
| csv | 3 | no | yes | PARTIALLY_SUPPORTED | csv.md |
| json | 7071 | no | yes | NEEDS_CUSTOM_PARSER | json.md |
| log | 4086 | no | yes | READY_FOR_FEATURE_EXTRACTION | log.md |
| netflow_day | 2 | no | yes | READY_FOR_FEATURE_EXTRACTION | netflow_day.md |
| txt | 274419 | no | yes | READY_FOR_FEATURE_EXTRACTION | txt.md |
| wls_day | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | wls_day.md |

---

## Source: `bson.md`

# Format Analysis: bson

## 1. Purpose
Host TEST BSON files contain binary process behaviour and system/API event traces. The format is useful as a source of ordered host-event sequences for later feature engineering; TEST data must not be used for model training.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | bson |
| Extension variants | .bson |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 9005 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\1000.bson
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\120__7c0ccef00c.bson
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\1372__1d508ea03c.bson
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes |
| Sampled files analyzed | 30 |
| Sample BSON documents parsed | 2325 |

## 5. Content Structure
The sample is a stream of consecutive BSON documents. It contains descriptor documents with `name`, `type`, `category`, `args`, `flags_value`, and `flags_bitmask`, plus event documents with `I`, `T`, `t`, `h`, and an `args` array. Semantically this is malware behaviour / host telemetry: process events, Windows API or syscall-like operations, call arguments, module paths, command lines, and nested flag structures.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| I | int32 | descriptor/event identifier | 0 |
| name | string | API/syscall-like event name | __process__ |
| type | string | descriptor document type | info |
| category | string | event category | __notification__ |
| args | array | argument values or argument-name array | nested_array |
| T | int32 | numeric thread/process context id | 1916 |
| t | int32 | relative time/order counter | 0 |
| h | int64 | additional numeric counter/handle | 0 |
| args.0 | string | argument values or argument-name array | is_success |
| args.1 | string | argument values or argument-name array | retval |
| flags_value.information_class.0 | array | nested flag values | nested_array |
| flags_value.information_class.0.0 | int32 | nested flag values | 0 |
| flags_value.information_class.0.1 | string | nested flag values | KeyValueBasicInformation |
| args.2 | int32 | argument values or argument-name array | -832834880 |
| args.3 | string | argument values or argument-name array | time_high |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required if available |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | BSON document order, numeric `t`/`h` event fields |
| Time format | relative numeric counters; timezone not specified |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable to this Host format.

### Host Features
- API/syscall event frequencies by `I` and descriptor `name`;
- event n-grams and transitions;
- trace length and event density;
- `args` features, including process paths, module basenames, and command line tokens;
- parent-child/process context from process notification documents;
- descriptor `category` frequencies;
- command line and module path entropy.

### Network / Hybrid Features
- no direct network flow fields were detected;
- correlation with network datasets may be possible through an external sample/file id if project metadata provides one.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors in sample: 0 |
| Missing values | yes | BSON arrays contain null/empty positions in `args` |
| Unstable structure | yes | descriptor and event documents use different schemas |
| Mixed schemas | yes | a single stream mixes metadata/descriptor/event documents |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
The format is valuable for host behaviour sequence features, but it is not ready for generic tabular reading. A dedicated BSON parser is required to map descriptor documents to event documents by `I`, expand `args`, and preserve event order. No explicit label field was found in the TEST/BSON sample.

---

## Source: `csv.md`

# Format Analysis: csv

## 1. Purpose
Host TEST CSV files contain packet/network metadata and separate CSV attack-label maps. The format is useful for network behaviour analysis and possible host+network correlation; TEST data must not be used for training.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 3 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_dataset.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels_sbseg.csv
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | yes |
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8/utf-8-sig in sample |
| Nested structure | no |
| Sampled files analyzed | 3 |

## 5. Content Structure
`attack_dataset.csv` contains packet metadata: frame time, epoch time, IP/TCP fields, addresses, ports, flags, lengths, and checksums. `attack_labels.csv` and `attack_labels_sbseg.csv` contain `ip -> label` mappings for attacks such as nmap scans. This is a network/hybrid structure inside the Host TEST bucket.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| frame_info.time | string | packet timestamp | Dec 31, 1969 21:03:41.953641000 -03 |
| frame_info.time_epoch | float | epoch seconds | 221.953641000 |
| ip.src | ip | source IP | 172.16.0.3 |
| ip.dst | ip | destination IP | 10.10.10.10 |
| ip.proto | integer | sampled CSV column | 6 |
| tcp.srcport | integer | source TCP port | 62218 |
| tcp.dstport | integer | destination TCP port | 8888 |
| tcp.flags | integer | TCP flags | 0x00000002 |
| frame_info.len | integer | sampled CSV column | 58 |
| ip.len | integer | sampled CSV column | 44 |
| label | string | attack class label | nmap_tcp_syn |
| ip | ip | sampled CSV column | 172.16.0.3 |
| frame_info.encap_type | integer | sampled CSV column | 1 |
| frame_info.number | integer | sampled CSV column | 20 |
| frame_info.cap_len | integer | sampled CSV column | 58 |
| eth.type | integer | sampled CSV column | 0x00000800 |
| ip.version | integer | sampled CSV column | 4 |
| ip.hdr_len | integer | sampled CSV column | 20 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | label in separate label CSV files; `attack_dataset.csv` has no label column |
| Label values | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 |
| Suitable for supervised learning | partial; requires IP join, and TEST must not be used for training |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | frame_info.time, frame_info.time_epoch |
| Time format | Wireshark timestamp string + epoch seconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected in the sample.

### Host Features
- direct syscall/process features were not detected.

### Network / Hybrid Features
- bytes/packet length from `frame_info.len`, `ip.len`, `tcp.len`;
- protocols and TCP flags;
- `ip.src`/`ip.dst` pairs and source/destination ports;
- packet inter-arrival times from `frame_info.time_epoch`;
- attack labels through an IP join;
- host + network correlation features if external metadata links these files to host traces.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | yes | packet CSV contains empty protocol/header fields |
| Unstable structure | yes | dataset CSV and label CSV files use different schemas |
| Mixed schemas | yes | one 41-column packet CSV and two 2-column label maps |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
Host TEST CSV is suitable for network/hybrid feature extraction, but it is not a single host telemetry CSV. Labels must be joined separately by IP for supervised evaluation; TEST data must not be used for training.

---

## Source: `json.md`

# Format Analysis: json

## 1. Purpose
Host TEST JSON files contain several malware sandbox telemetry schemas: event traces, file artifact maps, reboot events, task metadata, and large sandbox reports. The format is useful for sequence features, file-artifact features, and sandbox task context features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 7071 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\1808.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__1e940db677.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__3c66d805a1.json
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes, but not for every file |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | utf-8 |
| Nested structure | yes |
| Sampled files analyzed | 30 |
| Sample schemas | event_descriptor_json_lines: 1, file_artifact_json_lines: 8, reboot_event_json_lines: 4, multiline_json_document: 8, task_metadata_json: 9 |

## 5. Content Structure
The sample contains JSON Lines with process/API events (`I`, `T`, `t`, `h`, `args`), descriptor documents (`name`, `type`, `category`), file artifact maps (`path`, `pids`, `filepath`), reboot events, task metadata with `$dt` timestamps, and large multiline sandbox reports.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| I | int | event/descriptor id | 0 |
| name | unknown | event name | __process__ |
| type | unknown | event type | info |
| category | unknown | event category | __notification__ |
| args | list | arguments | ["is_success", "retval", "time_low", "time_high", "pid", "ppid", "module_path", "command_line", "is_64bit", "track", ... |
| T | int | sampled JSON field | 1556 |
| t | int | sampled JSON field | 0 |
| h | int | sampled JSON field | 0 |
| time | unknown | sampled JSON field | 18 |
| path | str | artifact path | shots/0001.jpg |
| pids | list | related process ids | [2548] |
| filepath | unknown | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| status | unknown | sampled JSON field | reported |
| filepath | str | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| filepath | NoneType | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| address | unknown | sampled JSON field |  |
| category | str | event category | __notification__ |
| type | str | event type | info |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent in sample |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` |
| Time format | numeric relative fields and ISO-like `$dt` |
| Can build sequences | yes |
| Can apply sliding windows | partial |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- API/syscall-like event frequencies by `I`/`name`;
- event n-grams and transitions;
- sandbox event categories;
- file artifact features from `path`, `filepath`, and `pids`;
- sandbox task duration and execution status;
- sequence features by JSONL event order.

### Network / Hybrid Features
- direct flow fields were not detected;
- correlation with CSV/pcap may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | yes | parse errors: 1 |
| Missing values | yes | `filepath`, `owner`, and `machine` may be null |
| Unstable structure | yes | several schemas share the same extension |
| Mixed schemas | yes | event, files, reboot, report, task |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
JSON is useful for feature extraction, but it needs a dedicated parser: some files are JSON Lines, some use Mongo-style `NumberLong(...)`, and some are large multiline reports. No explicit label field was found for TEST.

---

## Source: `log.md`

# Format Analysis: log

## 1. Purpose
Host TEST log files contain Cuckoo/analyzer sandbox execution logs. The format is useful for runtime event sequences, log levels, components, task ids, PIDs, and timing features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | log |
| Extension variants | .log |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 4086 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__13148e1b98.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__26c4060830.log
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, via regex fields |
| Header | no |
| Delimiter | custom log pattern |
| Encoding | utf-8 |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed log lines | 4834 |

## 5. Content Structure
Lines use `timestamp [component] LEVEL: message`. The sample includes analyzer events, Cuckoo scheduler events, sniffer startup, auxiliary modules, machine acquisition, processing, and runtime warnings/errors.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| timestamp | datetime string | event time | 2017-09-24 15:28:47,000 |
| component | string | logging component | analyzer |
| level | string | log level | DEBUG |
| message | string | event text | Starting analyzer from: C:\tmpptgfi_ |
| task_id | integer/string | task id extracted from message | 552 |
| pid | integer/string | PID extracted from message | 8727 |

### Frequent Components
| component | count |
|---|---:|
| cuckoo.core.resultserver | 1600 |
| analyzer | 1067 |
| cuckoo.core.guest | 1008 |
| cuckoo.core.plugins | 524 |
| modules.auxiliary.human | 461 |
| cuckoo.core.scheduler | 72 |
| cuckoo.machinery.virtualbox | 44 |
| lib.api.process | 15 |
| cuckoo.auxiliary.sniffer | 15 |
| cuckoo.processing.baseline | 14 |

### Log Levels
| level | count |
|---|---:|
| DEBUG | 3405 |
| INFO | 1242 |
| WARNING | 171 |
| ERROR | 16 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no without external labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | timestamp |
| Time format | `%Y-%m-%d %H:%M:%S,%f` |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- `level` and `component` frequencies;
- log event and message-prefix sequences;
- task lifecycle timings;
- warning/error counts;
- PID/task id activity counts.

### Network / Hybrid Features
- sniffer/pcap path indicators from Cuckoo messages;
- host+network correlation through task id and pcap path.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | required regex fields are populated in parsed lines |
| Unstable structure | no | the main pattern is stable |
| Mixed schemas | partial | analyzer and cuckoo components differ semantically |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | medium |

## 12. Conclusion
The format is ready for feature extraction as line-oriented sandbox runtime logs. Supervised learning requires external labels, but sequence/log-level/component features can be extracted directly.

---

## Source: `netflow_day.md`

# Format Analysis: netflow_day

## 1. Purpose
`netflow_day` in Host TEST contains large headerless CSV-like netflow files. The format is useful for network/hybrid features: flow duration, protocol, endpoints, ports, packets, and bytes.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | netflow_day |
| Extension variants | no extension; `netflow_day-*` names |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 2 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\netflow_day\netflow_day-02
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\netflow_day\netflow_day-90
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | yes |
| Header | no |
| Delimiter | comma |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 2 |
| Sample rows parsed | 2000 |

## 5. Content Structure
Rows describe LANL-like netflow events: `time,duration,src_host,dst_host,protocol,src_port,dst_port,src_packets,dst_packets,src_bytes,dst_bytes`. Hosts and some ports are anonymized (`Comp...`, `IP...`, `Port...`). Protocols in sample: 6: 1369, 17: 621, 1: 10.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| time | integer | flow start time | 118781 |
| duration | integer | flow duration | 5580 |
| src_host | anonymized_host | source host | Comp364445 |
| dst_host | anonymized_host | destination host | Comp547245 |
| protocol | integer | IP protocol number | 17 |
| src_port | anonymized_port | source port | Port05507 |
| dst_port | integer | destination port | Port46272 |
| src_packets | integer | source packets | 0 |
| dst_packets | integer | destination packets | 755065 |
| src_bytes | integer | source bytes | 0 |
| dst_bytes | integer | destination bytes | 1042329018 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no without external labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | time |
| Time format | numeric offset/second counter |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- DNS can be inferred indirectly from `dst_port=53`, but DNS payload is absent.

### Host Features
- host endpoint activity by `src_host`/`dst_host`;
- user-host features are absent.

### Network / Hybrid Features
- flow duration;
- bidirectional bytes/packets;
- protocol and ports;
- host fan-in/fan-out;
- time-window netflow activity;
- host + network correlation features.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | no empty cells in sample |
| Unstable structure | no | 11 columns in sample |
| Mixed schemas | no | both files use the same structure |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
`netflow_day` is ready for feature extraction as a large line-oriented network flow source. The pipeline must account for very large file sizes and the absence of embedded labels.

---

## Source: `txt.md`

# Format Analysis: txt

## 1. Purpose
Host TEST TXT files contain line-oriented Windows NT syscall/API traces in `key=value` format. The format is useful for syscall frequencies, n-grams, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 274419 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\name.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\NtSetEventBoostPriority__a1e94de9b9.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\ZwAccessCheckByTypeAndAuditAlarm__45f5f1fa41.txt
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, key=value |
| Header | no |
| Delimiter | comma + key=value |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed lines | 6901 |

## 5. Content Structure
The main schema is `Time`, `Pid`, `MethodName`, `ProcessName`, plus method-specific `argN` values. File names also encode the syscall method (`ZwAccessCheck__...txt`). Methods in sample include: NtSetEventBoostPriority, ZwAllocateVirtualMemory, ZwQueryInformationToken, ZwWaitForSingleObject, ZwReplyWaitReceivePort, ZwDuplicateObject, ZwPlugPlayControl, ZwQueryVolumeInformationFile. `name.txt` is a service file with executable path/pid metadata and does not follow the main schema.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| Time | integer | relative timestamp | 203913 |
| Pid | integer | process id | 1392 |
| MethodName | string | syscall/API method | NtSetEventBoostPriority |
| ProcessName | string | process path | \Device\HarddiskVolume1\WINDOWS\system32\svchost.exe |
| arg1 | integer | method-specific argument | 684 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no without external labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | Time |
| Time format | numeric relative timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- `MethodName` frequencies;
- syscall/API n-grams;
- call transitions;
- syscall trace length;
- `argN` parameters;
- activity by `Pid` and `ProcessName`;
- command/path tokens from `ProcessName`.

### Network / Hybrid Features
- direct flow/network fields were not detected;
- correlation with network data may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | partial | `argN` fields are method-specific |
| Unstable structure | partial | `argN` set depends on method |
| Mixed schemas | partial | `name.txt` is service metadata, most files are syscall traces |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for syscall/API sequence feature extraction. The pipeline must account for the very large file count, method-specific `argN` fields, and service `name.txt`.

---

## Source: `wls_day.md`

# Format Analysis: wls_day

## 1. Purpose
`wls_day` in Host TEST contains Windows security log events in JSON Lines format. The format is useful for Event ID frequencies, authentication/logon sequences, parent-child process chains, and user-host interaction features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | wls_day |
| Extension variants | no extension; `wls_day-*` names |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 3 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-01
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-57
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-85
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | no, JSON Lines |
| Header | no |
| Delimiter | newline-delimited JSON |
| Encoding | utf-8 |
| Nested structure | no |
| Sampled files analyzed | 3 |
| Parsed records | 3000 |

## 5. Content Structure
Rows contain Windows security events: `EventID`, `UserName`, `LogHost`, `DomainName`, `LogonID`, `Time`, process fields, and authentication/logon fields. EventID distribution in sample: 4688: 1474, 4624: 609, 4672: 375, 4634: 234, 4776: 126, 4769: 101, 4768: 47, 4648: 31, 4625: 3.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| Time | int | event time offset | 1 |
| EventID | int | Windows Event ID | 4688 |
| UserName | str | user/account | Comp607982$ |
| LogHost | str | logging host | Comp607982 |
| DomainName | str | domain | Domain001 |
| LogonID | str | logon session id | 0x3e7 |
| LogonType | int | logon type | 5 |
| LogonTypeDescription | str | event-specific field | Service |
| AuthenticationPackage | str | auth package | Negotiate |
| Source | str | source host | Comp939275 |
| ProcessName | str | process name | svchost.exe |
| ProcessID | str | event-specific field | 0x1418 |
| ParentProcessName | str | parent process | services |
| ParentProcessID | str | event-specific field | 0x2ac |
| Destination | str | event-specific field | Comp457365 |
| FailureReason | str | event-specific field | Unknown user name or bad password. |
| ServiceName | str | event-specific field | AppService |
| Status | str | event-specific field | 0x0 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no without external labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | Time |
| Time format | numeric day/second offset |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- Event ID frequencies;
- login success/failure and logon type ratios;
- user-host interaction frequency;
- authentication package distribution;
- parent-child process chains;
- process name frequencies;
- event sequences and sliding windows.

### Network / Hybrid Features
- source/loghost interaction graph from `Source` and `LogHost`;
- host + network correlation features when external netflow data is available.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | partial | fields depend on EventID |
| Unstable structure | partial | different EventIDs expose different fields |
| Mixed schemas | partial | 4624/4634/4672/4688 and other events |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
`wls_day` is ready for Windows/Sysmon-like authentication and process event feature extraction. The pipeline must account for huge file sizes and event-specific schemas.

# Format Analysis: netflow_day

## 1. Purpose
`netflow_day` in Host VALIDATION contains large headerless CSV-like netflow files. The format is useful for network/hybrid features: flow duration, protocol, endpoints, ports, packets, and bytes.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | netflow_day |
| Extension variants | no extension; `netflow_day-*` names |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 2 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-02
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-90
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

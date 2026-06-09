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

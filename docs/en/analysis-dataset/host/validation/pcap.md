# Format Analysis: pcap

## 1. Purpose
`.pcap` in Host VALIDATION contains classic pcap packet capture files for network attack scenarios. The format is useful for network/hybrid feature extraction, but full extraction requires a dedicated packet parser.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 1 |

## 3. Example Files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcap\pcap_log4shell_cve2021_44228_jndi_reference_2022-05-11181020.pcap
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcap global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | 1 |
| Sample packets | 67 |

## 5. Content Structure
Files contain packet metadata and payload bytes in a classic pcap container. The sample contains Ethernet/IPv4 packets; IP protocol distribution: 6: 65. File names identify attack scenarios and can be used as external context, but there is no embedded label field.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 262144 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 443 |
| udp_dst_port | integer | sample UDP destination port |  |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected inside the file |
| Suitable for supervised learning | partial; only with external labels/scenario from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet header ts_sec/ts_usec |
| Time format | pcap timestamp seconds + micro/nanoseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- DNS query/response features after packet parsing.

### Host Features
- direct host syscall/EventID fields are absent.

### Network / Hybrid Features
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports and TCP flags;
- DNS/LDAP/SMB/DCERPC indicators after parsing;
- host + network correlation by scenario/file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | pcap headers are available |
| Unstable structure | no | classic pcap magic/header is stable |
| Mixed schemas | no | one binary capture format |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
`.pcap` is useful for network/hybrid feature extraction, but a dedicated pcap parser or Scapy/tshark-like tooling is required for the production pipeline. Source VALIDATION files were not modified.

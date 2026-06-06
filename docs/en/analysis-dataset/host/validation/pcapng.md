# Format Analysis: pcapng

## 1. Purpose
`.pcapng` in Host VALIDATION contains next-generation packet capture files with a block-based structure. The format is useful for network/hybrid feature extraction, but packet and flow extraction requires a dedicated pcapng parser.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcapng |
| Extension variants | .pcapng |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 5 |

## 3. Example Files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\aadinternals_export_adfsdatabaseconfig_remotely_20210427020247.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\empire_ninjacopy_dumping_ntds_dit_file.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\pcap_log4shell_cve2021_44228_java_serialized_2022-05-13045800.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_create_2020-12-1907003032.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_modification_2020-12-1907505969.pcapng
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcapng Section Header Block |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, typed blocks |
| Sampled files analyzed | 5 |
| Sample blocks | 1676 |
| Sample packets | 1664 |

## 5. Content Structure
Files contain Section Header, Interface Description, and Enhanced Packet blocks. Block type distribution in the sample: 0x00000006: 1664, 0x0a0d0d0a: 5, 0x00000001: 5, 0x00000005: 2. IP protocol distribution after limited packet parsing: 6: 1353, 17: 56, 1: 40, 2: 16.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| section_magic | hex | pcapng Section Header Block magic | 0a0d0d0a |
| byte_order_magic | hex | endianness marker | 4d3c2b1a |
| version | string | pcapng version | 1.0 |
| link_type | integer | interface link-layer type | 1 |
| block_type | hex | pcapng block type | 0x00000006 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 3389 |
| udp_dst_port | integer | sample UDP destination port | 53 |

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
| Field name | Enhanced Packet Block timestamp_high/timestamp_low |
| Time format | pcapng interface timestamp resolution |
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
| Missing values | no | pcapng headers/blocks are available |
| Unstable structure | no | Section Header Block is stable |
| Mixed schemas | no | one binary capture format |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
`.pcapng` is useful for network/hybrid feature extraction, but a dedicated pcapng parser or Scapy/tshark-like tooling is required for the production pipeline. Source VALIDATION files were not modified.

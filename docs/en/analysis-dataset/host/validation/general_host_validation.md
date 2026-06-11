# General Host Validation Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/host/validation`.

## Source documents

- `README.md`
- `cap.md`
- `csv.md`
- `json.md`
- `netflow_day.md`
- `pcap.md`
- `pcapng.md`
- `txt.md`
- `wls_day.md`

---

## Source: `README.md`

# Dataset File Content Analysis (Host VALIDATION)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| cap | 44 | no | yes | NEEDS_CUSTOM_PARSER | cap.md |
| csv | 6 | no | yes | READY_FOR_FEATURE_EXTRACTION | csv.md |
| json | 130 | no | yes | READY_FOR_FEATURE_EXTRACTION | json.md |
| netflow_day | 2 | no | yes | READY_FOR_FEATURE_EXTRACTION | netflow_day.md |
| pcap | 1 | no | yes | NEEDS_CUSTOM_PARSER | pcap.md |
| pcapng | 5 | no | yes | NEEDS_CUSTOM_PARSER | pcapng.md |
| txt | 6495 | no | yes | READY_FOR_FEATURE_EXTRACTION | txt.md |
| wls_day | 3 | no | yes | READY_FOR_FEATURE_EXTRACTION | wls_day.md |

---

## Source: `cap.md`

# Format Analysis: cap

## 1. Purpose
`.cap` in Host VALIDATION contains classic pcap packet capture files for network attack scenarios. The format is useful for network/hybrid feature extraction, but full extraction requires a dedicated packet parser.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | cap |
| Extension variants | .cap |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 44 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_copy_smb_CreateRequest_2020-09-22145302.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_executeexcel4macro_allowed_2020-09-17174542.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_iertutil_dll_hijack_WORKSTATION5_2020-10-09183000.cap
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
| Sampled files analyzed | 30 |
| Sample packets | 10258 |

## 5. Content Structure
Files contain packet metadata and payload bytes in a classic pcap container. The sample contains Ethernet/IPv4 packets; IP protocol distribution: 6: 10148, 17: 110. File names identify attack scenarios and can be used as external context, but there is no embedded label field.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 65535 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 80 |
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
| Corrupted files | yes | parse errors: 6 |
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
`.cap` is useful for network/hybrid feature extraction, but a dedicated pcap parser or Scapy/tshark-like tooling is required for the production pipeline. Source VALIDATION files were not modified.

---

## Source: `csv.md`

# Format Analysis: csv

## 1. Purpose
Host VALIDATION CSV files contain scenario run metadata: image, scenario name, exploit execution flag, and timing parameters. The format is suitable for validation/evaluation labels and context features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 6 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__02fd419ec8.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__0f6fa8a7a1.csv
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | yes |
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8 |
| Nested structure | no |
| Sample rows | 6000 |

## 5. Content Structure
`runs*.csv` files describe validation scenarios: `image_name`, `scenario_name`, binary `is_executing_exploit`, `warmup_time`, `recording_time`, and `exploit_start_time`.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| image_name | string | container/image identifier | victim_bruteforce:latest |
| scenario_name | string | scenario id | crashing_hamilton_4459 |
| is_executing_exploit | boolean | binary exploit label | False |
| warmup_time | integer | warmup seconds | 10 |
| recording_time | integer | recording seconds | 35 |
| exploit_start_time | integer | exploit start offset | -1 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | is_executing_exploit |
| Label values | False: 5813, True: 187 |
| Suitable for supervised learning | yes, as validation labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | warmup_time, recording_time, exploit_start_time |
| Time format | seconds/relative offsets |
| Can build sequences | no |
| Can apply sliding windows | no |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- scenario/image context;
- exploit flag;
- recording duration and exploit start offset.

### Network / Hybrid Features
- correlation key through scenario/image for packet captures.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | no gaps in core sample fields |
| Unstable structure | no | stable header |
| Mixed schemas | no | all files are `runs*.csv` |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
CSV is ready as validation metadata and label/context feature source. Source datasets were not modified.

---

## Source: `json.md`

# Format Analysis: json

## 1. Purpose
Host VALIDATION JSON files contain Windows Security/Sysmon/Eventlog events in JSON Lines format. The format is useful for Event ID, process, command-line, authentication, and host activity features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 130 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\aadinternals_export_adfsdatabaseconfig_remotely_2021-04-27040833.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_bitsadmin_download_psh_script_2020-10-2302365189.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_lsass_memory_dumpert_syscalls_2020-10-1822561997.json
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
| Nested structure | yes |
| Parsed records | 19930 |

## 5. Content Structure
Contains Windows/Sysmon events: `EventID`, `SourceName`, `Channel`, `Hostname`, `TimeCreated`, `@timestamp`, `CommandLine`, and process/user/security fields. EventID sample: 10: 5590, 7: 2793, 12: 2404, 13: 1055, 4658: 989, 5156: 867, 800: 609, 4103: 553, 4656: 531, 5158: 510, 4690: 469, 5447: 436, 4663: 353, 23: 320, 4703: 278, 4799: 195, 3: 191, 9: 178, 11: 140, 4673: 135.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| EventID | int | Windows Event ID | 5058 |
| SourceName | str | event provider | Microsoft-Windows-Security-Auditing |
| Channel | str | event channel | Security |
| Hostname | str | host name | ADFS01.blacksmith.local |
| TimeCreated | str | event timestamp | 2021-04-27T04:07:34.160Z |
| @timestamp | str | event timestamp | 2021-04-27T04:07:34.160Z |
| CommandLine | str | process command line | 1432 |
| ProcessName | str | process name | C:\Windows\System32\wbem\WmiPrvSE.exe |
| SubjectUserName | str | user name | LOCAL SERVICE |
| @version | str | event field | 1 |
| AccessList | str | event field | %%1538\n				%%4432\n				%%4435\n				%%4436\n				 |
| AccessMask | str | event field | 0x20019 |
| AccessReason | str | event field | - |
| AccountDomain | str | event field | THESHIRE |
| AccountName | str | event field | SYSTEM |
| AccountType | str | event field | User |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | partial, with external labels from scenario/file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | TimeCreated, @timestamp |
| Time format | ISO-8601 / Windows timestamp string |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not the primary content.

### Host Features
- Event ID frequencies;
- process and command-line features;
- parent/child process fields where present;
- authentication/security event sequences;
- user-host interaction counts.

### Network / Hybrid Features
- SourceAddress/DestAddress/ports where present;
- correlation with packet captures by scenario.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | yes | parse/line errors: 5 |
| Missing values | partial | fields depend on EventID/provider |
| Unstable structure | partial | Security/Sysmon/Eventlog schemas differ |
| Mixed schemas | yes | different providers/channels |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
JSON is ready for feature extraction as JSON Lines Windows/Sysmon telemetry. Provider-specific fields and missing embedded labels must be handled explicitly.

---

## Source: `netflow_day.md`

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

---

## Source: `pcap.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcap\pcap_log4shell_cve2021_44228_jndi_reference_2022-05-11181020.pcap
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

---

## Source: `pcapng.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\aadinternals_export_adfsdatabaseconfig_remotely_20210427020247.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\empire_ninjacopy_dumping_ntds_dit_file.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\pcap_log4shell_cve2021_44228_java_serialized_2022-05-13045800.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_create_2020-12-1907003032.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_modification_2020-12-1907505969.pcapng
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

---

## Source: `txt.md`

# Format Analysis: txt

## 1. Purpose
Host VALIDATION TXT files contain line-oriented syscall traces in a sysdig-like format. The format is suitable for syscall frequencies, n-grams, call transitions, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 6495 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\abundant_bell_8827.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\attractive_northcutt_4737.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\blue_sammet_2668.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\chubby_mayer_3250.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\creamy_sinoussi_7198.txt
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, positional fields + syscall args |
| Header | no |
| Delimiter | whitespace + key=value args |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed lines | 30000 |
| Unmatched lines | 0 |

## 5. Content Structure
Rows use `event_index time cpu user_id process pid direction syscall args`. Syscalls in the sample include: read, munmap, close, mmap, open, mprotect, fstat, newfstatat, switch, write. Top processes: apache2, pstoedit, java, puma, mysqld, gs, python3, <NA>, server.rb:358, reactor.rb:249.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| EventIndex | integer | event sequence number | 13 |
| Time | string | event timestamp | 01:44:52.778494980 |
| Cpu | integer | CPU id | 4 |
| UserId | integer | user id | 101 |
| ProcessName | string | process name | mysqld |
| Pid | integer | process id | 25413 |
| Direction | string | syscall enter/exit | < |
| MethodName | string | syscall name | select |
| Args | string | raw syscall arguments | res=0 |
| arg_addr | string | syscall argument key | addr |
| arg_args | string | syscall argument key | args |
| arg_argument | string | syscall argument key | argument |
| arg_cgroups | string | syscall argument key | cgroups |
| arg_charset | string | syscall argument key | charset |

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
| Time format | HH:MM:SS.nanoseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not directly represented.

### Host Features
- `MethodName` frequencies;
- syscall n-grams and transitions;
- syscall trace length;
- direction `<`/`>` for enter/exit events;
- syscall arguments from `key=value` suffixes;
- activity by `Pid`, `ProcessName`, `UserId`, and `Cpu`.

### Network / Hybrid Features
- network syscalls such as `recvfrom`, `sendto`, `connect`, and `accept`;
- socket arguments from syscall suffixes;
- correlation with packet/netflow data by scenario/file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | partial | args are syscall-specific |
| Unstable structure | partial | suffix args vary by syscall |
| Mixed schemas | no | sample follows one sysdig-like trace schema |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for feature extraction as a line-oriented syscall trace. The pipeline must stream files and account for the large file count and size.

---

## Source: `wls_day.md`

# Format Analysis: wls_day

## 1. Purpose
`wls_day` in Host VALIDATION contains Windows security log events in JSON Lines format. The format is useful for Event ID frequencies, authentication/logon sequences, parent-child process chains, and user-host interaction features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | wls_day |
| Extension variants | no extension; `wls_day-*` names |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 3 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-01
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-57
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-85
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

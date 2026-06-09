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

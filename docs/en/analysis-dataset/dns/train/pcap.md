# Format Analysis: pcap

## 1. Purpose
DNS TRAIN PCAP files contain packet capture traffic for benign, malware, phishing, and spam classes. The format is needed for DNS query/response parsing, packet/flow features, and validation of CSV-derived features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
| File count | 4 |

## 3. Example Files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\benign.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\malware.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\phishing.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\spam.pcap
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcap/pcapng global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | 4 |
| Sample packets | 2000 |

## 5. Content Structure
Containers in the sample: classic_pcap: 3, pcapng: 1. IP protocol distribution: 17: 2000. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: 1000.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| container_variant | string | classic pcap or pcapng | classic_pcap |
| magic | hex | capture signature | 0a0d0d0a |
| ip_protocol | integer | IP protocol | 17 |
| udp_dst_port | integer | UDP destination port sample | 53 |
| tcp_dst_port | integer | TCP destination port sample |  |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name |
| Label values | benign, malware, phishing, spam |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet timestamp |
| Time format | pcap seconds/usec or pcapng timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- query name, query length, subdomain depth;
- qtype/qclass;
- response size, TTL, answer count;
- NXDOMAIN/RCODE distribution;
- inter-query intervals.

### Network / Hybrid Features
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- correlation with CSV domain/IP features.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | packet headers are available |
| Unstable structure | partial | `.pcap` bucket contains classic pcap and pcapng |
| Mixed schemas | yes | parser must support both containers |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN pcap is useful for network/DNS feature extraction, but the production pipeline must use a packet parser that supports both classic pcap and pcapng.

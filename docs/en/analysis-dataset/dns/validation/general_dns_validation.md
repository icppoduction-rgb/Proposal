# General DNS Validation Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/dns/validation`.

## Source documents

- `README.md`
- `pcap.md`
- `txt.md`

---

## Source: `README.md`

# Dataset File Content Analysis (DNS VALIDATION)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| pcap | 5 | yes | no | NEEDS_CUSTOM_PARSER | pcap.md |
| txt | 3 | yes | no | READY_FOR_FEATURE_EXTRACTION | txt.md |

---

## Source: `pcap.md`

# Format Analysis: pcap

## 1. Purpose
DNS VALIDATION PCAP files contain raw packet capture traffic for DNS amplification attack / benign validation scenarios. The format is needed for packet-level DNS features, network aggregates, and downstream feature extraction checks.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | VALIDATION |
| File count | 5 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack__f291ed87a1.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign1.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign__60a57c3a63.pcap
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
| Sampled files analyzed | 5 |
| Sample packets | 2500 |

## 5. Content Structure
Containers in the sample: classic_pcap: 5. IP protocol distribution: 17: 2500. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: 754.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| container_variant | string | classic pcap or pcapng | classic_pcap |
| magic | hex | capture signature | d4c3b2a1 |
| ip_protocol | integer | IP protocol | 17 |
| udp_dst_port | integer | UDP destination port sample | 53 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name |
| Label values | attack, benign |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet timestamp |
| Time format | pcap seconds/usec |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- qname, qtype/qclass, response size;
- DNS amplification query/response ratios;
- RCODE/NXDOMAIN distribution;
- TTL and answer count;
- inter-query intervals.

### Network / Hybrid Features
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- attack/benign label from file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | packet headers are available |
| Unstable structure | no | sample contains classic pcap |
| Mixed schemas | no | one container type in sample |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
DNS VALIDATION pcap is useful for validating a DNS amplification detection pipeline, but production processing must use a packet parser with DNS protocol decoding.

---

## Source: `txt.md`

# Format Analysis: txt

## 1. Purpose
DNS VALIDATION TXT files contain domain lists for DNS/domain feature extraction, enrichment, and validation scenarios without packet parsing.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | yes |
| Host | no |
| Roles | VALIDATION |
| File count | 3 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\benign_domains.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains__bdb83c6bf8.txt
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | newline |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 3 |
| Sample lines | 10955 |

## 5. Content Structure
Files are domain lists: one domain entry per line. Class hints from file names: unknown: 2, benign: 1. Domain-like lines in sample: 10955.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| domain | domain | domain name | computerweekly.com |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name / class_hint |
| Label values | unknown, benign |
| Suitable for supervised learning | partial, only after explicitly assigning class semantics |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | no |
| Field name | - |
| Time format | - |
| Can build sequences | no |
| Can apply sliding windows | no |

## 9. Potential Feature Extraction
### DNS Features
- domain and subdomain length;
- label count;
- TLD/SLD;
- entropy and character composition;
- domain reputation/enrichment features.

### Network / Hybrid Features
- join with pcap-derived DNS queries;
- allow/block list intersection checks.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | non-empty lines in sample: 10955 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | blank lines in sample: 0 |
| Unstable structure | no | newline-separated domain list |
| Mixed schemas | no | all sampled rows are domain-like |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | medium |

## 12. Conclusion
DNS VALIDATION txt is ready for feature extraction as domain lists; supervised evaluation requires explicit semantics for `unknown` lists.

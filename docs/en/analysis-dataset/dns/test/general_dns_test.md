# General DNS Test Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/dns/test`.

## Source documents

- `README.md`
- `csv.md`
- `pcap.csv.md`
- `pcap.md`

---

## Source: `README.md`

# Dataset File Content Analysis (DNS TEST)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | 1 | yes | no | PARTIALLY_SUPPORTED | csv.md |
| pcap | 0 | yes | no | BROKEN_OR_EMPTY | pcap.md |
| pcap.csv | 0 | yes | no | BROKEN_OR_EMPTY | pcap.csv.md |

---

## Source: `csv.md`

# Format Analysis: csv

## 1. Purpose
The DNS TEST CSV file contains a large tabular sample of DNS/domain features for final pipeline validation. The dataset must not be used for training; it is intended for normalization, feature-engineering, and inference-readiness checks.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | yes |
| Host | no |
| Roles | TEST |
| File count | 1 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TEST\csv\dataset.csv
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
| Sampled files analyzed | 1 |
| Parsed rows in sample | 1000 |

## 5. Content Structure
Detected schema: headerless_dns_test_feature_table: 1. The sample shows a fixed 22-column structure: IP/domain/timestamp/flag/query-domain followed by numeric DNS/domain features. Because the file has no header, an explicit positional schema is required before production normalization.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| source_ip | domain_or_ip | source/client IP address | 186.169.253.58 |
| resolver_or_parent_domain | domain_or_ip | parent domain or DNSBL service domain | surbl.org |
| timestamp_ms | integer | event timestamp in Unix milliseconds | 1624438272607 |
| label_or_flag | boolean | boolean flag in the row | False |
| query_domain | domain_or_ip | queried domain or DNSBL lookup name | h.surbl.org |
| feature_01 | integer | numeric DNS/domain feature | 1 |
| feature_02 | integer | numeric DNS/domain feature | 1 |
| feature_03 | integer | numeric DNS/domain feature | 0 |
| feature_04 | integer | numeric DNS/domain feature | 0 |
| feature_05 | float | numeric DNS/domain feature | -0.0 |
| feature_06 | float | numeric DNS/domain feature | 0.0 |
| feature_07 | float | numeric DNS/domain feature | 0.0 |
| feature_08 | float | numeric DNS/domain feature | 0.0 |
| feature_09 | float | numeric DNS/domain feature | 0.0 |
| feature_10 | float | numeric DNS/domain feature | 3.4444444444444446 |
| feature_11 | float | numeric DNS/domain feature | 9.59311095410544 |
| feature_12 | integer | numeric DNS/domain feature | 1.5 |
| feature_13 | float | numeric DNS/domain feature | 1.5811388300841898 |
| feature_14 | float | numeric DNS/domain feature | 468.75 |
| feature_15 | float | numeric DNS/domain feature | 0.4444444444444444 |
| feature_16 | float | numeric DNS/domain feature | 0.25849625007211563 |
| feature_17 | float | numeric DNS/domain feature | 0.81743691684035 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | `label_or_flag` |
| Label values | boolean-like flag in sample |
| Suitable for supervised learning | no, this is the TEST role; use for evaluation only |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | `timestamp_ms` |
| Time format | Unix milliseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes, after chunked sorting/grouping |

## 9. Potential Feature Extraction
### DNS Features
- source/client IP;
- parent/resolver domain;
- queried DNSBL/domain name;
- timestamp-derived windows;
- numeric domain/DNS ratios and aggregate features;
- entropy-like and distribution-like numeric features.

### Network / Hybrid Features
- grouping by `source_ip`;
- query sequences by `timestamp_ms`;
- correlation of query-domain with DNSBL/provider domain.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample contains rows |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | missing cells in sample: 0 |
| Unstable structure | no | inconsistent column files: 0 |
| Mixed schemas | no | one CSV file |
| Oversized file | yes | file is about 8.25 GB; streaming/chunked reader is required |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Separate parser required | no, but an explicit positional schema is required |
| Processing priority | medium |

## 12. Conclusion
DNS TEST csv is suitable for downstream processing, but because it is headerless and large it should be read as a stream and normalized through a fixed 22-column positional schema.

---

## Source: `pcap.csv.md`

# Format Analysis: pcap.csv

## 1. Purpose
DNS TEST `pcap.csv` files should contain tabular features extracted from pcap traffic for feature-extraction validation without reparsing raw captures. At this stage, no such files are present in the TEST dataset.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap.csv |
| Extension variants | .pcap.csv |
| DNS | yes |
| Host | no |
| Roles | TEST |
| File count | 0 |

## 3. Example Files
```text
no files in `TEST.pcap.csv`
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes, if files are added |
| Tabular structure | expected CSV |
| Header | unavailable |
| Delimiter | comma, if files are added |
| Encoding | utf-8-compatible, if files are added |
| Nested structure | no |
| Sampled files analyzed | 0 |
| Parsed rows | 0 |

## 5. Content Structure
Content analysis is not possible: No TEST/pcap.csv bucket is present in sort-path-dns-file.json.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| - | - | no files to analyze | - |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | no |

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
- unavailable without pcap.csv files.

### Network / Hybrid Features
- unavailable without pcap.csv files.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | yes | bucket is missing or empty |
| Corrupted files | no | no files exist |
| Missing values | no | no files exist |
| Unstable structure | no | no files exist |
| Mixed schemas | no | no files exist |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | BROKEN_OR_EMPTY |
| Separate parser required | no, while no input files exist |
| Processing priority | low |

## 12. Conclusion
DNS TEST `pcap.csv` cannot be analyzed at this stage because the prepared JSON has no `TEST.pcap.csv` bucket. The reason is recorded in the summary and report.

---

## Source: `pcap.md`

# Format Analysis: pcap

## 1. Purpose
DNS TEST PCAP files should contain raw packet capture traffic for packet-level DNS feature extraction validation. At this stage, no such files are present in the prepared TEST dataset.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | TEST |
| File count | 0 |

## 3. Example Files
```text
no files in `TEST.pcap`
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | unavailable |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | packet records, if files are added |
| Sampled files analyzed | 0 |
| Sample packets | 0 |

## 5. Content Structure
Content analysis is not possible: No TEST/pcap bucket is present in sort-path-dns-file.json.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| - | - | no files to analyze | - |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | no |

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
- unavailable without raw pcap files.

### Network / Hybrid Features
- unavailable without raw pcap files.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | yes | bucket is missing or empty |
| Corrupted files | no | no files exist |
| Missing values | no | no files exist |
| Unstable structure | no | no files exist |
| Mixed schemas | no | no files exist |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | BROKEN_OR_EMPTY |
| Separate parser required | no, while no input files exist |
| Processing priority | low |

## 12. Conclusion
DNS TEST pcap cannot be analyzed at this stage because the prepared JSON has no `TEST.pcap` bucket. The reason is recorded in the summary and report.

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

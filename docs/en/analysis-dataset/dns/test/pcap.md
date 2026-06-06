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

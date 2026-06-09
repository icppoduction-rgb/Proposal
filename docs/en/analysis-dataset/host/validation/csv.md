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

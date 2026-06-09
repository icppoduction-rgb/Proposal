# Format Analysis: csv

## 1. Purpose
Host TRAIN CSV files are used as the main source of system telemetry (date/time, process, syscall/event, attack labels) for downstream feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 101 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\1.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\10.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\11.csv
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | yes |
| Header | not always (utility files with header are present) |
| Delimiter | , (30) |
| Encoding | cp1252 (1), utf-8-sig (29) |
| Nested structure | no |
| Sampled files | 30 |
| Sampled rows | 29027 |

## 5. Semantic structure
The primary CSV block (numbered files `1.csv`..`99.csv`) contains host telemetry: event date/time, process identifier, process path, syscall/event field, and attack label fields.
Additional utility CSV files are present:
- `feature_descr.csv` - feature dictionary;
- `ground_truth.csv` - attack scenario ground-truth details.

## 6. Detected fields / columns
| Column | Inferred name | Type | Example value |
|---|---|---|---|
| 1 | date | date | 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016 |
| 2 | time | time | 2:45:01, 2:45:06, 2:45:06, 2:45:35, 2:45:44 |
| 3 | process_id | integer | 1830, 1804, 2133, 4528, 1847 |
| 4 | path | string | /sbin/upstart-dbus-bridge, /bin/dbus-daemon, /usr/lib/i386-linux-gnu/gconf/gconfd-2, /usr/bin/python3.4, /usr/bin/ibus-daemon |
| 5 | sys_call | integer | 142, 256, 168, 3, 102 |
| 6 | event_id | integer | 45354, 45352, 45372, 39459, 37263 |
| 7 | category_7 | string | normal, normal, normal, normal, normal |
| 8 | category_8 | string | normal, normal, normal, normal, normal |
| 9 | label | integer | 0, 0, 0, 0, 0 |

### Extra mapping from feature_descr.csv
| Feature No | Feature Name | Type |
|---|---|---|
| 1 | date | date |
| 2 | time | time |
| 3 | pro_id | number |
| 4 | path | nominal |
| 5 | sys_call | number |
| 6 | event_id | number |
| 7 | attack_cat | nominal |
| 8 | attack_subcat | nominal |
| 9 | label | binary |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | column(s) 7, 8, 9 |
| Label values | normal/attack categories plus binary label (0/1) |
| Suitable for supervised learning | yes |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | date + time (separate columns) |
| Timestamp format | date + time in separate columns (dd/mm/yyyy and HH:MM:SS) |
| Timezone | not specified |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable for this format scope.

### Host features
- `sys_call`/`event_id` frequency features;
- syscall n-grams and transition features;
- process-centric sequence features (`process_id` + `path`);
- attack category/subcategory distributions;
- binary target from label (0/1).

### Network / hybrid features
- `ground_truth.csv` can provide additional context indicators (attack campaign and IP pair metadata) for host+network correlation.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted/unreadable files | no | encoding/read errors: 0 |
| Missing values | yes | found in sample: 66 |
| Unstable structure | yes | observed 9/7/5-column schemas |
| Mixed schemas | yes | special schema files: 2 |
| Duplicate rows | yes | found in sample: 13 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/csv` is suitable for host-side feature extraction and supervised learning. The main data flow has a stable 9-column schema, but utility files (`feature_descr.csv`, `ground_truth.csv`) use separate schemas, so partial parser branching is required for full-format coverage.

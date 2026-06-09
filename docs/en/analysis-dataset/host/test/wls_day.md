# Format Analysis: wls_day

## 1. Purpose
`wls_day` in Host TEST contains Windows security log events in JSON Lines format. The format is useful for Event ID frequencies, authentication/logon sequences, parent-child process chains, and user-host interaction features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | wls_day |
| Extension variants | no extension; `wls_day-*` names |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 3 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-01
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-57
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-85
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

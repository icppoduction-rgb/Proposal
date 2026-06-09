# Format Analysis: txt

## 1. Purpose
Host TEST TXT files contain line-oriented Windows NT syscall/API traces in `key=value` format. The format is useful for syscall frequencies, n-grams, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 274419 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\name.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\NtSetEventBoostPriority__a1e94de9b9.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\ZwAccessCheckByTypeAndAuditAlarm__45f5f1fa41.txt
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, key=value |
| Header | no |
| Delimiter | comma + key=value |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed lines | 6901 |

## 5. Content Structure
The main schema is `Time`, `Pid`, `MethodName`, `ProcessName`, plus method-specific `argN` values. File names also encode the syscall method (`ZwAccessCheck__...txt`). Methods in sample include: NtSetEventBoostPriority, ZwAllocateVirtualMemory, ZwQueryInformationToken, ZwWaitForSingleObject, ZwReplyWaitReceivePort, ZwDuplicateObject, ZwPlugPlayControl, ZwQueryVolumeInformationFile. `name.txt` is a service file with executable path/pid metadata and does not follow the main schema.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| Time | integer | relative timestamp | 203913 |
| Pid | integer | process id | 1392 |
| MethodName | string | syscall/API method | NtSetEventBoostPriority |
| ProcessName | string | process path | \Device\HarddiskVolume1\WINDOWS\system32\svchost.exe |
| arg1 | integer | method-specific argument | 684 |

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
| Time format | numeric relative timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- `MethodName` frequencies;
- syscall/API n-grams;
- call transitions;
- syscall trace length;
- `argN` parameters;
- activity by `Pid` and `ProcessName`;
- command/path tokens from `ProcessName`.

### Network / Hybrid Features
- direct flow/network fields were not detected;
- correlation with network data may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | partial | `argN` fields are method-specific |
| Unstable structure | partial | `argN` set depends on method |
| Mixed schemas | partial | `name.txt` is service metadata, most files are syscall traces |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for syscall/API sequence feature extraction. The pipeline must account for the very large file count, method-specific `argN` fields, and service `name.txt`.

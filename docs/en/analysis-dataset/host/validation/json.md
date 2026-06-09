# Format Analysis: json

## 1. Purpose
Host VALIDATION JSON files contain Windows Security/Sysmon/Eventlog events in JSON Lines format. The format is useful for Event ID, process, command-line, authentication, and host activity features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 130 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\aadinternals_export_adfsdatabaseconfig_remotely_2021-04-27040833.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_bitsadmin_download_psh_script_2020-10-2302365189.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_lsass_memory_dumpert_syscalls_2020-10-1822561997.json
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
| Nested structure | yes |
| Parsed records | 19930 |

## 5. Content Structure
Contains Windows/Sysmon events: `EventID`, `SourceName`, `Channel`, `Hostname`, `TimeCreated`, `@timestamp`, `CommandLine`, and process/user/security fields. EventID sample: 10: 5590, 7: 2793, 12: 2404, 13: 1055, 4658: 989, 5156: 867, 800: 609, 4103: 553, 4656: 531, 5158: 510, 4690: 469, 5447: 436, 4663: 353, 23: 320, 4703: 278, 4799: 195, 3: 191, 9: 178, 11: 140, 4673: 135.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| EventID | int | Windows Event ID | 5058 |
| SourceName | str | event provider | Microsoft-Windows-Security-Auditing |
| Channel | str | event channel | Security |
| Hostname | str | host name | ADFS01.blacksmith.local |
| TimeCreated | str | event timestamp | 2021-04-27T04:07:34.160Z |
| @timestamp | str | event timestamp | 2021-04-27T04:07:34.160Z |
| CommandLine | str | process command line | 1432 |
| ProcessName | str | process name | C:\Windows\System32\wbem\WmiPrvSE.exe |
| SubjectUserName | str | user name | LOCAL SERVICE |
| @version | str | event field | 1 |
| AccessList | str | event field | %%1538\n				%%4432\n				%%4435\n				%%4436\n				 |
| AccessMask | str | event field | 0x20019 |
| AccessReason | str | event field | - |
| AccountDomain | str | event field | THESHIRE |
| AccountName | str | event field | SYSTEM |
| AccountType | str | event field | User |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | partial, with external labels from scenario/file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | TimeCreated, @timestamp |
| Time format | ISO-8601 / Windows timestamp string |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not the primary content.

### Host Features
- Event ID frequencies;
- process and command-line features;
- parent/child process fields where present;
- authentication/security event sequences;
- user-host interaction counts.

### Network / Hybrid Features
- SourceAddress/DestAddress/ports where present;
- correlation with packet captures by scenario.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | yes | parse/line errors: 5 |
| Missing values | partial | fields depend on EventID/provider |
| Unstable structure | partial | Security/Sysmon/Eventlog schemas differ |
| Mixed schemas | yes | different providers/channels |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
JSON is ready for feature extraction as JSON Lines Windows/Sysmon telemetry. Provider-specific fields and missing embedded labels must be handled explicitly.

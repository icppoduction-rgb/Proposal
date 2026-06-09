# Format Analysis: json

## 1. Purpose
Host TEST JSON files contain several malware sandbox telemetry schemas: event traces, file artifact maps, reboot events, task metadata, and large sandbox reports. The format is useful for sequence features, file-artifact features, and sandbox task context features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 7071 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\1808.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__1e940db677.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__3c66d805a1.json
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes, but not for every file |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | utf-8 |
| Nested structure | yes |
| Sampled files analyzed | 30 |
| Sample schemas | event_descriptor_json_lines: 1, file_artifact_json_lines: 8, reboot_event_json_lines: 4, multiline_json_document: 8, task_metadata_json: 9 |

## 5. Content Structure
The sample contains JSON Lines with process/API events (`I`, `T`, `t`, `h`, `args`), descriptor documents (`name`, `type`, `category`), file artifact maps (`path`, `pids`, `filepath`), reboot events, task metadata with `$dt` timestamps, and large multiline sandbox reports.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| I | int | event/descriptor id | 0 |
| name | unknown | event name | __process__ |
| type | unknown | event type | info |
| category | unknown | event category | __notification__ |
| args | list | arguments | ["is_success", "retval", "time_low", "time_high", "pid", "ppid", "module_path", "command_line", "is_64bit", "track", ... |
| T | int | sampled JSON field | 1556 |
| t | int | sampled JSON field | 0 |
| h | int | sampled JSON field | 0 |
| time | unknown | sampled JSON field | 18 |
| path | str | artifact path | shots/0001.jpg |
| pids | list | related process ids | [2548] |
| filepath | unknown | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| status | unknown | sampled JSON field | reported |
| filepath | str | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| filepath | NoneType | original file path | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| address | unknown | sampled JSON field |  |
| category | str | event category | __notification__ |
| type | str | event type | info |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent in sample |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` |
| Time format | numeric relative fields and ISO-like `$dt` |
| Can build sequences | yes |
| Can apply sliding windows | partial |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- API/syscall-like event frequencies by `I`/`name`;
- event n-grams and transitions;
- sandbox event categories;
- file artifact features from `path`, `filepath`, and `pids`;
- sandbox task duration and execution status;
- sequence features by JSONL event order.

### Network / Hybrid Features
- direct flow fields were not detected;
- correlation with CSV/pcap may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | yes | parse errors: 1 |
| Missing values | yes | `filepath`, `owner`, and `machine` may be null |
| Unstable structure | yes | several schemas share the same extension |
| Mixed schemas | yes | event, files, reboot, report, task |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
JSON is useful for feature extraction, but it needs a dedicated parser: some files are JSON Lines, some use Mongo-style `NumberLong(...)`, and some are large multiline reports. No explicit label field was found for TEST.

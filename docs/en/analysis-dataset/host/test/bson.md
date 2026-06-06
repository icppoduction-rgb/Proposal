# Format Analysis: bson

## 1. Purpose
Host TEST BSON files contain binary process behaviour and system/API event traces. The format is useful as a source of ordered host-event sequences for later feature engineering; TEST data must not be used for model training.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | bson |
| Extension variants | .bson |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 9005 |

## 3. Example Files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\bson\1000.bson
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\bson\120__7c0ccef00c.bson
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\bson\1372__1d508ea03c.bson
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes |
| Sampled files analyzed | 30 |
| Sample BSON documents parsed | 2325 |

## 5. Content Structure
The sample is a stream of consecutive BSON documents. It contains descriptor documents with `name`, `type`, `category`, `args`, `flags_value`, and `flags_bitmask`, plus event documents with `I`, `T`, `t`, `h`, and an `args` array. Semantically this is malware behaviour / host telemetry: process events, Windows API or syscall-like operations, call arguments, module paths, command lines, and nested flag structures.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| I | int32 | descriptor/event identifier | 0 |
| name | string | API/syscall-like event name | __process__ |
| type | string | descriptor document type | info |
| category | string | event category | __notification__ |
| args | array | argument values or argument-name array | nested_array |
| T | int32 | numeric thread/process context id | 1916 |
| t | int32 | relative time/order counter | 0 |
| h | int64 | additional numeric counter/handle | 0 |
| args.0 | string | argument values or argument-name array | is_success |
| args.1 | string | argument values or argument-name array | retval |
| flags_value.information_class.0 | array | nested flag values | nested_array |
| flags_value.information_class.0.0 | int32 | nested flag values | 0 |
| flags_value.information_class.0.1 | string | nested flag values | KeyValueBasicInformation |
| args.2 | int32 | argument values or argument-name array | -832834880 |
| args.3 | string | argument values or argument-name array | time_high |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required if available |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | BSON document order, numeric `t`/`h` event fields |
| Time format | relative numeric counters; timezone not specified |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable to this Host format.

### Host Features
- API/syscall event frequencies by `I` and descriptor `name`;
- event n-grams and transitions;
- trace length and event density;
- `args` features, including process paths, module basenames, and command line tokens;
- parent-child/process context from process notification documents;
- descriptor `category` frequencies;
- command line and module path entropy.

### Network / Hybrid Features
- no direct network flow fields were detected;
- correlation with network datasets may be possible through an external sample/file id if project metadata provides one.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors in sample: 0 |
| Missing values | yes | BSON arrays contain null/empty positions in `args` |
| Unstable structure | yes | descriptor and event documents use different schemas |
| Mixed schemas | yes | a single stream mixes metadata/descriptor/event documents |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
The format is valuable for host behaviour sequence features, but it is not ready for generic tabular reading. A dedicated BSON parser is required to map descriptor documents to event documents by `I`, expand `args`, and preserve event order. No explicit label field was found in the TEST/BSON sample.

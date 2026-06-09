# Format Analysis: journal

## 1. Purpose
`journal` in `TRAIN` is a binary systemd journal container and requires a dedicated parser to extract events.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | journal |
| Extension variants | `.journal` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 17 |

## 3. Example files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__1451ab8d6a.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__53b42cbacc.journal
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | binary signature present |
| Delimiter | none |
| Encoding | unknown (container bytes) |
| Nested structure | yes |
| Sampled files | 17 |
| Files with `LPKSHHRH` signature | 17 |

## 5. Semantic structure
The format matches a systemd journal-like binary container. Direct text parsing is not reliable.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| header_signature_hex | string | first 8-byte signature | `4c504b5348485248` |
| size_bytes | integer | file size | `16777216` |
| printable_ratio | float | printable bytes ratio in sampled header | `0.12` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | no |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | no |
| Field name | - |
| Timestamp format | not directly readable |
| Sequence-ready | no |
| Sliding-window-ready | no |

## 9. Potential feature extraction signals
### DNS features
- not applicable at raw binary stage.

### Host features
- journal size and growth pace;
- entry count and event families after `journalctl` parsing.

### Network / hybrid features
- correlation of extracted journal events with network/process logs after normalization.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse/read errors: 0 |
| Missing values | no | binary container format |
| Unstable structure | no | binary and text-like files mixed |
| Mixed schemas | no | binary_like=17, text_like=0 |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/journal` should not be handled as a plain text log. A dedicated parser/toolchain for systemd journal is required for reliable feature extraction.

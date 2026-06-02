# Format Analysis: ghc

## 1. Purpose
`ghc` in `TRAIN` contains text trace sequences in `<module>+0x<offset>` form for host process behavior analysis.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | ghc |
| Extension variants | `.ghc`, `.GHC` |
| DNS | no |
| Host | yes |
| Roles | TRAIN |
| File count | 56158 |

## 3. Example files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-0.GHC
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-1.GHC
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-10.GHC
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | space |
| Encoding | utf-8 (30) |
| Nested structure | no |
| Sampled files | 30 |
| Sampled lines | 30 |
| Token count | 6000 |
| Valid trace tokens | 6000 |

## 5. Semantic structure
Data is represented as trace-like token sequences containing:
- module name (`kernel32.dll`);
- hexadecimal offset (`0xb50b`);
- token order in a line as behavioral sequence.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| trace.token | string | raw trace token | `kernel32.dll+0xb50b` |
| trace.module | string | module/library name | `kernel32.dll` |
| trace.offset_hex | string | hexadecimal offset | `0xb50b` |
| filename.scenario_tag | string | filename scenario prefix | `S1-1-Full` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | partially |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | no |
| Field name | - |
| Timestamp format | not present |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- module frequency counts (`top_modules_detected`);
- trace token n-grams;
- transitions between modules;
- trace sequence length;
- per-module offset distributions.

### Network / hybrid features
- correlate trace sequences with process/network activity by host and external timestamps.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | invalid tokens: 0 |
| Unstable structure | no | non-trace tokens exist |
| Mixed schemas | no | includes tokens outside `<module>+0x<hex>` |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Needs dedicated parser | yes |
| Processing priority | high |

## 12. Conclusion
`TRAIN/ghc` is usable for feature extraction only through a dedicated specialized parser.
Token-per-file stats (sample): min=200.0, max=200.0, avg=200.0.

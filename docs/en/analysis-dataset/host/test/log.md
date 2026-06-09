# Format Analysis: log

## 1. Purpose
Host TEST log files contain Cuckoo/analyzer sandbox execution logs. The format is useful for runtime event sequences, log levels, components, task ids, PIDs, and timing features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | log |
| Extension variants | .log |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | 4086 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__13148e1b98.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__26c4060830.log
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, via regex fields |
| Header | no |
| Delimiter | custom log pattern |
| Encoding | utf-8 |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed log lines | 4834 |

## 5. Content Structure
Lines use `timestamp [component] LEVEL: message`. The sample includes analyzer events, Cuckoo scheduler events, sniffer startup, auxiliary modules, machine acquisition, processing, and runtime warnings/errors.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| timestamp | datetime string | event time | 2017-09-24 15:28:47,000 |
| component | string | logging component | analyzer |
| level | string | log level | DEBUG |
| message | string | event text | Starting analyzer from: C:\tmpptgfi_ |
| task_id | integer/string | task id extracted from message | 552 |
| pid | integer/string | PID extracted from message | 8727 |

### Frequent Components
| component | count |
|---|---:|
| cuckoo.core.resultserver | 1600 |
| analyzer | 1067 |
| cuckoo.core.guest | 1008 |
| cuckoo.core.plugins | 524 |
| modules.auxiliary.human | 461 |
| cuckoo.core.scheduler | 72 |
| cuckoo.machinery.virtualbox | 44 |
| lib.api.process | 15 |
| cuckoo.auxiliary.sniffer | 15 |
| cuckoo.processing.baseline | 14 |

### Log Levels
| level | count |
|---|---:|
| DEBUG | 3405 |
| INFO | 1242 |
| WARNING | 171 |
| ERROR | 16 |

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
| Field name | timestamp |
| Time format | `%Y-%m-%d %H:%M:%S,%f` |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- `level` and `component` frequencies;
- log event and message-prefix sequences;
- task lifecycle timings;
- warning/error counts;
- PID/task id activity counts.

### Network / Hybrid Features
- sniffer/pcap path indicators from Cuckoo messages;
- host+network correlation through task id and pcap path.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | required regex fields are populated in parsed lines |
| Unstable structure | no | the main pattern is stable |
| Mixed schemas | partial | analyzer and cuckoo components differ semantically |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | medium |

## 12. Conclusion
The format is ready for feature extraction as line-oriented sandbox runtime logs. Supervised learning requires external labels, but sequence/log-level/component features can be extracted directly.

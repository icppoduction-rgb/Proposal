# Format Analysis: txt

## 1. Purpose
Host VALIDATION TXT files contain line-oriented syscall traces in a sysdig-like format. The format is suitable for syscall frequencies, n-grams, call transitions, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | 6495 |

## 3. Example Files
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\abundant_bell_8827.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\attractive_northcutt_4737.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\blue_sammet_2668.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\chubby_mayer_3250.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\creamy_sinoussi_7198.txt
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | partial, positional fields + syscall args |
| Header | no |
| Delimiter | whitespace + key=value args |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 30 |
| Parsed lines | 30000 |
| Unmatched lines | 0 |

## 5. Content Structure
Rows use `event_index time cpu user_id process pid direction syscall args`. Syscalls in the sample include: read, munmap, close, mmap, open, mprotect, fstat, newfstatat, switch, write. Top processes: apache2, pstoedit, java, puma, mysqld, gs, python3, <NA>, server.rb:358, reactor.rb:249.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| EventIndex | integer | event sequence number | 13 |
| Time | string | event timestamp | 01:44:52.778494980 |
| Cpu | integer | CPU id | 4 |
| UserId | integer | user id | 101 |
| ProcessName | string | process name | mysqld |
| Pid | integer | process id | 25413 |
| Direction | string | syscall enter/exit | < |
| MethodName | string | syscall name | select |
| Args | string | raw syscall arguments | res=0 |
| arg_addr | string | syscall argument key | addr |
| arg_args | string | syscall argument key | args |
| arg_argument | string | syscall argument key | argument |
| arg_cgroups | string | syscall argument key | cgroups |
| arg_charset | string | syscall argument key | charset |

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
| Time format | HH:MM:SS.nanoseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not directly represented.

### Host Features
- `MethodName` frequencies;
- syscall n-grams and transitions;
- syscall trace length;
- direction `<`/`>` for enter/exit events;
- syscall arguments from `key=value` suffixes;
- activity by `Pid`, `ProcessName`, `UserId`, and `Cpu`.

### Network / Hybrid Features
- network syscalls such as `recvfrom`, `sendto`, `connect`, and `accept`;
- socket arguments from syscall suffixes;
- correlation with packet/netflow data by scenario/file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | partial | args are syscall-specific |
| Unstable structure | partial | suffix args vary by syscall |
| Mixed schemas | no | sample follows one sysdig-like trace schema |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for feature extraction as a line-oriented syscall trace. The pipeline must stream files and account for the large file count and size.

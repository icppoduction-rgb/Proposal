# Общий анализ validation datasets Host

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/host/validation`.

## Состав исходных документов

- `README.md`
- `cap.md`
- `csv.md`
- `json.md`
- `netflow_day.md`
- `pcap.md`
- `pcapng.md`
- `txt.md`
- `wls_day.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (Host VALIDATION)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| cap | 44 | нет | да | NEEDS_CUSTOM_PARSER | cap.md |
| csv | 6 | нет | да | READY_FOR_FEATURE_EXTRACTION | csv.md |
| json | 130 | нет | да | READY_FOR_FEATURE_EXTRACTION | json.md |
| netflow_day | 2 | нет | да | READY_FOR_FEATURE_EXTRACTION | netflow_day.md |
| pcap | 1 | нет | да | NEEDS_CUSTOM_PARSER | pcap.md |
| pcapng | 5 | нет | да | NEEDS_CUSTOM_PARSER | pcapng.md |
| txt | 6495 | нет | да | READY_FOR_FEATURE_EXTRACTION | txt.md |
| wls_day | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | wls_day.md |

---

## Источник: `cap.md`

# Анализ формата: cap

## 1. Назначение
`.cap` в Host VALIDATION содержит classic pcap packet capture файлы с сетевым трафиком attack-сценариев. Формат нужен для network/hybrid feature extraction, но требует специализированного packet parser для полного извлечения признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | cap |
| Варианты расширения | .cap |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 44 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_copy_smb_CreateRequest_2020-09-22145302.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_executeexcel4macro_allowed_2020-09-17174542.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_iertutil_dll_hijack_WORKSTATION5_2020-10-09183000.cap
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcap global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | 30 |
| Sample packets | 10258 |

## 5. Содержательная структура
Файлы содержат packet metadata и payload bytes в classic pcap container. В sample обнаружены Ethernet/IPv4 пакеты; IP protocol distribution: 6: 10148, 17: 110. Имена файлов указывают на attack scenario и могут использоваться как внешний контекст, но не как встроенное label-поле.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 65535 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 80 |
| udp_dst_port | integer | sample UDP destination port | 53 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены внутри файла |
| Можно использовать для supervised learning | частично; только при внешней разметке/сценарии из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet header ts_sec/ts_usec |
| Формат времени | pcap timestamp seconds + micro/nanoseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS query/response признаки после packet parsing.

### Host-признаки
- прямые host syscall/EventID признаки отсутствуют.

### Network / hybrid-признаки
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports, TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | да | parse errors: 6 |
| Missing values | нет | pcap headers доступны |
| Нестабильная структура | нет | classic pcap magic/header стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.cap` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcap parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

---

## Источник: `csv.md`

# Анализ формата: csv

## 1. Назначение
CSV-файлы Host VALIDATION содержат metadata запусков сценариев: образ, имя сценария, флаг эксплуатации и временные параметры. Формат пригоден для validation/evaluation разметки и контекстных признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 6 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__02fd419ec8.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__0f6fa8a7a1.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-строк | 6000 |

## 5. Содержательная структура
Файлы `runs*.csv` описывают validation сценарии: `image_name`, `scenario_name`, бинарный флаг `is_executing_exploit`, `warmup_time`, `recording_time`, `exploit_start_time`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| image_name | string | container/image identifier | victim_bruteforce:latest |
| scenario_name | string | scenario id | crashing_hamilton_4459 |
| is_executing_exploit | boolean | binary exploit label | False |
| warmup_time | integer | warmup seconds | 10 |
| recording_time | integer | recording seconds | 35 |
| exploit_start_time | integer | exploit start offset | -1 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | is_executing_exploit |
| Значения label | False: 5813, True: 187 |
| Можно использовать для supervised learning | да, как validation labels |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | warmup_time, recording_time, exploit_start_time |
| Формат времени | seconds/relative offsets |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- scenario/image context;
- exploit flag;
- recording duration and exploit start offset.

### Network / hybrid-признаки
- correlation key через scenario/image для packet captures.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | sample без пропусков в основных полях |
| Нестабильная структура | нет | header стабилен |
| Смешанные схемы | нет | все файлы `runs*.csv` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV готов к использованию как validation metadata и источник label/context признаков. Исходные датасеты не изменялись.

---

## Источник: `json.md`

# Анализ формата: json

## 1. Назначение
JSON-файлы Host VALIDATION содержат Windows Security/Sysmon/Eventlog события в JSON Lines формате. Формат нужен для Event ID, process, command-line, authentication и host activity признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json |
| Варианты расширения | .json |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 130 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\aadinternals_export_adfsdatabaseconfig_remotely_2021-04-27040833.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_bitsadmin_download_psh_script_2020-10-2302365189.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_lsass_memory_dumpert_syscalls_2020-10-1822561997.json
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет, JSON Lines |
| Заголовок | нет |
| Разделитель | newline-delimited JSON |
| Кодировка | utf-8 |
| Вложенная структура | да |
| Parsed records | 19930 |

## 5. Содержательная структура
Содержит Windows/Sysmon events: `EventID`, `SourceName`, `Channel`, `Hostname`, `TimeCreated`, `@timestamp`, `CommandLine`, process/user/security fields. EventID sample: 10: 5590, 7: 2793, 12: 2404, 13: 1055, 4658: 989, 5156: 867, 800: 609, 4103: 553, 4656: 531, 5158: 510, 4690: 469, 5447: 436, 4663: 353, 23: 320, 4703: 278, 4799: 195, 3: 191, 9: 178, 11: 140, 4673: 135.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
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

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | частично, при внешней разметке из scenario/file name |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | TimeCreated, @timestamp |
| Формат времени | ISO-8601 / Windows timestamp string |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не являются основным содержимым.

### Host-признаки
- Event ID frequencies;
- process and command-line features;
- parent/child process fields where present;
- authentication/security event sequences;
- user-host interaction counts.

### Network / hybrid-признаки
- SourceAddress/DestAddress/ports fields where present;
- correlation with packet captures by scenario.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | да | parse/line errors: 5 |
| Missing values | частично | поля зависят от EventID/provider |
| Нестабильная структура | частично | Security/Sysmon/Eventlog схемы отличаются |
| Смешанные схемы | да | разные providers/channels |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
JSON готов к feature extraction как JSON Lines Windows/Sysmon telemetry. Нужно учитывать provider-specific поля и отсутствие встроенных labels.

---

## Источник: `netflow_day.md`

# Анализ формата: netflow_day

## 1. Назначение
`netflow_day` в Host VALIDATION содержит большие CSV-like netflow-файлы без заголовка. Формат нужен для извлечения network/hybrid признаков: длительность flow, протокол, endpoints, ports, packets и bytes.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | netflow_day |
| Варианты расширения | без расширения; имя `netflow_day-*` |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 2 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-02
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-90
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | нет |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 2 |
| Sample-строк разобрано | 2000 |

## 5. Содержательная структура
Строки описывают netflow-события LANL-like формата: `time,duration,src_host,dst_host,protocol,src_port,dst_port,src_packets,dst_packets,src_bytes,dst_bytes`. Хосты и часть портов анонимизированы (`Comp...`, `IP...`, `Port...`). Протоколы в sample: 6: 1369, 17: 621, 1: 10.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| time | integer | время начала flow | 118781 |
| duration | integer | длительность flow | 5580 |
| src_host | anonymized_host | source host | Comp364445 |
| dst_host | anonymized_host | destination host | Comp547245 |
| protocol | integer | номер IP protocol | 17 |
| src_port | anonymized_port | source port | Port05507 |
| dst_port | integer | destination port | Port46272 |
| src_packets | integer | packets от source | 0 |
| dst_packets | integer | packets от destination | 755065 |
| src_bytes | integer | bytes от source | 0 |
| dst_bytes | integer | bytes от destination | 1042329018 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет без внешних меток |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | time |
| Формат времени | числовой offset/second counter |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS можно косвенно выделять по `dst_port=53`, но DNS payload отсутствует.

### Host-признаки
- активность host endpoint по `src_host`/`dst_host`;
- user-host признаки отсутствуют.

### Network / hybrid-признаки
- длительность flow;
- bytes/packets в обоих направлениях;
- protocol и ports;
- fan-in/fan-out по host;
- временные окна netflow activity;
- host + network correlation features.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | в sample пустые ячейки не обнаружены |
| Нестабильная структура | нет | 11 колонок в sample |
| Смешанные схемы | нет | оба файла имеют одинаковую структуру |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
`netflow_day` готов к feature extraction как большой line-oriented network flow источник. Нужно учитывать очень большой размер файлов и отсутствие встроенных labels.

---

## Источник: `pcap.md`

# Анализ формата: pcap

## 1. Назначение
`.pcap` в Host VALIDATION содержит classic pcap packet capture файлы с сетевым трафиком attack-сценариев. Формат нужен для network/hybrid feature extraction, но требует специализированного packet parser для полного извлечения признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcap\pcap_log4shell_cve2021_44228_jndi_reference_2022-05-11181020.pcap
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcap global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | 1 |
| Sample packets | 67 |

## 5. Содержательная структура
Файлы содержат packet metadata и payload bytes в classic pcap container. В sample обнаружены Ethernet/IPv4 пакеты; IP protocol distribution: 6: 65. Имена файлов указывают на attack scenario и могут использоваться как внешний контекст, но не как встроенное label-поле.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 262144 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 443 |
| udp_dst_port | integer | sample UDP destination port |  |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены внутри файла |
| Можно использовать для supervised learning | частично; только при внешней разметке/сценарии из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet header ts_sec/ts_usec |
| Формат времени | pcap timestamp seconds + micro/nanoseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS query/response признаки после packet parsing.

### Host-признаки
- прямые host syscall/EventID признаки отсутствуют.

### Network / hybrid-признаки
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports, TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | pcap headers доступны |
| Нестабильная структура | нет | classic pcap magic/header стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.pcap` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcap parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

---

## Источник: `pcapng.md`

# Анализ формата: pcapng

## 1. Назначение
`.pcapng` в Host VALIDATION содержит packet capture файлы нового поколения с block-based структурой. Формат полезен для network/hybrid feature extraction, но требует специализированного pcapng parser для извлечения пакетов и потоков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcapng |
| Варианты расширения | .pcapng |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 5 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\aadinternals_export_adfsdatabaseconfig_remotely_20210427020247.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\empire_ninjacopy_dumping_ntds_dit_file.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\pcap_log4shell_cve2021_44228_java_serialized_2022-05-13045800.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_create_2020-12-1907003032.pcapng
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_modification_2020-12-1907505969.pcapng
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcapng Section Header Block |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, typed blocks |
| Sample-файлов проанализировано | 5 |
| Sample blocks | 1676 |
| Sample packets | 1664 |

## 5. Содержательная структура
Файлы содержат Section Header, Interface Description и Enhanced Packet blocks. Распределение block types в sample: 0x00000006: 1664, 0x0a0d0d0a: 5, 0x00000001: 5, 0x00000005: 2. IP protocol distribution после ограниченного packet parsing: 6: 1353, 17: 56, 1: 40, 2: 16.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| section_magic | hex | pcapng Section Header Block magic | 0a0d0d0a |
| byte_order_magic | hex | endianness marker | 4d3c2b1a |
| version | string | pcapng version | 1.0 |
| link_type | integer | interface link-layer type | 1 |
| block_type | hex | pcapng block type | 0x00000006 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 3389 |
| udp_dst_port | integer | sample UDP destination port | 53 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены внутри файла |
| Можно использовать для supervised learning | частично; только при внешней разметке/сценарии из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Enhanced Packet Block timestamp_high/timestamp_low |
| Формат времени | pcapng interface timestamp resolution |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS query/response признаки после packet parsing.

### Host-признаки
- прямые host syscall/EventID признаки отсутствуют.

### Network / hybrid-признаки
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports и TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | pcapng headers/blocks доступны |
| Нестабильная структура | нет | Section Header Block стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.pcapng` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcapng parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

---

## Источник: `txt.md`

# Анализ формата: txt

## 1. Назначение
TXT-файлы Host VALIDATION содержат line-oriented syscall traces в sysdig-like формате. Формат пригоден для частот syscall, n-grams, переходов между вызовами, process activity и sequence features.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 6495 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\abundant_bell_8827.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\attractive_northcutt_4737.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\blue_sammet_2668.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\chubby_mayer_3250.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\creamy_sinoussi_7198.txt
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | частично, positional fields + syscall args |
| Заголовок | нет |
| Разделитель | whitespace + key=value args |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Parsed lines | 30000 |
| Unmatched lines | 0 |

## 5. Содержательная структура
Строки имеют структуру `event_index time cpu user_id process pid direction syscall args`. В sample встречаются syscalls: read, munmap, close, mmap, open, mprotect, fstat, newfstatat, switch, write. Основные процессы: apache2, pstoedit, java, puma, mysqld, gs, python3, <NA>, server.rb:358, reactor.rb:249.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
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

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет без внешней разметки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Time |
| Формат времени | HH:MM:SS.nanoseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- напрямую не представлены.

### Host-признаки
- `MethodName` frequencies;
- syscall n-grams и transitions;
- syscall trace length;
- direction `<`/`>` для enter/exit событий;
- аргументы syscall из `key=value` suffix;
- активность по `Pid`, `ProcessName`, `UserId`, `Cpu`.

### Network / hybrid-признаки
- network syscalls (`recvfrom`, `sendto`, `connect`, `accept`) и socket args;
- корреляция с packet/netflow данными по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | частично | args зависят от syscall |
| Нестабильная структура | частично | suffix args различаются по syscall |
| Смешанные схемы | нет | sample соответствует sysdig-like trace |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
TXT готов к feature extraction как line-oriented syscall trace. Pipeline должен читать файлы streaming-режимом и учитывать большой размер/количество файлов.

---

## Источник: `wls_day.md`

# Анализ формата: wls_day

## 1. Назначение
`wls_day` в Host VALIDATION содержит Windows security log events в JSON Lines формате. Формат нужен для Event ID частот, authentication/logon последовательностей, parent-child process chains и user-host interaction признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | wls_day |
| Варианты расширения | без расширения; имя `wls_day-*` |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-01
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-57
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\wls_day\wls_day-85
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет, JSON Lines |
| Заголовок | нет |
| Разделитель | newline-delimited JSON |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 3 |
| Parsed records | 3000 |

## 5. Содержательная структура
Строки содержат Windows security events: `EventID`, `UserName`, `LogHost`, `DomainName`, `LogonID`, `Time`, process fields и authentication/logon fields. EventID distribution in sample: 4688: 1474, 4624: 609, 4672: 375, 4634: 234, 4776: 126, 4769: 101, 4768: 47, 4648: 31, 4625: 3.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| Time | int | время события | 1 |
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

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет без внешних меток |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Time |
| Формат времени | числовой day/second offset |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты Event ID;
- login success/failure и logon type ratios;
- user-host interaction frequency;
- authentication package distribution;
- parent-child process chains;
- process name frequencies;
- event sequences и sliding windows.

### Network / hybrid-признаки
- source/loghost interaction graph по `Source` и `LogHost`;
- host + network correlation features при наличии внешних netflow данных.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | частично | поля зависят от EventID |
| Нестабильная структура | частично | разные EventID имеют разные поля |
| Смешанные схемы | частично | 4624/4634/4672/4688 и другие события |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
`wls_day` готов к feature extraction для Windows/Sysmon-like authentication и process event признаков. Нужно учитывать огромный размер файлов и event-specific schema.

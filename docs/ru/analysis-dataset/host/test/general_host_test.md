# Общий анализ test datasets Host

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/host/test`.

## Состав исходных документов

- `README.md`
- `bson.md`
- `csv.md`
- `json.md`
- `log.md`
- `netflow_day.md`
- `txt.md`
- `wls_day.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (Host TEST)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| bson | 9005 | нет | да | NEEDS_CUSTOM_PARSER | bson.md |
| csv | 3 | нет | да | PARTIALLY_SUPPORTED | csv.md |
| json | 7071 | нет | да | NEEDS_CUSTOM_PARSER | json.md |
| log | 4086 | нет | да | READY_FOR_FEATURE_EXTRACTION | log.md |
| netflow_day | 2 | нет | да | READY_FOR_FEATURE_EXTRACTION | netflow_day.md |
| txt | 274419 | нет | да | READY_FOR_FEATURE_EXTRACTION | txt.md |
| wls_day | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | wls_day.md |

---

## Источник: `bson.md`

# Анализ формата: bson

## 1. Назначение
BSON-файлы в Host TEST содержат бинарные трассы поведения процессов и системных/API-событий. Формат нужен проекту как источник последовательностей host-событий для дальнейшего feature engineering; для обучения TEST-набор не используется.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | bson |
| Варианты расширения | .bson |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 9005 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\1000.bson
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\120__7c0ccef00c.bson
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\bson\1372__1d508ea03c.bson
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да |
| Sample-файлов проанализировано | 30 |
| Sample BSON-документов разобрано | 2325 |

## 5. Содержательная структура
Sample показывает BSON-поток из последовательных документов. Встречаются descriptor-документы с полями `name`, `type`, `category`, `args`, `flags_value`, `flags_bitmask`, а также event-документы с `I`, `T`, `t`, `h` и массивом `args`. По содержанию это malware behaviour / host telemetry traces: события процессов, Windows API/syscall-like операции, аргументы вызовов, пути модулей, command line и вложенные структуры flags.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| I | int32 | идентификатор descriptor/event | 0 |
| name | string | имя API/syscall-like события | __process__ |
| type | string | тип descriptor-документа | info |
| category | string | категория события | __notification__ |
| args | array | массив аргументов или имён аргументов | nested_array |
| T | int32 | числовой идентификатор thread/process контекста | 1916 |
| t | int32 | относительный временной/порядковый счётчик | 0 |
| h | int64 | дополнительный числовой счётчик/handle | 0 |
| args.0 | string | массив аргументов или имён аргументов | is_success |
| args.1 | string | массив аргументов или имён аргументов | retval |
| flags_value.information_class.0 | array | вложенные значения flags | nested_array |
| flags_value.information_class.0.0 | int32 | вложенные значения flags | 0 |
| flags_value.information_class.0.1 | string | вложенные значения flags | KeyValueBasicInformation |
| args.2 | int32 | массив аргументов или имён аргументов | -832834880 |
| args.3 | string | массив аргументов или имён аргументов | time_high |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет для TEST; нужны внешние метки, если они существуют |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | порядок BSON-документов, числовые `t`/`h` в event-записях |
| Формат времени | относительные числовые счетчики; timezone не указан |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо для этого Host-формата.

### Host-признаки
- частоты API/syscall-событий по `I` и descriptor `name`;
- n-grams и переходы между событиями;
- длина trace и плотность событий;
- признаки аргументов `args`, включая пути процессов, module basename, command line;
- parent-child/process context признаки из process notification документов;
- частоты категорий descriptor `category`;
- энтропия и токены command line / module path.

### Network / hybrid-признаки
- напрямую network flow-поля не обнаружены;
- возможна корреляция с network-датасетами по внешнему sample/file id, если такая связь есть в метаданных проекта.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors in sample: 0 |
| Missing values | да | в BSON встречаются null/пустые позиции в `args` |
| Нестабильная структура | да | descriptor и event-документы имеют разные схемы |
| Смешанные схемы | да | один поток содержит metadata/descriptor/event документы |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
Формат полезен для дальнейшего pipeline как источник host behaviour sequence features, но не готов к универсальному табличному чтению. Нужен отдельный BSON parser, который сопоставляет descriptor-документы с event-документами по `I`, разворачивает `args` и сохраняет порядок событий. Явных label-полей в TEST/BSON sample не найдено.

---

## Источник: `csv.md`

# Анализ формата: csv

## 1. Назначение
CSV-файлы Host TEST содержат packet/network metadata и отдельные CSV-карты меток атак. Формат нужен для анализа сетевого поведения и возможной host+network корреляции, но TEST-набор не должен использоваться для обучения.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_dataset.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels_sbseg.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8/utf-8-sig по sample |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 3 |

## 5. Содержательная структура
`attack_dataset.csv` содержит packet metadata: frame time, epoch time, IP/TCP поля, адреса, порты, flags, длины и checksum. `attack_labels.csv` и `attack_labels_sbseg.csv` содержат соответствие `ip -> label` для атак вроде nmap scan. Это network/hybrid-структура внутри Host TEST bucket.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| frame_info.time | string | время пакета | Dec 31, 1969 21:03:41.953641000 -03 |
| frame_info.time_epoch | float | epoch seconds | 221.953641000 |
| ip.src | ip | source IP | 172.16.0.3 |
| ip.dst | ip | destination IP | 10.10.10.10 |
| ip.proto | integer | колонка sample CSV | 6 |
| tcp.srcport | integer | source TCP port | 62218 |
| tcp.dstport | integer | destination TCP port | 8888 |
| tcp.flags | integer | TCP flags | 0x00000002 |
| frame_info.len | integer | колонка sample CSV | 58 |
| ip.len | integer | колонка sample CSV | 44 |
| label | string | метка класса атаки | nmap_tcp_syn |
| ip | ip | колонка sample CSV | 172.16.0.3 |
| frame_info.encap_type | integer | колонка sample CSV | 1 |
| frame_info.number | integer | колонка sample CSV | 20 |
| frame_info.cap_len | integer | колонка sample CSV | 58 |
| eth.type | integer | колонка sample CSV | 0x00000800 |
| ip.version | integer | колонка sample CSV | 4 |
| ip.hdr_len | integer | колонка sample CSV | 20 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | label в отдельных label CSV; `attack_dataset.csv` label не содержит |
| Значения label | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 |
| Можно использовать для supervised learning | частично; нужен join по IP и TEST нельзя применять для обучения |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | frame_info.time, frame_info.time_epoch |
| Формат времени | строка Wireshark timestamp + epoch seconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля в sample не обнаружены.

### Host-признаки
- прямые syscall/process признаки не обнаружены.

### Network / hybrid-признаки
- bytes/packet length по `frame_info.len`, `ip.len`, `tcp.len`;
- протоколы и TCP flags;
- пары `ip.src`/`ip.dst` и source/destination ports;
- временные интервалы между пакетами по `frame_info.time_epoch`;
- attack label через join по IP;
- host + network correlation features при наличии внешней связи с host traces.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | да | в packet CSV есть пустые protocol/header поля |
| Нестабильная структура | да | dataset CSV и label CSV имеют разные схемы |
| Смешанные схемы | да | 41-колоночный packet CSV и 2-колоночные label maps |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV в Host TEST пригоден для network/hybrid feature extraction, но не является единым host telemetry CSV. Для supervised evaluation метки нужно присоединять отдельно по IP; TEST-данные не использовать для обучения.

---

## Источник: `json.md`

# Анализ формата: json

## 1. Назначение
JSON-файлы Host TEST содержат несколько схем malware sandbox telemetry: event traces, file artifact maps, reboot events, task metadata и большие sandbox reports. Формат нужен для построения sequence-признаков, признаков файловых артефактов и контекстных признаков sandbox-задач.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json |
| Варианты расширения | .json |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 7071 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\1808.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__1e940db677.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\json\files__3c66d805a1.json
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да, но не для всех файлов |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none |
| Кодировка | utf-8 |
| Вложенная структура | да |
| Sample-файлов проанализировано | 30 |
| Схемы sample | event_descriptor_json_lines: 1, file_artifact_json_lines: 8, reboot_event_json_lines: 4, multiline_json_document: 8, task_metadata_json: 9 |

## 5. Содержательная структура
В sample обнаружены JSON Lines с событиями процессов/API (`I`, `T`, `t`, `h`, `args`), descriptor-документы (`name`, `type`, `category`), карты файловых артефактов (`path`, `pids`, `filepath`), reboot-события, task metadata с `$dt` timestamp и большие многострочные sandbox reports.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| I | int | идентификатор event/descriptor | 0 |
| name | unknown | имя события | __process__ |
| type | unknown | тип события | info |
| category | unknown | категория события | __notification__ |
| args | list | аргументы | ["is_success", "retval", "time_low", "time_high", "pid", "ppid", "module_path", "command_line", "is_64bit", "track", ... |
| T | int | поле sample JSON | 1556 |
| t | int | поле sample JSON | 0 |
| h | int | поле sample JSON | 0 |
| time | unknown | поле sample JSON | 18 |
| path | str | путь артефакта | shots/0001.jpg |
| pids | list | связанные process ids | [2548] |
| filepath | unknown | исходный путь файла | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| status | unknown | поле sample JSON | reported |
| filepath | str | исходный путь файла | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| filepath | NoneType | исходный путь файла | c:\docume~1\nunes\locals~1\temp\tmprywxxi |
| address | unknown | поле sample JSON |  |
| category | str | категория события | __notification__ |
| type | str | тип события | info |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует в sample |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет для TEST; нужны внешние метки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` |
| Формат времени | числовые относительные поля и ISO-like `$dt` |
| Можно строить sequence | да |
| Можно применять sliding window | частично |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля не обнаружены.

### Host-признаки
- частоты API/syscall-like событий по `I`/`name`;
- n-grams и переходы событий;
- категории sandbox events;
- признаки файловых артефактов по `path`, `filepath`, `pids`;
- длительность sandbox task и статусы выполнения;
- sequence по порядку JSONL events.

### Network / hybrid-признаки
- напрямую flow-поля не обнаружены;
- возможна корреляция с CSV/pcap по внешнему sample id.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | да | parse errors: 1 |
| Missing values | да | `filepath`, `owner`, `machine` могут быть null |
| Нестабильная структура | да | несколько схем в одном формате |
| Смешанные схемы | да | event, files, reboot, report, task |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
JSON полезен для feature extraction, но требует отдельного parser: часть файлов является JSON Lines, часть содержит Mongo-style `NumberLong(...)`, часть является большими многострочными reports. Для TEST нет явных label-полей.

---

## Источник: `log.md`

# Анализ формата: log

## 1. Назначение
Log-файлы Host TEST содержат журналы Cuckoo/analyzer выполнения sandbox-задач. Формат нужен для извлечения последовательностей runtime-событий, уровней логирования, компонентов, task id, PID и временных интервалов.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log |
| Варианты расширения | .log |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 4086 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__13148e1b98.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__26c4060830.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | частично, через regex-поля |
| Заголовок | нет |
| Разделитель | custom log pattern |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Parsed log lines | 4834 |

## 5. Содержательная структура
Строки имеют структуру `timestamp [component] LEVEL: message`. В sample встречаются analyzer events, Cuckoo scheduler events, запуск sniffer, auxiliary modules, machine acquisition, processing и runtime warnings/errors.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| timestamp | datetime string | время события | 2017-09-24 15:28:47,000 |
| component | string | компонент логирования | analyzer |
| level | string | уровень лога | DEBUG |
| message | string | текст события | Starting analyzer from: C:\tmpptgfi_ |
| task_id | integer/string | task id из message | 552 |
| pid | integer/string | PID из message | 8727 |

### Частые компоненты
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

### Уровни логов
| level | count |
|---|---:|
| DEBUG | 3405 |
| INFO | 1242 |
| WARNING | 171 |
| ERROR | 16 |

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
| Название поля | timestamp |
| Формат времени | `%Y-%m-%d %H:%M:%S,%f` |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля не обнаружены.

### Host-признаки
- частоты `level` и `component`;
- последовательности log events и message prefixes;
- task lifecycle timings;
- количество warnings/errors;
- PID/task id activity counts.

### Network / hybrid-признаки
- sniffer/pcap path indicators из Cuckoo messages;
- host+network correlation через task id и pcap path.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | обязательные regex-поля заполнены в parsed lines |
| Нестабильная структура | нет | основной паттерн стабилен |
| Смешанные схемы | частично | analyzer и cuckoo компоненты различаются семантически |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | средний |

## 12. Вывод
Формат готов к feature extraction как line-oriented журнал sandbox runtime. Для supervised learning нужны внешние метки, но sequence/log-level/component признаки можно извлекать напрямую.

---

## Источник: `netflow_day.md`

# Анализ формата: netflow_day

## 1. Назначение
`netflow_day` в Host TEST содержит большие CSV-like netflow-файлы без заголовка. Формат нужен для извлечения network/hybrid признаков: длительность flow, протокол, endpoints, ports, packets и bytes.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | netflow_day |
| Варианты расширения | без расширения; имя `netflow_day-*` |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 2 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\netflow_day\netflow_day-02
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\netflow_day\netflow_day-90
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

## Источник: `txt.md`

# Анализ формата: txt

## 1. Назначение
TXT-файлы Host TEST содержат line-oriented трассы Windows NT syscall/API событий в формате `key=value`. Формат нужен для извлечения syscall frequencies, n-grams, process activity и sequence-признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 274419 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\name.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\NtSetEventBoostPriority__a1e94de9b9.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\txt\ZwAccessCheckByTypeAndAuditAlarm__45f5f1fa41.txt
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | частично, key=value |
| Заголовок | нет |
| Разделитель | comma + key=value |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Parsed lines | 6901 |

## 5. Содержательная структура
Основная схема: `Time`, `Pid`, `MethodName`, `ProcessName` и дополнительные `argN`. Имена файлов также кодируют syscall method (`ZwAccessCheck__...txt`). В sample встречаются методы: NtSetEventBoostPriority, ZwAllocateVirtualMemory, ZwQueryInformationToken, ZwWaitForSingleObject, ZwReplyWaitReceivePort, ZwDuplicateObject, ZwPlugPlayControl, ZwQueryVolumeInformationFile. `name.txt` является служебным файлом с sample executable path/pid и не имеет основной схемы.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| Time | integer | relative timestamp | 203913 |
| Pid | integer | process id | 1392 |
| MethodName | string | syscall/API method | NtSetEventBoostPriority |
| ProcessName | string | путь процесса | \Device\HarddiskVolume1\WINDOWS\system32\svchost.exe |
| arg1 | integer | method-specific argument | 684 |

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
| Формат времени | числовой relative timestamp |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты `MethodName`;
- n-grams syscall/API;
- переходы между вызовами;
- длина syscall trace;
- параметры `argN`;
- активность по `Pid` и `ProcessName`;
- command/path tokens из `ProcessName`.

### Network / hybrid-признаки
- прямые flow/network поля не обнаружены;
- возможна корреляция с network по внешнему sample id.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | частично | `argN` присутствуют не во всех методах |
| Нестабильная структура | частично | набор `argN` зависит от метода |
| Смешанные схемы | частично | `name.txt` служебный, основная масса syscall traces |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
TXT готов к feature extraction для syscall/API sequence-признаков. Нужно учитывать очень большое число файлов, метод-специфичные `argN` и служебный `name.txt`.

---

## Источник: `wls_day.md`

# Анализ формата: wls_day

## 1. Назначение
`wls_day` в Host TEST содержит Windows security log events в JSON Lines формате. Формат нужен для Event ID частот, authentication/logon последовательностей, parent-child process chains и user-host interaction признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | wls_day |
| Варианты расширения | без расширения; имя `wls_day-*` |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-01
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-57
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\wls_day\wls_day-85
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

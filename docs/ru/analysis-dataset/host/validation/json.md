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
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\json\aadinternals_export_adfsdatabaseconfig_remotely_2021-04-27040833.json
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_bitsadmin_download_psh_script_2020-10-2302365189.json
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\json\cmd_lsass_memory_dumpert_syscalls_2020-10-1822561997.json
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

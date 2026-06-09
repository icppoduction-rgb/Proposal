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

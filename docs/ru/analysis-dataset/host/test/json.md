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

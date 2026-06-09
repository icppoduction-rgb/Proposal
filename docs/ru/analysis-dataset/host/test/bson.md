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

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
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\abundant_bell_8827.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\attractive_northcutt_4737.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\blue_sammet_2668.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\chubby_mayer_3250.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\txt\creamy_sinoussi_7198.txt
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

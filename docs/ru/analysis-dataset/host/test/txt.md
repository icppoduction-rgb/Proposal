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
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\txt\name.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\txt\NtSetEventBoostPriority__a1e94de9b9.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TEST\txt\ZwAccessCheckByTypeAndAuditAlarm__45f5f1fa41.txt
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

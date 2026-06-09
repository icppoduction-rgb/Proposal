# Анализ формата: fsstat.log

## 1. Назначение
`fsstat.log` в `TRAIN` содержит агрегированную телеметрию файловых систем host (Metricbeat `system.fsstat`) для оценки заполнения дисков и ёмкости хранилища.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | fsstat.log |
| Варианты расширения | `.log` (группа `fsstat.log`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-13-system.fsstat.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-13-system.fsstat__2a7b781935.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\fsstat.log\2022-01-14-system.fsstat.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none (JSON-lines) |
| Кодировка | utf-8 (12) |
| Вложенная структура | да (вложенные JSON-объекты) |
| Sample-файлов проанализировано | 12 |
| Sample-строк проанализировано | 4451 |
| JSON lines | 4451 |
| Metric rows | 4451 |

## 5. Содержательная структура
Основной поток - записи `system.fsstat` с полями:
- `count`, `total_files`, `total_size.used/free/total`;
- `metricset.period`, `event.duration`;
- `agent.version`, `host.name`, `event.dataset`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:34.544Z` |
| host.name | string | идентификатор host | `internal-share` |
| event.dataset | string | тип telemetry-события | `system.fsstat` |
| system.fsstat.count | float | число смонтированных файловых систем | `3` |
| system.fsstat.total_files | float | общее число файлов (inode) | `6451200` |
| system.fsstat.total_size.used | float | занято байт по всем ФС | `3170240512` |
| system.fsstat.total_size.free | float | свободно байт по всем ФС | `48787542016` |
| system.fsstat.total_size.total | float | общий объём байт по всем ФС | `51957782528` |
| metricset.period | float | период сбора метрики (мс) | `60000` |
| event.duration | float | длительность события (нс) | `182471` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | no |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | @timestamp |
| Формат времени | ISO-8601 |
| Timezone | UTC (suffix Z), event ingestion timezone |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- rolling statistics по `total_size.used`, `total_size.free`, `total_size.total`;
- коэффициент заполнения `total_size.used / total_size.total`;
- динамика изменения `count` и `total_files`;
- тренды `event.duration` и `metricset.period`.

### Network / hybrid-признаки
- корреляция роста использования ФС с network/auth/process событиями на том же host.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | missing total_size rows: 0 |
| Нестабильная структура | нет | unknown/non-json rows present |
| Смешанные схемы | нет | unknown json rows: 0 |
| Дубли строк | нет | duplicates in sample: 0 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | medium |

## 12. Вывод
`TRAIN/fsstat.log` имеет стабильную JSON-lines структуру и пригоден для извлечения host storage-признаков.
Статистика `total_size.used` (sample): min=2805981184.0, max=4335140864.0, avg=3768959051.920018.

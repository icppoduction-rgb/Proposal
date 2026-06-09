# Анализ формата: filesystem.log

## 1. Назначение
`filesystem.log` в `TRAIN` содержит телеметрию файловых систем host (Metricbeat `system.filesystem`) для оценки заполнения дисков, доступной ёмкости и деградации подсистемы хранения.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | filesystem.log |
| Варианты расширения | `.log` (группа `filesystem.log`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-13-system.filesystem.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-13-system.filesystem__ce51cdb62b.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\filesystem.log\2022-01-14-system.filesystem.log
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
| Sample-строк проанализировано | 9833 |
| JSON lines | 9833 |
| Metric rows | 9833 |

## 5. Содержательная структура
Основной поток — записи `system.filesystem` с полями:
- `mount_point`, `type`, `device_name`;
- `used.pct`, `used.bytes`;
- `total`, `free`, `available`, `files`, `free_files`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:34.543Z` |
| host.name | string | идентификатор host | `internal-share` |
| event.dataset | string | тип telemetry-события | `system.filesystem` |
| system.filesystem.mount_point | string | точка монтирования | `/` |
| system.filesystem.type | string | тип файловой системы | `ext4` |
| system.filesystem.device_name | string | устройство | `/dev/vda1` |
| system.filesystem.used.pct | float | доля занятого места | `0.061` |
| system.filesystem.used.bytes | float | занято байт | `3163922432` |
| system.filesystem.total | float | общий объём | `51848359936` |
| system.filesystem.available | float | доступный объём | `48667660288` |

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
- rolling statistics по `used.pct` и `used.bytes`;
- pressure-признаки по `available/total`;
- по-device baseline deviation;
- признаки исчерпания inode по `free_files`.

### Network / hybrid-признаки
- корреляция роста использования ФС с network/auth/process событиями на том же host.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | missing usage rows: 0 |
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
`TRAIN/filesystem.log` содержит стабильную JSON-lines структуру и пригоден для извлечения host storage-признаков.
Статистика `used.pct` (sample): min=0.0, max=0.0835, avg=0.04468810129156921.

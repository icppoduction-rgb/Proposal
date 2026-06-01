# Анализ формата: diskio.log

## 1. Назначение
`diskio.log` в `TRAIN` содержит телеметрию дискового ввода-вывода хоста (Metricbeat `system.diskio`) для анализа нагрузки, аномалий I/O и деградации дисковой подсистемы.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | diskio.log |
| Варианты расширения | `.log` (группа `diskio.log`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio__6ab638e312.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-14-system.diskio.log
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
| Sample-строк проанализировано | 12000 |
| JSON lines | 12000 |
| Рядов `system.diskio` | 10501 |
| Рядов `host.disk.*` | 1499 |

## 5. Содержательная структура
Основной поток: записи `system.diskio` с детализацией по устройствам (`system.diskio.name`) и счётчиками:
- `system.diskio.read.bytes`, `system.diskio.write.bytes`;
- `system.diskio.io.ops`, `system.diskio.io.time`;
- вложенный блок `system.diskio.iostat.*`.

Также присутствует вторичная под-схема: агрегированные записи с `host.disk.read.bytes` и `host.disk.write.bytes` без блока `system`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:43.135Z` |
| host.name | string | идентификатор host | `internal-share` |
| event.dataset | string | тип telemetry-события | `system.diskio` |
| system.diskio.name | string | имя дискового устройства | `vda15` |
| system.diskio.read.bytes | float | счётчик прочитанных байт | `9526272` |
| system.diskio.write.bytes | float | счётчик записанных байт | `5120` |
| system.diskio.io.ops | float | число I/O операций | `0` |
| host.disk.read.bytes | float | агрегированные чтения host (альтернативная схема) | `1572864` |
| host.disk.write.bytes | float | агрегированные записи host (альтернативная схема) | `432029696` |

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
- rolling statistics по `system.diskio.read.bytes` / `system.diskio.write.bytes`;
- read/write ratio и burst-признаки;
- признаки насыщения I/O по `system.diskio.io.ops` и `system.diskio.iostat.busy`;
- device-level baseline deviation;
- корреляция device-уровня с host-level `host.disk.*` агрегатами.

### Network / hybrid-признаки
- корреляция I/O spikes с network flow и authentication событиями на том же host.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | missing system bytes rows: 0 |
| Нестабильная структура | да | сочетание `system.diskio` и `host.disk.*` |
| Смешанные схемы | да | unknown json rows: 0 |
| Дубли строк | нет | в sample не обнаружены |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/diskio.log` пригоден для извлечения host I/O признаков, но формат содержит минимум две рабочие под-схемы в рамках одного расширения (`system.diskio` и `host.disk.*`). Для production-пайплайна нужен парсер с явным ветвлением по типу строки.

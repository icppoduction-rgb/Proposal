# Анализ формата: cpu.log

## 1. Назначение
`cpu.log` в `TRAIN` содержит host CPU telemetry, пригодную для извлечения нагрузочных и временных признаков (CPU utilization, idle/user/system/iowait доли).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | cpu.log |
| Варианты расширения | `.log` (группа `cpu.log`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 13 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-13-system.cpu__e874294b43.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\cpu.log\2022-01-14-system.cpu.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none (JSON-lines) |
| Кодировка | utf-8 (13) |
| Вложенная структура | да (вложенные объекты JSON) |
| Sample-файлов проанализировано | 13 |
| Sample-строк проанализировано | 10479 |
| JSON lines | 10479 |
| Metric rows | 10435 |
| Label rows | 44 |

## 5. Содержательная структура
Основной поток — записи `system.cpu` (Metricbeat) с полями:
- `@timestamp`
- `host.name`, `host.cpu.pct`
- `system.cpu.total.norm.pct`, `system.cpu.user.norm.pct`, `system.cpu.system.norm.pct`, `system.cpu.idle.norm.pct`
- `event.dataset=system.cpu`, `metricset.name=cpu`.

Дополнительно обнаружены аннотационные строки (`line`, `labels`, `rules`) внутри части файлов.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:34.512Z` |
| host.name | string | имя host | `internal-share` |
| host.cpu.pct | float | агрегированная загрузка CPU | `0.1183` |
| system.cpu.total.norm.pct | float | нормализованная total CPU доля | `0.1183` |
| system.cpu.user.norm.pct | float | user CPU доля | `0.0578` |
| system.cpu.system.norm.pct | float | kernel/system CPU доля | `0.0246` |
| system.cpu.idle.norm.pct | float | idle CPU доля | `0.873` |
| labels[] | array[string] | attack/annotation labels (не везде) | `["escalate","crack_passwords"]` |
| rules | object | источники/правила аннотаций | `{"escalate":["attacker.escalate.wpcrack"]}` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | labels |
| Значения label | crack_passwords, escalate |
| Можно использовать для supervised learning | partially |

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
- rolling statistics для `host.cpu.pct` и `system.cpu.total.norm.pct`;
- user/system/iowait/idle ratio признаки;
- burst/anomaly признаки по изменению CPU во времени;
- host-level baseline deviation;
- (частично) weak labels из `labels/rules` для semi-supervised/validation.

### Network / hybrid-признаки
- корреляция CPU spikes с network flow нагрузкой и auth/session событиями.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | missing cpu pct rows: 0 |
| Нестабильная структура | да | metric rows + label/annotation rows |
| Смешанные схемы | да | unknown json rows: 0 |
| Дубли строк | нет | в sample не обнаружены |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/cpu.log` в основном готов для feature extraction по CPU-метрикам, но внутри формата присутствуют отдельные label/annotation строки с другой схемой. Поэтому рекомендуется парсер с ветвлением: `metric row` vs `annotation row`.

CPU статистика (sample):
- `host.cpu.pct`: min=0.0, max=1.0, avg=0.07404315285098227
- `system.cpu.total.norm.pct`: min=0.0, max=1.0, avg=0.07404315285098227

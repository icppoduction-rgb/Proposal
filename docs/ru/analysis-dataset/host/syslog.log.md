# Анализ формата: syslog.log

## 1. Назначение
Смешанный формат `syslog.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog__66beef41ca.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-14-system.syslog.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | JSON object / JSON-lines |
| Кодировка | utf-8 |
| Вложенная структура | да |
| JSON document | 0 |
| JSON-lines | 12 |
| Raw text | 0 |
| Неразобранные | 0 |

## 5. Содержательная структура
Обнаружены две схемы: сценарные документы (`container`, `exploit`, `time`) и JSON-lines события (`timestamp`, `event_type`, `alert`, `dns`).

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| exploit | bool | индикатор сценария | `false` |
| container.role | string | роль контейнера | `normal`, `victim` |
| time.container_ready.absolute | float | время готовности | `1631222503.73` |
| timestamp | string | время события | `2022-01-13T14:37:36.251509+0000` |
| event_type | string | тип события | `stats`, `dns`, `alert` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | exploit / container.role / alert (schema-dependent) |
| Значения label | True, False, normal, victim, alert-derived |
| Можно использовать для supervised learning | partially |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля | time.container_ready.absolute, timestamp |
| Формат времени | Unix epoch float + ISO-8601 |
| Timezone | UTC(+0000) for JSON-lines; scenario JSON timezone implicit |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- частоты `event_type=dns`;
- разнообразие DNS-событий.

### Host-признаки
- `exploit`, роли контейнеров, `recording_time`;
- последовательности `event_type`.

### Network / hybrid-признаки
- `src_ip`, `dest_ip`, `src_port`, `dest_port`, `proto`;
- корреляция alert-событий с host-контекстом.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | критичных пропусков в sample не обнаружено |
| Нестабильная структура | нет | смешаны JSON document и JSON-lines |
| Смешанные схемы | нет | нужен schema-aware parser |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | medium |

## 12. Вывод
`TRAIN/syslog.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

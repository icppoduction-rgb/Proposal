# Анализ формата: auth.log

## 1. Назначение
Файлы `auth.log` в `TRAIN` содержат события аутентификации и сессий (sudo/cron/systemd/useradd/sshd), пригодные для построения host-поведенческих признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | auth.log |
| Варианты расширения | `.log` (группа `auth.log`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 23 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth__0c52d9c83a.log
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-14-system.auth.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none (line-oriented logs / JSON-lines) |
| Кодировка | utf-8 (23) |
| Вложенная структура | да (JSON-lines + вложенные объекты) |
| Sample-файлов проанализировано | 23 |
| Sample-строк проанализировано | 5263 |
| JSON lines | 2827 |
| Raw syslog lines | 2436 |

## 5. Содержательная структура
Внутри `TRAIN/auth.log` обнаружены две подструктуры:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- JSON-lines обертка (Filebeat/ECS) с ключами `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Примеры активностей:
- `session_opened`: 2187
- `session_closed`: 2168

Примеры источников/процессов:
- `sudo`: 1468
- `systemd-logind[1011]`: 37
- `systemd-logind[987]`: 36
- `systemd`: 25
- `useradd[952]`: 24
- `useradd[877]`: 24
- `auth`: 24
- `useradd[25248]`: 18

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример |
|---|---|---|---|
| message | string | текст auth/syslog события | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | точка времени ingest (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | тип события в обертке | `system.auth` |
| host.name | string | хост-источник события | `internal-share` |
| log.file.path | string | исходный путь лога | `/var/log/auth.log` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | partially |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | @timestamp, message(syslog prefix) |
| Формат времени | ISO-8601 (@timestamp) + syslog time without year |
| Timezone | event.timezone (+00:00) for JSON lines; implicit for raw lines |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты `session_opened/session_closed`;
- частоты `sudo`, `cron`, `systemd`, `sshd` действий;
- user-level признаки (login/session активности пользователей);
- source IP frequency и аномалии по источникам;
- последовательности auth-событий во времени.

### Network / hybrid-признаки
- корреляция source IP из auth-событий с сетевыми flow-признаками.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | read errors: 0 |
| Missing values | да | missing `message`: 12 |
| Нестабильная структура | да | смешаны raw syslog и JSON-lines |
| Смешанные схемы | да | json_only=13, raw_only=10 |
| Дубли строк | нет | duplicate lines in sample: 0 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/auth.log` содержит полезные authentication logs и пригоден для feature extraction, но внутри расширения есть два разных представления (raw syslog и JSON-lines). Для корректной промышленной обработки нужен отдельный parser с ветвлением по структуре входной строки.

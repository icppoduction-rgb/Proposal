# Анализ формата: info

## 1. Назначение
Файлы `info` в `TRAIN` содержат события аутентификации и сессий (sudo/cron/systemd/useradd/sshd), пригодные для построения host-поведенческих признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | info |
| Варианты расширения | `.log` (группа `info`) |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail.info
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__b37332a09e.info
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__f74e14508c.info
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none (line-oriented logs / JSON-lines) |
| Кодировка | utf-8 (3) |
| Вложенная структура | да (JSON-lines + вложенные объекты) |
| Sample-файлов проанализировано | 3 |
| Sample-строк проанализировано | 3000 |
| JSON lines | 0 |
| Raw syslog lines | 3000 |

## 5. Содержательная структура
Внутри `TRAIN/info` обнаружены две подструктуры:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- JSON-lines обертка (Filebeat/ECS) с ключами `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Примеры активностей:
- `login`: 1503
- `logged_out`: 1497
- `disconnected`: 6
- `auth_failed`: 6

Примеры источников/процессов:
- `dovecot`: 3000

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример |
|---|---|---|---|
| message | string | текст auth/syslog события | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | точка времени ingest (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | тип события в обертке | `mail.info/dovecot` |
| host.name | string | хост-источник события | `internal-share` |
| log.file.path | string | исходный путь лога | `/var/log/info` |

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
- частоты `login/logged_out/disconnected`;
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
| Missing values | нет | missing `message`: 0 |
| Нестабильная структура | нет | смешаны raw syslog и JSON-lines |
| Смешанные схемы | нет | json_only=0, raw_only=3 |
| Дубли строк | да | duplicate lines in sample: 3 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | medium |

## 12. Вывод
`TRAIN/info` содержит полезные mail service logs и пригоден для feature extraction, но внутри расширения есть два разных представления (raw syslog и JSON-lines). Для корректной промышленной обработки нужен отдельный parser с ветвлением по структуре входной строки.

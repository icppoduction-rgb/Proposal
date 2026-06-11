# Общий анализ train datasets Host

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/host/train`.

## Состав исходных документов

- `README.md`
- `auth.log.md`
- `cpu.log.md`
- `csv.md`
- `diskio.log.md`
- `filesystem.log.md`
- `fsstat.log.md`
- `ghc.md`
- `info.md`
- `journal.md`
- `journal~.md`
- `json-1.md`
- `json.md`
- `load.log.md`
- `log-1.md`
- `log-2.md`
- `log-3.md`
- `log.md`
- `mail-info-1.md`
- `mail-warn-1.md`
- `mainlog-1.md`
- `mainlog-2.md`
- `mainlog-3.md`
- `mainlog.md`
- `memory.log.md`
- `messages-1.md`
- `messages.md`
- `netflow_ids.md`
- `network.log.md`
- `pcap.md`
- `process.log.md`
- `process.summary.log.md`
- `sc.md`
- `service.log.md`
- `socket.summary.log.md`
- `syslog-1.md`
- `syslog-2.md`
- `syslog-3.md`
- `syslog-4.md`
- `syslog.log.md`
- `syslog.md`
- `txt.md`
- `uptime.log.md`
- `xml.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | 101 | нет | да | PARTIALLY_SUPPORTED | csv.md |
| auth.log | 23 | нет | да | NEEDS_CUSTOM_PARSER | auth.log.md |
| cpu.log | 13 | нет | да | PARTIALLY_SUPPORTED | cpu.log.md |
| diskio.log | 12 | нет | да | PARTIALLY_SUPPORTED | diskio.log.md |
| filesystem.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | filesystem.log.md |
| fsstat.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | fsstat.log.md |
| ghc | 56158 | нет | да | NEEDS_CUSTOM_PARSER | ghc.md |
| info | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | info.md |
| journal | 17 | нет | да | NEEDS_CUSTOM_PARSER | journal.md |
| journal~ | 1 | нет | да | NEEDS_CUSTOM_PARSER | journal~.md |
| json | 219 | нет | да | NEEDS_CUSTOM_PARSER | json.md |
| json-1 | 1 | нет | да | READY_FOR_FEATURE_EXTRACTION | json-1.md |
| load.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | load.log.md |
| log | 98 | нет | да | NEEDS_CUSTOM_PARSER | log.md |
| log-1 | 32 | нет | да | READY_FOR_FEATURE_EXTRACTION | log-1.md |
| log-2 | 9 | нет | да | READY_FOR_FEATURE_EXTRACTION | log-2.md |
| log-3 | 8 | нет | да | READY_FOR_FEATURE_EXTRACTION | log-3.md |
| mail-info-1 | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | mail-info-1.md |
| mail-warn-1 | 2 | нет | да | READY_FOR_FEATURE_EXTRACTION | mail-warn-1.md |
| mainlog | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | mainlog.md |
| mainlog-1 | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | mainlog-1.md |
| mainlog-2 | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | mainlog-2.md |
| mainlog-3 | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | mainlog-3.md |
| memory.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | memory.log.md |
| messages | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | messages.md |
| messages-1 | 3 | нет | да | READY_FOR_FEATURE_EXTRACTION | messages-1.md |
| netflow_ids | 50 | нет | да | READY_FOR_FEATURE_EXTRACTION | netflow_ids.md |
| network.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | network.log.md |
| process.log | 2 | нет | да | READY_FOR_FEATURE_EXTRACTION | process.log.md |
| process.summary.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | process.summary.log.md |
| sc | 210 | нет | да | READY_FOR_FEATURE_EXTRACTION | sc.md |
| service.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | service.log.md |
| socket.summary.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | socket.summary.log.md |
| syslog | 9 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog.md |
| syslog-1 | 10 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog-1.md |
| syslog-2 | 10 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog-2.md |
| syslog-3 | 10 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog-3.md |
| syslog-4 | 1 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog-4.md |
| syslog.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | syslog.log.md |
| txt | 3170 | нет | да | READY_FOR_FEATURE_EXTRACTION | txt.md |
| uptime.log | 12 | нет | да | READY_FOR_FEATURE_EXTRACTION | uptime.log.md |
| xml | 40 | нет | да | READY_FOR_FEATURE_EXTRACTION | xml.md |

---

## Источник: `auth.log.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-13-system.auth__0c52d9c83a.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\auth.log\2022-01-14-system.auth.log
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

---

## Источник: `cpu.log.md`

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

---

## Источник: `csv.md`

# Анализ формата: csv

## 1. Назначение
CSV-файлы в Host TRAIN используются как основной источник системных событий (дата/время, процесс, syscall/event, attack labels) для дальнейшего feature engineering.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 101 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\1.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\10.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\csv\11.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | не всегда (обнаружены служебные файлы с header) |
| Разделитель | , (30) |
| Кодировка | cp1252 (1), utf-8-sig (29) |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Sample-строк проанализировано | 29027 |

## 5. Содержательная структура
Основной массив CSV (числовые файлы `1.csv`..`99.csv`) содержит host telemetry: дата/время события, идентификатор процесса, путь процесса, системный вызов/событие и поля меток атаки.
Дополнительно присутствуют служебные CSV:
- `feature_descr.csv` - описание признаков;
- `ground_truth.csv` - детализация attack сценариев.

## 6. Найденные поля / колонки
| Колонка | Имя (эвристика) | Тип | Пример значения |
|---|---|---|---|
| 1 | date | date | 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016, 11/03/2016 |
| 2 | time | time | 2:45:01, 2:45:06, 2:45:06, 2:45:35, 2:45:44 |
| 3 | process_id | integer | 1830, 1804, 2133, 4528, 1847 |
| 4 | path | string | /sbin/upstart-dbus-bridge, /bin/dbus-daemon, /usr/lib/i386-linux-gnu/gconf/gconfd-2, /usr/bin/python3.4, /usr/bin/ibus-daemon |
| 5 | sys_call | integer | 142, 256, 168, 3, 102 |
| 6 | event_id | integer | 45354, 45352, 45372, 39459, 37263 |
| 7 | category_7 | string | normal, normal, normal, normal, normal |
| 8 | category_8 | string | normal, normal, normal, normal, normal |
| 9 | label | integer | 0, 0, 0, 0, 0 |

### Дополнение из feature_descr.csv
| Feature No | Feature Name | Type |
|---|---|---|
| 1 | date | date |
| 2 | time | time |
| 3 | pro_id | number |
| 4 | path | nominal |
| 5 | sys_call | number |
| 6 | event_id | number |
| 7 | attack_cat | nominal |
| 8 | attack_subcat | nominal |
| 9 | label | binary |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | колонка(и) 7, 8, 9 |
| Значения label | нормальные/атакующие категории + бинарный label (0/1) |
| Можно использовать для supervised learning | да |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | date + time (раздельные колонки) |
| Формат времени | date + time in separate columns (dd/mm/yyyy and HH:MM:SS) |
| Timezone | not specified |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо для этого формата/набора.

### Host-признаки
- частоты `sys_call`/`event_id`;
- n-grams и переходы системных вызовов;
- частоты и последовательности по `process_id` + `path`;
- распределения attack category/subcategory;
- бинарный target из label (0/1).

### Network / hybrid-признаки
- в `ground_truth.csv` можно извлекать дополнительные контекстные индикаторы (attack campaign и IP pair metadata) для host+network correlation.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | обнаружено: 0 |
| Повреждённые/нечитаемые | нет | encoding/read errors: 0 |
| Missing values | да | в sample найдено: 66 |
| Нестабильная структура | да | встречаются 9/7/5-колоночные схемы |
| Смешанные схемы | да | спец-файлы: 2 |
| Дубли строк | да | в sample найдено: 13 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
CSV в `TRAIN` пригоден для этапа feature extraction по host telemetry и supervised learning. Основной поток данных имеет стабильную 9-колоночную схему, но есть служебные файлы (`feature_descr.csv`, `ground_truth.csv`) с отдельной структурой, поэтому для полного охвата формата нужна частичная ветвизация парсера.

---

## Источник: `diskio.log.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-13-system.diskio__6ab638e312.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\diskio.log\2022-01-14-system.diskio.log
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

---

## Источник: `filesystem.log.md`

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

---

## Источник: `fsstat.log.md`

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

---

## Источник: `ghc.md`

# Анализ формата: ghc

## 1. Назначение
`ghc` в `TRAIN` содержит текстовые trace-последовательности вида `<module>+0x<offset>` для анализа поведения процессов host.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | ghc |
| Варианты расширения | `.ghc`, `.GHC` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 56158 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-0.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-1.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-10.GHC
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | space |
| Кодировка | utf-8 (30) |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Sample-строк проанализировано | 30 |
| Token count | 6000 |
| Valid trace tokens | 6000 |

## 5. Содержательная структура
Данные представляют последовательности trace-токенов, похожих на stack frame адреса:
- имя модуля (`kernel32.dll`);
- смещение в hex-формате (`0xb50b`);
- порядок токенов внутри строки как sequence-поведение.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| trace.token | string | исходный токен trace | `kernel32.dll+0xb50b` |
| trace.module | string | имя модуля/библиотеки | `kernel32.dll` |
| trace.offset_hex | string | смещение в hex | `0xb50b` |
| filename.scenario_tag | string | сценарный префикс имени файла | `S1-1-Full` |

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
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | not present |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты модулей (`top_modules_detected`);
- n-grams trace-токенов;
- переходы между модулями;
- длина trace-последовательности;
- распределение offset по модулям.

### Network / hybrid-признаки
- корреляция trace-последовательностей с process/network событиями по общему host и времени из внешних источников.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | invalid tokens: 0 |
| Нестабильная структура | нет | non-trace tokens exist |
| Смешанные схемы | нет | includes tokens outside `<module>+0x<hex>` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/ghc` пригоден для этапа feature extraction только через отдельный специализированный parser.
Статистика токенов на файл (sample): min=200.0, max=200.0, avg=200.0.

---

## Источник: `info.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail.info
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__b37332a09e.info
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\info\mail__f74e14508c.info
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

---

## Источник: `journal.md`

# Анализ формата: journal

## 1. Назначение
`journal` в `TRAIN` представлен бинарным контейнером systemd journal и требует отдельного парсера для извлечения событий.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | journal |
| Варианты расширения | `.journal` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 17 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__1451ab8d6a.journal
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal\system__53b42cbacc.journal
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | есть бинарная сигнатура |
| Разделитель | none |
| Кодировка | unknown (container bytes) |
| Вложенная структура | да |
| Sample-файлов проанализировано | 17 |
| Файлов с сигнатурой `LPKSHHRH` | 17 |

## 5. Содержательная структура
Формат похож на контейнер systemd journal: данные хранятся бинарно и не предназначены для прямого текстового чтения.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| header_signature_hex | string | сигнатура первых 8 байт | `4c504b5348485248` |
| size_bytes | integer | размер файла | `16777216` |
| printable_ratio | float | доля печатных байт в sample-header | `0.12` |

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
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | not directly readable |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо на этапе сырого бинарного чтения.

### Host-признаки
- объём журнала и темп роста;
- количество записей и типы событий после парсинга `journalctl`.

### Network / hybrid-признаки
- корреляция извлечённых journal-событий с сетевыми/процессными логами после нормализации.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse/read errors: 0 |
| Missing values | нет | контейнерный бинарный формат |
| Нестабильная структура | нет | смешение бинарных и text-like файлов |
| Смешанные схемы | нет | binary_like=17, text_like=0 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/journal` не должен обрабатываться как обычный текстовый лог. Для корректного извлечения признаков нужен отдельный parser/toolchain для systemd journal.

---

## Источник: `journal~.md`

# Анализ формата: journal~

## 1. Назначение
`journal~` в `TRAIN` представлен бинарным контейнером systemd journal и требует отдельного парсера для извлечения событий.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | journal~ |
| Варианты расширения | `.journal~` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\journal~\system@0005d5746689b192-0aaa58de307081cb.journal~
-
-
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | есть бинарная сигнатура |
| Разделитель | none |
| Кодировка | unknown (container bytes) |
| Вложенная структура | да |
| Sample-файлов проанализировано | 1 |
| Файлов с сигнатурой `LPKSHHRH` | 1 |

## 5. Содержательная структура
Формат похож на контейнер systemd journal: данные хранятся бинарно и не предназначены для прямого текстового чтения.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| header_signature_hex | string | сигнатура первых 8 байт | `4c504b5348485248` |
| size_bytes | integer | размер файла | `16777216` |
| printable_ratio | float | доля печатных байт в sample-header | `0.12` |

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
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | not directly readable |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо на этапе сырого бинарного чтения.

### Host-признаки
- объём журнала и темп роста;
- количество записей и типы событий после парсинга `journalctl`.

### Network / hybrid-признаки
- корреляция извлечённых journal-событий с сетевыми/процессными логами после нормализации.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse/read errors: 0 |
| Missing values | нет | контейнерный бинарный формат |
| Нестабильная структура | нет | смешение бинарных и text-like файлов |
| Смешанные схемы | нет | binary_like=1, text_like=0 |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/journal~` не должен обрабатываться как обычный текстовый лог. Для корректного извлечения признаков нужен отдельный parser/toolchain для systemd journal.

---

## Источник: `json-1.md`

# Анализ формата: json-1

## 1. Назначение
Смешанный формат `json-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json-1\eve.json.1
-
-
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
| JSON-lines | 1 |
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
| Timestamp найден | да |
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
`TRAIN/json-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `json.md`

# Анализ формата: json

## 1. Назначение
Смешанный формат `json` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 219 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_buck_7911.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_jang_1984.json
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\json\abundant_moser_1096.json
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
| JSON document | 29 |
| JSON-lines | 1 |
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
| Label найден | да |
| Название поля | exploit / container.role / alert (schema-dependent) |
| Значения label | True, False, normal, victim, alert-derived |
| Можно использовать для supervised learning | partially |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
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
| Нестабильная структура | да | смешаны JSON document и JSON-lines |
| Смешанные схемы | да | нужен schema-aware parser |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/json` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `load.log.md`

# Анализ формата: load.log

## 1. Назначение
Смешанный формат `load.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | load.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-13-system.load.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-13-system.load__5fb44b3774.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\load.log\2022-01-14-system.load.log
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
| Название поля | - |
| Значения label |  |
| Можно использовать для supervised learning | no |

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
`TRAIN/load.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `log-1.md`

# Анализ формата: log-1

## 1. Назначение
Смешанный формат `log-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 32 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log__2c25d4bfe3.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-1\auth.log__5869f86552.1
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
| JSON-lines | 0 |
| Raw text | 30 |
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
| Timestamp найден | да |
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
`TRAIN/log-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `log-2.md`

# Анализ формата: log-2

## 1. Назначение
Смешанный формат `log-2` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log-2 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 9 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\cloud.smith.santos.com-access.log.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\error.log.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-2\error.log__4546271eaa.2
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
| JSON-lines | 0 |
| Raw text | 9 |
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
`TRAIN/log-2` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `log-3.md`

# Анализ формата: log-3

## 1. Назначение
Смешанный формат `log-3` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log-3 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 8 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\cloud.smith.santos.com-access.log.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\error.log.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log-3\error.log__37add883a7.3
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
| JSON-lines | 0 |
| Raw text | 8 |
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
`TRAIN/log-3` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `log.md`

# Анализ формата: log

## 1. Назначение
Смешанный формат `log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 98 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\attacks.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\audit.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\log\audit__102e01617c.log
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
| JSON-lines | 7 |
| Raw text | 23 |
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
| Timestamp найден | да |
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
| Нестабильная структура | да | смешаны JSON document и JSON-lines |
| Смешанные схемы | да | нужен schema-aware parser |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mail-info-1.md`

# Анализ формата: mail-info-1

## 1. Назначение
Смешанный формат `mail-info-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mail-info-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info__19c6dd9286.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-info-1\mail.info__e9f0904d0f.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/mail-info-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mail-warn-1.md`

# Анализ формата: mail-warn-1

## 1. Назначение
Смешанный формат `mail-warn-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mail-warn-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 2 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-warn-1\mail.warn.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mail-warn-1\mail.warn__3fed34c246.1
-
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
| JSON-lines | 0 |
| Raw text | 2 |
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
`TRAIN/mail-warn-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mainlog-1.md`

# Анализ формата: mainlog-1

## 1. Назначение
Смешанный формат `mainlog-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mainlog-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog__10ce3c1dea.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-1\mainlog__30704dbbbe.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp найден | да |
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
`TRAIN/mainlog-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mainlog-2.md`

# Анализ формата: mainlog-2

## 1. Назначение
Смешанный формат `mainlog-2` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mainlog-2 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog__240133fe49.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-2\mainlog__cd47151943.2
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp найден | да |
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
`TRAIN/mainlog-2` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mainlog-3.md`

# Анализ формата: mainlog-3

## 1. Назначение
Смешанный формат `mainlog-3` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mainlog-3 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog__74d65a7798.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog-3\mainlog__eb89245528.3
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp найден | да |
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
`TRAIN/mainlog-3` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `mainlog.md`

# Анализ формата: mainlog

## 1. Назначение
Смешанный формат `mainlog` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | mainlog |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog__0c75e068e4
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\mainlog\mainlog__220033d95b
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
| JSON-lines | 0 |
| Raw text | 3 |
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
| Timestamp найден | да |
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
`TRAIN/mainlog` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `memory.log.md`

# Анализ формата: memory.log

## 1. Назначение
Смешанный формат `memory.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | memory.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-13-system.memory.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-13-system.memory__c01f1006f7.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\memory.log\2022-01-14-system.memory.log
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
`TRAIN/memory.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `messages-1.md`

# Анализ формата: messages-1

## 1. Назначение
Смешанный формат `messages-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | messages-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages__4260d24d73.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages-1\messages__4e26791260.1
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/messages-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `messages.md`

# Анализ формата: messages

## 1. Назначение
Смешанный формат `messages` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | messages |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages__0f8a1d8071
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\messages\messages__de412018b2
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
| JSON-lines | 0 |
| Raw text | 3 |
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
`TRAIN/messages` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `netflow_ids.md`

# Анализ формата: netflow_ids

## 1. Назначение
Смешанный формат `netflow_ids` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | netflow_ids |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 50 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_fri.netflow_ids
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_fri__dd3db04938.netflow_ids
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\netflow_ids\week1_mon.netflow_ids
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/netflow_ids` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `network.log.md`

# Анализ формата: network.log

## 1. Назначение
Смешанный формат `network.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | network.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-13-system.network.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-13-system.network__3342ea8eb0.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\network.log\2022-01-14-system.network.log
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
`TRAIN/network.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `pcap.md`

# Анализ формата: pcap

## 1. Назначение
Смешанный формат `pcap` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 15 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084616
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084634
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\pcap\log.pcap.1642084645
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
| JSON-lines | 0 |
| Raw text | 15 |
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
| Название поля | - |
| Значения label |  |
| Можно использовать для supervised learning | no |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля |  |
| Формат времени | requires PCAP parser |
| Timezone | unknown |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

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
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/pcap` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `process.log.md`

# Анализ формата: process.log

## 1. Назначение
Смешанный формат `process.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | process.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 2 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.log\2022-01-13-system.process.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.log\2022-01-13-system.process__1b19d2a0f4.log
-
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
| JSON-lines | 2 |
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
`TRAIN/process.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `process.summary.log.md`

# Анализ формата: process.summary.log

## 1. Назначение
Смешанный формат `process.summary.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | process.summary.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-13-system.process.summary__27dcbaf600.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\process.summary.log\2022-01-14-system.process.summary.log
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
`TRAIN/process.summary.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `sc.md`

# Анализ формата: sc

## 1. Назначение
Смешанный формат `sc` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | sc |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 210 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_buck_7911.sc
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_jang_1984.sc
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\sc\abundant_moser_1096.sc
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
| JSON-lines | 0 |
| Raw text | 30 |
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
| Timestamp найден | да |
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
`TRAIN/sc` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `service.log.md`

# Анализ формата: service.log

## 1. Назначение
Смешанный формат `service.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | service.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-13-system.service.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-13-system.service__ea8ef3f753.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\service.log\2022-01-14-system.service.log
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
`TRAIN/service.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `socket.summary.log.md`

# Анализ формата: socket.summary.log

## 1. Назначение
Смешанный формат `socket.summary.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | socket.summary.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-13-system.socket.summary.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-13-system.socket.summary__ee3c7fe60e.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\socket.summary.log\2022-01-14-system.socket.summary.log
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
`TRAIN/socket.summary.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `syslog-1.md`

# Анализ формата: syslog-1

## 1. Назначение
Смешанный формат `syslog-1` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog-1 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 10 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog__2b89be2198.1
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-1\syslog__31309f5830.1
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-1` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `syslog-2.md`

# Анализ формата: syslog-2

## 1. Назначение
Смешанный формат `syslog-2` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog-2 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 10 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog__03421c5fb5.2
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-2\syslog__060eb57e99.2
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-2` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `syslog-3.md`

# Анализ формата: syslog-3

## 1. Назначение
Смешанный формат `syslog-3` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog-3 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 10 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog__08b69a348f.3
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-3\syslog__1ff252de29.3
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
| JSON-lines | 0 |
| Raw text | 10 |
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
`TRAIN/syslog-3` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `syslog-4.md`

# Анализ формата: syslog-4

## 1. Назначение
Смешанный формат `syslog-4` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog-4 |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog-4\syslog.4
-
-
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
| JSON-lines | 0 |
| Raw text | 1 |
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
`TRAIN/syslog-4` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `syslog.log.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-13-system.syslog__66beef41ca.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog.log\2022-01-14-system.syslog.log
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

---

## Источник: `syslog.md`

# Анализ формата: syslog

## 1. Назначение
Смешанный формат `syslog` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | syslog |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 9 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog__072490aa2f
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\syslog\syslog__07c7f78139
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
| JSON-lines | 0 |
| Raw text | 9 |
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
`TRAIN/syslog` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `txt.md`

# Анализ формата: txt

## 1. Назначение
Смешанный формат `txt` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 3170 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\ADFA-LD+Syscall+List.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\fox_alerts.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\txt\harrison_alerts.txt
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/txt` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `uptime.log.md`

# Анализ формата: uptime.log

## 1. Назначение
Смешанный формат `uptime.log` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | uptime.log |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 12 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-13-system.uptime.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-13-system.uptime__bb8fbe0154.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\uptime.log\2022-01-14-system.uptime.log
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
`TRAIN/uptime.log` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

---

## Источник: `xml.md`

# Анализ формата: xml

## 1. Назначение
Смешанный формат `xml` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | xml |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 40 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-1.XML
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-10.XML
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\xml\S1-2.XML
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
| JSON-lines | 0 |
| Raw text | 30 |
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
`TRAIN/xml` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.

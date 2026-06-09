# Анализ формата: log

## 1. Назначение
Log-файлы Host TEST содержат журналы Cuckoo/analyzer выполнения sandbox-задач. Формат нужен для извлечения последовательностей runtime-событий, уровней логирования, компонентов, task id, PID и временных интервалов.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log |
| Варианты расширения | .log |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 4086 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__13148e1b98.log
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\log\analysis__26c4060830.log
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | частично, через regex-поля |
| Заголовок | нет |
| Разделитель | custom log pattern |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Parsed log lines | 4834 |

## 5. Содержательная структура
Строки имеют структуру `timestamp [component] LEVEL: message`. В sample встречаются analyzer events, Cuckoo scheduler events, запуск sniffer, auxiliary modules, machine acquisition, processing и runtime warnings/errors.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| timestamp | datetime string | время события | 2017-09-24 15:28:47,000 |
| component | string | компонент логирования | analyzer |
| level | string | уровень лога | DEBUG |
| message | string | текст события | Starting analyzer from: C:\tmpptgfi_ |
| task_id | integer/string | task id из message | 552 |
| pid | integer/string | PID из message | 8727 |

### Частые компоненты
| component | count |
|---|---:|
| cuckoo.core.resultserver | 1600 |
| analyzer | 1067 |
| cuckoo.core.guest | 1008 |
| cuckoo.core.plugins | 524 |
| modules.auxiliary.human | 461 |
| cuckoo.core.scheduler | 72 |
| cuckoo.machinery.virtualbox | 44 |
| lib.api.process | 15 |
| cuckoo.auxiliary.sniffer | 15 |
| cuckoo.processing.baseline | 14 |

### Уровни логов
| level | count |
|---|---:|
| DEBUG | 3405 |
| INFO | 1242 |
| WARNING | 171 |
| ERROR | 16 |

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
| Название поля | timestamp |
| Формат времени | `%Y-%m-%d %H:%M:%S,%f` |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля не обнаружены.

### Host-признаки
- частоты `level` и `component`;
- последовательности log events и message prefixes;
- task lifecycle timings;
- количество warnings/errors;
- PID/task id activity counts.

### Network / hybrid-признаки
- sniffer/pcap path indicators из Cuckoo messages;
- host+network correlation через task id и pcap path.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | обязательные regex-поля заполнены в parsed lines |
| Нестабильная структура | нет | основной паттерн стабилен |
| Смешанные схемы | частично | analyzer и cuckoo компоненты различаются семантически |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | средний |

## 12. Вывод
Формат готов к feature extraction как line-oriented журнал sandbox runtime. Для supervised learning нужны внешние метки, но sequence/log-level/component признаки можно извлекать напрямую.

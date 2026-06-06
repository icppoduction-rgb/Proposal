# Анализ формата: csv

## 1. Назначение
CSV-файлы Host VALIDATION содержат metadata запусков сценариев: образ, имя сценария, флаг эксплуатации и временные параметры. Формат пригоден для validation/evaluation разметки и контекстных признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 6 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__02fd419ec8.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\csv\runs__0f6fa8a7a1.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-строк | 6000 |

## 5. Содержательная структура
Файлы `runs*.csv` описывают validation сценарии: `image_name`, `scenario_name`, бинарный флаг `is_executing_exploit`, `warmup_time`, `recording_time`, `exploit_start_time`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| image_name | string | container/image identifier | victim_bruteforce:latest |
| scenario_name | string | scenario id | crashing_hamilton_4459 |
| is_executing_exploit | boolean | binary exploit label | False |
| warmup_time | integer | warmup seconds | 10 |
| recording_time | integer | recording seconds | 35 |
| exploit_start_time | integer | exploit start offset | -1 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | is_executing_exploit |
| Значения label | False: 5813, True: 187 |
| Можно использовать для supervised learning | да, как validation labels |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | warmup_time, recording_time, exploit_start_time |
| Формат времени | seconds/relative offsets |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- scenario/image context;
- exploit flag;
- recording duration and exploit start offset.

### Network / hybrid-признаки
- correlation key через scenario/image для packet captures.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | sample без пропусков в основных полях |
| Нестабильная структура | нет | header стабилен |
| Смешанные схемы | нет | все файлы `runs*.csv` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV готов к использованию как validation metadata и источник label/context признаков. Исходные датасеты не изменялись.

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
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\csv\1.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\csv\10.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\TRAIN\csv\11.csv
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

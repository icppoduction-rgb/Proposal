# Анализ формата: netflow_day

## 1. Назначение
`netflow_day` в Host VALIDATION содержит большие CSV-like netflow-файлы без заголовка. Формат нужен для извлечения network/hybrid признаков: длительность flow, протокол, endpoints, ports, packets и bytes.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | netflow_day |
| Варианты расширения | без расширения; имя `netflow_day-*` |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 2 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-02
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\netflow_day\netflow_day-90
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | нет |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 2 |
| Sample-строк разобрано | 2000 |

## 5. Содержательная структура
Строки описывают netflow-события LANL-like формата: `time,duration,src_host,dst_host,protocol,src_port,dst_port,src_packets,dst_packets,src_bytes,dst_bytes`. Хосты и часть портов анонимизированы (`Comp...`, `IP...`, `Port...`). Протоколы в sample: 6: 1369, 17: 621, 1: 10.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| time | integer | время начала flow | 118781 |
| duration | integer | длительность flow | 5580 |
| src_host | anonymized_host | source host | Comp364445 |
| dst_host | anonymized_host | destination host | Comp547245 |
| protocol | integer | номер IP protocol | 17 |
| src_port | anonymized_port | source port | Port05507 |
| dst_port | integer | destination port | Port46272 |
| src_packets | integer | packets от source | 0 |
| dst_packets | integer | packets от destination | 755065 |
| src_bytes | integer | bytes от source | 0 |
| dst_bytes | integer | bytes от destination | 1042329018 |

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
| Название поля | time |
| Формат времени | числовой offset/second counter |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS можно косвенно выделять по `dst_port=53`, но DNS payload отсутствует.

### Host-признаки
- активность host endpoint по `src_host`/`dst_host`;
- user-host признаки отсутствуют.

### Network / hybrid-признаки
- длительность flow;
- bytes/packets в обоих направлениях;
- protocol и ports;
- fan-in/fan-out по host;
- временные окна netflow activity;
- host + network correlation features.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | в sample пустые ячейки не обнаружены |
| Нестабильная структура | нет | 11 колонок в sample |
| Смешанные схемы | нет | оба файла имеют одинаковую структуру |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
`netflow_day` готов к feature extraction как большой line-oriented network flow источник. Нужно учитывать очень большой размер файлов и отсутствие встроенных labels.

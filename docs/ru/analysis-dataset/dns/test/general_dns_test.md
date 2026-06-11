# Общий анализ test datasets DNS

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/dns/test`.

## Состав исходных документов

- `README.md`
- `csv.md`
- `pcap.csv.md`
- `pcap.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (DNS TEST)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | 1 | да | нет | PARTIALLY_SUPPORTED | csv.md |
| pcap | 0 | да | нет | BROKEN_OR_EMPTY | pcap.md |
| pcap.csv | 0 | да | нет | BROKEN_OR_EMPTY | pcap.csv.md |

---

## Источник: `csv.md`

# Анализ формата: csv

## 1. Назначение
CSV-файл DNS TEST содержит крупную табличную выборку DNS/domain признаков для финальной проверки pipeline. Датасет не должен использоваться для обучения; он нужен для оценки качества нормализации, feature engineering и inference-ready обработки.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | да |
| Host | нет |
| Роли | TEST |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TEST\csv\dataset.csv
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
| Sample-файлов проанализировано | 1 |
| Parsed rows in sample | 1000 |

## 5. Содержательная структура
Обнаруженная схема: headerless_dns_test_feature_table: 1. Sample показывает фиксированную 22-колоночную структуру: IP/domain/timestamp/flag/query-domain и набор числовых DNS/domain признаков. Из-за отсутствия заголовка требуется явная positional schema перед production-нормализацией.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| source_ip | domain_or_ip | source/client IP address | 186.169.253.58 |
| resolver_or_parent_domain | domain_or_ip | parent domain or DNSBL service domain | surbl.org |
| timestamp_ms | integer | event timestamp in Unix milliseconds | 1624438272607 |
| label_or_flag | boolean | boolean flag in the row | False |
| query_domain | domain_or_ip | queried domain or DNSBL lookup name | h.surbl.org |
| feature_01 | integer | numeric DNS/domain feature | 1 |
| feature_02 | integer | numeric DNS/domain feature | 1 |
| feature_03 | integer | numeric DNS/domain feature | 0 |
| feature_04 | integer | numeric DNS/domain feature | 0 |
| feature_05 | float | numeric DNS/domain feature | -0.0 |
| feature_06 | float | numeric DNS/domain feature | 0.0 |
| feature_07 | float | numeric DNS/domain feature | 0.0 |
| feature_08 | float | numeric DNS/domain feature | 0.0 |
| feature_09 | float | numeric DNS/domain feature | 0.0 |
| feature_10 | float | numeric DNS/domain feature | 3.4444444444444446 |
| feature_11 | float | numeric DNS/domain feature | 9.59311095410544 |
| feature_12 | integer | numeric DNS/domain feature | 1.5 |
| feature_13 | float | numeric DNS/domain feature | 1.5811388300841898 |
| feature_14 | float | numeric DNS/domain feature | 468.75 |
| feature_15 | float | numeric DNS/domain feature | 0.4444444444444444 |
| feature_16 | float | numeric DNS/domain feature | 0.25849625007211563 |
| feature_17 | float | numeric DNS/domain feature | 0.81743691684035 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | `label_or_flag` |
| Значения label | boolean-like flag в sample |
| Можно использовать для supervised learning | нет, это TEST-роль; использовать только для оценки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | `timestamp_ms` |
| Формат времени | Unix milliseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да, после chunked-сортировки/группировки |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- source/client IP;
- parent/resolver domain;
- queried DNSBL/domain name;
- timestamp-derived windows;
- numeric domain/DNS ratios and aggregate features;
- entropy-like and distribution-like numeric features.

### Network / hybrid-признаки
- группировка по `source_ip`;
- последовательности запросов по `timestamp_ms`;
- корреляция query-domain с DNSBL/provider domain.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | sample содержит строки |
| Поврежденные файлы | нет | parse errors: 0 |
| Missing values | нет | missing cells в sample: 0 |
| Нестабильная структура | нет | inconsistent column files: 0 |
| Смешанные схемы | нет | один CSV-файл |
| Слишком большой файл | да | файл около 8.25 GB; нужен streaming/chunked reader |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | нет, но нужна explicit positional schema |
| Приоритет обработки | средний |

## 12. Вывод
DNS TEST csv пригоден для дальнейшей обработки, но из-за отсутствия заголовка и большого размера его следует читать потоково и нормализовать по заранее закрепленной 22-колоночной схеме.

---

## Источник: `pcap.csv.md`

# Анализ формата: pcap.csv

## 1. Назначение
Файлы DNS TEST `pcap.csv` должны содержать табличные признаки, извлеченные из pcap-трафика, для проверки feature extraction без повторного парсинга raw captures. На текущем этапе такие файлы в TEST-наборе отсутствуют.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap.csv |
| Варианты расширения | .pcap.csv |
| DNS | да |
| Host | нет |
| Роли | TEST |
| Количество файлов | 0 |

## 3. Примеры файлов
```text
нет файлов в `TEST.pcap.csv`
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да, если файлы появятся |
| Табличная структура | ожидается CSV |
| Заголовок | недоступно |
| Разделитель | comma, если файлы появятся |
| Кодировка | utf-8-compatible, если файлы появятся |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 0 |
| Parsed rows | 0 |

## 5. Содержательная структура
Анализ содержимого невозможен: No TEST/pcap.csv bucket is present in sort-path-dns-file.json.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| - | - | нет файлов для анализа | - |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | нет |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | - |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- недоступны без pcap.csv файлов.

### Network / hybrid-признаки
- недоступны без pcap.csv файлов.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | да | bucket отсутствует или пуст |
| Поврежденные файлы | нет | файлов нет |
| Missing values | нет | файлов нет |
| Нестабильная структура | нет | файлов нет |
| Смешанные схемы | нет | файлов нет |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | BROKEN_OR_EMPTY |
| Нужен отдельный парсер | нет, пока нет входных файлов |
| Приоритет обработки | низкий |

## 12. Вывод
DNS TEST `pcap.csv` на текущем этапе непригоден для анализа, потому что в подготовленном JSON нет `TEST.pcap.csv`. Причина зафиксирована в summary и отчете.

---

## Источник: `pcap.md`

# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS TEST должны содержать raw packet capture трафик для проверки packet-level DNS feature extraction. На текущем этапе такие файлы в подготовленном TEST-наборе отсутствуют.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | TEST |
| Количество файлов | 0 |

## 3. Примеры файлов
```text
нет файлов в `TEST.pcap`
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | недоступно |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | packet records, если файлы появятся |
| Sample-файлов проанализировано | 0 |
| Sample packets | 0 |

## 5. Содержательная структура
Анализ содержимого невозможен: No TEST/pcap bucket is present in sort-path-dns-file.json.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| - | - | нет файлов для анализа | - |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | нет |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | - |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- недоступны без raw pcap файлов.

### Network / hybrid-признаки
- недоступны без raw pcap файлов.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | да | bucket отсутствует или пуст |
| Поврежденные файлы | нет | файлов нет |
| Missing values | нет | файлов нет |
| Нестабильная структура | нет | файлов нет |
| Смешанные схемы | нет | файлов нет |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | BROKEN_OR_EMPTY |
| Нужен отдельный парсер | нет, пока нет входных файлов |
| Приоритет обработки | низкий |

## 12. Вывод
DNS TEST pcap на текущем этапе непригоден для анализа, потому что в подготовленном JSON нет `TEST.pcap`. Причина зафиксирована в summary и отчете.

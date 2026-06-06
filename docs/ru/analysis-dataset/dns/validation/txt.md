# Анализ формата: txt

## 1. Назначение
TXT-файлы DNS VALIDATION содержат доменные списки для проверки DNS/domain feature extraction, enrichment и validation-сценариев без packet parsing.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
| DNS | да |
| Host | нет |
| Роли | VALIDATION |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\benign_domains.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains.txt
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains__bdb83c6bf8.txt
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | newline |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 3 |
| Sample lines | 10955 |

## 5. Содержательная структура
Файлы являются domain-list: одна доменная запись на строку. Class hints из имен файлов: unknown: 2, benign: 1. В sample domain-like строк: 10955.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| domain | domain | доменное имя | computerweekly.com |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла / class_hint |
| Значения label | unknown, benign |
| Можно использовать для supervised learning | частично, только после явного назначения класса |

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
- длина домена и поддомена;
- количество labels;
- TLD/SLD;
- entropy и character composition;
- domain reputation/enrichment признаки.

### Network / hybrid-признаки
- join с pcap-derived DNS queries;
- проверка пересечений с allow/block lists.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | non-empty lines в sample: 10955 |
| Поврежденные файлы | нет | parse errors: 0 |
| Missing values | нет | blank lines в sample: 0 |
| Нестабильная структура | нет | newline-separated domain list |
| Смешанные схемы | нет | все sample-строки domain-like |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет |
| Приоритет обработки | средний |

## 12. Вывод
DNS VALIDATION txt готов к feature extraction как набор доменных списков; для supervised evaluation нужно явно закрепить семантику `unknown` списков.

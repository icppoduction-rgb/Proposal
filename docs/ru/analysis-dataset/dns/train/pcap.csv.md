# Анализ формата: pcap.csv

## 1. Назначение
Файлы DNS TRAIN `pcap.csv` содержат табличные признаки, уже извлеченные из pcap-трафика. Набор пригоден для feature engineering без чтения raw-pcap: часть файлов содержит stateful DNS/resource-record признаки, часть - stateless lexical/time признаки доменных запросов.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap.csv |
| Варианты расширения | .pcap.csv |
| DNS | да |
| Host | нет |
| Роли | TRAIN |
| Количество файлов | 14 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_audio.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_benign.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_compressed.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_exe.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_image.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_text.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_video.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_audio.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_benign.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_compressed.pcap.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 14 |
| Parsed rows | 12577 |

## 5. Содержательная структура
Обнаружены две схемы pcap-derived признаков: stateful_dns_pcap_features: 7, stateless_dns_pcap_features: 7. Классы/типы трафика берутся из имен файлов: audio: 2, benign: 2, compressed: 2, exe: 2, image: 2, text: 2, video: 2. Stateful-файлы описывают DNS RR, TTL, NS/IP/ASN и агрегаты; stateless-файлы содержат timestamp и lexical признаки FQDN/subdomain.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| AAAA_frequency | integer | DNS pcap-derived feature | 0 |
| A_frequency | integer | DNS pcap-derived feature | 0 |
| CNAME_frequency | integer | DNS pcap-derived feature | 0 |
| FQDN_count | integer | fully qualified domain name length/count feature | 27 |
| HINFO_frequency | integer | DNS pcap-derived feature | 0 |
| MX_frequency | integer | DNS pcap-derived feature | 0 |
| NS_frequency | integer | DNS pcap-derived feature | 0 |
| NULL_frequency | integer | DNS pcap-derived feature | 0 |
| OPT_frequency | integer | DNS pcap-derived feature | 0 |
| PTR_frequency | integer | DNS pcap-derived feature | 2 |
| SOA_frequency | integer | DNS pcap-derived feature | 0 |
| SRV_frequency | integer | DNS pcap-derived feature | 0 |
| TXT_frequency | integer | DNS pcap-derived feature | 0 |
| a_records | integer | A-record count | 0 |
| distinct_domains | string | distinct domain count | {} |
| distinct_ip | string | distinct IP count | set() |
| distinct_ns | integer | distinct name server count | 0 |
| entropy | float | domain entropy | 2.5704170701729945 |
| labels | integer | DNS label count | 6 |
| labels_average | float | average label length | 3.6666666666666665 |
| labels_max | integer | maximum label length | 7 |
| len | integer | domain/query length | 14 |
| longest_word | integer | longest token length | 2 |
| lower | integer | lowercase character count | 10 |
| numeric | integer | numeric character count | 11 |
| reverse_dns | string | reverse DNS feature | unknown |
| rr | float | resource record ratio or rate feature | 0.0 |
| rr_count | integer | resource record count | 0 |
| rr_name_entropy | float | resource record name entropy | 3.2224634371756076 |
| rr_name_length | integer | resource record name length | 27 |
| rr_type | string | resource record type category | {'PTR'} |
| sld | integer | second-level domain feature | 192 |
| special | integer | special character count | 6 |
| subdomain | integer | subdomain indicator or value | 1 |
| subdomain_length | integer | subdomain character length | 10 |
| timestamp | datetime | packet-derived event timestamp | 2020-11-21 19:13:27.034607 |
| ttl_mean | float | mean TTL | 1.0 |
| ttl_variance | float | TTL variance | 0.0 |
| unique_asn | string | unique ASN count | set() |
| unique_country | string | unique country count | set() |
| unique_ttl | string | unique TTL count | [1, 1] |
| upper | integer | uppercase character count | 0 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла / class_hint |
| Значения label | audio, benign, compressed, exe, image, text, video |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | timestamp |
| Формат времени | `YYYY-MM-DD HH:MM:SS.microseconds` |
| Можно строить sequence | да, для stateless-схемы |
| Можно применять sliding window | да, после сортировки по timestamp |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- частоты RR-типов: `A_frequency`, `NS_frequency`, `TXT_frequency`, `AAAA_frequency`;
- `rr_count`, `rr_name_entropy`, `rr_name_length`;
- `distinct_ns`, `distinct_ip`, `unique_asn`, `unique_ttl`;
- `ttl_mean`, `ttl_variance`;
- lexical признаки FQDN: `entropy`, `labels`, `subdomain_length`, `longest_word`.

### Network / hybrid-признаки
- stateful/stateless feature family;
- тип трафика из имени файла;
- агрегация по timestamp и DNS-запросам;
- связь с raw `pcap` файлами для валидации признаков.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Поврежденные файлы | нет | parse errors: 0 |
| Missing values | нет | missing cells: 0 |
| Нестабильная структура | нет | inconsistent column files: 0 |
| Смешанные схемы | да | две валидные схемы: stateful и stateless |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | READY_FOR_FEATURE_EXTRACTION |
| Нужен отдельный парсер | нет, достаточно CSV reader и schema-aware маршрутизации |
| Приоритет обработки | высокий |

## 12. Вывод
DNS TRAIN `pcap.csv` готов к feature extraction: CSV-структура стабильна, заголовки присутствуют, временные признаки доступны в stateless-схеме, а label можно назначать из имени файла.

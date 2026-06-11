# Общий анализ train datasets DNS

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/dns/train`.

## Состав исходных документов

- `README.md`
- `csv.md`
- `pcap.csv.md`
- `pcap.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (DNS TRAIN)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | 8 | да | нет | PARTIALLY_SUPPORTED | csv.md |
| pcap | 4 | да | нет | NEEDS_CUSTOM_PARSER | pcap.md |
| pcap.csv | 14 | да | нет | READY_FOR_FEATURE_EXTRACTION | pcap.csv.md |

---

## Источник: `csv.md`

# Анализ формата: csv

## 1. Назначение
CSV-файлы DNS TRAIN содержат доменные списки и табличные DNS/domain features для benign, malware, phishing и spam классов. Формат пригоден для доменных lexical features, TTL/IP/ASN признаков, WHOIS-derived признаков и обучения supervised моделей при использовании класса из имени файла.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | да |
| Host | нет |
| Роли | TRAIN |
| Количество файлов | 8 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\benign_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_benign.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_malware.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_phishing.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_spam.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\malware_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\phishing_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\spam_domains.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | частично |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 8 |
| Parsed rows | 7996 |

## 5. Содержательная структура
Обнаружены несколько CSV-схем: dns_feature_table: 4, domain_list: 3, phishtank_url_feed: 1. Классы берутся из имён файлов: benign: 2, malware: 2, phishing: 2, spam: 2. Feature tables содержат `Domain`, `TTL`, `IP`, `ASN`, `entropy`, `tld`, n-gram и WHOIS-derived поля; domain-list файлы содержат один домен на строку. В feature CSV есть неэкранированные list/dict значения с запятыми, поэтому для них нужен schema-aware normalization.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| domain | domain_or_ip | domain name | cypress.com |
| Domain | unknown | queried/resolved domain |  |
| Domain_Name | unknown | normalized domain name |  |
| url | url | phishing URL | http://programafidelidadeitacard2.cf/ |
| IP | unknown | resolved IP address |  |
| TTL | unknown | DNS TTL |  |
| ASN | unknown | autonomous system number |  |
| entropy | unknown | domain entropy |  |
| tld | unknown | top-level domain |  |
| len | unknown | domain length |  |
| subdomain | unknown | subdomain indicator/count |  |
| Creation_Date_Time | unknown | DNS/domain feature |  |
| Domain_Age | unknown | DNS/domain feature |  |
| phish_id | integer | PhishTank id | 6086873 |
| submission_time | string | feed submission timestamp | 2019-06-20T12:56:11+00:00 |
| 1gram | unknown | DNS/domain feature |  |
| 2gram | unknown | DNS/domain feature |  |
| 3gram | unknown | DNS/domain feature |  |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла / class_hint |
| Значения label | benign, malware, phishing, spam |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | Creation_Date_Time, Domain_Age, submission_time |
| Формат времени | datetime / duration string / ISO-like timestamp |
| Можно строить sequence | нет, это domain-level tables/lists |
| Можно применять sliding window | нет без внешнего времени запроса |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- длина domain/subdomain и `len`;
- entropy domain name;
- `TTL`, `IP`, `ASN`;
- `tld`, `sld`, `subdomain`;
- n-gram признаки (`1gram`, `2gram`, `3gram`);
- `Domain_Age`, `Creation_Date_Time`, `Name_Server_Count`;
- URL/domain признаки из PhishTank-like feed.

### Network / hybrid-признаки
- IP/ASN enrichment;
- корреляция с pcap/pcap.csv по domain/IP.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | да | feature CSV содержат `nan` и пустые поля |
| Нестабильная структура | да | inconsistent column count files: 4 |
| Смешанные схемы | да | требуется schema-specific normalization |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | частично, для feature CSV с неэкранированными list/dict полями |
| Приоритет обработки | высокий |

## 12. Вывод
DNS TRAIN CSV частично готов к feature extraction: domain-list и PhishTank-like файлы читаются напрямую, а feature CSV требуют schema-aware normalization из-за неэкранированных list/dict полей с запятыми. Class label назначается из имени файла.

---

## Источник: `pcap.csv.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_audio.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_benign.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_compressed.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_exe.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_image.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_text.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_video.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_audio.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_benign.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_compressed.pcap.csv
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

---

## Источник: `pcap.md`

# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS TRAIN содержат packet capture трафик для benign, malware, phishing и spam классов. Формат нужен для DNS query/response parsing, packet/flow features и проверки признаков, извлечённых из CSV.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | TRAIN |
| Количество файлов | 4 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\benign.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\malware.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\phishing.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\spam.pcap
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcap/pcapng global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | 4 |
| Sample packets | 2000 |

## 5. Содержательная структура
Контейнеры в sample: classic_pcap: 3, pcapng: 1. IP protocol distribution: 17: 2000. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: 1000.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| container_variant | string | classic pcap или pcapng | classic_pcap |
| magic | hex | capture signature | 0a0d0d0a |
| ip_protocol | integer | IP protocol | 17 |
| udp_dst_port | integer | UDP destination port sample | 53 |
| tcp_dst_port | integer | TCP destination port sample |  |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла |
| Значения label | benign, malware, phishing, spam |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet timestamp |
| Формат времени | pcap seconds/usec или pcapng timestamp |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- query name, query length, subdomain depth;
- qtype/qclass;
- response size, TTL, answer count;
- NXDOMAIN/RCODE distribution;
- inter-query intervals.

### Network / hybrid-признаки
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- correlation with CSV domain/IP features.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | packet headers доступны |
| Нестабильная структура | частично | `.pcap` bucket содержит classic pcap и pcapng |
| Смешанные схемы | да | нужен parser, поддерживающий оба контейнера |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
DNS TRAIN pcap полезен для network/DNS feature extraction, но production pipeline должен использовать packet parser с поддержкой classic pcap и pcapng.

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

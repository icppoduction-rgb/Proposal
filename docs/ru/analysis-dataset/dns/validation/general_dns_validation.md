# Общий анализ validation datasets DNS

Файл собран автоматически из markdown-файлов каталога `docs/ru/analysis-dataset/dns/validation`.

## Состав исходных документов

- `README.md`
- `pcap.md`
- `txt.md`

---

## Источник: `README.md`

# Анализ содержимого файлов датасетов (DNS VALIDATION)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| pcap | 5 | да | нет | NEEDS_CUSTOM_PARSER | pcap.md |
| txt | 3 | да | нет | READY_FOR_FEATURE_EXTRACTION | txt.md |

---

## Источник: `pcap.md`

# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS VALIDATION содержат raw packet capture трафик для проверки DNS amplification attack / benign сценариев. Формат нужен для валидации packet-level DNS признаков, сетевых агрегатов и сверки downstream feature extraction.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | VALIDATION |
| Количество файлов | 5 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack__f291ed87a1.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign1.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign__60a57c3a63.pcap
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcap global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | 5 |
| Sample packets | 2500 |

## 5. Содержательная структура
Контейнеры в sample: classic_pcap: 5. IP protocol distribution: 17: 2500. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: 754.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| container_variant | string | classic pcap или pcapng | classic_pcap |
| magic | hex | capture signature | d4c3b2a1 |
| ip_protocol | integer | IP protocol | 17 |
| udp_dst_port | integer | UDP destination port sample | 53 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла |
| Значения label | attack, benign |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet timestamp |
| Формат времени | pcap seconds/usec |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- qname, qtype/qclass, response size;
- DNS amplification query/response ratios;
- RCODE/NXDOMAIN distribution;
- TTL and answer count;
- inter-query intervals.

### Network / hybrid-признаки
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- attack/benign label from file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Поврежденные файлы | нет | parse errors: 0 |
| Missing values | нет | packet headers доступны |
| Нестабильная структура | нет | sample содержит classic pcap |
| Смешанные схемы | нет | один контейнерный тип в sample |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
DNS VALIDATION pcap полезен для проверки DNS amplification detection pipeline, но production processing должен использовать packet parser с DNS protocol decoding.

---

## Источник: `txt.md`

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
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\benign_domains.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains.txt
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\txt\domains__bdb83c6bf8.txt
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

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

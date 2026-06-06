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
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_attack__f291ed87a1.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign1.pcap
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap\ens33-dns_amplification_benign__60a57c3a63.pcap
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

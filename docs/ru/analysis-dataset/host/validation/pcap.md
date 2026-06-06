# Анализ формата: pcap

## 1. Назначение
`.pcap` в Host VALIDATION содержит classic pcap packet capture файлы с сетевым трафиком attack-сценариев. Формат нужен для network/hybrid feature extraction, но требует специализированного packet parser для полного извлечения признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 1 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcap\pcap_log4shell_cve2021_44228_jndi_reference_2022-05-11181020.pcap
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
| Sample-файлов проанализировано | 1 |
| Sample packets | 67 |

## 5. Содержательная структура
Файлы содержат packet metadata и payload bytes в classic pcap container. В sample обнаружены Ethernet/IPv4 пакеты; IP protocol distribution: 6: 65. Имена файлов указывают на attack scenario и могут использоваться как внешний контекст, но не как встроенное label-поле.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 262144 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 443 |
| udp_dst_port | integer | sample UDP destination port |  |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены внутри файла |
| Можно использовать для supervised learning | частично; только при внешней разметке/сценарии из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet header ts_sec/ts_usec |
| Формат времени | pcap timestamp seconds + micro/nanoseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS query/response признаки после packet parsing.

### Host-признаки
- прямые host syscall/EventID признаки отсутствуют.

### Network / hybrid-признаки
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports, TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | pcap headers доступны |
| Нестабильная структура | нет | classic pcap magic/header стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.pcap` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcap parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

# Анализ формата: cap

## 1. Назначение
`.cap` в Host VALIDATION содержит classic pcap packet capture файлы с сетевым трафиком attack-сценариев. Формат нужен для network/hybrid feature extraction, но требует специализированного packet parser для полного извлечения признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | cap |
| Варианты расширения | .cap |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 44 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_copy_smb_CreateRequest_2020-09-22145302.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_executeexcel4macro_allowed_2020-09-17174542.cap
C:\Users\Public\PythonProjects\storages\datasets-filter\host\VALIDATION\cap\covenant_dcom_iertutil_dll_hijack_WORKSTATION5_2020-10-09183000.cap
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
| Sample-файлов проанализировано | 30 |
| Sample packets | 10258 |

## 5. Содержательная структура
Файлы содержат packet metadata и payload bytes в classic pcap container. В sample обнаружены Ethernet/IPv4 пакеты; IP protocol distribution: 6: 10148, 17: 110. Имена файлов указывают на attack scenario и могут использоваться как внешний контекст, но не как встроенное label-поле.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| magic | hex | pcap signature | d4c3b2a1 |
| version | string | pcap version | 2.4 |
| snaplen | integer | capture snap length | 65535 |
| network | integer | link-layer type | 1 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 80 |
| udp_dst_port | integer | sample UDP destination port | 53 |

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
| Повреждённые файлы | да | parse errors: 6 |
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
`.cap` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcap parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

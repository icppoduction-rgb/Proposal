# Анализ формата: pcapng

## 1. Назначение
`.pcapng` в Host VALIDATION содержит packet capture файлы нового поколения с block-based структурой. Формат полезен для network/hybrid feature extraction, но требует специализированного pcapng parser для извлечения пакетов и потоков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcapng |
| Варианты расширения | .pcapng |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | 5 |

## 3. Примеры файлов
```text
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\aadinternals_export_adfsdatabaseconfig_remotely_20210427020247.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\empire_ninjacopy_dumping_ntds_dit_file.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\pcap_log4shell_cve2021_44228_java_serialized_2022-05-13045800.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_create_2020-12-1907003032.pcapng
C:\Users\fmark\PythonProjects\storages\datasets-filter\host\VALIDATION\pcapng\schtask_modification_2020-12-1907505969.pcapng
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcapng Section Header Block |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, typed blocks |
| Sample-файлов проанализировано | 5 |
| Sample blocks | 1676 |
| Sample packets | 1664 |

## 5. Содержательная структура
Файлы содержат Section Header, Interface Description и Enhanced Packet blocks. Распределение block types в sample: 0x00000006: 1664, 0x0a0d0d0a: 5, 0x00000001: 5, 0x00000005: 2. IP protocol distribution после ограниченного packet parsing: 6: 1353, 17: 56, 1: 40, 2: 16.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| section_magic | hex | pcapng Section Header Block magic | 0a0d0d0a |
| byte_order_magic | hex | endianness marker | 4d3c2b1a |
| version | string | pcapng version | 1.0 |
| link_type | integer | interface link-layer type | 1 |
| block_type | hex | pcapng block type | 0x00000006 |
| ip_protocol | integer | IP protocol | 6 |
| tcp_dst_port | integer | sample TCP destination port | 3389 |
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
| Название поля | Enhanced Packet Block timestamp_high/timestamp_low |
| Формат времени | pcapng interface timestamp resolution |
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
- TCP/UDP ports и TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | pcapng headers/blocks доступны |
| Нестабильная структура | нет | Section Header Block стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.pcapng` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcapng parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.

# Анализ формата: csv

## 1. Назначение
CSV-файлы Host TEST содержат packet/network metadata и отдельные CSV-карты меток атак. Формат нужен для анализа сетевого поведения и возможной host+network корреляции, но TEST-набор не должен использоваться для обучения.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | 3 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_dataset.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TEST\csv\attack_labels_sbseg.csv
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8/utf-8-sig по sample |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 3 |

## 5. Содержательная структура
`attack_dataset.csv` содержит packet metadata: frame time, epoch time, IP/TCP поля, адреса, порты, flags, длины и checksum. `attack_labels.csv` и `attack_labels_sbseg.csv` содержат соответствие `ip -> label` для атак вроде nmap scan. Это network/hybrid-структура внутри Host TEST bucket.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| frame_info.time | string | время пакета | Dec 31, 1969 21:03:41.953641000 -03 |
| frame_info.time_epoch | float | epoch seconds | 221.953641000 |
| ip.src | ip | source IP | 172.16.0.3 |
| ip.dst | ip | destination IP | 10.10.10.10 |
| ip.proto | integer | колонка sample CSV | 6 |
| tcp.srcport | integer | source TCP port | 62218 |
| tcp.dstport | integer | destination TCP port | 8888 |
| tcp.flags | integer | TCP flags | 0x00000002 |
| frame_info.len | integer | колонка sample CSV | 58 |
| ip.len | integer | колонка sample CSV | 44 |
| label | string | метка класса атаки | nmap_tcp_syn |
| ip | ip | колонка sample CSV | 172.16.0.3 |
| frame_info.encap_type | integer | колонка sample CSV | 1 |
| frame_info.number | integer | колонка sample CSV | 20 |
| frame_info.cap_len | integer | колонка sample CSV | 58 |
| eth.type | integer | колонка sample CSV | 0x00000800 |
| ip.version | integer | колонка sample CSV | 4 |
| ip.hdr_len | integer | колонка sample CSV | 20 |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | label в отдельных label CSV; `attack_dataset.csv` label не содержит |
| Значения label | nmap_tcp_syn, nmap_tcp_conn, nmap_tcp_null, nmap_tcp_xmas, nmap_tcp_fin, nmap_tcp_ack, nmap_tcp_window, nmap_tcp_maimon, unicornscan_tcp_syn, unicornscan_tcp_conn, unicornscan_tcp_null, unicornscan_tcp_xmas, unicornscan_tcp_fxmas, unicornscan_tcp_fin, unicornscan_tcp_ack, hping_tcp_syn, hping_tcp_null, hping_tcp_xmas, hping_tcp_fin, hping_tcp_ack, zmap_tcp_syn, masscan_tcp_syn, nmap_ping_scan, nmap_vvv, nmap_connect, nmap_fast, nmap_servinfo, nmap_reason, nmap_open, nmap_top10 |
| Можно использовать для supervised learning | частично; нужен join по IP и TEST нельзя применять для обучения |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | frame_info.time, frame_info.time_epoch |
| Формат времени | строка Wireshark timestamp + epoch seconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля в sample не обнаружены.

### Host-признаки
- прямые syscall/process признаки не обнаружены.

### Network / hybrid-признаки
- bytes/packet length по `frame_info.len`, `ip.len`, `tcp.len`;
- протоколы и TCP flags;
- пары `ip.src`/`ip.dst` и source/destination ports;
- временные интервалы между пакетами по `frame_info.time_epoch`;
- attack label через join по IP;
- host + network correlation features при наличии внешней связи с host traces.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | в sample: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | да | в packet CSV есть пустые protocol/header поля |
| Нестабильная структура | да | dataset CSV и label CSV имеют разные схемы |
| Смешанные схемы | да | 41-колоночный packet CSV и 2-колоночные label maps |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | PARTIALLY_SUPPORTED |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV в Host TEST пригоден для network/hybrid feature extraction, но не является единым host telemetry CSV. Для supervised evaluation метки нужно присоединять отдельно по IP; TEST-данные не использовать для обучения.

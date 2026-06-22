# DNS datasets

DNS-ветка содержит 8 format buckets и 35 файлов. Она делится на табличные CSV, packet captures и domain-list TXT. DNS `TEST` не содержит подготовленных `pcap`/`pcap.csv` файлов, поэтому TEST packet-level проверка в текущем наборе невозможна.

## DNS TRAIN

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 8 | `PARTIALLY_SUPPORTED` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | частично | Domain-list и PhishTank-like файлы читаются напрямую; feature CSV могут содержать неэкранированные list/dict поля с запятыми. |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | да, packet timestamp | Нужен packet parser с classic pcap/pcapng и DNS protocol decoding. |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | class hint из имени файла: `audio`, `benign`, `compressed`, `exe`, `image`, `text`, `video` | да | CSV-структура стабильна, заголовки присутствуют; подходит для DNS feature extraction после label mapping. |

Правило labels: filename/class hint можно использовать только как `label_source=filename`/`inferred_label`. Payload classes (`audio`, `compressed`, `exe`, `image`, `text`, `video`) нельзя автоматически считать exfiltration labels без зафиксированного target mapping.

## DNS VALIDATION

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `attack`, `benign` | да, packet timestamp | Подходит для проверки DNS amplification/detection pipeline, но требует packet parser. |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | class hint: `unknown`, `benign` | нет | Domain-list: одна доменная запись на строку. `unknown` нельзя считать benign или attack без policy. |

## DNS TEST

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 1 | `PARTIALLY_SUPPORTED` | частичное boolean-like поле `label_or_flag` в sample | да | Большой CSV без заголовка; нужна закрепленная 22-колоночная схема и streaming-read. Использовать только для evaluation. |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap` нет файлов. |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap.csv` нет файлов. |

## Выводы для DNS parsers

| Компонент Stage Two | Что требуется |
| --- | --- |
| `DnsCsvParser` | Различать TRAIN CSV под-схемы, DNS TEST headerless 22-column schema и domain-list/PhishTank-like sources. |
| `DnsPcapCsvParser` | Поддерживать стабильные CSV headers и сохранять filename class hints как label metadata. |
| `DnsTxtDomainListParser` | Читать одну доменную запись на строку, сохранять `timestamp=null`, `timestamp_type=missing` или `event_order`. |
| `DnsPacketCaptureParser` | Извлекать packet timestamp, DNS query/response fields, qtype/qclass/rcode/ttl, network tuple и packet-level metadata. |

## DNS feature extraction

Приоритетные признаки:

- длина домена, поддомена, query string;
- entropy и charset distribution;
- unique subdomain ratio;
- query rate/window counts;
- qtype/rcode/ttl distribution;
- packet size/response size;
- payload class context для pcap.csv, если mapping утвержден.

## DNS quality risks

- DNS TEST packet buckets пустые (`BROKEN_OR_EMPTY`).
- DNS TEST CSV без header требует fixed positional schema.
- `unknown` в VALIDATION TXT не является class label.
- Filename labels требуют audit trail и не должны попадать в X features.

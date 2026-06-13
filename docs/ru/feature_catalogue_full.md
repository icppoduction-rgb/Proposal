# Каталог признаков (Feature Catalogue) для проекта Proposal

**Дата подготовки:** 2026-06-13  
**Проект:** Behaviour-driven hybrid learning for data exfiltration detection  
**Назначение:** зафиксировать полный перечень признаков, которые нужно извлекать в Stage Two / Feature Engineering для DNS, Host, Network/Hybrid и sequence-веток.
**Обновление:** добавлены дополнительные признаки из новых изображений: file-access diversity, sensitive file access, archiving/compression, external destinations, failed-then-success authentication, rare process execution и stage-transition sequence indicators.

---

## 1. Как читать этот документ

Этот каталог отвечает на вопрос: **какие конкретные признаки используются в итоговом framework**.

Документ построен не по датасетам, а по самим признакам. Это соответствует структуре, показанной на присланных изображениях:

- `Название признака`
- `Набор данных / источник`
- `Этап атаки`
- `Тип признака`
- `Описание`
- `Формула / расчёт`
- `Используемые модели`

Связанный документ `Dataset Feature Extraction Map` нужен как карта: **из какого датасета какие группы признаков извлекаются**. Этот каталог нужен как словарь: **какие признаки должны существовать в итоговом feature store / Parquet artifacts / model-ready datasets**.

---

## 2. Принципы отбора признаков

1. **TRAIN / VALIDATION / TEST не смешивать.** Признаки можно рассчитывать одинаковыми функциями, но обучать модели на TEST нельзя.
2. **DNS и Host не склеивать на raw-уровне.** Интеграция выполняется на уровне нормализованных событий, временных окон и признаков.
3. **Labels не являются input features.** `label_binary`, `label_family`, `label_status` нужны для supervised learning и аудита, но не должны попадать в `X_train`.
4. **Поля с прямым leakage исключать.** Нельзя использовать `source_file`, имя файла, `dataset_role`, `scenario_name` как обычный модельный признак, если они напрямую кодируют класс.
5. **Sequence-признаки строить отдельно.** Для LSTM нужны упорядоченные события и sliding windows; для RF/XGBoost/CNN нужны агрегаты по событиям/окнам.
6. **Отсутствие label не означает benign.** Для unlabeled источников использовать `label_binary=NULL`, пока не настроен label resolver.

---

## 3. Уровни расчёта признаков

| Уровень | Описание | Основные модели |
|---|---|---|
| Event-level | Признаки одного DNS query, syscall, process event, auth event, packet или log event | RF, XGBoost, CNN |
| Window-level | Агрегации за временное окно по host/source_ip/user/domain/process | RF, XGBoost, CNN |
| Flow-level | Агрегации сетевого соединения или 5-tuple | RF, XGBoost |
| Trace-level | Syscall/API/module trace как последовательность | CNN, LSTM |
| Sequence-level | Упорядоченные multi-source события 50-100 событий на окно | LSTM |
| Hybrid-level | Корреляция host + network/DNS по времени, host, scenario или external mapping | Late fusion, RF/XGBoost, LSTM |

---

## 4. Каталог DNS-признаков

|Название признака|Набор данных / источник|Этап атаки|Тип признака|Описание|Формула / расчёт|Используемые модели|
|---|---|---|---|---|---|---|
|dns_query_length|CIC-Bell-DNS-EXF-2021; CIC-Bell-DNS-2021; Mendeley DNS; DNS TRAIN csv/pcap/pcap.csv; DNS VALIDATION pcap/txt; DNS TEST csv|Exfiltration|Network/DNS lexical|Длина queried domain / qname / FQDN.|len(qname) или поле `len` / `FQDN_count`.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_subdomain_length|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv/csv; DNS VALIDATION txt/pcap|Exfiltration|Network/DNS lexical|Длина поддомена без TLD/SLD.|len(subdomain_part).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_subdomain_depth|CIC-Bell; Mendeley DNS; DNS TRAIN pcap; DNS VALIDATION pcap/txt|Exfiltration|Network/DNS lexical|Количество уровней поддомена.|max(label_count - 2, 0).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_label_count|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS lexical|Количество labels в домене.|count(split(qname, ".")).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_label_avg_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Средняя длина label.|mean(len(label_i)).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_label_max_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Максимальная длина label.|max(len(label_i)).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_longest_word_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Длина самого длинного токена/слова в домене.|max(token_length).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_entropy|CIC-Bell; Mendeley DNS; DNS TRAIN csv/pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS entropy|Энтропия символов домена; индикатор encoded/high-random subdomain.|Shannon entropy по qname/subdomain.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_rr_name_entropy|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS entropy|Энтропия имени resource record.|Shannon entropy по rr_name.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_lowercase_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Количество lowercase символов.|count(c.islower()).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_uppercase_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Количество uppercase символов.|count(c.isupper()).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_digit_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Количество цифр в домене.|count(c.isdigit()).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_special_char_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Количество неалфавитно-цифровых символов.|count(non-alnum chars).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_tld|CIC-Bell; Mendeley DNS; DNS TRAIN csv; DNS VALIDATION txt|Exfiltration|Network/DNS categorical|Top-level domain.|extract_tld(qname). Кодировать через frequency/target-safe encoding.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_sld|CIC-Bell; Mendeley DNS; DNS TRAIN csv/pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS categorical|Second-level domain / родительский домен.|extract_sld(qname).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_1gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Частоты unigram символов/токенов.|count 1-gram / total grams.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_2gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Частоты bigram.|count 2-gram / total grams.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_3gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Частоты trigram.|count 3-gram / total grams.|RF, XGBoost, CNN; SHAP для важности признаков|
|domain_age_days|DNS TRAIN csv; domain feature tables|Exfiltration|DNS enrichment|Возраст домена, если доступен WHOIS-derived field.|parse `Domain_Age` или now - Creation_Date_Time.|RF, XGBoost, CNN; SHAP для важности признаков|
|domain_creation_time_features|DNS TRAIN csv|Exfiltration|DNS enrichment/time|Производные признаки из Creation_Date_Time.|year/month/age_bucket, missing flag.|RF, XGBoost, CNN; SHAP для важности признаков|
|name_server_count|DNS TRAIN csv; pcap.csv|Exfiltration|DNS enrichment/RR|Количество NS / distinct name servers.|count(distinct NS).|RF, XGBoost, CNN; SHAP для важности признаков|
|distinct_domain_count|DNS TRAIN pcap.csv; DNS pcap windows|Exfiltration|DNS aggregation|Количество уникальных доменов в окне.|nunique(qname) over window.|RF, XGBoost, CNN; SHAP для важности признаков|
|distinct_subdomain_count|CIC-Bell; Mendeley DNS; pcap windows|Exfiltration|DNS aggregation|Количество уникальных subdomains в окне.|nunique(subdomain) over {src_ip, domain, window}.|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_subdomain_ratio|CIC-Bell; Mendeley DNS|Exfiltration|DNS aggregation|Доля уникальных subdomains к общему числу запросов.|unique_subdomains / total_queries.|RF, XGBoost, CNN; SHAP для важности признаков|
|distinct_ip_count|DNS TRAIN pcap.csv; pcap parser|Exfiltration|DNS enrichment/RR|Количество уникальных IP в ответах.|nunique(answer_ip).|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_asn_count|DNS TRAIN csv/pcap.csv|Exfiltration|DNS enrichment|Количество ASN по ответам или enrichment.|nunique(ASN).|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_country_count|DNS TRAIN pcap.csv|Exfiltration|DNS enrichment|Количество стран по IP/ASN enrichment.|nunique(country).|RF, XGBoost, CNN; SHAP для важности признаков|
|ttl_mean|DNS TRAIN csv/pcap.csv; DNS pcap; DNS VALIDATION pcap|Exfiltration|DNS protocol/RR|Средний TTL в ответах.|mean(TTL) per domain/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|ttl_variance|DNS TRAIN pcap.csv; DNS pcap|Exfiltration|DNS protocol/RR|Дисперсия TTL.|var(TTL) per domain/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_ttl_count|DNS TRAIN pcap.csv|Exfiltration|DNS protocol/RR|Количество уникальных TTL.|nunique(TTL).|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_count|DNS TRAIN pcap.csv; DNS pcap|Exfiltration|DNS protocol/RR|Количество resource records.|count(RR).|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_rate|DNS TRAIN pcap.csv; DNS pcap windows|Exfiltration|DNS protocol/RR|Темп RR в окне.|rr_count / window_duration.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_A|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота A-records.|count(rr_type == A) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_AAAA|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота AAAA-records.|count(rr_type == AAAA) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_CNAME|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота CNAME-records.|count(rr_type == CNAME) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_MX|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота MX-records.|count(rr_type == MX) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_NS|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота NS-records.|count(rr_type == NS) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_PTR|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота PTR-records.|count(rr_type == PTR) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_SOA|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота SOA-records.|count(rr_type == SOA) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_SRV|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота SRV-records.|count(rr_type == SRV) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_TXT|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частота TXT-records; важна для DNS tunnelling/exfiltration.|count(rr_type == TXT) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|rr_type_frequency_NULL_OPT_HINFO|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Частоты редких RR типов.|count(NULL/OPT/HINFO) / rr_count.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_qtype_frequency|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Распределение query type.|count(qtype)/total_queries.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_qclass_frequency|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Распределение qclass.|count(qclass)/total_queries.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_response_size_stats|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol/network|Статистика размера DNS response.|mean/max/std(response_bytes) per window.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_answer_count|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Количество answer records в response.|count(answers) per response/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_rcode_distribution|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Распределение response codes.|count(rcode)/responses.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_nxdomain_rate|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol/anomaly|Доля NXDOMAIN.|count(rcode == NXDOMAIN) / responses.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_amplification_ratio|DNS VALIDATION pcap; DNS pcap|Exfiltration|DNS attack-specific|Отношение response size/count к query size/count для amplification.|sum(response_bytes)/max(sum(query_bytes),1).|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_inter_query_interval_stats|DNS TRAIN/VALIDATION pcap; DNS TEST csv|Exfiltration|DNS temporal|Интервалы между DNS-запросами.|diff(timestamp) по src_ip/domain; mean/std/min/max.|LSTM; RF/XGBoost по агрегатам окна|
|dns_query_rate|CIC-Bell; Mendeley DNS; DNS TEST csv|Exfiltration|DNS temporal|Частота DNS-запросов.|count(query)/time_window.|LSTM; RF/XGBoost по агрегатам окна|
|dns_queries_per_window|CIC-Bell; Mendeley DNS; DNS TEST csv|Exfiltration|DNS temporal|Количество запросов в фиксированном окне.|count(query) over sliding window.|LSTM; RF/XGBoost по агрегатам окна|
|dns_source_ip_query_count|DNS TEST csv; DNS pcap|Exfiltration|DNS/network aggregation|Количество запросов по source/client IP.|count(query) group by source_ip/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|dnsbl_provider_match|DNS TEST csv|Exfiltration|DNS enrichment|Связь query_domain с DNSBL/provider domain.|join/compare resolver_or_parent_domain and query_domain.|RF, XGBoost, CNN; SHAP для важности признаков|
|url_length|DNS TRAIN csv PhishTank-like feed|Reconnaissance/Exfiltration|URL lexical|Длина URL из phishing/feed источников.|len(url).|RF, XGBoost, CNN; SHAP для важности признаков|
|url_token_entropy|DNS TRAIN csv PhishTank-like feed|Reconnaissance/Exfiltration|URL lexical|Энтропия URL path/query токенов.|Shannon entropy over URL tokens.|RF, XGBoost, CNN; SHAP для важности признаков|

---

## 5. Каталог сетевых / flow / packet признаков

|Название признака|Набор данных / источник|Этап атаки|Тип признака|Описание|Формула / расчёт|Используемые модели|
|---|---|---|---|---|---|---|
|packet_count|DNS pcap; Host VALIDATION cap/pcap/pcapng; Host TEST csv/netflow_day|Cross-stage / Exfiltration|Network flow|Количество пакетов в flow/window.|count(packet) group by flow/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|byte_count|DNS pcap; Host cap/pcap/pcapng/csv/netflow|Cross-stage / Exfiltration|Network flow|Количество байтов в flow/window.|sum(packet_len/ip_len/tcp_len/flow_bytes).|RF, XGBoost, CNN; SHAP для важности признаков|
|flow_duration|Host netflow_day; packet captures|Cross-stage / Exfiltration|Network flow|Длительность соединения или flow.|max(timestamp)-min(timestamp).|RF, XGBoost, CNN; SHAP для важности признаков|
|packet_size_mean|Packet captures; Host TEST csv|Cross-stage / Exfiltration|Network flow|Средний размер пакета.|mean(frame_info.len/ip.len).|RF, XGBoost, CNN; SHAP для важности признаков|
|packet_size_std|Packet captures; Host TEST csv|Cross-stage / Exfiltration|Network flow|Стандартное отклонение размера пакета.|std(frame_info.len/ip.len).|RF, XGBoost, CNN; SHAP для важности признаков|
|inter_arrival_time_stats|Packet captures; DNS TEST csv|Cross-stage / Exfiltration|Network temporal|Интервалы между пакетами/flow events.|diff(timestamp) per flow/src/dst.|LSTM; RF/XGBoost по агрегатам окна|
|protocol_distribution|Packet captures; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network protocol|Распределение IP protocol.|count(protocol)/total per window.|RF, XGBoost, CNN; SHAP для важности признаков|
|src_port_frequency|Packet captures; netflow_day; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network port|Распределение source ports.|count(src_port)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|dst_port_frequency|Packet captures; netflow_day; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network port|Распределение destination ports.|count(dst_port)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|tcp_flags_frequency|Host VALIDATION cap/pcap/pcapng; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network TCP|Распределение TCP flags.|count(flag)/tcp_packets.|RF, XGBoost, CNN; SHAP для важности признаков|
|port53_activity_count|DNS pcap; Host packet captures/netflow|Exfiltration|DNS/network|Активность TCP/UDP port 53.|count(dst_port==53 or src_port==53).|RF, XGBoost, CNN; SHAP для важности признаков|
|flow_fan_out|LANL/Unified Host-Network; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network graph|Количество уникальных назначений от источника.|nunique(dst_host/ip) per src/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|flow_fan_in|LANL/Unified Host-Network; netflow_day|Reconnaissance/Lateral Movement|Network graph|Количество уникальных источников к назначению.|nunique(src_host/ip) per dst/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|src_dst_pair_frequency|Host TEST csv; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network graph|Частота пар src/dst.|count(src,dst) per window.|RF, XGBoost, CNN; SHAP для важности признаков|
|outbound_byte_ratio|Unified Host-Network; Host TEST netflow_day/csv; Host VALIDATION cap/pcap/pcapng; DNS/NetFlow windows|Exfiltration|Network flow|Показывает, насколько объём исходящего трафика превышает входящий; полезно для выявления передачи данных наружу.|outbound_bytes / max(inbound_bytes,1) per host/src_ip/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|external_destination_count|Unified Host-Network; Host TEST netflow_day/csv; DNS TEST csv; packet captures|Exfiltration|Network destination|Количество уникальных внешних IP-адресов или доменов, с которыми установлены соединения за окно.|nunique(external_dst_ip/domain) per host/src_ip/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|new_external_destination_indicator|Unified Host-Network; Host TEST netflow_day/csv; DNS TEST csv; packet captures|Exfiltration|Network anomaly|Индикатор соединения с внешним адресом или доменом, который ранее не наблюдался в baseline.|1 if dst not in historical_baseline(host/src_ip), else 0.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|unique_dst_host_count|LANL; Unified Host-Network; Host TEST netflow_day/csv; Host VALIDATION cap/pcap/pcapng|Reconnaissance/Lateral Movement|Network graph|Количество уникальных destination hosts; сильный индикатор сканирования или перемещения между хостами.|nunique(dst_host/dst_ip) per src_host/src_ip/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|dns_ldap_smb_dcerpc_indicator|Host VALIDATION packet captures|Reconnaissance/Lateral Movement/Collection|Network protocol indicators|Индикаторы DNS/LDAP/SMB/DCERPC по портам/декодеру.|binary/count per protocol family.|RF, XGBoost, CNN; SHAP для важности признаков|
|network_burst_score|Packet captures; netflow_day|Exfiltration|Network temporal|Всплески сетевой активности.|current_window_count / rolling_baseline.|RF, XGBoost, CNN; SHAP для важности признаков|

---

## 6. Каталог host-признаков

|Название признака|Набор данных / источник|Этап атаки|Тип признака|Описание|Формула / расчёт|Используемые модели|
|---|---|---|---|---|---|---|
|syscall_frequency|ADFA IDS; LID-DS 2021/2019; Host TRAIN csv/txt/sc; Host TEST txt/json/bson|Collection/Data Staging|Host syscall/API|Частоты системных вызовов/API событий.|count(sys_call/event/name/MethodName)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|syscall_ngram_2_frequency|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Частоты bigram системных вызовов/API.|count((call_i, call_i+1))/sequence.|LSTM; RF/XGBoost по агрегатам окна|
|syscall_ngram_3_frequency|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Частоты trigram системных вызовов/API.|count((call_i, call_i+1, call_i+2))/sequence.|LSTM; RF/XGBoost по агрегатам окна|
|syscall_transition_probability|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Вероятности переходов между вызовами.|P(call_j / call_i) from transition matrix.|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_syscall_count|ADFA IDS; LID-DS; Host csv/txt/sc|Collection/Data Staging|Host complexity|Количество уникальных вызовов в окне/trace.|nunique(syscall).|RF, XGBoost, CNN; SHAP для важности признаков|
|syscall_trace_length|ADFA IDS; LID-DS; Host ghc/txt/sc/bson/json|Collection/Data Staging|Host complexity|Длина последовательности/trace.|count(events) per trace/window.|LSTM; RF/XGBoost по агрегатам окна|
|syscall_interarrival_stats|LID-DS; Host events with timestamps|Collection/Data Staging|Host temporal|Интервалы между syscall/API событиями.|diff(timestamp) per process/trace.|LSTM; RF/XGBoost по агрегатам окна|
|collection_syscall_count|ADFA IDS; LID-DS; Host csv/txt/sc|Collection|Host collection indicator|Частоты open/read/access/stat/readdir и аналогов.|sum(call in collection_call_set).|RF, XGBoost, CNN; SHAP для важности признаков|
|directory_enumeration_count|ADFA IDS; LID-DS; Dynamic Malware; Host txt/sc|Collection|Host collection indicator|События обхода директорий/перечисления файлов.|count(readdir/list_dir/find-like events).|RF, XGBoost, CNN; SHAP для важности признаков|
|network_syscall_count|Host txt/sc; Dynamic Malware|Exfiltration/Data Staging|Host-network bridge|Системные вызовы sendto/recvfrom/connect/accept/socket.|sum(call in network_call_set).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|api_descriptor_frequency|Dynamic Malware; Host TEST bson/json|Collection/Data Staging|Host API|Частоты API/syscall-like descriptor name.|count(descriptor.name)/trace.|RF, XGBoost, CNN; SHAP для важности признаков|
|api_category_frequency|Dynamic Malware; Host TEST bson/json|Collection/Data Staging|Host API|Частоты категорий sandbox/API events.|count(category)/trace.|RF, XGBoost, CNN; SHAP для важности признаков|
|api_arg_token_count|LID-DS; Dynamic Malware; Host TEST bson/json/txt|Collection/Data Staging|Host API args|Количество/частоты токенов аргументов.|tokenize(args); count/token_frequency.|RF, XGBoost, CNN; SHAP для важности признаков|
|trace_module_frequency|Host TRAIN ghc; Dynamic Malware|Collection/Data Staging|Host trace|Частоты module/library из trace tokens.|count(trace.module)/trace.|RF, XGBoost, CNN; SHAP для важности признаков|
|trace_module_transition_frequency|Host TRAIN ghc|Collection/Data Staging|Host trace sequence|Переходы между модулями.|count((module_i,module_i+1))/trace.|LSTM; RF/XGBoost по агрегатам окна|
|trace_offset_distribution|Host TRAIN ghc|Collection/Data Staging|Host trace|Распределение offset внутри module.|bucketize(offset_hex) per module.|RF, XGBoost, CNN; SHAP для важности признаков|
|trace_density|Host TRAIN ghc; Host TEST bson/json|Collection/Data Staging|Host sequence|Плотность событий в trace/окне.|event_count / duration или event_count/trace.|LSTM; RF/XGBoost по агрегатам окна|
|login_success_count|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Количество успешных входов.|count(success_login events).|RF, XGBoost, CNN; SHAP для важности признаков|
|login_failure_count|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Количество неуспешных входов.|count(failed_login events).|RF, XGBoost, CNN; SHAP для важности признаков|
|failed_login_ratio|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Доля неуспешных попыток входа.|failed_login_count / max(total_login_count,1).|RF, XGBoost, CNN; SHAP для важности признаков|
|session_opened_count|auth.log; LANL/Windows logs|Privilege Escalation/Lateral Movement|Host auth|Количество открытых сессий.|count(session_opened).|RF, XGBoost, CNN; SHAP для важности признаков|
|session_closed_count|auth.log; LANL/Windows logs|Privilege Escalation/Lateral Movement|Host auth|Количество закрытых сессий.|count(session_closed).|RF, XGBoost, CNN; SHAP для важности признаков|
|session_duration_stats|auth.log; LANL; Windows logs|Privilege Escalation/Lateral Movement|Host auth temporal|Длительность сессий.|session_closed_time - session_opened_time; aggregate stats.|RF, XGBoost, CNN; SHAP для важности признаков|
|sudo_activity_count|auth.log/info; Linux logs|Privilege Escalation|Host privilege|Количество sudo-related событий.|count(process/source == sudo).|RF, XGBoost, CNN; SHAP для важности признаков|
|sshd_activity_count|auth.log/info; Linux logs|Lateral Movement|Host auth|Количество SSH-related событий.|count(source contains sshd).|RF, XGBoost, CNN; SHAP для важности признаков|
|cron_activity_count|auth.log/info; Linux logs|Data Staging|Host scheduled activity|Количество cron-related событий.|count(source contains cron).|RF, XGBoost, CNN; SHAP для важности признаков|
|useradd_activity_count|auth.log/info; Linux logs|Privilege Escalation|Host account management|Количество useradd/account modification events.|count(source contains useradd or account events).|RF, XGBoost, CNN; SHAP для важности признаков|
|privileged_account_ratio|LANL; Windows Event Log; OTRF; auth.log|Privilege Escalation|Host privilege|Доля событий привилегированных аккаунтов.|privileged_events / total_events.|RF, XGBoost, CNN; SHAP для важности признаков|
|user_host_interaction_count|LANL; Windows Event Log; wls_day|Lateral Movement|Host graph|Количество взаимодействий user-host.|count(user,host) per window.|RF, XGBoost, CNN; SHAP для важности признаков|
|source_ip_auth_frequency|auth.log; LANL; Windows Event Log|Lateral Movement|Host/network auth|Частота source IP в auth-событиях.|count(source_ip) per user/host/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|auth_baseline_deviation|LANL; auth.log; wls_day|Privilege Escalation/Lateral Movement|Host anomaly|Отклонение auth-поведения от baseline.|z-score или ratio(current vs historical baseline).|RF, XGBoost, CNN; SHAP для важности признаков|
|event_id_frequency|OTRF; Windows Event Log; wls_day|Reconnaissance/Privilege Escalation/Lateral Movement|Windows/Sysmon|Частоты EventID.|count(EventID)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|security_event_sequence_entropy|OTRF; Windows Event Log; wls_day|Cross-stage|Windows/Sysmon sequence|Энтропия последовательности EventID.|Shannon entropy over ordered EventID tokens.|LSTM; RF/XGBoost по агрегатам окна|
|logon_type_distribution|Windows Event Log; wls_day|Privilege Escalation/Lateral Movement|Windows auth|Распределение LogonType.|count(LogonType)/logon_events.|RF, XGBoost, CNN; SHAP для важности признаков|
|authentication_package_distribution|Windows Event Log; wls_day|Privilege Escalation/Lateral Movement|Windows auth|Распределение AuthenticationPackage.|count(package)/auth_events.|RF, XGBoost, CNN; SHAP для важности признаков|
|parent_child_process_count|OTRF; Windows Event Log; wls_day; Dynamic Malware|Reconnaissance/Privilege Escalation/Data Staging|Process tree|Количество parent-child process связей.|count(parent_process, child_process).|RF, XGBoost, CNN; SHAP для важности признаков|
|process_name_frequency|OTRF; Windows Event Log; Host process logs; wls_day|Cross-stage|Process|Частоты процессов.|count(ProcessName/path/process_id)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|command_line_length|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Длина командной строки.|len(CommandLine).|RF, XGBoost, CNN; SHAP для важности признаков|
|command_arg_count|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Количество аргументов командной строки.|len(split_commandline(CommandLine)).|RF, XGBoost, CNN; SHAP для важности признаков|
|command_line_entropy|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Энтропия аргументов; индикатор obfuscation/encoded payload.|Shannon entropy(CommandLine).|RF, XGBoost, CNN; SHAP для важности признаков|
|encoded_powershell_indicator|OTRF; Windows Event Log|Reconnaissance/Privilege Escalation/Data Staging|Command line|Индикатор закодированных PowerShell команд.|regex flags: -enc, -encodedcommand, base64-like tokens.|RF, XGBoost, CNN; SHAP для важности признаков|
|privileged_process_indicator|OTRF; Windows Event Log; auth logs|Privilege Escalation|Process/privilege|Выполнение процесса с повышенными правами.|binary/count from token/elevation/4672-like events.|RF, XGBoost, CNN; SHAP для важности признаков|
|account_discovery_indicator|OTRF; Windows Event Log|Reconnaissance|ATT&CK indicator|События/команды обнаружения учетных записей.|regex/process/event mapping to account discovery.|RF, XGBoost, CNN; SHAP для важности признаков|
|object_access_count|Windows Event Log; OTRF|Collection/Data Staging|Object access|Количество object/file access events.|count(4663/4656-like object access events).|RF, XGBoost, CNN; SHAP для важности признаков|
|source_dest_address_port_count|Windows Event Log; OTRF; netflow|Lateral Movement/Exfiltration|Hybrid network fields|Счетчики SourceAddress/DestAddress/ports из событий.|count(src,dst,port)/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|process_path_entropy|Host process logs; Dynamic Malware; Windows Event Log|Data Staging|Process/path|Энтропия пути процесса/модуля.|Shannon entropy(path).|RF, XGBoost, CNN; SHAP для важности признаков|
|suspicious_path_indicator|Host process logs; Dynamic Malware; Windows Event Log|Data Staging|Process/path|Индикатор временных/пользовательских/нестандартных путей.|regex/path category flags.|RF, XGBoost, CNN; SHAP для важности признаков|
|module_basename_frequency|Dynamic Malware; BSON/JSON; GHC|Data Staging|Module/path|Частоты basename библиотек/модулей.|count(basename(module_path)).|RF, XGBoost, CNN; SHAP для важности признаков|
|module_path_entropy|Dynamic Malware; BSON/JSON; GHC|Data Staging|Module/path|Энтропия module/path строк.|Shannon entropy(module_path).|RF, XGBoost, CNN; SHAP для важности признаков|
|unique_file_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Collection|File activity|Количество уникальных файлов, к которым был выполнен доступ; помогает отличить доступ к большому числу разных файлов от многократного чтения одного файла.|nunique(file_path/object_name) per process/user/host/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|sensitive_file_extension_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Collection|File activity / sensitive data|Количество обращений к потенциально чувствительным расширениям файлов: `.docx`, `.xlsx`, `.pdf`, `.csv`, `.sql`, `.zip` и другим.|count(file_ext in sensitive_ext_set) per process/user/host/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|archive_creation_count|Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Data Staging|File/archive activity|Количество событий создания архивов перед возможной эксфильтрацией: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`.|count(created_file_ext in archive_ext_set) or archive-write events per window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|compression_process_indicator|Windows Event Log / OTRF; Dynamic Malware; Host process logs; command-line telemetry|Data Staging|Process/command-line|Индикатор использования процессов и утилит архивации или компрессии: `zip`, `rar`, `7z`, `tar`, `gzip`, `powershell Compress-Archive` и др.|binary/count if process_name or command_line matches compression_tool_set.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|failed_then_success_login_indicator|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth sequence|Индикатор последовательности: несколько неуспешных входов, затем успешный вход; характерно для brute-force/password spraying.|1 if failed_login_count >= k before success_login within T for same user/src/host.|RF, XGBoost, CNN, LSTM; SHAP|
|rare_process_execution_score|OTRF; Windows Event Log; Dynamic Malware; Host process logs; Maintainable Log Dataset|Reconnaissance/Data Staging|Process anomaly|Оценка редкости запуска процесса относительно нормального поведения системы, пользователя или хоста.|-log(P(process_name | host/user/baseline)) или inverse frequency rank.|RF, XGBoost, CNN; SHAP для важности признаков|
|file_access_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware|Collection|File activity|Количество операций доступа к файлам.|count(open/read/access/stat/readdir/object access).|RF, XGBoost, CNN; SHAP для важности признаков|
|file_access_rate|ADFA/LID-DS; Maintainable; Dynamic Malware|Collection|File activity temporal|Частота доступа к файлам.|file_access_count / window_duration.|LSTM; RF/XGBoost по агрегатам окна|
|file_access_entropy|Host logs; Maintainable; Dynamic Malware|Collection/Data Staging|File activity|Энтропия accessed file paths.|Shannon entropy(file_path tokens).|RF, XGBoost, CNN; SHAP для важности признаков|
|filesystem_used_pct_stats|Host TRAIN filesystem.log|Data Staging|Host resource/storage|Статистика использования ФС.|mean/max/std(system.filesystem.used.pct).|RF, XGBoost, CNN; SHAP для важности признаков|
|filesystem_pressure_ratio|Host TRAIN filesystem.log|Data Staging|Host resource/storage|Давление по свободному месту.|1 - available/total или used/total.|RF, XGBoost, CNN; SHAP для важности признаков|
|inode_free_ratio|Host TRAIN filesystem.log/fsstat.log|Data Staging|Host resource/storage|Доля свободных inode.|free_files/total_files.|RF, XGBoost, CNN; SHAP для важности признаков|
|fs_total_used_ratio|Host TRAIN fsstat.log|Data Staging|Host resource/storage|Общее заполнение ФС.|total_size.used / total_size.total.|RF, XGBoost, CNN; SHAP для важности признаков|
|disk_read_bytes_rate|Host TRAIN diskio.log|Collection/Data Staging|Host resource/I/O|Скорость чтения с диска.|delta(read.bytes)/delta(time).|RF, XGBoost, CNN; SHAP для важности признаков|
|disk_write_bytes_rate|Host TRAIN diskio.log|Data Staging|Host resource/I/O|Скорость записи на диск.|delta(write.bytes)/delta(time).|RF, XGBoost, CNN; SHAP для важности признаков|
|disk_read_write_ratio|Host TRAIN diskio.log|Collection/Data Staging|Host resource/I/O|Соотношение чтения и записи.|read_bytes / max(write_bytes,1).|RF, XGBoost, CNN; SHAP для важности признаков|
|diskio_ops_rate|Host TRAIN diskio.log|Data Staging|Host resource/I/O|Темп I/O операций.|delta(io.ops)/delta(time).|RF, XGBoost, CNN; SHAP для важности признаков|
|diskio_busy_pct|Host TRAIN diskio.log|Data Staging|Host resource/I/O|Занятость дискового I/O.|system.diskio.iostat.busy или derived rate.|RF, XGBoost, CNN; SHAP для важности признаков|
|cpu_total_pct_stats|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|Статистика общей загрузки CPU.|mean/max/std(host.cpu.pct or total.norm.pct).|RF, XGBoost, CNN; SHAP для важности признаков|
|cpu_user_system_idle_ratio|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|Соотношения user/system/idle CPU.|user_pct/system_pct/idle_pct ratios.|RF, XGBoost, CNN; SHAP для важности признаков|
|cpu_burst_score|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|Всплески CPU относительно baseline.|current_cpu / rolling_mean_cpu.|RF, XGBoost, CNN; SHAP для важности признаков|
|memory_usage_stats|Host TRAIN memory.log; ISOT Cloud IDS|Data Staging|Host resource/memory|Статистика использования памяти, если поля доступны после normalization.|mean/max/std(memory used/pct).|RF, XGBoost, CNN; SHAP для важности признаков|
|load_average_stats|Host TRAIN load.log; ISOT Cloud IDS|Data Staging|Host resource/load|Статистика load average.|mean/max/std(load fields).|RF, XGBoost, CNN; SHAP для важности признаков|
|network_interface_bytes_rate|Host TRAIN network.log|Exfiltration|Host resource/network|Темп bytes по network interface telemetry.|delta(network.bytes)/delta(time).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|socket_count|Host TRAIN socket.summary.log|Exfiltration/Lateral Movement|Host network/socket|Количество открытых sockets.|count sockets or socket.summary metrics.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|service_state_change_count|Host TRAIN service.log|Data Staging|Host service|Количество изменений состояния сервисов.|count(service state changes).|RF, XGBoost, CNN; SHAP для важности признаков|
|uptime_seconds|Host TRAIN uptime.log|Operational context|Host context|Время работы системы.|parse uptime seconds.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|log_event_count|Maintainable Log Dataset; Host log/syslog/messages/mainlog|Cross-stage|Log volume|Количество log events.|count(log events)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|log_volume_rate|Maintainable; Host logs|Cross-stage|Log volume temporal|Темп генерации логов.|event_count/window_duration.|LSTM; RF/XGBoost по агрегатам окна|
|log_level_frequency|Host TEST log; syslog-like logs|Cross-stage|Log categorical|Частоты уровней log level.|count(level)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|warning_error_count|Host TEST log; syslog-like logs|Cross-stage|Log anomaly|Количество warnings/errors.|count(level in {warn,error,critical}).|RF, XGBoost, CNN; SHAP для важности признаков|
|component_frequency|Host TEST log; syslog-like logs|Cross-stage|Log categorical|Частоты компонентов/источников логов.|count(component/source)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|message_template_frequency|Maintainable; Host logs|Cross-stage|Log template|Частоты шаблонов сообщений.|parse template; count(template_id).|RF, XGBoost, CNN; SHAP для важности признаков|
|event_type_frequency|Host TRAIN json/log-derived files|Cross-stage|Log/event type|Частоты event_type: stats/dns/alert и др.|count(event_type)/window.|RF, XGBoost, CNN; SHAP для важности признаков|
|alert_count|Host TRAIN json/log-derived files|Cross-stage|Alert context|Количество alert-событий.|count(event_type==alert or alert present).|RF, XGBoost, CNN; SHAP для важности признаков|
|task_lifecycle_duration|Dynamic Malware; Host TEST log/json|Data Staging|Sandbox context|Длительность sandbox task/lifecycle.|completed_on - started_on or task timing fields.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|scenario_image_context|Host VALIDATION csv; Maintainable/LID-DS metadata|Context/labeling|Scenario context|Контекст image/scenario для join с событиями.|categorical scenario_name/image_name; не использовать как модельный признак при leakage risk.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|exploit_start_offset|Host VALIDATION csv|Context/labeling|Scenario context/time|Смещение старта exploit.|exploit_start_time field; use for window labeling.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|recording_duration|Host VALIDATION csv; LID-DS metadata|Context/labeling|Scenario context/time|Длительность записи сценария.|recording_time.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|

---

## 7. Каталог hybrid и sequence-признаков

|Название признака|Набор данных / источник|Этап атаки|Тип признака|Описание|Формула / расчёт|Используемые модели|
|---|---|---|---|---|---|---|
|host_network_time_delta|Unified Host-Network; LANL; Host + DNS/NetFlow joins|Cross-stage|Hybrid temporal|Временной лаг между host event и network event.|abs(t_host - nearest(t_network)).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|process_to_network_burst_score|Unified Host-Network; Dynamic Malware + pcap/netflow|Data Staging/Exfiltration|Hybrid correlation|Связь запуска процесса и сетевого всплеска.|network_burst_score within N seconds after process start.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|auth_to_network_correlation|LANL; Unified Host-Network; auth.log + netflow|Lateral Movement/Exfiltration|Hybrid correlation|Корреляция auth-событий с сетевыми flows.|count(network flows after auth event)/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|file_to_network_correlation|Unified Host-Network; LID-DS/Dynamic Malware + netflow|Collection/Exfiltration|Hybrid correlation|Связь file access/data staging с network outflow.|network bytes after file_access window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|cpu_io_network_correlation|Host telemetry + netflow|Data Staging/Exfiltration|Hybrid correlation|Связь CPU/I/O spikes с network spikes.|rolling_corr(cpu/disk/network metrics).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|source_loghost_graph_degree|wls_day; Windows logs; LANL|Lateral Movement|Hybrid graph|Степень source/loghost graph.|degree(Source, LogHost) per window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|cross_source_event_count|Multi-source integration layer|Cross-stage|Hybrid aggregation|Количество событий из разных источников в одном окне.|count events by domain/source within unified window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|sequence_window_event_count|All timestamped DNS/host/network sources|Cross-stage|Sequence|Количество событий в LSTM window.|count(events) in ordered window.|LSTM; RF/XGBoost по агрегатам окна|
|sequence_window_duration|All timestamped DNS/host/network sources|Cross-stage|Sequence|Длительность sequence window.|last_event_time - first_event_time.|LSTM; RF/XGBoost по агрегатам окна|
|sequence_event_type_entropy|All event streams|Cross-stage|Sequence|Энтропия типов событий в последовательности.|Shannon entropy(event_type tokens).|LSTM; RF/XGBoost по агрегатам окна|
|sequence_temporal_order_pattern|All event streams|Cross-stage|Sequence|Порядок стадий/типов событий в атаке.|ordered tokens mapped to ATT&CK/stage labels.|LSTM; RF/XGBoost по агрегатам окна|
|process_file_network_sequence|Unified Host-Network; Dynamic Malware + pcap/netflow; LID-DS/Dynamic Malware + network joins|Collection → Data Staging → Exfiltration|Hybrid sequence|Отслеживает цепочку действий: доступ к файлам → архивация/подготовка → передача данных по сети.|ordered pattern match: file_access -> archive/compress -> outbound_network_event within T.|LSTM, late fusion; RF/XGBoost по агрегатам окна|
|stage_transition_pattern|All timestamped DNS/host/network sources; MITRE ATT&CK mapped events|Sequential modelling|Sequence / attack progression|Явно моделирует переходы между стадиями атаки и помогает LSTM выявлять поведенческую прогрессию злоумышленника.|ordered stage tokens; transition counts/probabilities between Reconnaissance, Privilege Escalation, Lateral Movement, Collection, Data Staging, Exfiltration.|LSTM; RF/XGBoost по агрегатам окна; SHAP для sequence-aware attribution|
|label_binary|All supervised-ready artifacts|Target/context|Label|Целевая бинарная метка. Не является input feature.|0=benign, 1=malicious/exfiltration, NULL=unknown.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|label_family|All supervised-ready artifacts|Target/context|Label|Семейство/тип атаки. Не input feature.|benign/dns_exfiltration/malware/phishing/lateral_movement/etc.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|
|label_status|All artifacts|Target/context|Label quality|Статус метки для контроля качества и leakage.|explicit/inferred/weak/partial/unlabeled/conflicting.|Pipeline/label resolver; не использовать как независимый признак без контроля leakage|

---

## 8. Матрица датасетов и ключевых групп признаков

| Датасет / источник | Роль | Основные группы признаков | Этапы атаки | Комментарий по использованию |
|---|---|---|---|---|
| CIC-Bell-DNS-EXF-2021 | TRAIN | DNS lexical, entropy, RR/TTL, query-rate, inter-query intervals, unique subdomain ratio | Exfiltration | Основной attack-class DNS источник. |
| CIC-Bell-DNS-2021 | TRAIN + VALIDATION split | Те же DNS признаки, но для benign baseline и FP-контроля | Exfiltration / Benign baseline | Использовать для benign-поведения и настройки threshold. |
| Mendeley DNS Exfiltration Dataset | TEST | DNS lexical/temporal/numeric feature table, source_ip windows | Exfiltration | Только финальная проверка generalization; не обучать. |
| ADFA IDS | TRAIN | syscall frequencies, n-grams, transitions, trace length, collection syscalls | Collection, Data Staging | Базовый HIDS/syscall benchmark. |
| LID-DS 2021 | TRAIN | syscall/API sequence, syscall args, file access, inter-arrival timings | Collection, Data Staging, Pre-exfiltration | Основной sequence source для LSTM host branch. |
| LID-DS 2019 | VALIDATION | Те же признаки, что LID-DS 2021 | Collection, Data Staging | Cross-version validation. |
| Maintainable Log Dataset | TRAIN | log templates, event volume, multi-stage event sequences, file access/log correlation | Reconnaissance, Collection, Data Staging | Enterprise log behaviour и multi-stage modelling. |
| LANL Dataset | VALIDATION | auth frequency, user-host interaction, failed login ratio, privileged account usage, lateral movement graph | Privilege Escalation, Lateral Movement | Валидация enterprise behaviour. |
| Windows Event Log / OTRF | VALIDATION | EventID, process tree, PowerShell/command line, logon/auth, object access, SourceAddress/DestAddress | Reconnaissance, Privilege Escalation, Lateral Movement | SOC-oriented Windows/Sysmon validation. |
| Unified Host-Network / LANL | TEST | host auth/process + netflow + correlation features | Full lifecycle | Финальный hybrid test. |
| ISOT Cloud IDS | TEST | CPU/memory/I/O/log/cloud workload anomalies | Data Staging | Проверка переносимости в cloud-like среду. |
| Dynamic Malware Analysis Dataset | TEST | API/syscall events, command line/path/module tokens, process tree, sandbox task lifecycle | Collection, Data Staging, Pre-exfiltration | Проверка malware-driven host behaviour. |
| DNS VALIDATION pcap | VALIDATION | DNS amplification ratio, qname/qtype, response size, TTL, RCODE/NXDOMAIN, packet/byte counts | Exfiltration / DNS amplification | Требуется packet parser с DNS decoding. |
| DNS VALIDATION txt | VALIDATION | domain length, label count, TLD/SLD, entropy, enrichment | Exfiltration / domain validation | `unknown` class нельзя использовать как supervised class без явного решения. |
| Host VALIDATION cap/pcap/pcapng | VALIDATION | packet/flow counts, protocol distribution, TCP/UDP ports, TCP flags, DNS/LDAP/SMB/DCERPC indicators | Reconnaissance, Lateral Movement, Exfiltration | Labels только через scenario/file metadata или внешний mapping. |
| Host VALIDATION csv | VALIDATION | scenario/image context, exploit flag, recording duration, exploit start offset | Context / evaluation | Использовать как label/context metadata, не как обычный model feature. |
| Host TEST bson/json/txt | TEST | API/syscall-like frequencies, n-grams, transitions, args, process context, command/path entropy | Collection, Data Staging | Только testing/inference evaluation; нужны внешние labels для supervised метрик. |
| Host TEST wls_day | TEST | EventID, login ratios, auth package, process chains, event sequences | Privilege Escalation, Lateral Movement | Учитывать event-specific schema. |
| Host TEST netflow_day/csv | TEST | flow duration, bytes/packets, ports, protocol, fan-in/fan-out, TCP flags | Reconnaissance, Lateral Movement, Exfiltration | TEST-only; не обучать. |

---

## 9. Минимальный feature schema для Parquet artifacts

### 9.1. Обязательные traceability-поля

| Поле | Назначение | Использовать как model feature? |
|---|---|---|
| `event_id` | Уникальный ID нормализованного события | Нет |
| `source_file_id` | ID raw-файла из catalog | Нет |
| `source_row_id` / `packet_id` | Номер строки/пакета/события | Нет |
| `dataset_domain` | `dns`, `host`, `network`, `hybrid` | Нет |
| `dataset_role` | TRAIN / VALIDATION / TEST | Нет |
| `dataset_name` | Название датасета | Нет, кроме audit/reporting |
| `dataset_format` | csv, pcap, json, log, bson, txt, ... | Нет, кроме parser/debug |
| `parser_name` | Имя parser handler | Нет |
| `parser_version` | Версия parser logic | Нет |
| `event_timestamp` | Нормализованное время события | Да, только как derived time features / ordering |
| `window_id` | ID временного окна | Нет |
| `sequence_id` | ID sequence-window | Нет |

### 9.2. Обязательные label-поля

| Поле | Назначение |
|---|---|
| `label_binary` | 0=benign, 1=attack/exfiltration/malicious, NULL=unknown |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, collection, data_staging, unknown |
| `label_subtype` | Конкретный subtype/scenario, если доступен |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label |
| `label_confidence` | 1.0 explicit; 0.7-0.9 inferred; 0.4-0.7 weak; 0 unlabeled |
| `label_mapping_rule_id` | ID правила label resolver |

---

## 10. Что исключать из model features

| Поле / группа | Почему исключать |
|---|---|
| `source_file`, basename файла, полный путь | Может напрямую кодировать класс через `benign`, `malware`, `attack`, `exfiltration`. |
| `dataset_role` | TRAIN/VALIDATION/TEST leakage. |
| `dataset_name` | Может позволить модели запомнить датасет вместо поведения. |
| `scenario_name`, `image_name` | Использовать только для label join / evaluation metadata; как feature — высокий leakage risk. |
| `label_*` | Это target/audit fields, не input features. |
| Raw payload/body | В scope проекта metadata/behavioural detection, не payload inspection. |
| Абсолютные локальные пути | Непереносимы и могут создавать leakage. |

---

## 11. Приоритет реализации признаков

### P0 — сначала реализовать

1. DNS lexical/entropy: `dns_query_length`, `dns_subdomain_depth`, `dns_entropy`, `dns_label_count`, `dns_digit_count`, `dns_special_char_count`.
2. DNS temporal: `dns_query_rate`, `dns_inter_query_interval_stats`, `dns_queries_per_window`.
3. DNS protocol: `ttl_mean`, `ttl_variance`, `rr_count`, `rr_type_frequency_*`, `dns_response_size_stats`, `dns_nxdomain_rate`.
4. Host syscall/API: `syscall_frequency`, `syscall_ngram_2_frequency`, `syscall_transition_probability`, `syscall_trace_length`.
5. Host auth: `failed_login_ratio`, `failed_then_success_login_indicator`, `session_opened_count`, `sudo_activity_count`, `user_host_interaction_count`.
6. Windows/Sysmon: `event_id_frequency`, `parent_child_process_count`, `command_line_entropy`, `encoded_powershell_indicator`.
7. Network: `packet_count`, `byte_count`, `flow_duration`, `protocol_distribution`, `dst_port_frequency`, `outbound_byte_ratio`, `external_destination_count`.
8. Sequence: `sequence_window_event_count`, `sequence_event_type_entropy`, `process_file_network_sequence`, `stage_transition_pattern`, ordered event tokens.

### P1 — после базового pipeline

1. Domain enrichment: ASN/country/domain age/reputation.
2. Hybrid correlations: host-network time delta, file-to-network, auth-to-network.
3. Resource telemetry and staging indicators: CPU/disk/filesystem/network interface burst features, `archive_creation_count`, `compression_process_indicator`, `sensitive_file_extension_count`.
4. Graph and baseline features: fan-in/fan-out, Source-LogHost degree, `unique_dst_host_count`, `new_external_destination_indicator`, `rare_process_execution_score`.

### P2 — расширение после baseline

1. Advanced command-line tokenization.
2. Template mining для logs.
3. Per-user/per-host long-term baseline deviation.
4. Feature stability checks across folds and datasets.

---

## 12. Рекомендуемый порядок реализации в коде

1. Создать `feature_catalog.yml/json` из этого Markdown как машинно-читаемый контракт.
2. Для каждого parser output создать normalized event schema.
3. Реализовать feature extractors по группам:
   - `dns_lexical_extractor`
   - `dns_protocol_extractor`
   - `dns_temporal_extractor`
   - `network_flow_extractor`
   - `host_syscall_extractor`
   - `host_auth_extractor`
   - `windows_event_extractor`
   - `resource_telemetry_extractor`
   - `hybrid_correlation_extractor`
   - `sequence_window_builder`
4. Сохранять результаты в Parquet:
   - `normalized_events/`
   - `feature_windows/`
   - `sequence_windows/`
   - `model_ready/`
5. Для каждого output сохранять `feature_extraction_report.md` с количеством строк, missing values, label_status и leakage checks.

---

## 13. Итоговое решение

Для проекта нужно реализовать не один общий extractor, а набор специализированных extractor layers:

- DNS lexical / protocol / temporal extractors;
- host syscall/API/trace extractors;
- authentication and Windows/Sysmon extractors;
- resource telemetry extractors;
- network/flow extractors;
- staging/compression and sensitive-file activity extractors;
- hybrid correlation extractors;
- sequence window builder для LSTM, включая process-file-network и stage-transition patterns.

Итоговый framework должен использовать один согласованный feature catalogue, но разные parser-specific источники данных. Это позволит сохранить traceability, избежать leakage и подготовить признаки для RF, XGBoost, CNN, LSTM и SHAP-анализа.
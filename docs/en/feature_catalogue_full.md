# Feature Catalogue for the Proposal Project

**Preparation date:** 2026-06-13  
**Project:** Behaviour-driven hybrid learning for data exfiltration detection  
**Purpose:** to define the complete list of features that must be extracted during Stage Two / Feature Engineering for the DNS, Host, Network/Hybrid, and sequence branches.
**Update:** additional features from the new reference images were added: file-access diversity, sensitive file access, archiving/compression, external destinations, failed-then-success authentication, rare process execution, and stage-transition sequence indicators.

---

## 1. How to read this document

This catalogue answers the question: **which exact features are used in the final framework**.

The document is organized by features rather than by datasets. This follows the structure shown in the submitted reference images:

- `Feature name`
- `Dataset / source`
- `Attack stage`
- `Feature type`
- `Description`
- `Formula / calculation`
- `Models used`

The related document `Dataset Feature Extraction Map` serves as a map: **which groups of features are extracted from each dataset**. This catalogue serves as a dictionary: **which features must exist in the final feature store / Parquet artifacts / model-ready datasets**.

---

## 2. Feature selection principles

1. **Do not mix TRAIN / VALIDATION / TEST.** Features may be calculated with the same functions, but models must not be trained on TEST data.
2. **Do not merge DNS and Host data at the raw level.** Integration is performed at the level of normalized events, time windows, and features.
3. **Labels are not input features.** `label_binary`, `label_family`, and `label_status` are required for supervised learning and auditing, but must not be included in `X_train`.
4. **Exclude fields that cause direct leakage.** `source_file`, file name, `dataset_role`, and `scenario_name` must not be used as ordinary model features if they directly encode the class.
5. **Build sequence features separately.** LSTM requires ordered events and sliding windows; RF/XGBoost/CNN require aggregates over events/windows.
6. **The absence of a label does not mean benign.** For unlabeled sources, use `label_binary=NULL` until the label resolver is configured.

---

## 3. Feature calculation levels

| Level | Description | Main models |
|---|---|---|
| Event-level | Features of a single DNS query, syscall, process event, auth event, packet, or log event | RF, XGBoost, CNN |
| Window-level | Aggregations over a time window by host/source_ip/user/domain/process | RF, XGBoost, CNN |
| Flow-level | Aggregations for a network connection or 5-tuple | RF, XGBoost |
| Trace-level | Syscall/API/module trace as a sequence | CNN, LSTM |
| Sequence-level | Ordered multi-source events, 50-100 events per window | LSTM |
| Hybrid-level | Host + network/DNS correlation by time, host, scenario, or external mapping | Late fusion, RF/XGBoost, LSTM |

---

## 4. DNS feature catalogue

|Feature name|Dataset / source|Attack stage|Feature type|Description|Formula / calculation|Models used|
|---|---|---|---|---|---|---|
|dns_query_length|CIC-Bell-DNS-EXF-2021; CIC-Bell-DNS-2021; Mendeley DNS; DNS TRAIN csv/pcap/pcap.csv; DNS VALIDATION pcap/txt; DNS TEST csv|Exfiltration|Network/DNS lexical|Length of the queried domain / qname / FQDN.|len(qname) or field `len` / `FQDN_count`.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_subdomain_length|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv/csv; DNS VALIDATION txt/pcap|Exfiltration|Network/DNS lexical|Length of the subdomain without TLD/SLD.|len(subdomain_part).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_subdomain_depth|CIC-Bell; Mendeley DNS; DNS TRAIN pcap; DNS VALIDATION pcap/txt|Exfiltration|Network/DNS lexical|Number of subdomain levels.|max(label_count - 2, 0).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_label_count|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS lexical|Number of labels in the domain.|count(split(qname, ".")).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_label_avg_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Average label length.|mean(len(label_i)).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_label_max_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Maximum label length.|max(len(label_i)).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_longest_word_len|CIC-Bell; Mendeley DNS; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Length of the longest token/word in the domain.|max(token_length).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_entropy|CIC-Bell; Mendeley DNS; DNS TRAIN csv/pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS entropy|Character entropy of the domain; indicator of encoded/high-random subdomains.|Shannon entropy over qname/subdomain.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_rr_name_entropy|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS entropy|Entropy of the resource-record name.|Shannon entropy over rr_name.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_lowercase_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Number of lowercase characters.|count(c.islower()).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_uppercase_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Number of uppercase characters.|count(c.isupper()).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_digit_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Number of digits in the domain.|count(c.isdigit()).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_special_char_count|CIC-Bell; DNS TRAIN pcap.csv|Exfiltration|Network/DNS lexical|Number of non-alphanumeric characters.|count(non-alnum chars).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_tld|CIC-Bell; Mendeley DNS; DNS TRAIN csv; DNS VALIDATION txt|Exfiltration|Network/DNS categorical|Top-level domain.|extract_tld(qname). Encode using frequency/target-safe encoding.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_sld|CIC-Bell; Mendeley DNS; DNS TRAIN csv/pcap.csv; DNS VALIDATION txt|Exfiltration|Network/DNS categorical|Second-level domain / parent domain.|extract_sld(qname).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_1gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Frequencies of unigram characters/tokens.|count 1-gram / total grams.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_2gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Bigram frequencies.|count 2-gram / total grams.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_3gram_frequency|DNS TRAIN csv; CIC-Bell domain feature tables|Exfiltration|Network/DNS lexical|Trigram frequencies.|count 3-gram / total grams.|RF, XGBoost, CNN; SHAP for feature importance|
|domain_age_days|DNS TRAIN csv; domain feature tables|Exfiltration|DNS enrichment|Domain age, if a WHOIS-derived field is available.|parse `Domain_Age` or now - Creation_Date_Time.|RF, XGBoost, CNN; SHAP for feature importance|
|domain_creation_time_features|DNS TRAIN csv|Exfiltration|DNS enrichment/time|Derived features from Creation_Date_Time.|year/month/age_bucket, missing flag.|RF, XGBoost, CNN; SHAP for feature importance|
|name_server_count|DNS TRAIN csv; pcap.csv|Exfiltration|DNS enrichment/RR|Number of NS / distinct name servers.|count(distinct NS).|RF, XGBoost, CNN; SHAP for feature importance|
|distinct_domain_count|DNS TRAIN pcap.csv; DNS pcap windows|Exfiltration|DNS aggregation|Number of unique domains in the window.|nunique(qname) over window.|RF, XGBoost, CNN; SHAP for feature importance|
|distinct_subdomain_count|CIC-Bell; Mendeley DNS; pcap windows|Exfiltration|DNS aggregation|Number of unique subdomains in the window.|nunique(subdomain) over {src_ip, domain, window}.|RF, XGBoost, CNN; SHAP for feature importance|
|unique_subdomain_ratio|CIC-Bell; Mendeley DNS|Exfiltration|DNS aggregation|Ratio of unique subdomains to total queries.|unique_subdomains / total_queries.|RF, XGBoost, CNN; SHAP for feature importance|
|distinct_ip_count|DNS TRAIN pcap.csv; pcap parser|Exfiltration|DNS enrichment/RR|Number of unique IPs in responses.|nunique(answer_ip).|RF, XGBoost, CNN; SHAP for feature importance|
|unique_asn_count|DNS TRAIN csv/pcap.csv|Exfiltration|DNS enrichment|Number of ASNs from responses or enrichment.|nunique(ASN).|RF, XGBoost, CNN; SHAP for feature importance|
|unique_country_count|DNS TRAIN pcap.csv|Exfiltration|DNS enrichment|Number of countries from IP/ASN enrichment.|nunique(country).|RF, XGBoost, CNN; SHAP for feature importance|
|ttl_mean|DNS TRAIN csv/pcap.csv; DNS pcap; DNS VALIDATION pcap|Exfiltration|DNS protocol/RR|Mean TTL in responses.|mean(TTL) per domain/window.|RF, XGBoost, CNN; SHAP for feature importance|
|ttl_variance|DNS TRAIN pcap.csv; DNS pcap|Exfiltration|DNS protocol/RR|TTL variance.|var(TTL) per domain/window.|RF, XGBoost, CNN; SHAP for feature importance|
|unique_ttl_count|DNS TRAIN pcap.csv|Exfiltration|DNS protocol/RR|Number of unique TTL values.|nunique(TTL).|RF, XGBoost, CNN; SHAP for feature importance|
|rr_count|DNS TRAIN pcap.csv; DNS pcap|Exfiltration|DNS protocol/RR|Number of resource records.|count(RR).|RF, XGBoost, CNN; SHAP for feature importance|
|rr_rate|DNS TRAIN pcap.csv; DNS pcap windows|Exfiltration|DNS protocol/RR|RR rate within the window.|rr_count / window_duration.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_A|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of A records.|count(rr_type == A) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_AAAA|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of AAAA records.|count(rr_type == AAAA) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_CNAME|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of CNAME records.|count(rr_type == CNAME) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_MX|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of MX records.|count(rr_type == MX) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_NS|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of NS records.|count(rr_type == NS) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_PTR|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of PTR records.|count(rr_type == PTR) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_SOA|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of SOA records.|count(rr_type == SOA) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_SRV|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of SRV records.|count(rr_type == SRV) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_TXT|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequency of TXT records; important for DNS tunnelling/exfiltration.|count(rr_type == TXT) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|rr_type_frequency_NULL_OPT_HINFO|DNS TRAIN pcap.csv; DNS pcap parser|Exfiltration|DNS protocol/RR|Frequencies of rare RR types.|count(NULL/OPT/HINFO) / rr_count.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_qtype_frequency|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Distribution of query types.|count(qtype)/total_queries.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_qclass_frequency|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Distribution of qclass.|count(qclass)/total_queries.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_response_size_stats|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol/network|Statistics of DNS response size.|mean/max/std(response_bytes) per window.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_answer_count|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Number of answer records in the response.|count(answers) per response/window.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_rcode_distribution|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol|Distribution of response codes.|count(rcode)/responses.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_nxdomain_rate|DNS TRAIN/VALIDATION pcap|Exfiltration|DNS protocol/anomaly|NXDOMAIN rate.|count(rcode == NXDOMAIN) / responses.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_amplification_ratio|DNS VALIDATION pcap; DNS pcap|Exfiltration|DNS attack-specific|Ratio of response size/count to query size/count for amplification.|sum(response_bytes)/max(sum(query_bytes),1).|RF, XGBoost, CNN; SHAP for feature importance|
|dns_inter_query_interval_stats|DNS TRAIN/VALIDATION pcap; DNS TEST csv|Exfiltration|DNS temporal|Intervals between DNS queries.|diff(timestamp) by src_ip/domain; mean/std/min/max.|LSTM; RF/XGBoost on window aggregates|
|dns_query_rate|CIC-Bell; Mendeley DNS; DNS TEST csv|Exfiltration|DNS temporal|DNS query frequency.|count(query)/time_window.|LSTM; RF/XGBoost on window aggregates|
|dns_queries_per_window|CIC-Bell; Mendeley DNS; DNS TEST csv|Exfiltration|DNS temporal|Number of queries in a fixed window.|count(query) over sliding window.|LSTM; RF/XGBoost on window aggregates|
|dns_source_ip_query_count|DNS TEST csv; DNS pcap|Exfiltration|DNS/network aggregation|Number of queries by source/client IP.|count(query) group by source_ip/window.|RF, XGBoost, CNN; SHAP for feature importance|
|dnsbl_provider_match|DNS TEST csv|Exfiltration|DNS enrichment|Relationship between query_domain and DNSBL/provider domain.|join/compare resolver_or_parent_domain and query_domain.|RF, XGBoost, CNN; SHAP for feature importance|
|url_length|DNS TRAIN csv PhishTank-like feed|Reconnaissance/Exfiltration|URL lexical|URL length from phishing/feed sources.|len(url).|RF, XGBoost, CNN; SHAP for feature importance|
|url_token_entropy|DNS TRAIN csv PhishTank-like feed|Reconnaissance/Exfiltration|URL lexical|Entropy of URL path/query tokens.|Shannon entropy over URL tokens.|RF, XGBoost, CNN; SHAP for feature importance|

---

## 5. Network / flow / packet feature catalogue

|Feature name|Dataset / source|Attack stage|Feature type|Description|Formula / calculation|Models used|
|---|---|---|---|---|---|---|
|packet_count|DNS pcap; Host VALIDATION cap/pcap/pcapng; Host TEST csv/netflow_day|Cross-stage / Exfiltration|Network flow|Number of packets in a flow/window.|count(packet) group by flow/window.|RF, XGBoost, CNN; SHAP for feature importance|
|byte_count|DNS pcap; Host cap/pcap/pcapng/csv/netflow|Cross-stage / Exfiltration|Network flow|Number of bytes in a flow/window.|sum(packet_len/ip_len/tcp_len/flow_bytes).|RF, XGBoost, CNN; SHAP for feature importance|
|flow_duration|Host netflow_day; packet captures|Cross-stage / Exfiltration|Network flow|Connection or flow duration.|max(timestamp)-min(timestamp).|RF, XGBoost, CNN; SHAP for feature importance|
|packet_size_mean|Packet captures; Host TEST csv|Cross-stage / Exfiltration|Network flow|Mean packet size.|mean(frame_info.len/ip.len).|RF, XGBoost, CNN; SHAP for feature importance|
|packet_size_std|Packet captures; Host TEST csv|Cross-stage / Exfiltration|Network flow|Standard deviation of packet size.|std(frame_info.len/ip.len).|RF, XGBoost, CNN; SHAP for feature importance|
|inter_arrival_time_stats|Packet captures; DNS TEST csv|Cross-stage / Exfiltration|Network temporal|Intervals between packets/flow events.|diff(timestamp) per flow/src/dst.|LSTM; RF/XGBoost on window aggregates|
|protocol_distribution|Packet captures; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network protocol|Distribution of IP protocol values.|count(protocol)/total per window.|RF, XGBoost, CNN; SHAP for feature importance|
|src_port_frequency|Packet captures; netflow_day; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network port|Distribution of source ports.|count(src_port)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|dst_port_frequency|Packet captures; netflow_day; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network port|Distribution of destination ports.|count(dst_port)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|tcp_flags_frequency|Host VALIDATION cap/pcap/pcapng; Host TEST csv|Reconnaissance/Lateral Movement/Exfiltration|Network TCP|Distribution of TCP flags.|count(flag)/tcp_packets.|RF, XGBoost, CNN; SHAP for feature importance|
|port53_activity_count|DNS pcap; Host packet captures/netflow|Exfiltration|DNS/network|TCP/UDP port 53 activity.|count(dst_port==53 or src_port==53).|RF, XGBoost, CNN; SHAP for feature importance|
|flow_fan_out|LANL/Unified Host-Network; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network graph|Number of unique destinations per source.|nunique(dst_host/ip) per src/window.|RF, XGBoost, CNN; SHAP for feature importance|
|flow_fan_in|LANL/Unified Host-Network; netflow_day|Reconnaissance/Lateral Movement|Network graph|Number of unique sources per destination.|nunique(src_host/ip) per dst/window.|RF, XGBoost, CNN; SHAP for feature importance|
|src_dst_pair_frequency|Host TEST csv; netflow_day|Reconnaissance/Lateral Movement/Exfiltration|Network graph|Frequency of src/dst pairs.|count(src,dst) per window.|RF, XGBoost, CNN; SHAP for feature importance|
|outbound_byte_ratio|Unified Host-Network; Host TEST netflow_day/csv; Host VALIDATION cap/pcap/pcapng; DNS/NetFlow windows|Exfiltration|Network flow|Shows whether outbound traffic volume exceeds inbound traffic; useful for detecting data transfer out of the environment.|outbound_bytes / max(inbound_bytes,1) per host/src_ip/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|external_destination_count|Unified Host-Network; Host TEST netflow_day/csv; DNS TEST csv; packet captures|Exfiltration|Network destination|Number of unique external IP addresses or domains contacted during a time window.|nunique(external_dst_ip/domain) per host/src_ip/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|new_external_destination_indicator|Unified Host-Network; Host TEST netflow_day/csv; DNS TEST csv; packet captures|Exfiltration|Network anomaly|Indicator for connections to external addresses or domains not previously observed in the baseline.|1 if dst not in historical_baseline(host/src_ip), else 0.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|unique_dst_host_count|LANL; Unified Host-Network; Host TEST netflow_day/csv; Host VALIDATION cap/pcap/pcapng|Reconnaissance/Lateral Movement|Network graph|Number of unique destination hosts; a strong indicator of scanning or lateral movement between hosts.|nunique(dst_host/dst_ip) per src_host/src_ip/window.|RF, XGBoost, CNN; SHAP for feature importance|
|dns_ldap_smb_dcerpc_indicator|Host VALIDATION packet captures|Reconnaissance/Lateral Movement/Collection|Network protocol indicators|DNS/LDAP/SMB/DCERPC indicators based on ports/decoder output.|binary/count per protocol family.|RF, XGBoost, CNN; SHAP for feature importance|
|network_burst_score|Packet captures; netflow_day|Exfiltration|Network temporal|Network activity bursts.|current_window_count / rolling_baseline.|RF, XGBoost, CNN; SHAP for feature importance|

---

## 6. Host feature catalogue

|Feature name|Dataset / source|Attack stage|Feature type|Description|Formula / calculation|Models used|
|---|---|---|---|---|---|---|
|syscall_frequency|ADFA IDS; LID-DS 2021/2019; Host TRAIN csv/txt/sc; Host TEST txt/json/bson|Collection/Data Staging|Host syscall/API|Frequencies of system calls/API events.|count(sys_call/event/name/MethodName)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|syscall_ngram_2_frequency|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Bigram frequencies of system calls/API events.|count((call_i, call_i+1))/sequence.|LSTM; RF/XGBoost on window aggregates|
|syscall_ngram_3_frequency|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Trigram frequencies of system calls/API events.|count((call_i, call_i+1, call_i+2))/sequence.|LSTM; RF/XGBoost on window aggregates|
|syscall_transition_probability|ADFA IDS; LID-DS; Host csv/txt/sc/bson/json|Collection/Data Staging|Host sequence|Transition probabilities between calls.|P(call_j / call_i) from transition matrix.|RF, XGBoost, CNN; SHAP for feature importance|
|unique_syscall_count|ADFA IDS; LID-DS; Host csv/txt/sc|Collection/Data Staging|Host complexity|Number of unique calls in the window/trace.|nunique(syscall).|RF, XGBoost, CNN; SHAP for feature importance|
|syscall_trace_length|ADFA IDS; LID-DS; Host ghc/txt/sc/bson/json|Collection/Data Staging|Host complexity|Length of the sequence/trace.|count(events) per trace/window.|LSTM; RF/XGBoost on window aggregates|
|syscall_interarrival_stats|LID-DS; Host events with timestamps|Collection/Data Staging|Host temporal|Intervals between syscall/API events.|diff(timestamp) per process/trace.|LSTM; RF/XGBoost on window aggregates|
|collection_syscall_count|ADFA IDS; LID-DS; Host csv/txt/sc|Collection|Host collection indicator|Frequencies of open/read/access/stat/readdir and analogues.|sum(call in collection_call_set).|RF, XGBoost, CNN; SHAP for feature importance|
|directory_enumeration_count|ADFA IDS; LID-DS; Dynamic Malware; Host txt/sc|Collection|Host collection indicator|Directory traversal/file enumeration events.|count(readdir/list_dir/find-like events).|RF, XGBoost, CNN; SHAP for feature importance|
|network_syscall_count|Host txt/sc; Dynamic Malware|Exfiltration/Data Staging|Host-network bridge|System calls sendto/recvfrom/connect/accept/socket.|sum(call in network_call_set).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|api_descriptor_frequency|Dynamic Malware; Host TEST bson/json|Collection/Data Staging|Host API|Frequencies of API/syscall-like descriptor names.|count(descriptor.name)/trace.|RF, XGBoost, CNN; SHAP for feature importance|
|api_category_frequency|Dynamic Malware; Host TEST bson/json|Collection/Data Staging|Host API|Frequencies of sandbox/API event categories.|count(category)/trace.|RF, XGBoost, CNN; SHAP for feature importance|
|api_arg_token_count|LID-DS; Dynamic Malware; Host TEST bson/json/txt|Collection/Data Staging|Host API args|Counts/frequencies of argument tokens.|tokenize(args); count/token_frequency.|RF, XGBoost, CNN; SHAP for feature importance|
|trace_module_frequency|Host TRAIN ghc; Dynamic Malware|Collection/Data Staging|Host trace|Frequencies of module/library values from trace tokens.|count(trace.module)/trace.|RF, XGBoost, CNN; SHAP for feature importance|
|trace_module_transition_frequency|Host TRAIN ghc|Collection/Data Staging|Host trace sequence|Transitions between modules.|count((module_i,module_i+1))/trace.|LSTM; RF/XGBoost on window aggregates|
|trace_offset_distribution|Host TRAIN ghc|Collection/Data Staging|Host trace|Distribution of offsets within the module.|bucketize(offset_hex) per module.|RF, XGBoost, CNN; SHAP for feature importance|
|trace_density|Host TRAIN ghc; Host TEST bson/json|Collection/Data Staging|Host sequence|Event density in the trace/window.|event_count / duration or event_count/trace.|LSTM; RF/XGBoost on window aggregates|
|login_success_count|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Number of successful logins.|count(success_login events).|RF, XGBoost, CNN; SHAP for feature importance|
|login_failure_count|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Number of failed logins.|count(failed_login events).|RF, XGBoost, CNN; SHAP for feature importance|
|failed_login_ratio|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth|Ratio of failed login attempts.|failed_login_count / max(total_login_count,1).|RF, XGBoost, CNN; SHAP for feature importance|
|session_opened_count|auth.log; LANL/Windows logs|Privilege Escalation/Lateral Movement|Host auth|Number of opened sessions.|count(session_opened).|RF, XGBoost, CNN; SHAP for feature importance|
|session_closed_count|auth.log; LANL/Windows logs|Privilege Escalation/Lateral Movement|Host auth|Number of closed sessions.|count(session_closed).|RF, XGBoost, CNN; SHAP for feature importance|
|session_duration_stats|auth.log; LANL; Windows logs|Privilege Escalation/Lateral Movement|Host auth temporal|Session duration.|session_closed_time - session_opened_time; aggregate stats.|RF, XGBoost, CNN; SHAP for feature importance|
|sudo_activity_count|auth.log/info; Linux logs|Privilege Escalation|Host privilege|Number of sudo-related events.|count(process/source == sudo).|RF, XGBoost, CNN; SHAP for feature importance|
|sshd_activity_count|auth.log/info; Linux logs|Lateral Movement|Host auth|Number of SSH-related events.|count(source contains sshd).|RF, XGBoost, CNN; SHAP for feature importance|
|cron_activity_count|auth.log/info; Linux logs|Data Staging|Host scheduled activity|Number of cron-related events.|count(source contains cron).|RF, XGBoost, CNN; SHAP for feature importance|
|useradd_activity_count|auth.log/info; Linux logs|Privilege Escalation|Host account management|Number of useradd/account modification events.|count(source contains useradd or account events).|RF, XGBoost, CNN; SHAP for feature importance|
|privileged_account_ratio|LANL; Windows Event Log; OTRF; auth.log|Privilege Escalation|Host privilege|Ratio of privileged account events.|privileged_events / total_events.|RF, XGBoost, CNN; SHAP for feature importance|
|user_host_interaction_count|LANL; Windows Event Log; wls_day|Lateral Movement|Host graph|Number of user-host interactions.|count(user,host) per window.|RF, XGBoost, CNN; SHAP for feature importance|
|source_ip_auth_frequency|auth.log; LANL; Windows Event Log|Lateral Movement|Host/network auth|Frequency of source IPs in auth events.|count(source_ip) per user/host/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|auth_baseline_deviation|LANL; auth.log; wls_day|Privilege Escalation/Lateral Movement|Host anomaly|Deviation of authentication behavior from the baseline.|z-score or ratio(current vs historical baseline).|RF, XGBoost, CNN; SHAP for feature importance|
|event_id_frequency|OTRF; Windows Event Log; wls_day|Reconnaissance/Privilege Escalation/Lateral Movement|Windows/Sysmon|EventID frequencies.|count(EventID)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|security_event_sequence_entropy|OTRF; Windows Event Log; wls_day|Cross-stage|Windows/Sysmon sequence|Entropy of the EventID sequence.|Shannon entropy over ordered EventID tokens.|LSTM; RF/XGBoost on window aggregates|
|logon_type_distribution|Windows Event Log; wls_day|Privilege Escalation/Lateral Movement|Windows auth|Distribution of LogonType.|count(LogonType)/logon_events.|RF, XGBoost, CNN; SHAP for feature importance|
|authentication_package_distribution|Windows Event Log; wls_day|Privilege Escalation/Lateral Movement|Windows auth|Distribution of AuthenticationPackage.|count(package)/auth_events.|RF, XGBoost, CNN; SHAP for feature importance|
|parent_child_process_count|OTRF; Windows Event Log; wls_day; Dynamic Malware|Reconnaissance/Privilege Escalation/Data Staging|Process tree|Number of parent-child process relationships.|count(parent_process, child_process).|RF, XGBoost, CNN; SHAP for feature importance|
|process_name_frequency|OTRF; Windows Event Log; Host process logs; wls_day|Cross-stage|Process|Process frequencies.|count(ProcessName/path/process_id)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|command_line_length|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Command-line length.|len(CommandLine).|RF, XGBoost, CNN; SHAP for feature importance|
|command_arg_count|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Number of command-line arguments.|len(split_commandline(CommandLine)).|RF, XGBoost, CNN; SHAP for feature importance|
|command_line_entropy|OTRF; Windows Event Log; Dynamic Malware|Reconnaissance/Data Staging|Command line|Argument entropy; indicator of obfuscation/encoded payload.|Shannon entropy(CommandLine).|RF, XGBoost, CNN; SHAP for feature importance|
|encoded_powershell_indicator|OTRF; Windows Event Log|Reconnaissance/Privilege Escalation/Data Staging|Command line|Indicator of encoded PowerShell commands.|regex flags: -enc, -encodedcommand, base64-like tokens.|RF, XGBoost, CNN; SHAP for feature importance|
|privileged_process_indicator|OTRF; Windows Event Log; auth logs|Privilege Escalation|Process/privilege|Process execution with elevated privileges.|binary/count from token/elevation/4672-like events.|RF, XGBoost, CNN; SHAP for feature importance|
|account_discovery_indicator|OTRF; Windows Event Log|Reconnaissance|ATT&CK indicator|Account-discovery events/commands.|regex/process/event mapping to account discovery.|RF, XGBoost, CNN; SHAP for feature importance|
|object_access_count|Windows Event Log; OTRF|Collection/Data Staging|Object access|Number of object/file access events.|count(4663/4656-like object access events).|RF, XGBoost, CNN; SHAP for feature importance|
|source_dest_address_port_count|Windows Event Log; OTRF; netflow|Lateral Movement/Exfiltration|Hybrid network fields|Counters for SourceAddress/DestAddress/ports from events.|count(src,dst,port)/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|process_path_entropy|Host process logs; Dynamic Malware; Windows Event Log|Data Staging|Process/path|Entropy of the process/module path.|Shannon entropy(path).|RF, XGBoost, CNN; SHAP for feature importance|
|suspicious_path_indicator|Host process logs; Dynamic Malware; Windows Event Log|Data Staging|Process/path|Indicator of temporary/user/non-standard paths.|regex/path category flags.|RF, XGBoost, CNN; SHAP for feature importance|
|module_basename_frequency|Dynamic Malware; BSON/JSON; GHC|Data Staging|Module/path|Frequencies of library/module basenames.|count(basename(module_path)).|RF, XGBoost, CNN; SHAP for feature importance|
|module_path_entropy|Dynamic Malware; BSON/JSON; GHC|Data Staging|Module/path|Entropy of module/path strings.|Shannon entropy(module_path).|RF, XGBoost, CNN; SHAP for feature importance|
|unique_file_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Collection|File activity|Number of unique files accessed; helps distinguish broad file discovery/collection from repeated reads of the same file.|nunique(file_path/object_name) per process/user/host/window.|RF, XGBoost, CNN; SHAP for feature importance|
|sensitive_file_extension_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Collection|File activity / sensitive data|Number of accesses to potentially sensitive file extensions such as `.docx`, `.xlsx`, `.pdf`, `.csv`, `.sql`, `.zip`, and others.|count(file_ext in sensitive_ext_set) per process/user/host/window.|RF, XGBoost, CNN; SHAP for feature importance|
|archive_creation_count|Maintainable Log Dataset; Windows Event Log; Dynamic Malware; Host logs|Data Staging|File/archive activity|Number of archive-creation events before potential exfiltration: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`.|count(created_file_ext in archive_ext_set) or archive-write events per window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|compression_process_indicator|Windows Event Log / OTRF; Dynamic Malware; Host process logs; command-line telemetry|Data Staging|Process/command-line|Indicator for use of archiving or compression tools such as `zip`, `rar`, `7z`, `tar`, `gzip`, `powershell Compress-Archive`, and similar utilities.|binary/count if process_name or command_line matches compression_tool_set.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|failed_then_success_login_indicator|LANL; OTRF; Windows Event Log; auth.log/info/wls_day|Privilege Escalation/Lateral Movement|Host auth sequence|Indicator for a sequence of failed login attempts followed by a successful login; typical for brute-force and password-spraying activity.|1 if failed_login_count >= k before success_login within T for same user/src/host.|RF, XGBoost, CNN, LSTM; SHAP|
|rare_process_execution_score|OTRF; Windows Event Log; Dynamic Malware; Host process logs; Maintainable Log Dataset|Reconnaissance/Data Staging|Process anomaly|Rarity score for process execution relative to normal system, user, or host behaviour.|-log(P(process_name | host/user/baseline)) or inverse frequency rank.|RF, XGBoost, CNN; SHAP for feature importance|
|file_access_count|ADFA/LID-DS; Maintainable Log Dataset; Windows Event Log; Dynamic Malware|Collection|File activity|Number of file access operations.|count(open/read/access/stat/readdir/object access).|RF, XGBoost, CNN; SHAP for feature importance|
|file_access_rate|ADFA/LID-DS; Maintainable; Dynamic Malware|Collection|File activity temporal|File access frequency.|file_access_count / window_duration.|LSTM; RF/XGBoost on window aggregates|
|file_access_entropy|Host logs; Maintainable; Dynamic Malware|Collection/Data Staging|File activity|Entropy of accessed file paths.|Shannon entropy(file_path tokens).|RF, XGBoost, CNN; SHAP for feature importance|
|filesystem_used_pct_stats|Host TRAIN filesystem.log|Data Staging|Host resource/storage|Filesystem usage statistics.|mean/max/std(system.filesystem.used.pct).|RF, XGBoost, CNN; SHAP for feature importance|
|filesystem_pressure_ratio|Host TRAIN filesystem.log|Data Staging|Host resource/storage|Free-space pressure indicator.|1 - available/total or used/total.|RF, XGBoost, CNN; SHAP for feature importance|
|inode_free_ratio|Host TRAIN filesystem.log/fsstat.log|Data Staging|Host resource/storage|Ratio of free inodes.|free_files/total_files.|RF, XGBoost, CNN; SHAP for feature importance|
|fs_total_used_ratio|Host TRAIN fsstat.log|Data Staging|Host resource/storage|Overall filesystem utilization.|total_size.used / total_size.total.|RF, XGBoost, CNN; SHAP for feature importance|
|disk_read_bytes_rate|Host TRAIN diskio.log|Collection/Data Staging|Host resource/I/O|Disk read rate.|delta(read.bytes)/delta(time).|RF, XGBoost, CNN; SHAP for feature importance|
|disk_write_bytes_rate|Host TRAIN diskio.log|Data Staging|Host resource/I/O|Disk write rate.|delta(write.bytes)/delta(time).|RF, XGBoost, CNN; SHAP for feature importance|
|disk_read_write_ratio|Host TRAIN diskio.log|Collection/Data Staging|Host resource/I/O|Read/write ratio.|read_bytes / max(write_bytes,1).|RF, XGBoost, CNN; SHAP for feature importance|
|diskio_ops_rate|Host TRAIN diskio.log|Data Staging|Host resource/I/O|I/O operation rate.|delta(io.ops)/delta(time).|RF, XGBoost, CNN; SHAP for feature importance|
|diskio_busy_pct|Host TRAIN diskio.log|Data Staging|Host resource/I/O|Disk I/O busy percentage.|system.diskio.iostat.busy or derived rate.|RF, XGBoost, CNN; SHAP for feature importance|
|cpu_total_pct_stats|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|Total CPU utilization statistics.|mean/max/std(host.cpu.pct or total.norm.pct).|RF, XGBoost, CNN; SHAP for feature importance|
|cpu_user_system_idle_ratio|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|User/system/idle CPU ratios.|user_pct/system_pct/idle_pct ratios.|RF, XGBoost, CNN; SHAP for feature importance|
|cpu_burst_score|Host TRAIN cpu.log; ISOT Cloud IDS|Data Staging|Host resource/CPU|CPU bursts relative to the baseline.|current_cpu / rolling_mean_cpu.|RF, XGBoost, CNN; SHAP for feature importance|
|memory_usage_stats|Host TRAIN memory.log; ISOT Cloud IDS|Data Staging|Host resource/memory|Memory usage statistics, if fields are available after normalization.|mean/max/std(memory used/pct).|RF, XGBoost, CNN; SHAP for feature importance|
|load_average_stats|Host TRAIN load.log; ISOT Cloud IDS|Data Staging|Host resource/load|Load average statistics.|mean/max/std(load fields).|RF, XGBoost, CNN; SHAP for feature importance|
|network_interface_bytes_rate|Host TRAIN network.log|Exfiltration|Host resource/network|Byte rate from network interface telemetry.|delta(network.bytes)/delta(time).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|socket_count|Host TRAIN socket.summary.log|Exfiltration/Lateral Movement|Host network/socket|Number of open sockets.|count sockets or socket.summary metrics.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|service_state_change_count|Host TRAIN service.log|Data Staging|Host service|Number of service state changes.|count(service state changes).|RF, XGBoost, CNN; SHAP for feature importance|
|uptime_seconds|Host TRAIN uptime.log|Operational context|Host context|System uptime.|parse uptime seconds.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|log_event_count|Maintainable Log Dataset; Host log/syslog/messages/mainlog|Cross-stage|Log volume|Number of log events.|count(log events)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|log_volume_rate|Maintainable; Host logs|Cross-stage|Log volume temporal|Log generation rate.|event_count/window_duration.|LSTM; RF/XGBoost on window aggregates|
|log_level_frequency|Host TEST log; syslog-like logs|Cross-stage|Log categorical|Log-level frequencies.|count(level)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|warning_error_count|Host TEST log; syslog-like logs|Cross-stage|Log anomaly|Number of warnings/errors.|count(level in {warn,error,critical}).|RF, XGBoost, CNN; SHAP for feature importance|
|component_frequency|Host TEST log; syslog-like logs|Cross-stage|Log categorical|Frequencies of log components/sources.|count(component/source)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|message_template_frequency|Maintainable; Host logs|Cross-stage|Log template|Message-template frequencies.|parse template; count(template_id).|RF, XGBoost, CNN; SHAP for feature importance|
|event_type_frequency|Host TRAIN json/log-derived files|Cross-stage|Log/event type|Frequencies of event_type: stats/dns/alert, etc.|count(event_type)/window.|RF, XGBoost, CNN; SHAP for feature importance|
|alert_count|Host TRAIN json/log-derived files|Cross-stage|Alert context|Number of alert events.|count(event_type==alert or alert present).|RF, XGBoost, CNN; SHAP for feature importance|
|task_lifecycle_duration|Dynamic Malware; Host TEST log/json|Data Staging|Sandbox context|Sandbox task/lifecycle duration.|completed_on - started_on or task timing fields.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|scenario_image_context|Host VALIDATION csv; Maintainable/LID-DS metadata|Context/labeling|Scenario context|Image/scenario context for joining with events.|categorical scenario_name/image_name; do not use as a model feature when leakage risk is present.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|exploit_start_offset|Host VALIDATION csv|Context/labeling|Scenario context/time|Exploit start offset.|exploit_start_time field; use for window labeling.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|recording_duration|Host VALIDATION csv; LID-DS metadata|Context/labeling|Scenario context/time|Scenario recording duration.|recording_time.|Pipeline/label resolver; do not use as an independent feature without leakage control|

---

## 7. Hybrid and sequence feature catalogue

|Feature name|Dataset / source|Attack stage|Feature type|Description|Formula / calculation|Models used|
|---|---|---|---|---|---|---|
|host_network_time_delta|Unified Host-Network; LANL; Host + DNS/NetFlow joins|Cross-stage|Hybrid temporal|Time lag between a host event and a network event.|abs(t_host - nearest(t_network)).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|process_to_network_burst_score|Unified Host-Network; Dynamic Malware + pcap/netflow|Data Staging/Exfiltration|Hybrid correlation|Relationship between process start and network burst.|network_burst_score within N seconds after process start.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|auth_to_network_correlation|LANL; Unified Host-Network; auth.log + netflow|Lateral Movement/Exfiltration|Hybrid correlation|Correlation of auth events with network flows.|count(network flows after auth event)/window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|file_to_network_correlation|Unified Host-Network; LID-DS/Dynamic Malware + netflow|Collection/Exfiltration|Hybrid correlation|Relationship between file access/data staging and network outflow.|network bytes after file_access window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|cpu_io_network_correlation|Host telemetry + netflow|Data Staging/Exfiltration|Hybrid correlation|Relationship between CPU/I/O spikes and network spikes.|rolling_corr(cpu/disk/network metrics).|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|source_loghost_graph_degree|wls_day; Windows logs; LANL|Lateral Movement|Hybrid graph|Degree of the source/loghost graph.|degree(Source, LogHost) per window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|cross_source_event_count|Multi-source integration layer|Cross-stage|Hybrid aggregation|Number of events from different sources in the same window.|count events by domain/source within unified window.|RF, XGBoost, CNN, LSTM late-fusion; SHAP|
|sequence_window_event_count|All timestamped DNS/host/network sources|Cross-stage|Sequence|Number of events in an LSTM window.|count(events) in ordered window.|LSTM; RF/XGBoost on window aggregates|
|sequence_window_duration|All timestamped DNS/host/network sources|Cross-stage|Sequence|Sequence-window duration.|last_event_time - first_event_time.|LSTM; RF/XGBoost on window aggregates|
|sequence_event_type_entropy|All event streams|Cross-stage|Sequence|Entropy of event types in the sequence.|Shannon entropy(event_type tokens).|LSTM; RF/XGBoost on window aggregates|
|sequence_temporal_order_pattern|All event streams|Cross-stage|Sequence|Order of stages/event types in the attack.|ordered tokens mapped to ATT&CK/stage labels.|LSTM; RF/XGBoost on window aggregates|
|process_file_network_sequence|Unified Host-Network; Dynamic Malware + pcap/netflow; LID-DS/Dynamic Malware + network joins|Collection → Data Staging → Exfiltration|Hybrid sequence|Tracks the action chain: file access → archiving/preparation → data transfer over the network.|ordered pattern match: file_access -> archive/compress -> outbound_network_event within T.|LSTM, late fusion; RF/XGBoost on window aggregates|
|stage_transition_pattern|All timestamped DNS/host/network sources; MITRE ATT&CK mapped events|Sequential modelling|Sequence / attack progression|Explicitly models transitions between attack stages and helps LSTM detect behavioural progression by an attacker.|ordered stage tokens; transition counts/probabilities between Reconnaissance, Privilege Escalation, Lateral Movement, Collection, Data Staging, Exfiltration.|LSTM; RF/XGBoost on window aggregates; SHAP for sequence-aware attribution|
|label_binary|All supervised-ready artifacts|Target/context|Label|Target binary label. Not an input feature.|0=benign, 1=malicious/exfiltration, NULL=unknown.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|label_family|All supervised-ready artifacts|Target/context|Label|Attack family/type. Not an input feature.|benign/dns_exfiltration/malware/phishing/lateral_movement/etc.|Pipeline/label resolver; do not use as an independent feature without leakage control|
|label_status|All artifacts|Target/context|Label quality|Label status for quality control and leakage control.|explicit/inferred/weak/partial/unlabeled/conflicting.|Pipeline/label resolver; do not use as an independent feature without leakage control|

---

## 8. Dataset and key feature group matrix

| Dataset / source | Role | Main feature groups | Attack stages | Usage comment |
|---|---|---|---|---|
| CIC-Bell-DNS-EXF-2021 | TRAIN | DNS lexical, entropy, RR/TTL, query-rate, inter-query intervals, unique subdomain ratio | Exfiltration | Main attack-class DNS source. |
| CIC-Bell-DNS-2021 | TRAIN + VALIDATION split | The same DNS features, but for benign baseline and FP control | Exfiltration / Benign baseline | Use for benign behavior and threshold tuning. |
| Mendeley DNS Exfiltration Dataset | TEST | DNS lexical/temporal/numeric feature table, source_ip windows | Exfiltration | Final generalization check only; do not train on it. |
| ADFA IDS | TRAIN | syscall frequencies, n-grams, transitions, trace length, collection syscalls | Collection, Data Staging | Baseline HIDS/syscall benchmark. |
| LID-DS 2021 | TRAIN | syscall/API sequence, syscall args, file access, inter-arrival timings | Collection, Data Staging, Pre-exfiltration | Main sequence source for the LSTM host branch. |
| LID-DS 2019 | VALIDATION | The same features as LID-DS 2021 | Collection, Data Staging | Cross-version validation. |
| Maintainable Log Dataset | TRAIN | log templates, event volume, multi-stage event sequences, file access/log correlation | Reconnaissance, Collection, Data Staging | Enterprise log behaviour and multi-stage modelling. |
| LANL Dataset | VALIDATION | auth frequency, user-host interaction, failed login ratio, privileged account usage, lateral movement graph | Privilege Escalation, Lateral Movement | Validation of enterprise behaviour. |
| Windows Event Log / OTRF | VALIDATION | EventID, process tree, PowerShell/command line, logon/auth, object access, SourceAddress/DestAddress | Reconnaissance, Privilege Escalation, Lateral Movement | SOC-oriented Windows/Sysmon validation. |
| Unified Host-Network / LANL | TEST | host auth/process + netflow + correlation features | Full lifecycle | Final hybrid test. |
| ISOT Cloud IDS | TEST | CPU/memory/I/O/log/cloud workload anomalies | Data Staging | Portability test in a cloud-like environment. |
| Dynamic Malware Analysis Dataset | TEST | API/syscall events, command line/path/module tokens, process tree, sandbox task lifecycle | Collection, Data Staging, Pre-exfiltration | Evaluation of malware-driven host behaviour. |
| DNS VALIDATION pcap | VALIDATION | DNS amplification ratio, qname/qtype, response size, TTL, RCODE/NXDOMAIN, packet/byte counts | Exfiltration / DNS amplification | Requires a packet parser with DNS decoding. |
| DNS VALIDATION txt | VALIDATION | domain length, label count, TLD/SLD, entropy, enrichment | Exfiltration / domain validation | The `unknown` class must not be used as a supervised class without an explicit decision. |
| Host VALIDATION cap/pcap/pcapng | VALIDATION | packet/flow counts, protocol distribution, TCP/UDP ports, TCP flags, DNS/LDAP/SMB/DCERPC indicators | Reconnaissance, Lateral Movement, Exfiltration | Labels only through scenario/file metadata or external mapping. |
| Host VALIDATION csv | VALIDATION | scenario/image context, exploit flag, recording duration, exploit start offset | Context / evaluation | Use as label/context metadata, not as an ordinary model feature. |
| Host TEST bson/json/txt | TEST | API/syscall-like frequencies, n-grams, transitions, args, process context, command/path entropy | Collection, Data Staging | Testing/inference evaluation only; external labels are required for supervised metrics. |
| Host TEST wls_day | TEST | EventID, login ratios, auth package, process chains, event sequences | Privilege Escalation, Lateral Movement | Account for the event-specific schema. |
| Host TEST netflow_day/csv | TEST | flow duration, bytes/packets, ports, protocol, fan-in/fan-out, TCP flags | Reconnaissance, Lateral Movement, Exfiltration | TEST-only; do not train on it. |

---

## 9. Minimum feature schema for Parquet artifacts

### 9.1. Required traceability fields

| Field | Purpose | Use as model feature? |
|---|---|---|
| `event_id` | Unique normalized event ID | No |
| `source_file_id` | Raw file ID from the catalog | No |
| `source_row_id` / `packet_id` | Row/packet/event number | No |
| `dataset_domain` | `dns`, `host`, `network`, `hybrid` | No |
| `dataset_role` | TRAIN / VALIDATION / TEST | No |
| `dataset_name` | Dataset name | No, except for audit/reporting |
| `dataset_format` | csv, pcap, json, log, bson, txt, ... | No, except for parser/debug |
| `parser_name` | Parser handler name | No |
| `parser_version` | Parser logic version | No |
| `event_timestamp` | Normalized event time | Yes, only as derived time features / ordering |
| `window_id` | Time-window ID | No |
| `sequence_id` | Sequence-window ID | No |

### 9.2. Required label fields

| Field | Purpose |
|---|---|
| `label_binary` | 0=benign, 1=attack/exfiltration/malicious, NULL=unknown |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, collection, data_staging, unknown |
| `label_subtype` | Specific subtype/scenario, if available |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label |
| `label_confidence` | 1.0 explicit; 0.7-0.9 inferred; 0.4-0.7 weak; 0 unlabeled |
| `label_mapping_rule_id` | Label resolver rule ID |

---

## 10. What to exclude from model features

| Field / group | Why exclude |
|---|---|
| `source_file`, file basename, full path | May directly encode the class through `benign`, `malware`, `attack`, or `exfiltration`. |
| `dataset_role` | TRAIN/VALIDATION/TEST leakage. |
| `dataset_name` | May allow the model to memorize the dataset instead of behavior. |
| `scenario_name`, `image_name` | Use only for label joins / evaluation metadata; as a feature, it creates high leakage risk. |
| `label_*` | These are target/audit fields, not input features. |
| Raw payload/body | The project scope is metadata/behavioural detection, not payload inspection. |
| Absolute local paths | Not portable and may create leakage. |

---

## 11. Feature implementation priority

### P0 — implement first

1. DNS lexical/entropy: `dns_query_length`, `dns_subdomain_depth`, `dns_entropy`, `dns_label_count`, `dns_digit_count`, `dns_special_char_count`.
2. DNS temporal: `dns_query_rate`, `dns_inter_query_interval_stats`, `dns_queries_per_window`.
3. DNS protocol: `ttl_mean`, `ttl_variance`, `rr_count`, `rr_type_frequency_*`, `dns_response_size_stats`, `dns_nxdomain_rate`.
4. Host syscall/API: `syscall_frequency`, `syscall_ngram_2_frequency`, `syscall_transition_probability`, `syscall_trace_length`.
5. Host auth: `failed_login_ratio`, `failed_then_success_login_indicator`, `session_opened_count`, `sudo_activity_count`, `user_host_interaction_count`.
6. Windows/Sysmon: `event_id_frequency`, `parent_child_process_count`, `command_line_entropy`, `encoded_powershell_indicator`.
7. Network: `packet_count`, `byte_count`, `flow_duration`, `protocol_distribution`, `dst_port_frequency`, `outbound_byte_ratio`, `external_destination_count`.
8. Sequence: `sequence_window_event_count`, `sequence_event_type_entropy`, `process_file_network_sequence`, `stage_transition_pattern`, ordered event tokens.

### P1 — after the baseline pipeline

1. Domain enrichment: ASN/country/domain age/reputation.
2. Hybrid correlations: host-network time delta, file-to-network, auth-to-network.
3. Resource telemetry and staging indicators: CPU/disk/filesystem/network interface burst features, `archive_creation_count`, `compression_process_indicator`, `sensitive_file_extension_count`.
4. Graph and baseline features: fan-in/fan-out, Source-LogHost degree, `unique_dst_host_count`, `new_external_destination_indicator`, `rare_process_execution_score`.

### P2 — extension after the baseline

1. Advanced command-line tokenization.
2. Template mining for logs.
3. Per-user/per-host long-term baseline deviation.
4. Feature stability checks across folds and datasets.

---

## 12. Recommended implementation order in code

1. Create `feature_catalog.yml/json` from this Markdown as a machine-readable contract.
2. Create a normalized event schema for each parser output.
3. Implement feature extractors by group:
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
4. Save results in Parquet:
   - `normalized_events/`
   - `feature_windows/`
   - `sequence_windows/`
   - `model_ready/`
5. For each output, save `feature_extraction_report.md` with row counts, missing values, label_status, and leakage checks.

---

## 13. Final decision

The project should implement not one general extractor, but a set of specialized extractor layers:

- DNS lexical / protocol / temporal extractors;
- host syscall/API/trace extractors;
- authentication and Windows/Sysmon extractors;
- resource telemetry extractors;
- network/flow extractors;
- staging/compression and sensitive-file activity extractors;
- hybrid correlation extractors;
- sequence window builder for LSTM, including process-file-network and stage-transition patterns.

The final framework should use one consistent feature catalogue, but different parser-specific data sources. This will preserve traceability, prevent leakage, and prepare features for RF, XGBoost, CNN, LSTM, and SHAP analysis.
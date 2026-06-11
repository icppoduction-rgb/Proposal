# General DNS Train Dataset Analysis

This file is assembled from markdown files in `docs/en/analysis-dataset/dns/train`.

## Source documents

- `README.md`
- `csv.md`
- `pcap.csv.md`
- `pcap.md`

---

## Source: `README.md`

# Dataset File Content Analysis (DNS TRAIN)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | 8 | yes | no | PARTIALLY_SUPPORTED | csv.md |
| pcap | 4 | yes | no | NEEDS_CUSTOM_PARSER | pcap.md |
| pcap.csv | 14 | yes | no | READY_FOR_FEATURE_EXTRACTION | pcap.csv.md |

---

## Source: `csv.md`

# Format Analysis: csv

## 1. Purpose
DNS TRAIN CSV files contain domain lists and tabular DNS/domain features for benign, malware, phishing, and spam classes. The format is suitable for lexical domain features, TTL/IP/ASN features, WHOIS-derived signals, and supervised training when labels are assigned from file names.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
| File count | 8 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\benign_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_benign.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_malware.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_phishing.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\CSV_spam.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\malware_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\phishing_domains.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\csv\spam_domains.csv
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | yes |
| Header | partial |
| Delimiter | comma |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 8 |
| Parsed rows | 7996 |

## 5. Content Structure
Detected CSV schemas: dns_feature_table: 4, domain_list: 3, phishtank_url_feed: 1. Classes are available from file names: benign: 2, malware: 2, phishing: 2, spam: 2. Feature tables contain `Domain`, `TTL`, `IP`, `ASN`, `entropy`, `tld`, n-gram, and WHOIS-derived fields; domain-list files contain one domain per row. Feature CSV files include unescaped list/dict values with commas, so they require schema-aware normalization.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| domain | domain_or_ip | domain name | cypress.com |
| Domain | unknown | queried/resolved domain |  |
| Domain_Name | unknown | normalized domain name |  |
| url | url | phishing URL | http://programafidelidadeitacard2.cf/ |
| IP | unknown | resolved IP address |  |
| TTL | unknown | DNS TTL |  |
| ASN | unknown | autonomous system number |  |
| entropy | unknown | domain entropy |  |
| tld | unknown | top-level domain |  |
| len | unknown | domain length |  |
| subdomain | unknown | subdomain indicator/count |  |
| Creation_Date_Time | unknown | DNS/domain feature |  |
| Domain_Age | unknown | DNS/domain feature |  |
| phish_id | integer | PhishTank id | 6086873 |
| submission_time | string | feed submission timestamp | 2019-06-20T12:56:11+00:00 |
| 1gram | unknown | DNS/domain feature |  |
| 2gram | unknown | DNS/domain feature |  |
| 3gram | unknown | DNS/domain feature |  |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name / class_hint |
| Label values | benign, malware, phishing, spam |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | Creation_Date_Time, Domain_Age, submission_time |
| Time format | datetime / duration string / ISO-like timestamp |
| Can build sequences | no, these are domain-level tables/lists |
| Can apply sliding windows | no without external query time |

## 9. Potential Feature Extraction
### DNS Features
- domain/subdomain length and `len`;
- domain name entropy;
- `TTL`, `IP`, `ASN`;
- `tld`, `sld`, `subdomain`;
- n-gram features (`1gram`, `2gram`, `3gram`);
- `Domain_Age`, `Creation_Date_Time`, `Name_Server_Count`;
- URL/domain features from the PhishTank-like feed.

### Network / Hybrid Features
- IP/ASN enrichment;
- correlation with pcap/pcap.csv by domain/IP.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | yes | feature CSV files contain `nan` and empty fields |
| Unstable structure | yes | inconsistent column count files: 4 |
| Mixed schemas | yes | schema-specific normalization is required |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | PARTIALLY_SUPPORTED |
| Separate parser required | partial, for feature CSV files with unescaped list/dict fields |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN CSV is partially ready for feature extraction: domain-list and PhishTank-like files are directly readable, while feature CSV files require schema-aware normalization because of unescaped list/dict fields with commas. Class labels are assigned from file names.

---

## Source: `pcap.csv.md`

# Format Analysis: pcap.csv

## 1. Purpose
DNS TRAIN `pcap.csv` files contain tabular features already extracted from pcap traffic. The format is suitable for feature engineering without parsing raw pcap: one family contains stateful DNS/resource-record features, and another contains stateless lexical/time features for domain queries.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap.csv |
| Extension variants | .pcap.csv |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
| File count | 14 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_audio.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_benign.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_compressed.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_exe.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_image.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_text.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_video.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_audio.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_benign.pcap.csv
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_compressed.pcap.csv
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | yes |
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | 14 |
| Parsed rows | 12577 |

## 5. Content Structure
Detected two pcap-derived feature schemas: stateful_dns_pcap_features: 7, stateless_dns_pcap_features: 7. Traffic classes/types are available from file names: audio: 2, benign: 2, compressed: 2, exe: 2, image: 2, text: 2, video: 2. Stateful files describe DNS RR, TTL, NS/IP/ASN, and aggregate features; stateless files contain timestamp and lexical FQDN/subdomain features.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| AAAA_frequency | integer | DNS pcap-derived feature | 0 |
| A_frequency | integer | DNS pcap-derived feature | 0 |
| CNAME_frequency | integer | DNS pcap-derived feature | 0 |
| FQDN_count | integer | fully qualified domain name length/count feature | 27 |
| HINFO_frequency | integer | DNS pcap-derived feature | 0 |
| MX_frequency | integer | DNS pcap-derived feature | 0 |
| NS_frequency | integer | DNS pcap-derived feature | 0 |
| NULL_frequency | integer | DNS pcap-derived feature | 0 |
| OPT_frequency | integer | DNS pcap-derived feature | 0 |
| PTR_frequency | integer | DNS pcap-derived feature | 2 |
| SOA_frequency | integer | DNS pcap-derived feature | 0 |
| SRV_frequency | integer | DNS pcap-derived feature | 0 |
| TXT_frequency | integer | DNS pcap-derived feature | 0 |
| a_records | integer | A-record count | 0 |
| distinct_domains | string | distinct domain count | {} |
| distinct_ip | string | distinct IP count | set() |
| distinct_ns | integer | distinct name server count | 0 |
| entropy | float | domain entropy | 2.5704170701729945 |
| labels | integer | DNS label count | 6 |
| labels_average | float | average label length | 3.6666666666666665 |
| labels_max | integer | maximum label length | 7 |
| len | integer | domain/query length | 14 |
| longest_word | integer | longest token length | 2 |
| lower | integer | lowercase character count | 10 |
| numeric | integer | numeric character count | 11 |
| reverse_dns | string | reverse DNS feature | unknown |
| rr | float | resource record ratio or rate feature | 0.0 |
| rr_count | integer | resource record count | 0 |
| rr_name_entropy | float | resource record name entropy | 3.2224634371756076 |
| rr_name_length | integer | resource record name length | 27 |
| rr_type | string | resource record type category | {'PTR'} |
| sld | integer | second-level domain feature | 192 |
| special | integer | special character count | 6 |
| subdomain | integer | subdomain indicator or value | 1 |
| subdomain_length | integer | subdomain character length | 10 |
| timestamp | datetime | packet-derived event timestamp | 2020-11-21 19:13:27.034607 |
| ttl_mean | float | mean TTL | 1.0 |
| ttl_variance | float | TTL variance | 0.0 |
| unique_asn | string | unique ASN count | set() |
| unique_country | string | unique country count | set() |
| unique_ttl | string | unique TTL count | [1, 1] |
| upper | integer | uppercase character count | 0 |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name / class_hint |
| Label values | audio, benign, compressed, exe, image, text, video |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | timestamp |
| Time format | `YYYY-MM-DD HH:MM:SS.microseconds` |
| Can build sequences | yes, for the stateless schema |
| Can apply sliding windows | yes, after sorting by timestamp |

## 9. Potential Feature Extraction
### DNS Features
- RR type frequencies: `A_frequency`, `NS_frequency`, `TXT_frequency`, `AAAA_frequency`;
- `rr_count`, `rr_name_entropy`, `rr_name_length`;
- `distinct_ns`, `distinct_ip`, `unique_asn`, `unique_ttl`;
- `ttl_mean`, `ttl_variance`;
- FQDN lexical features: `entropy`, `labels`, `subdomain_length`, `longest_word`.

### Network / Hybrid Features
- stateful/stateless feature family;
- traffic type from file name;
- aggregation by timestamp and DNS query events;
- correlation with raw `pcap` files for feature validation.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | missing cells: 0 |
| Unstable structure | no | inconsistent column files: 0 |
| Mixed schemas | yes | two valid schemas: stateful and stateless |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | READY_FOR_FEATURE_EXTRACTION |
| Separate parser required | no, CSV reader and schema-aware routing are enough |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN `pcap.csv` is ready for feature extraction: CSV structure is stable, headers are present, time features are available in the stateless schema, and labels can be assigned from file names.

---

## Source: `pcap.md`

# Format Analysis: pcap

## 1. Purpose
DNS TRAIN PCAP files contain packet capture traffic for benign, malware, phishing, and spam classes. The format is needed for DNS query/response parsing, packet/flow features, and validation of CSV-derived features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
| File count | 4 |

## 3. Example Files
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\benign.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\malware.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\phishing.pcap
C:\Users\Public\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap\spam.pcap
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcap/pcapng global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | 4 |
| Sample packets | 2000 |

## 5. Content Structure
Containers in the sample: classic_pcap: 3, pcapng: 1. IP protocol distribution: 17: 2000. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: 1000.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| container_variant | string | classic pcap or pcapng | classic_pcap |
| magic | hex | capture signature | 0a0d0d0a |
| ip_protocol | integer | IP protocol | 17 |
| udp_dst_port | integer | UDP destination port sample | 53 |
| tcp_dst_port | integer | TCP destination port sample |  |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name |
| Label values | benign, malware, phishing, spam |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet timestamp |
| Time format | pcap seconds/usec or pcapng timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- query name, query length, subdomain depth;
- qtype/qclass;
- response size, TTL, answer count;
- NXDOMAIN/RCODE distribution;
- inter-query intervals.

### Network / Hybrid Features
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- correlation with CSV domain/IP features.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample count: 0 |
| Corrupted files | no | parse errors: 0 |
| Missing values | no | packet headers are available |
| Unstable structure | partial | `.pcap` bucket contains classic pcap and pcapng |
| Mixed schemas | yes | parser must support both containers |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | NEEDS_CUSTOM_PARSER |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN pcap is useful for network/DNS feature extraction, but the production pipeline must use a packet parser that supports both classic pcap and pcapng.

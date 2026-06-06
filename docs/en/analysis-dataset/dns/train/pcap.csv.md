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
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_audio.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_benign.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_compressed.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_exe.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_image.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_text.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateful_features-light_video.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_audio.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_benign.pcap.csv
C:\Users\fmark\PythonProjects\storages\datasets-filter\dns\TRAIN\pcap.csv\stateless_features-light_compressed.pcap.csv
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

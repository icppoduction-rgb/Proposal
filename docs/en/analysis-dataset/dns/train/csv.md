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

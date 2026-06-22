# DNS datasets

The DNS branch contains 8 format buckets and 35 files. It is split into tabular CSV files, packet captures, and domain-list TXT files. DNS `TEST` does not contain prepared `pcap` or `pcap.csv` files, so packet-level TEST evaluation is not possible with the current prepared set.

## DNS TRAIN

| Format | Files | Status | Labels | Timestamp | Purpose and limitations |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 8 | `PARTIALLY_SUPPORTED` | class hint from filename: `benign`, `malware`, `phishing`, `spam` | partial | Domain-list and PhishTank-like files can be read directly; feature CSV files may contain unescaped list/dict fields with commas. |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | class hint from filename: `benign`, `malware`, `phishing`, `spam` | yes, packet timestamp | Requires a packet parser with classic pcap/pcapng support and DNS protocol decoding. |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | class hint from filename: `audio`, `benign`, `compressed`, `exe`, `image`, `text`, `video` | yes | CSV structure is stable and headers are present; suitable for DNS feature extraction after label mapping. |

Label rule: filename/class hints may be used only as `label_source=filename`/`inferred_label`. Payload classes such as `audio`, `compressed`, `exe`, `image`, `text`, and `video` must not be automatically treated as exfiltration labels without an approved target mapping.

## DNS VALIDATION

| Format | Files | Status | Labels | Timestamp | Purpose and limitations |
| --- | ---: | --- | --- | --- | --- |
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | class hint from filename: `attack`, `benign` | yes, packet timestamp | Suitable for validating the DNS amplification/detection pipeline, but requires a packet parser. |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | class hint: `unknown`, `benign` | no | Domain-list format: one domain record per line. `unknown` must not be treated as benign or attack without a policy. |

## DNS TEST

| Format | Files | Status | Labels | Timestamp | Purpose and limitations |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 1 | `PARTIALLY_SUPPORTED` | partial boolean-like `label_or_flag` field in the sample | yes | Large headerless CSV; requires a fixed 22-column schema and streaming reads. Use for evaluation only. |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | none | no | The prepared `TEST.pcap` bucket contains no files. |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | none | no | The prepared `TEST.pcap.csv` bucket contains no files. |

## Conclusions for DNS parsers

| Stage Two component | Requirement |
| --- | --- |
| `DnsCsvParser` | Distinguish TRAIN CSV sub-schemas, DNS TEST headerless 22-column schema, and domain-list/PhishTank-like sources. |
| `DnsPcapCsvParser` | Support stable CSV headers and preserve filename class hints as label metadata. |
| `DnsTxtDomainListParser` | Read one domain record per line; keep `timestamp=null`, `timestamp_type=missing` or `event_order`. |
| `DnsPacketCaptureParser` | Extract packet timestamp, DNS query/response fields, qtype/qclass/rcode/ttl, network tuple, and packet-level metadata. |

## DNS feature extraction

Priority features:

- domain, subdomain, and query string length;
- entropy and character set distribution;
- unique subdomain ratio;
- query rate and window counts;
- qtype/rcode/ttl distribution;
- packet size and response size;
- payload class context for `pcap.csv` if the mapping is approved.

## DNS quality risks

- DNS TEST packet buckets are empty (`BROKEN_OR_EMPTY`).
- DNS TEST CSV has no header and requires a fixed positional schema.
- `unknown` in VALIDATION TXT is not a class label.
- Filename labels require an audit trail and must not enter X features.

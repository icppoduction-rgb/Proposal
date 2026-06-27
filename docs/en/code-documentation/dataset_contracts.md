# Dataset-specific Contracts

This document summarizes dataset groups from existing Stage One analysis docs under `docs/ru/analysis-dataset`. Counts come from generated Stage One documentation; this is not a new filesystem recount.

## DNS TRAIN

| Format | Files | Status | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 8 | `PARTIALLY_SUPPORTED` | `DnsCsvParser` | filename/class hints: benign, malware, phishing, spam; non-TEST inference allowed but must be recorded |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints; parser emits packet summaries |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | `DnsPcapCsvParser` | filename/class hints: audio, benign, compressed, exe, image, text, video |

Constraints:

- Filename labels are inferred labels, not embedded ground truth.
- Raw files remain unchanged.
- Role path `TRAIN` is used only for training fit.

## DNS VALIDATION

| Format | Files | Status | Parser strategy | Labels |
|---|---:|---|---|---|
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints: attack/benign; validation only |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `DnsTxtDomainListParser` for `VALIDATION` | partial; explicit class assignment required |

Constraints:

- VALIDATION may be used for model selection/early stopping depending on experiment design, but not to fit scalers/encoders if policy requires TRAIN-only preprocessing fit.
- Keep separate from TRAIN and TEST artifacts.

## DNS TEST

| Format | Files | Status | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 1 | `PARTIALLY_SUPPORTED` | `DnsCsvParser`, headerless TEST support | sample has `label_or_flag`; evaluation only |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | no files |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | no files |

Constraints:

- TEST must not be used for training, preprocessing fit, threshold tuning, or feature selection.
- TEST filename heuristic is disabled.

## Host TRAIN

| Format | Files | Status | Parser strategy |
|---|---:|---|---|
| `csv` | 101 | `PARTIALLY_SUPPORTED` | `HostCsvParser` |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` registry covers log formats |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | `HostSyscallTraceParser` |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `log-1`, `log-2`, `log-3` | 49 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `mainlog*`, `messages*`, `syslog*`, `mail-*` | 66 | mostly `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` for TRAIN |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | `HostXmlParser` |

Labels:

- `csv` has embedded normal/attack categories and binary labels.
- `cpu.log` has partial labels.
- many telemetry/log/trace formats have no direct labels and require external mapping/window/scenario joins.
- absence of label remains `unlabeled`.

## Host VALIDATION

| Format | Files | Status | Parser strategy | Labels/timestamp |
|---|---:|---|---|---|
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet header timestamp; external labels/scenario needed |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `HostCsvParser` | `is_executing_exploit` |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` | timestamp fields; external/scenario labels |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` | time; no direct labels |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet timestamp; external labels |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | enhanced packet timestamp; external labels |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | Time; no direct labels |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` in current seed, JSON-lines semantics noted in analysis docs |

## Host TEST

| Format | Files | Status | Parser strategy | Labels |
|---|---:|---|---|---|
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | `HostBsonSandboxParser` for TEST | no direct labels in sample; external if exists |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | `HostCsvParser` | separate label CSV maps; TEST evaluation only |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` | no TEST training; external labels |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` | no external labels by default |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` | no external labels by default |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | no TEST training |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` in current seed, WLS JSON-lines semantics noted |

Constraints:

- TEST artifacts may be normalized and evaluated, but never used for any fit/tuning.
- Filename heuristic is disabled for TEST.
- Separate label files must be joined only for evaluation and must preserve `label_source`.

## Dataset Group Constraints

- Counts come from generated docs and should be refreshed after changing filters or sorted tree.
- Some Stage One statuses predate later parser implementation; use parser coverage to determine current runnable status.
- Large Host TEST `txt` and `bson` counts require memory-safe batching/splitting strategy.

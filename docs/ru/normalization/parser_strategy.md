# Parser strategy

Stage Two использует registry-driven parser pipeline:

```text
dataset_files.source_format -> parser_registry -> ParserResolver -> parser class -> ParserResult -> normalized Parquet
```

Parser seed: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Загрузка/обновление:

```powershell
python manage.py stage-two seed-parser-registry
```

## Source format detection

`DatasetFileScanner` в `scripts/stage_two/ingestion/scanner.py` определяет:

1. `branch` из path/root parts: `dns`, `host`, иначе `hybrid`.
2. `role` из path parts: `TRAIN`, `VALIDATION`, `TEST`. Файлы вне этих role directories пропускаются Stage Two catalog ingestion.
3. `source_format` сначала из sorted-tree format buckets, затем file-name heuristics.

`EXPERIMENTS` не является активной рабочей ролью. Значение может оставаться в старых DB constraints для совместимости, но scanner/catalog/normalization/reporting workflows его игнорируют.

Compound names сохраняются:

```text
pcap.csv -> pcap.csv
process.summary.log -> process.summary.log
journal~ -> journal~
netflow_day -> netflow_day
```

## Active parser coverage

| Branch | Parser class | Source formats | Role scope |
| --- | --- | --- | --- |
| dns | `DnsCsvParser` | `csv` | all roles |
| dns | `DnsPcapCsvParser` | `pcap.csv` | all roles |
| dns | `DnsTxtDomainListParser` | `txt` | VALIDATION |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all roles |
| host | `HostCsvParser` | `csv` | all roles |
| host | `HostJsonLinesParser` | `json`, `json-1` | all roles |
| host | `HostLineLogParser` | `auth.log`, `info`, `journal`, `journal~`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `messages`, `messages-1`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log` | all roles |
| host | `HostLineLogParser` -> `HostMetricbeatParser` | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | all roles |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` | all roles |
| host | `HostBsonSandboxParser` | `bson` | TEST |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all roles |
| host | `HostXmlParser` | `xml` | all roles |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION |

Authoritative runtime view:

```powershell
python manage.py stage-two parser-coverage
```

## ParserResolver

`ParserResolver`:

- выбирает active rows по `branch`, `role`, `source_format`, `priority`;
- проверяет module/class availability перед выбором parser;
- загружает parser classes как `BaseParser` subclasses;
- resolves `schema_version_id` из `schema_versions`;
- помечает files как `UNSUPPORTED_FORMAT`, если parser нет.

Missing classes показываются в parser coverage, а не скрываются как runtime exceptions.

## Input reader behavior

`UniversalInputReader` поддерживает:

| Mode | Purpose |
| --- | --- |
| `text` | Text stream with encoding fallback. |
| `lines` | Streaming line iteration. |
| `records` | Generic record iteration. |
| `json_lines` | JSON Lines. |
| `csv_rows` | CSV rows. |
| `binary` | Binary content. |
| `packet_bytes` | PCAP/CAP/PCAPNG bytes/chunks. |
| `bson_stream` | BSON document streams. |

Safety behavior:

- UTF-8 BOM detection и fallback через configured text encodings.
- gzip, bz2, xz/lzma и safe ZIP member handling.
- conservative whole-file, line-level, JSON payload base64 decoding.
- raw files не изменяются.
- нет eval/pickle/subprocess execution.
- bounded raw previews и bounded error samples.

## Status model

| Parser condition | Parser status | File status |
| --- | --- | --- |
| parsed > 0 and failed = 0 | `SUCCESS` | `PARSED` |
| parsed > 0 and failed > 0 | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| no usable content | `EMPTY_FILE` | `EMPTY_FILE` |
| cannot read/parse safely | `FAILED` | `FAILED` |
| intentionally skipped helper file | `SKIPPED` | `SKIPPED` |
| no active parser | `UNSUPPORTED_FORMAT` | `UNSUPPORTED_FORMAT` |

## Labels

Parsers делегируют label decisions в `LabelResolver`.

- Embedded labels и mapping rules разрешены только role-safe.
- TEST filename heuristics отключены.
- Отсутствие label дает explicit unlabeled fields.
- Label/source metadata исключаются из X/model input features schema contracts и leakage checks.

## Reports

Parser coverage:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md
PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md
```

Per-run parser diagnostics:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/
PATH_DATA_STORAGE/reports/ru/stage-two/parser/
```

## Adding parsers

См. [Parser development guide](parser_development_guide.md).

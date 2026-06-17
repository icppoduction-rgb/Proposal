# Final Codex Summary Template

Use this template after the full Stage Two parser chain has been implemented and validated. Do not claim full-corpus success unless the full staged validation commands were actually executed successfully in the current environment.

## Final Answer Template

````markdown
**Files Changed**
- `<path>`: <short description of the change>
- `<path>`: <short description of the change>

**New Parser Classes**
| Branch | Parser class | Source formats | Notes |
| --- | --- | --- | --- |
| dns | `DnsCsvParser` | `csv` | DNS CSV, domain-list, and headerless TEST CSV rows. |
| dns | `DnsPcapCsvParser` | `pcap.csv` | Packet-derived DNS/network CSV rows. |
| dns | `DnsTxtDomainListParser` | `txt` | One-domain-per-line DNS validation lists. |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | Summary-level packet capture parsing. |
| host | `HostCsvParser` | `csv` | Host CSV and metadata/helper CSV handling. |
| host | `HostJsonLinesParser` | `json`, `json-1` | JSON Lines, arrays, and single objects. |
| host | `HostLineLogParser` | syslog/auth/mail/journal/raw log formats | Host line logs and mixed JSON-lines. |
| host | `HostMetricbeatParser` | metric `*.log` formats through `HostLineLogParser` delegation | Host Metricbeat/system metrics rows. |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` | Ordered syscall/API/trace streams. |
| host | `HostBsonSandboxParser` | `bson` | BSON sandbox telemetry. |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | NetFlow/WLS delimited, whitespace, CSV-like, and JSON-line rows. |
| host | `HostXmlParser` | `xml` | Safe event-like XML parsing. |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | Summary-level host/network packet capture parsing. |

**Parser Coverage**
Paste the current `python manage.py stage-two parser-coverage` summary here.

| branch | role | source_format | files_count | parser_active | parser_class | parser_name | action |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `<branch>` | `<role>` | `<format>` | `<count>` | `<yes/no>` | `<ParserClass>` | `<parser_name>` | `<action>` |

Coverage report paths:
- `PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md`

**Commands Executed**
| Command | Result |
| --- | --- |
| `python -m compileall manage.py config.py scripts tests` | `<passed/failed/not run>` |
| `git diff --check` | `<passed/failed/not run>` |
| `<command>` | `<result>` |

**Test And Smoke Results**
- Direct parser smokes: `<passed/failed/not run; include script name>`
- Encoding/base64/compression smokes: `<passed/failed/not run; include script name>`
- Catalog rollback smokes: `<passed/failed/not run; include script name>`
- CLI smokes: `<passed/failed/not run; include script name>`
- DuckDB checks: `<SUCCESS/FAILED/not run>`
- Leakage checks: `<SUCCESS/FAILED/not run>`
- Readiness check: `<SUCCESS/FAILED/not run>`

**Remaining Unsupported Edge Cases**
- `<None, if no unavoidable edge case remains.>`
- `<Only list verified limitations. Do not add speculative issues.>`

**Full Staged Validation Commands**
Run these commands from the repository root after the database and storage configuration are available:

```powershell
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two seed-parser-registry
python manage.py stage-two catalog-ingest
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 10
python manage.py stage-two normalize-all --branch dns --limit 100
python manage.py stage-two normalize-all --branch host --limit 100
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

**Validation Claim**
State one of:
- `Full staged validation passed in this environment.`
- `Full staged validation was not run; only the commands listed above are prepared.`
- `Full staged validation was partially run; failed command: <command>; failure: <short reason>.`
````

## Validation Notes

- `mark-ready --apply` changes PostgreSQL file statuses from allowed pre-parse statuses to `READY_FOR_PARSING`.
- `normalize-format` and `normalize-all` write normalized Parquet artifacts and register parser runs/artifacts.
- Keep TRAIN, VALIDATION, and TEST results separate in any reported paths or summaries.
- Do not include raw packet payloads, BSON streams, or full raw logs in the final report.

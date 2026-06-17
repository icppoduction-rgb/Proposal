# Шаблон финального отчета Codex

Используйте этот шаблон после реализации и проверки всей Stage Two parser chain. Нельзя заявлять full-corpus success, если full staged validation commands не были реально выполнены успешно в текущем окружении.

## Шаблон финального ответа

````markdown
**Files Changed**
- `<path>`: <краткое описание изменения>
- `<path>`: <краткое описание изменения>

**New Parser Classes**
| Branch | Parser class | Source formats | Notes |
| --- | --- | --- | --- |
| dns | `DnsCsvParser` | `csv` | DNS CSV, domain-list и headerless TEST CSV rows. |
| dns | `DnsPcapCsvParser` | `pcap.csv` | Packet-derived DNS/network CSV rows. |
| dns | `DnsTxtDomainListParser` | `txt` | DNS validation lists в формате one-domain-per-line. |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | Summary-level packet capture parsing. |
| host | `HostCsvParser` | `csv` | Host CSV и metadata/helper CSV handling. |
| host | `HostJsonLinesParser` | `json`, `json-1` | JSON Lines, arrays и single objects. |
| host | `HostLineLogParser` | syslog/auth/mail/journal/raw log formats | Host line logs и mixed JSON-lines. |
| host | `HostMetricbeatParser` | metric `*.log` formats через delegation из `HostLineLogParser` | Host Metricbeat/system metrics rows. |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` | Ordered syscall/API/trace streams. |
| host | `HostBsonSandboxParser` | `bson` | BSON sandbox telemetry. |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | NetFlow/WLS delimited, whitespace, CSV-like и JSON-line rows. |
| host | `HostXmlParser` | `xml` | Safe event-like XML parsing. |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | Summary-level host/network packet capture parsing. |

**Parser Coverage**
Вставьте актуальный summary из `python manage.py stage-two parser-coverage`.

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
- Direct parser smokes: `<passed/failed/not run; указать script name>`
- Encoding/base64/compression smokes: `<passed/failed/not run; указать script name>`
- Catalog rollback smokes: `<passed/failed/not run; указать script name>`
- CLI smokes: `<passed/failed/not run; указать script name>`
- DuckDB checks: `<SUCCESS/FAILED/not run>`
- Leakage checks: `<SUCCESS/FAILED/not run>`
- Readiness check: `<SUCCESS/FAILED/not run>`

**Remaining Unsupported Edge Cases**
- `<None, если unavoidable edge cases не осталось.>`
- `<Указывать только проверенные ограничения. Не добавлять speculative issues.>`

**Full Staged Validation Commands**
Запускать из корня репозитория после настройки database и storage:

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
Указать один вариант:
- `Full staged validation passed in this environment.`
- `Full staged validation was not run; only the commands listed above are prepared.`
- `Full staged validation was partially run; failed command: <command>; failure: <short reason>.`
````

## Примечания по validation

- `mark-ready --apply` меняет PostgreSQL statuses файлов из разрешенных pre-parse statuses в `READY_FOR_PARSING`.
- `normalize-format` и `normalize-all` пишут normalized Parquet artifacts и регистрируют parser runs/artifacts.
- TRAIN, VALIDATION и TEST должны оставаться раздельными в любых paths и summaries.
- Не включайте raw packet payloads, BSON streams или full raw logs в финальный отчет.

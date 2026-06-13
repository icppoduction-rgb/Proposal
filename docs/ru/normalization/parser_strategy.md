# Parser strategy

Parser registry seed находится в `scripts/stage_two/parser_registry/parser_registry_seed.json`. Загрузка выполняется командой:

```powershell
python manage.py stage-two seed-parser-registry
```

Resolver выбирает активный parser по `branch`, `source_format` и optional `supported_role`, учитывая `priority`.

## Реализованные MVP parser classes

DNS:

- `DnsCsvParser`
- `DnsPcapCsvParser`
- `DnsTxtDomainListParser`
- `DnsPacketCaptureParser`

Host:

- `HostCsvParser`
- `HostJsonLinesParser`
- `HostLineLogParser`
- `HostSyscallTraceParser`
- `HostPacketCaptureParser`
- `HostBsonSandboxParser`

## Поддерживаемые source formats

Scanner распознает форматы из `scripts/stage_two/ingestion/scanner.py`, включая `csv`, `json`, `json-1`, `txt`, `pcap`, `pcap.csv`, `pcapng`, `cap`, `bson`, host log formats, syscall traces и netflow-like names.

## LabelResolver

Парсеры используют `LabelResolver`:

- сначала учитываются безопасные embedded/configured labels;
- затем применяются активные `label_mapping_rules`;
- конфликтующие labels получают `label_status=conflicting_label`;
- неизвестные labels остаются `unlabeled`;
- TEST filename heuristic не применяется.

## Известное ограничение

В seed зарегистрирован `host_netflow_parser`, но текущий `HostNormalizationService` не содержит mapping для класса `HostNetflowParser`. Такие файлы будут помечены как `SKIPPED`, пока класс parser не будет реализован и добавлен в `HOST_PARSER_CLASSES`.

## Ошибки парсинга

При исключении parser run помечается как `FAILED`, `dataset_files.status` становится `FAILED`, а error message сохраняется в catalog. Частичные ошибки строк приводят к `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`.

# Parser Strategy

The parser registry seed is stored in `scripts/stage_two/parser_registry/parser_registry_seed.json`. Load it with:

```powershell
python manage.py stage-two seed-parser-registry
```

The resolver selects an active parser by `branch`, `source_format`, and optional `supported_role`, respecting `priority`.

## Implemented MVP Parser Classes

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

## Supported Source Formats

The scanner recognizes formats from `scripts/stage_two/ingestion/scanner.py`, including `csv`, `json`, `json-1`, `txt`, `pcap`, `pcap.csv`, `pcapng`, `cap`, `bson`, host log formats, syscall traces, and netflow-like names.

## LabelResolver

Parsers use `LabelResolver`:

- safe embedded/configured labels are considered first;
- active `label_mapping_rules` are applied;
- conflicting labels receive `label_status=conflicting_label`;
- unknown labels remain `unlabeled`;
- TEST filename heuristic is not applied.

## Known Limitation

The seed contains `host_netflow_parser`, but the current `HostNormalizationService` does not map a `HostNetflowParser` class. Such files are marked `SKIPPED` until the parser class is implemented and added to `HOST_PARSER_CLASSES`.

## Parser Errors

On an exception, the parser run is marked `FAILED`, `dataset_files.status` becomes `FAILED`, and the error message is stored in the catalog. Row-level partial failures lead to `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`.

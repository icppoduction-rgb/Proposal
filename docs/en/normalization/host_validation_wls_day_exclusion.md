# Host VALIDATION wls_day exclusion

The raw bucket `host/VALIDATION/wls_day` is excluded from active Stage Two processing after its large JSONL files are split and registered as chunks.

Active processing must use only:

```text
chunked/host/VALIDATION/wls_day/...
```

Do not physically delete the raw files without a separate operator decision. Keep catalog traceability for the source files, parser runs, and any artifacts already produced from the source files. Invalid normalized artifacts from the original source-file runs should stay registered but must not remain `SUCCESS`.

Expected catalog state:

- original raw files: `dataset_files.status = SKIPPED`
- original source parser runs: `parser_runs.status = SKIPPED`
- normalized artifacts produced from original source parser runs: `normalized_artifacts.status = SKIPPED`
- chunked files: remain available as `READY_FOR_PARSING` or `PARSED`

The scanner and operational selectors must not re-activate the raw bucket. `TRAIN`, `VALIDATION`, and `TEST` remain separate role buckets; this exclusion applies only to Host `VALIDATION` `wls_day`.

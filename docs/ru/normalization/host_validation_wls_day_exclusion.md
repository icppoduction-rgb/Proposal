# Исключение Host VALIDATION wls_day

Raw bucket `host/VALIDATION/wls_day` исключен из активной Stage Two обработки после того, как большие JSONL-файлы были разделены и зарегистрированы как chunks.

Активная обработка должна использовать только:

```text
chunked/host/VALIDATION/wls_day/...
```

Не удаляйте raw-файлы физически без отдельного решения оператора. Traceability по исходным файлам, parser runs и уже созданным artifacts должна сохраняться. Невалидные normalized artifacts, созданные из исходных больших файлов, должны оставаться зарегистрированными, но не должны иметь `SUCCESS`.

Ожидаемое состояние catalog:

- исходные raw-файлы: `dataset_files.status = SKIPPED`
- parser runs исходных файлов: `parser_runs.status = SKIPPED`
- normalized artifacts от parser runs исходных файлов: `normalized_artifacts.status = SKIPPED`
- chunked-файлы: остаются доступными как `READY_FOR_PARSING` или `PARSED`

Scanner и operational selectors не должны повторно активировать raw bucket. Роли `TRAIN`, `VALIDATION` и `TEST` не смешиваются; это исключение относится только к Host `VALIDATION` `wls_day`.

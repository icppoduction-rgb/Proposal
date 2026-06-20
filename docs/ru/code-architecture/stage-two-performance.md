# Архитектура производительности Stage Two

Stage Two normalization использует file-level process parallelism и bounded output parts.

## Модель выполнения

- `NormalizeFormatRunner` выбирает файлы строго для одного `branch/role/source_format`.
- При `--workers > 1` файлы отправляются в `ProcessPoolExecutor`.
- Каждый worker открывает собственную PostgreSQL session, получает catalog row по `file_id`, запускает DNS или Host normalization, делает commit и возвращает компактный `NormalizeFileResult`.
- CPU-bound packet parsing не выполняется в threads.

## Модель памяти

- Сервисы потребляют parser output через `parse_batches`.
- Packet parsers читают PCAP/PCAPNG/CAP потоково и не загружают capture целиком в память.
- Output rows пишутся в Parquet parts с лимитом `max_output_part_rows`.
- Output artifact hashing по умолчанию выключен, чтобы не перечитывать большие Parquet файлы. Используйте `--hash-output-artifacts` только когда эта integrity-проверка действительно нужна.

## Resume

`--resume` повторно использует последний non-success `parser_run` для того же file/parser/schema. Уже зарегистрированные normalized artifacts с `metadata_json.part_index` пропускаются, а недостающие части добавляются под тем же parser run. Это сохраняет raw-to-normalized lineage без миграции схемы.

## Метрики

`parser_runs.metadata_json.performance` хранит input size, parse/write/catalog timings, throughput, peak memory и part counts. Normalized artifacts хранят per-part checkpoint metadata.

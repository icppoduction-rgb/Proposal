# Оптимизация производительности Stage Two normalization

Для больших файлов используйте ограниченные batch/part и process workers:

```powershell
python manage.py stage-two normalize-format --branch dns --role TRAIN --format pcap --limit 100 --workers 4 --batch-size 50000 --max-output-part-rows 50000 --packet-mode dns-only --resume
python manage.py stage-two normalize-all --branch host --limit 1000 --workers 4 --batch-size 50000 --max-output-part-rows 50000 --resume
```

## Флаги

| Флаг | Назначение |
| --- | --- |
| `--workers` | Количество процессов для обработки файлов. Используется `ProcessPoolExecutor`, не threads. |
| `--batch-size` | Размер parser batch перед записью normalized rows. |
| `--max-output-part-rows` | Максимальное число строк в одном Parquet part. |
| `--resume` | Повторно использовать последний resumable parser run и пропускать уже зарегистрированные part indexes. |
| `--packet-mode` | Режим packet parsing: `packet-summary`, `dns-only`, `sample`. |
| `--sample-size` | Лимит пакетов для `--packet-mode sample`. |
| `--hash-output-artifacts` | Включить SHA-256 hash output Parquet. По умолчанию выключено для больших output. |

## Метрики

Метрики одного файла сохраняются в `parser_runs.metadata_json.performance`:

- input size MB;
- rows или packets read;
- emitted events;
- parse, Parquet write, catalog и total time;
- rows/sec, packets/sec, events/sec, MB/sec;
- peak Python allocation memory;
- output part count.

Каждый `normalized_artifacts.metadata_json` содержит `part_index`, `batch_index`, `rows_in_part` и checkpoint counters. Это сохраняет traceability от raw file к normalized parts и downstream features/model-ready artifacts.

## Эксплуатационные замечания

`normalize-format` остается ограниченным одним `branch/role/source_format`. `normalize-all` группирует файлы по role и source format внутри одной branch, поэтому `TRAIN`, `VALIDATION` и `TEST` не смешиваются.

Для packet captures в DNS-датасетах используйте `--packet-mode dns-only`, если non-DNS packet summaries не нужны. Режим `sample` с `--sample-size` удобен для smoke/performance проверки перед запуском multi-GB файлов.

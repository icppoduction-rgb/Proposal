# Настройка производительности normalization

Документ описывает только реализованные runtime options из `scripts/stage_two/normalization/options.py` и `scripts/stage_two/cli.py`.

## Опции нормализации

| CLI option | Default | Назначение |
| --- | --- | --- |
| `--workers` | `STAGE_TWO_DEFAULT_WORKERS` (`1`) | Количество parallel worker processes для `normalize-format`/`normalize-all`. |
| `--batch-size` | `STAGE_TWO_DEFAULT_BATCH_SIZE` (`50000`) | Размер batch при parser batch processing. |
| `--max-output-part-rows` | `STAGE_TWO_MAX_OUTPUT_PART_ROWS` (`50000`) | Максимум rows в output part, если service делит output. |
| `--resume` | `false` | Пропускать уже успешно нормализованные files. |
| `--hash-output-artifacts` | `false` | Считать SHA-256 для output Parquet artifacts. |
| `--packet-mode` | `packet-summary` | Режим packet parsing: `packet-summary`, `dns-only`, `sample`. |
| `--sample-size` | unset | Обязателен для `--packet-mode sample`. |

Пример:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 10000 \
  --workers 4 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --resume
```

## Выбор `--workers`

`--workers > 1` включает `ProcessPoolExecutor` в normalization runner. Это полезно для независимых файлов, но увеличивает:

- количество открытых DB connections;
- конкуренцию за диск;
- memory pressure при больших parser outputs;
- сложность диагностики parser errors.

Практический порядок:

1. Начать с `--workers 1 --limit 10`.
2. Проверить parser status, Parquet output и DuckDB checks.
3. Увеличивать workers постепенно.
4. Для binary PCAP/PCAPNG не повышать workers без контроля RAM/IO.

## Packet modes

| Mode | Когда использовать |
| --- | --- |
| `packet-summary` | Default для безопасного summary parsing packet captures. |
| `dns-only` | Когда нужен DNS extraction из packet captures и parser это поддерживает. |
| `sample` | Для первичной оценки больших PCAP/PCAPNG; требует `--sample-size`. |

Если `packet-mode = sample` и `sample-size` не задан, validation options выбросит ошибку.

## Разделение больших файлов

Для больших line-based files используйте:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Splitter поддерживает text/line formats и не предназначен для `cap`, `pcap`, `pcapng`, `bson`.

Риски:

- JSON arrays/objects могут быть небезопасны для line split;
- header handling нужно проверять через `--header auto|yes|no`;
- без `--register` chunks не появятся в catalog.

## Хеширование output artifacts

`--hash-output-artifacts` повышает проверяемость, но добавляет IO cost, потому что файл нужно прочитать после записи. Для smoke/iteration можно оставить выключенным; для финальных artifacts лучше включать.

## Resume

`--resume` пропускает файлы, для которых уже есть успешный normalized artifact. Это не заменяет data quality checks: после resume все равно нужно запускать:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

## Ограничения

- Performance options не должны менять contracts и labels.
- Нельзя объединять роли ради ускорения.
- Нельзя использовать `TEST` для подбора batch/feature/preprocessing решений, если это влияет на training pipeline.
- Для mixed CSV/JSON schemas лучше уменьшить batch size и сначала прогнать `--limit`.
## Обновление performance architecture

Stage Two теперь поддерживает resource profiles, format-specific policy, bounded multiprocessing, streaming parser batches, chunk-aware large-file processing, atomic Parquet writes, benchmark reports и post-run quality gates.

### Performance target

- Цель по датасету: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Целевая скорость для текущего железа: `10-20+ GB/hour` для line-based formats при нормальном состоянии RAM, PostgreSQL, SSD и parser errors.

Текущее железо:

- CPU: Intel Core i7-14700KF.
- RAM: 64 GB DDR5.
- Storage: Samsung M.2 SSD 2 TB.
- GPU: MSI GeForce RTX 5060 Ti 16 GB.

GPU зарезервирован для feature/model-ready/training layers. Raw normalization parsers по умолчанию работают на CPU; PCAP/BSON/raw log parsing не переносится на GPU без отдельного backend и проверок корректности.

### Resource profiles

Используйте `--resource-profile safe|balanced|fast|aggressive` с `normalize-format`, `normalize-all` и `benchmark-normalization`.

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size | hash_output_artifacts |
| --- | ---: | ---: | ---: | ---: | --- |
| `safe` | 4 | 50000 | 100000 | 50000 | false |
| `balanced` | 8 | 100000 | 250000 | 50000 | false |
| `fast` | 12 | 200000 | 500000 | 50000 | false |
| `aggressive` | 14 | 300000 | 750000 | 50000 | false |

CLI arguments имеют приоритет над profile. Пример: `--resource-profile fast --workers 6` дает `workers=6`, остальные параметры берутся из `fast`.

CLI печатает `resolved_runtime_settings` перед запуском normalization. Для `aggressive` warning является эксплуатационным предупреждением: контролируйте RAM, DB connections, parser failures и SSD throttling.

### Format policy

Если пользователь явно не указал runtime параметры, `normalize-format` применяет format policy после profile resolution:

- быстрые line-based formats (`txt`, `sc`, `ghc`, log/syslog/messages/mainlog, `wls_day`, metric logs): больше workers и batch size;
- CSV / `pcap.csv` / NetFlow: умеренно высокие workers и большие batches;
- JSON / JSONL (`json`, `json-1`): умеренные workers и batches;
- BSON: низкое число workers;
- PCAP / PCAPNG / CAP: низкое число workers, `packet_batch_size=50000`, default `packet_mode=packet-summary`.

Явные CLI значения не перезаписываются policy.

### Рекомендуемый порядок

1. Готовить к запуску один точный bucket: `branch/role/source_format`.
2. Сначала benchmark на 5-10% данных: сначала `--dry-run`, затем небольшой actual run.
3. Начинать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки DuckDB, leakage, parser errors, RAM, DB connections и SSD.
5. Использовать `aggressive` только для line-based formats после чистых проверок.
6. Full run запускать с `--resume`.
7. После run запускать DuckDB, leakage и readiness checks.

### Команды

Benchmark 5-10%:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Split большого line-based файла:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Быстрая normalization для line-based формата:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

Post-run checks:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

### Safety invariants

- Raw files не изменяются.
- `TRAIN`, `VALIDATION`, `TEST` не смешиваются в catalog, Parquet paths, features и model-ready artifacts.
- `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается control plane; большие normalized/features/model-ready данные хранятся в Parquet.
- Labels и source/path/scenario/dataset role fields не попадают в model-ready X.
- Отсутствующий label не считается benign.
- Отсутствующий timestamp не заменяется текущим временем.
- Parser errors остаются явными: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.
- Traceability сохраняется по цепочке `raw -> normalized -> features -> model-ready`.

### Troubleshooting

| Симптом | Вероятная причина | Действие |
| --- | --- | --- |
| PostgreSQL timeout | слишком много workers или медленные catalog updates | уменьшить `--workers`, использовать `safe`, проверить DB locks/pool, перезапустить с `--resume` |
| too many DB connections | workers превышают capacity БД | ограничить workers до `4-8`, не использовать `aggressive`, проверить per-worker sessions |
| memory pressure | слишком большой batch/output part или binary parser load | уменьшить `--batch-size` и `--max-output-part-rows`; split для line-based files |
| SSD throttling | слишком много concurrent writes или hashing | уменьшить workers, не включать `--hash-output-artifacts` на итерациях, проверить температуру SSD |
| too many small files | overhead futures/DB/filesystem | использовать bounded executor, запускать точный format bucket, держать `--resume` |
| parser errors | malformed rows или новая schema variant | читать parser run report и error samples; failed rows не скрывать |
| empty DuckDB views | нет Parquet, неверный `PATH_DATA_STORAGE` или failed normalization | выполнить `bootstrap-storage`, проверить artifact paths, запустить `run-duckdb-checks` |
| leakage critical | forbidden X columns или TEST contamination | заблокировать artifact use, проверить `run-leakage-checks`, пересобрать features/model-ready |

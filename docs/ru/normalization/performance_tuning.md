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

# Stage Three Performance Tuning

## Default policy

Stage Three должен быть CPU-first и streaming-first:

- не загружать крупные datasets целиком в pandas/DataFrame memory;
- использовать Parquet column projection и predicate pushdown;
- держать PostgreSQL как metadata/catalog layer;
- хранить крупные feature/model-ready данные в Parquet;
- использовать GPU только после runtime probe и проверки корректности.

## Рекомендуемый профиль для текущего ПК

```text
STAGE_THREE_DEFAULT_PROFILE=balanced
STAGE_THREE_ACCELERATION_BACKEND=auto
STAGE_THREE_RESERVED_RAM_GB=8
STAGE_THREE_SOFT_RAM_LIMIT_GB=48
STAGE_THREE_HARD_RAM_LIMIT_GB=56
STAGE_THREE_DEFAULT_WORKERS=8
STAGE_THREE_MAX_WORKERS=12
STAGE_THREE_DB_WORKERS=4
STAGE_THREE_BATCH_ROWS=250000
STAGE_THREE_PARQUET_ROW_GROUP_SIZE=250000
STAGE_THREE_GPU_MEMORY_SOFT_LIMIT_GB=12
STAGE_THREE_GPU_MEMORY_HARD_LIMIT_GB=14
```

## CPU path

CPU path является обязательным production fallback. Предпочтительные инструменты:

- `pyarrow.dataset` для streaming/batch Parquet scans;
- `duckdb` для out-of-core SQL checks;
- `polars` lazy для тяжелых transforms, если он уже используется в реализации;
- bounded worker pools вместо запуска всех CPU threads.

## GPU path

GPU optional. На native Windows нельзя делать RAPIDS/cuDF обязательной зависимостью. В `auto` mode GPU можно использовать только если:

- dependency доступна;
- small correctness probe совпал с CPU output в допустимом tolerance;
- VRAM/RAM остаются в лимитах;
- CPU fallback остается рабочим.

## Workers and memory

Не стартовать сразу все 28 CPU threads. Практический порядок:

1. Начать с `STAGE_THREE_DEFAULT_WORKERS=8`.
2. Проверить runtime report и RAM usage.
3. Повышать workers только если storage, DB и memory остаются стабильными.
4. При memory pressure уменьшить `STAGE_THREE_BATCH_ROWS` и workers.

## MVP DNS path

Для первого результата держать scope узким:

- branch: `dns`;
- profile: `tree_unscaled`;
- target: `label_binary`;
- feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`;
- no SMOTE/resampling;
- class imbalance обрабатывать на Stage Four через `class_weight` или `scale_pos_weight`.

## Production path

Для production expansion:

- разделить jobs по branch/role/feature_group;
- использовать `--resume`;
- запускать checks после каждого крупного batch;
- не смешивать output разных experiment_id;
- писать final report для каждого production experiment_id.

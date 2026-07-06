# Stage Three Performance Tuning

## Default Policy

Stage Three should be CPU-first and streaming-first:

- do not load large datasets fully into pandas/DataFrame memory;
- use Parquet column projection and predicate pushdown;
- keep PostgreSQL as the metadata/catalog layer;
- store large feature/model-ready data in Parquet;
- use GPU only after runtime probing and correctness checks.

## Recommended Profile for This Machine

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

## CPU Path

The CPU path is the required production fallback. Preferred tools:

- `pyarrow.dataset` for streaming/batch Parquet scans;
- `duckdb` for out-of-core SQL checks;
- `polars` lazy for heavy transforms if already used by the implementation;
- bounded worker pools instead of using every CPU thread at once.

## GPU Path

GPU is optional. RAPIDS/cuDF must not be a required dependency on native Windows. In `auto` mode, GPU may be used only when:

- the dependency is available;
- a small correctness probe matches CPU output within tolerance;
- VRAM/RAM stays within limits;
- CPU fallback remains fully working.

## Workers and Memory

Do not start all 28 CPU threads immediately. Practical sequence:

1. Start with `STAGE_THREE_DEFAULT_WORKERS=8`.
2. Check the runtime report and RAM usage.
3. Increase workers only while storage, DB, and memory stay stable.
4. On memory pressure, reduce `STAGE_THREE_BATCH_ROWS` and workers.

## MVP DNS Path

For the first result, keep scope narrow:

- branch: `dns`;
- profile: `tree_unscaled`;
- target: `label_binary`;
- feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`;
- no SMOTE/resampling;
- handle class imbalance in Stage Four with `class_weight` or `scale_pos_weight`.

## Production Path

For production expansion:

- split jobs by branch/role/feature_group;
- use `--resume`;
- run checks after every large batch;
- do not mix outputs from different experiment IDs;
- write a final report for every production experiment ID.

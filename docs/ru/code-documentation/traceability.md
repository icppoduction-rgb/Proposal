# Трассируемость

Traceability связывает model-ready artifact с feature artifact, normalized Parquet, parser run, raw file и dataset.

## Сервис

Файл: `scripts/stage_two/traceability/service.py`.

Команда:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Режимы поиска:

- числовой argument -> `model_ready_artifacts.id`;
- нечисловой argument -> `model_ready_artifacts.artifact_path`.

## Цепочка

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

## Возвращаемая metadata

`TraceabilityChain` возвращает dictionaries для:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Ключевые fields включают artifact paths, role, branch, data type/modality, statuses, parser counters, raw file path/hash и dataset identity.

## Обязательные связи

Сервис поднимает `TraceabilityError`, если:

- model-ready artifact не найден;
- `feature_artifact_id` равен null;
- связанный feature artifact не найден;
- `normalized_artifact_id` равен null;
- связанный normalized artifact не найден;
- связанный parser run не найден;
- связанный dataset file не найден;
- связанный dataset не найден.

## Следствия контракта

Хотя некоторые FK columns nullable для поддержки staged/incomplete artifacts, production artifacts для экспериментов должны заполнять traceability links. Иначе:

- воспроизводимость нарушена;
- leakage audits не могут атрибутировать samples;
- academic implementation description не может доказать lineage;
- model-ready artifacts должны считаться incomplete.

## Traceability в row schemas

Normalized rows включают event/file/parser fields. Feature rows должны сохранять:

```text
sample_uid
dataset_id
normalized_artifact_id
role
branch
feature_group
feature_schema_name
feature_schema_version
source_event_uid_refs
source_normalized_path
created_at
```

Эти traceability fields обязательны в feature artifacts, но исключаются из model-ready X artifacts. Они остаются в catalog и audit layers.

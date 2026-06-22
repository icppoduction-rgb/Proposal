# Traceability и lineage

Traceability связывает model-ready artifact с исходным raw file через PostgreSQL Catalog и Parquet metadata. Цепочка нужна для audit, воспроизводимости, поиска leakage и проверки, что raw files не изменялись.

## Реализация

Код:

```text
scripts/stage_two/traceability/service.py
```

CLI:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Числовой аргумент ищется как `model_ready_artifacts.id`, строковый - как `model_ready_artifacts.artifact_path`.

## Обязательная цепочка

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

Если link отсутствует, `TraceabilityService` выбрасывает `TraceabilityError`. Readiness check считает это `FAILED`.

## Что возвращает service

Trace chain включает metadata блоки:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Этого достаточно, чтобы ответить:

- из какого raw файла получен artifact;
- каким parser и schema version он обработан;
- где лежит normalized Parquet;
- из какого feature artifact собран model-ready artifact;
- какая role/branch использовалась на каждом уровне.

## Правила сохранения traceability

1. `normalized_artifacts.parser_run_id` должен ссылаться на реальный `parser_runs.id`.
2. `parser_runs.file_id` должен ссылаться на `dataset_files.id`.
3. `feature_artifacts.normalized_artifact_id` должен быть заполнен для production artifacts.
4. `model_ready_artifacts.feature_artifact_id` должен быть заполнен для traceable model-ready artifacts.
5. Raw file hash в `dataset_files.file_hash_sha256` должен совпадать с текущим файлом при readiness check.

## Traceability и leakage

Traceability fields нельзя удалять из catalog, но нельзя включать в model-ready `X`. Поля paths, hashes, IDs и raw metadata могут идентифицировать dataset/source и создавать leakage. Они должны оставаться в catalog/metadata или быть исключены через `x_excluded_columns`.

## Проверка

```bash
python manage.py stage-two trace-artifact 123
python -m scripts.stage_two.readiness_check
```

`readiness_check` дополнительно проверяет один последний traceable model-ready artifact и raw file hashes.

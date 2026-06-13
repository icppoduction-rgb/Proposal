# Data leakage prevention

Stage Two защищает TRAIN/VALIDATION/TEST split на уровне storage paths, catalog constraints, schema contracts и quality checks.

## Основные правила

- TRAIN, VALIDATION и TEST остаются физически разделенными в Parquet paths.
- TEST не используется для fit preprocessing artifacts.
- X artifacts не должны содержать labels, source paths, raw metadata или traceability columns.
- y artifacts хранят labels отдельно от X.
- LabelResolver не применяет filename heuristic к TEST.

## TRAIN-only preprocessing

`preprocessing_artifacts.fitted_on_role` ограничен значением `TRAIN` на уровне PostgreSQL check constraint и Python validation. Model-ready registry также вызывает `validate_preprocessing_fit_role`.

## Запрещенные X columns

Контракт `schemas/model_ready/model_ready_v1.json` и `scripts/stage_two/model_ready/contracts.py` запрещают в X:

- label columns: `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`;
- split/source columns: `dataset_name`, `dataset_role`, `role`, `branch`, `source_file_path`, `source_file_hash`;
- traceability columns: `source_normalized_path`, `source_event_uid_refs`, `parser_run_id`, `normalized_artifact_id`, `event_uid`, `sample_uid`;
- raw metadata columns: `scenario_name`, `raw_fields_json`, `metadata_json`, `created_at`.

## LeakageChecker

Команда:

```powershell
python manage.py stage-two run-leakage-checks
```

Проверяет:

- forbidden X columns в model-ready Parquet;
- отсутствие TEST rows в TRAIN model-ready artifacts;
- что preprocessing artifacts fitted only on TRAIN.

При failed leakage report severity становится `CRITICAL`. Метод `block_model_ready_if_failed` может перевести successful model-ready artifact в `BLOCKED`.

## Traceability без leakage

Traceability metadata хранится в catalog и служит для аудита, но не должна попадать в X. Для анализа цепочки используется:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

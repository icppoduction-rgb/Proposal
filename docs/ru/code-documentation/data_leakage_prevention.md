# Предотвращение data leakage

Предотвращение leakage обеспечивается документацией, контрактами, runtime validation и DuckDB checks. Полагаться только на соглашения небезопасно.

## Жесткие правила

1. `TEST` никогда не используется для training, preprocessing fit, encoder/scaler fit, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` остаются физически разделенными по role в Parquet paths.
3. Labels хранятся отдельно от X-признаков.
4. Model-ready X artifacts не должны содержать label/source/traceability leakage columns.
5. Отсутствующие labels получают статус `unlabeled`, а не benign.
6. Filename heuristic для TEST отключен.

## Контроль в коде

| Правило | Код |
|---|---|
| X forbidden columns | `scripts/stage_two/model_ready/contracts.py::validate_x_columns` |
| Исключенные колонки feature layer | `scripts/stage_two/features/contracts.py::X_EXCLUDED_COLUMNS` |
| TRAIN-only preprocessing | `validate_preprocessing_fit_role()` и DB check constraint |
| Отключение TEST filename heuristic | `LabelResolver.label_hints_allowed()` |
| Отчет leakage | `LeakageChecker` |

## Запрещенные X columns

Текущий код использует `X_EXCLUDED_COLUMNS`/`X_FORBIDDEN_COLUMNS`. Обязательный forbidden list из задачи покрыт и расширен реализацией:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

Примечание: `model_ready_v1.json` сейчас не включает `entity_type`, `entity_id`, `window_start`, `window_end`, `window_size_seconds`, `window_step_seconds`, но `features/contracts.py` включает их в `X_EXCLUDED_COLUMNS`. Для X validation нужно использовать более строгий union.

## Проверки LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Проверки:

| Проверка | Условие отказа |
|---|---|
| `x_forbidden_columns` | forbidden X columns есть в model-ready X files и содержат non-null values |
| `test_absent_from_train` | `dataset_role='TEST'` найден в TRAIN model-ready files |
| `preprocessing_fit_only_train` | preprocessing artifact имеет `fitted_on_role != 'TRAIN'` |

Severity для failed leakage report: `CRITICAL`.

`block_model_ready_if_failed()` может пометить успешный model-ready artifact как `BLOCKED`, если leakage report завершился ошибкой.

## Безопасный паттерн model-ready

Ожидаемое разделение artifacts:

```text
parquet/model_ready/tabular/{branch}/TRAIN/schema=v1/X_train.parquet
parquet/model_ready/labels/{branch}/TRAIN/schema=v1/y_train.parquet
parquet/model_ready/tabular/{branch}/VALIDATION/schema=v1/X_validation.parquet
parquet/model_ready/labels/{branch}/VALIDATION/schema=v1/y_validation.parquet
parquet/model_ready/tabular/{branch}/TEST/schema=v1/X_test.parquet
parquet/model_ready/labels/{branch}/TEST/schema=v1/y_test.parquet
```

X files содержат только model features. y files содержат labels. Traceability/source fields остаются в catalog и optional audit artifacts, а не в X.

## Небезопасные предположения

- Не выводить `benign` из отсутствующего label.
- Не использовать filename labels для TEST.
- Не выполнять threshold tuning на TEST.
- Не смешивать role partitions в одном X artifact.
- Не хранить `source_file_path`/`event_uid`/`dataset_name` в X, потому что модели могут запомнить source identity.

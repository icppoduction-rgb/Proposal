# Предотвращение data leakage

Leakage prevention в Stage Two опирается на contract-level запреты, catalog traceability и runtime checks. Главная цель: labels, source identifiers и split metadata не должны попадать в model-ready `X`.

## Неприкосновенные правила

1. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` не смешиваются в одном model-ready artifact.
3. Labels не являются обычными input features.
4. Filename heuristic для `TEST` labels запрещен.
5. Отсутствующий label не означает benign.
6. Traceability fields сохраняются в catalog/metadata, но исключаются из `X`.

## Запрещенные X columns

Запрещенные columns берутся из feature/model-ready contracts:

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

`ModelReadyRegistryService.write_table_artifact()` вызывает `validate_x_columns()` для `data_type = "X"` и отклоняет rows, если в них есть запрещенные поля.

## LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Код:

```text
scripts/stage_two/quality/checkers.py
```

Проверки:

| Проверка | Что ловит |
| --- | --- |
| `x_forbidden_columns` | Label/source/traceability columns внутри model-ready `X`. |
| `test_absent_from_train` | Использование `TEST` в training context. |
| `preprocessing_fit_only_train` | Preprocessing artifact fitted на роли, отличной от `TRAIN`. |

CRITICAL нарушения регистрируются в `data_quality_reports` и должны блокировать использование artifact.

## Labels

Label fields могут присутствовать в normalized events для audit и в model-ready `y`, но не в `X`. События без label остаются unlabeled:

```json
{
  "label_binary": null,
  "label_source": "none",
  "label_status": "unlabeled"
}
```

См. [label_resolver.md](label_resolver.md).

## Traceability без leakage

Traceability chain обязателен:

```text
raw -> normalized -> features -> model-ready
```

Но traceability identifiers (`event_uid`, `sample_uid`, paths, hashes, parser IDs) не должны становиться признаками. Они должны храниться:

- в PostgreSQL Catalog;
- в artifact metadata;
- в non-X columns, исключенных из training matrix.

## DNS supervised 70/30 policy

Для DNS supervised split `dns_supervised_70_30_v1` leakage prevention включает
не только запрет label/source/path fields в `X`, но и запрет некорректных
источников:

- текущий DNS `TEST/csv` и его chunked downstream artifacts не используются в supervised evaluation;
- `ens33-dns_amplification_attack.pcap` исключен полностью;
- `ens33-dns_amplification_attack__f291ed87a1.pcap` ограничивается global target;
- `label_binary=NULL` исключается, а не конвертируется в normal;
- `split_index.parquet` проверяется на отсутствие пересечений `sample_uid` между `TRAIN`, `VALIDATION`, `TEST`;
- `traceability.parquet` сохраняет `source_role`, `normalized_artifact_id`, `source_normalized_path` и `split_policy_id`, но эти поля не попадают в `X.parquet`.

Проверочный отчет:

```text
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
```

Вердикт готовности:

- активный experiment: `dns_rebalanced_70_30_v1`;
- статус: готово для обучения supervised tabular модели;
- quality checks: `PASS`, без `blocking_issues`, без предупреждений по timestamp;
- leakage/traceability checks: `PASS`;
- `TEST` остается только для финальной evaluation.

## Типовые ошибки

| Ошибка | Последствие | Исправление |
| --- | --- | --- |
| `label_binary` попал в X | Модель обучается на ответе. | Пересобрать X после exclusion contract. |
| `source_file_path` попал в X | Модель может выучить dataset/source identity. | Удалить source fields из feature selection. |
| `TEST` использован для scaler fit | Метрики становятся завышенными. | Fit только на `TRAIN`, transform для `VALIDATION`/`TEST`. |
| Unlabeled заменен на benign | Искажение labels. | Сохранять `label_binary = null`, `label_status = unlabeled`. |
| Filename heuristic для TEST | Leakage из имени файла. | Отключить heuristic, использовать только explicit ground truth. |

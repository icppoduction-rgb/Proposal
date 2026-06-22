# Разрешение labels

`LabelResolver` находится в:

```text
scripts/stage_two/labels/resolver.py
```

Он приводит labels из разных источников к canonical normalized fields и защищает pipeline от опасного предположения "нет label = benign".

## Canonical label fields

| Поле | Значение |
| --- | --- |
| `label_binary` | `1`, `0` или `null`. |
| `label_family` | Семейство/класс атаки, если известно. |
| `label_subtype` | Более точный subtype, если известен. |
| `label_source` | `embedded_column`, `external_file`, `scenario_metadata`, `filename`, `ids_alert`, `none` и т.п. |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label`. |
| `label_confidence` | Число confidence, если применимо. |
| `label_mapping_rule_id` | ID rule из catalog/config, если label получен правилом. |

Unlabeled output:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

## Источники labels

| Источник | Приоритет | Комментарий |
| --- | --- | --- |
| Embedded column | 0 | Поля вроде `label_binary`, `label`, `target`, `class`, `is_attack`, `malicious`, `attack_cat`. |
| External/ground truth rule | 1 | Rule из catalog/config, если он явно матчится. |
| Scenario metadata | 2 | Metadata контекст dataset/scenario. |
| Filename | 3 | Weak/inferred hint из имени файла; запрещен для `TEST`. |
| IDS alert | 4 | Alert-derived weak signal. |
| None | 99 | Нет label. |

Точные поля embedded labels перечислены в `EMBEDDED_LABEL_FIELDS` в `resolver.py`.

## Политика TEST

`LabelResolver.label_hints_allowed()` возвращает `False` для `TEST`. Это означает:

- filename heuristic нельзя использовать для label inference в `TEST`;
- embedded/IDS hints, которые являются эвристикой, не должны превращать `TEST` в training signal;
- `TEST` не используется для threshold tuning, feature selection или preprocessing fit.

Explicit external ground truth rules допустимы только если они не являются filename heuristic и явно заданы как label source. Если label отсутствует, событие остается unlabeled.

## Конфликтующие labels

Если разные источники дают несовместимые canonical labels, результат должен фиксироваться как `conflicting_label`, а не silently выбирать benign/malicious. Такой случай должен попадать в metadata/errors и далее в quality review.

## Использование в parser

Parser должен передавать raw record и context в resolver и включать результат в normalized event:

```python
labels = self.label_resolver.resolve(record, context)
event.update(labels)
```

Если parser читает source, где label отсутствует, он не должен создавать `label_binary = 0`. Правильный output - unlabeled contract выше.

## Labels и model-ready artifacts

Labels не входят в X features. Они должны храниться отдельно:

- в normalized events как label metadata;
- в feature/model-ready metadata как label distribution;
- в model-ready `y` artifact, если downstream stage создает labels table.

Для model-ready `X` поля `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id` и другие label/source columns запрещены.

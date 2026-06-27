# Label Resolver

`LabelResolver` is implemented in:

```text
scripts/stage_two/labels/resolver.py
```

It maps labels from different sources to canonical normalized fields and protects the pipeline from the unsafe assumption "missing label = benign".

## Canonical Label Fields

| Field | Meaning |
| --- | --- |
| `label_binary` | `1`, `0`, or `null`. |
| `label_family` | Attack family/class when known. |
| `label_subtype` | More precise subtype when known. |
| `label_source` | `embedded_column`, `external_file`, `scenario_metadata`, `filename`, `ids_alert`, `none`, etc. |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label`. |
| `label_confidence` | Confidence value when applicable. |
| `label_mapping_rule_id` | Rule ID from catalog/config when a rule produced the label. |

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

## Label Sources

| Source | Priority | Comment |
| --- | --- | --- |
| Embedded column | 0 | Fields such as `label_binary`, `label`, `target`, `class`, `is_attack`, `malicious`, `attack_cat`. |
| External/ground truth rule | 1 | Rule from catalog/config when it explicitly matches. |
| Scenario metadata | 2 | Dataset/scenario metadata context. |
| Filename | 3 | Weak/inferred hint from file name; disabled for `TEST`. |
| IDS alert | 4 | Alert-derived weak signal. |
| None | 99 | No label. |

The exact embedded label fields are listed in `EMBEDDED_LABEL_FIELDS` in `resolver.py`.

## TEST Policy

`LabelResolver.label_hints_allowed()` returns `False` for `TEST`. This means:

- filename heuristics must not be used for label inference in `TEST`;
- embedded/IDS hints that are heuristic signals must not turn `TEST` into a training signal;
- `TEST` is not used for threshold tuning, feature selection, or preprocessing fit.

Explicit external ground truth rules are allowed only when they are not filename heuristics and are explicitly configured as label sources. If a label is missing, the event remains unlabeled.

## Conflicting Labels

If different sources provide incompatible canonical labels, the result must be recorded as `conflicting_label`, not silently resolved to benign/malicious. The case should be visible in metadata/errors and reviewed by quality checks.

## Parser Usage

A parser should pass the raw record and context to the resolver and include the result in the normalized event:

```python
labels = self.label_resolver.resolve(record, context)
event.update(labels)
```

If the parser reads a source without labels, it must not create `label_binary = 0`. The correct output is the unlabeled contract above.

## Labels and Model-Ready Artifacts

Labels are not X features. They should be stored separately:

- in normalized events as label metadata;
- in feature/model-ready metadata as label distribution;
- in a model-ready `y` artifact when the downstream stage creates a labels table.

For model-ready `X`, fields such as `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id`, and other label/source columns are forbidden.

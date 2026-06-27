# Label Resolver

File: `scripts/stage_two/labels/resolver.py`.

Goal: produce canonical label fields for normalized events, avoid treating missing labels as benign, and disable filename heuristics for TEST.

## Sources

Label candidates can come from:

| Source | Code value | Meaning |
|---|---|---|
| Embedded columns | `embedded_column` | direct fields such as `label`, `target`, `is_attack`, `attack_cat` |
| External rules/config | `external_label_file`, `ground_truth_csv`, etc. | DB/config mapping rules |
| Scenario metadata | `scenario_metadata` | contextual labels from scenario/rule metadata |
| Filename | `filename` | conservative filename tokens for non-TEST only |
| IDS alert | `ids_alert` | weak alert-like signal |
| None | `none` | explicit unlabeled result |

Priority in code:

```text
embedded_column < ground_truth_csv/external_label_file < scenario_metadata
< filename < ids_alert < none
```

## Embedded Labels

Recognized fields include:

```text
label_binary, label, labels, target, class, is_attack, is_malicious,
malicious, attack, attack_cat, attack_category, attack_subcat,
is_executing_exploit, exploit
```

For `TEST`, embedded/filename/IDS hint candidates are blocked by `label_hints_allowed(context) == False`. This is intentional to avoid TEST leakage and evaluation contamination through filename heuristics.

## Mapping Rules

Rules can be loaded from:

- `PATH_DATA_STORAGE/config/label_mapping_rules.json` through `LABEL_MAPPING_RULES_CONFIG`;
- PostgreSQL `label_mapping_rules` through `LabelRepository`.

Rule matching can use:

- branch;
- role;
- source_format;
- dataset_name_pattern;
- file_name_pattern;
- source_field;
- source_value_pattern.

Rule output fields:

- `label_binary`;
- `label_family`;
- `label_subtype`;
- `label_source`;
- `label_status`;
- `label_confidence`;
- `label_mapping_rule_id`.

## Filename Labels

Filename labels are only allowed when:

```python
context.dataset_role.upper() != "TEST"
```

Recognized benign tokens:

```text
0, false, benign, normal, clean, legitimate
```

Recognized malicious/family tokens include:

```text
1, true, attack, malicious, exploit, malware, phishing, spam,
exfil, exfiltration, tunnel, tunneling, dga, nmap, hping,
masscan, zmap
```

TEST filename heuristic is disabled. Do not re-enable it for evaluation datasets.

## Missing Labels

Missing labels produce:

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

Hard invariant: missing label does not mean benign.

## Weak and Inferred Labels

| Status | Use |
|---|---|
| `explicit_label` | trusted direct label |
| `inferred_label` | filename/scenario/rule inference |
| `weak_label` | weak signal such as IDS alert |
| `partial_label` | partial coverage or window/scenario labels |
| `unlabeled` | no reliable label |
| `conflicting_label` | same-priority candidates conflict |

Weak/inferred labels must be tracked with `label_source`, `label_status`, `label_confidence`, and preferably `label_mapping_rule_id`.

## Conflicts

If top-priority candidates disagree on `label_binary` or `label_family`, resolver returns:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_source": "<source>",
  "label_status": "conflicting_label",
  "label_confidence": 0.0
}
```

Downstream supervised training must not silently convert `conflicting_label` or `unlabeled` to benign.

## Canonical Label Fields

The normalized schema and model-ready contracts treat these as label/leakage fields:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
```

They may appear in normalized or y/analysis artifacts, but not in model-ready X artifacts.

# Разрешение labels

Файл: `scripts/stage_two/labels/resolver.py`.

Цель: формировать canonical label fields для normalized events, не трактовать missing labels как benign и не разрешать filename heuristics для TEST.

## Источники

Кандидаты labels могут поступать из:

| Источник | Значение в коде | Смысл |
|---|---|---|
| Embedded columns | `embedded_column` | прямые поля вроде `label`, `target`, `is_attack`, `attack_cat` |
| External rules/config | `external_label_file`, `ground_truth_csv`, etc. | DB/config mapping rules |
| Scenario metadata | `scenario_metadata` | contextual labels из scenario/rule metadata |
| Filename | `filename` | консервативные filename tokens только для non-TEST |
| IDS alert | `ids_alert` | слабый alert-like signal |
| None | `none` | явный unlabeled result |

Приоритет источников в коде:

```text
embedded_column < ground_truth_csv/external_label_file < scenario_metadata
< filename < ids_alert < none
```

## Встроенные labels

Распознаваемые fields:

```text
label_binary, label, labels, target, class, is_attack, is_malicious,
malicious, attack, attack_cat, attack_category, attack_subcat,
is_executing_exploit, exploit
```

Для `TEST` embedded/filename/IDS hint candidates блокируются условием `label_hints_allowed(context) == False`. Это сделано намеренно, чтобы избежать TEST leakage и загрязнения evaluation через filename heuristic.

## Правила mapping

Правила могут загружаться из:

- `PATH_DATA_STORAGE/config/label_mapping_rules.json` через `LABEL_MAPPING_RULES_CONFIG`;
- PostgreSQL `label_mapping_rules` через `LabelRepository`.

Rule matching может использовать:

- branch;
- role;
- source_format;
- dataset_name_pattern;
- file_name_pattern;
- source_field;
- source_value_pattern.

Выходные fields правила:

- `label_binary`;
- `label_family`;
- `label_subtype`;
- `label_source`;
- `label_status`;
- `label_confidence`;
- `label_mapping_rule_id`.

## Labels из имени файла

Filename labels разрешены только при условии:

```python
context.dataset_role.upper() != "TEST"
```

Распознаваемые benign tokens:

```text
0, false, benign, normal, clean, legitimate
```

Распознаваемые malicious/family tokens:

```text
1, true, attack, malicious, exploit, malware, phishing, spam,
exfil, exfiltration, tunnel, tunneling, dga, nmap, hping,
masscan, zmap
```

TEST filename heuristic отключен. Его нельзя включать для evaluation datasets.

## Отсутствующие labels

Отсутствующие labels дают:

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

Это жесткий инвариант: отсутствие label не означает benign.

## Weak и inferred labels

| Статус | Использование |
|---|---|
| `explicit_label` | trusted direct label |
| `inferred_label` | inference по filename/scenario/rule |
| `weak_label` | weak signals, например IDS alert |
| `partial_label` | partial coverage или window/scenario labels |
| `unlabeled` | reliable label отсутствует |
| `conflicting_label` | конфликт candidates с одинаковым priority |

Weak/inferred labels должны сопровождаться `label_source`, `label_status`, `label_confidence` и желательно `label_mapping_rule_id`.

## Конфликты

Если top-priority candidates расходятся по `label_binary` или `label_family`, resolver возвращает:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_source": "<source>",
  "label_status": "conflicting_label",
  "label_confidence": 0.0
}
```

Downstream supervised training не должен неявно преобразовывать `conflicting_label` или `unlabeled` в benign.

## Канонические label fields

Normalized schema и model-ready contracts трактуют эти поля как label/leakage fields:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
```

Они могут присутствовать в normalized или y/analysis artifacts, но не в model-ready X artifacts.

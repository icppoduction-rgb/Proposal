# Stage Three Command Reference

Run all commands from `C:\Users\Public\PythonProjects\Proposal`.

## Help

```powershell
python manage.py stage-three --help
```

## validate-inputs

```powershell
python manage.py stage-three validate-inputs --branch <dns|host|network|hybrid> --role <TRAIN|VALIDATION|TEST>
```

Checks whether Stage Two normalized artifacts can be used as Stage Three input.

## build-feature-catalog

```powershell
python manage.py stage-three build-feature-catalog [--feature-group <name>]
```

Validates the machine-readable feature catalog and writes Task05 reports.

## probe-runtime-backend

```powershell
python manage.py stage-three probe-runtime-backend --backend <auto|cpu|gpu> [--profile balanced] [--skip-probe]
```

Resolves runtime backend and memory guard settings.

## extract-features

```powershell
python manage.py stage-three extract-features --branch <branch> --role <role> --feature-group <name> [--experiment-id <id>] [--resume]
```

Reads normalized Parquet, creates feature artifacts, and registers them in the catalog.

## align-labels

```powershell
python manage.py stage-three align-labels --branch <branch> --role <role> --label-policy explicit_only [--experiment-id <id>] [--resume]
```

Supported policies:

- `explicit_only`
- `any_attack_in_window`
- `majority_label`
- `last_event_label`
- `weak_allowed_with_confidence`

## build-sequences

```powershell
python manage.py stage-three build-sequences --branch <branch> [--role <role>] [--feature-group <name>] [--experiment-id <id>] [--resume]
```

Creates sequence/window artifacts for downstream DL models when the production path needs sequence modeling.

## build-model-ready

```powershell
python manage.py stage-three build-model-ready --experiment-id <id> --branch <branch> --target label_binary --preprocessing-profile tree_unscaled [--role <role>] [--feature-group <name>] [--include-sequences] [--resume]
```

Builds X/y/metadata/traceability, split index, and preprocessing metadata.

## run-quality-checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Checks schemas, empty artifacts, dtype consistency, class balance, label coverage, and model-ready contracts.

## run-leakage-checks

```powershell
python manage.py stage-three run-leakage-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Checks forbidden X columns, TEST leakage, preprocessing fit role, balancing policy, and traceability chain.

## trace-artifact

```powershell
python manage.py stage-three trace-artifact <model_ready_artifact_id>
python manage.py stage-three trace-artifact --experiment-id <id>
```

Resolves lineage:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset -> raw source
```

## final-report

```powershell
python manage.py stage-three final-report --experiment-id <id> [--branch <branch>]
```

Writes the RU/EN Task20 final report and prints the Stage Four readiness status.

# Stage Three Command Reference

Все команды запускаются из корня проекта `C:\Users\Public\PythonProjects\Proposal`.

## Help

```powershell
python manage.py stage-three --help
```

## validate-inputs

```powershell
python manage.py stage-three validate-inputs --branch <dns|host|network|hybrid> --role <TRAIN|VALIDATION|TEST>
```

Проверяет, можно ли использовать normalized artifacts из Stage Two как вход Stage Three.

## build-feature-catalog

```powershell
python manage.py stage-three build-feature-catalog [--feature-group <name>]
```

Валидирует machine-readable feature catalog и пишет отчеты Task05.

## probe-runtime-backend

```powershell
python manage.py stage-three probe-runtime-backend --backend <auto|cpu|gpu> [--profile balanced] [--skip-probe]
```

Резолвит runtime backend и memory guard settings.

## extract-features

```powershell
python manage.py stage-three extract-features --branch <branch> --role <role> --feature-group <name> [--experiment-id <id>] [--resume]
```

Читает normalized Parquet, создает feature artifacts и регистрирует их в catalog.

## align-labels

```powershell
python manage.py stage-three align-labels --branch <branch> --role <role> --label-policy explicit_only [--experiment-id <id>] [--resume]
```

Поддерживаемые policies:

- `explicit_only`
- `any_attack_in_window`
- `majority_label`
- `last_event_label`
- `weak_allowed_with_confidence`

## build-sequences

```powershell
python manage.py stage-three build-sequences --branch <branch> [--role <role>] [--feature-group <name>] [--experiment-id <id>] [--resume]
```

Создает sequence/window artifacts для downstream DL-моделей, если production path требует sequence branch.

## build-model-ready

```powershell
python manage.py stage-three build-model-ready --experiment-id <id> --branch <branch> --target label_binary --preprocessing-profile tree_unscaled [--role <role>] [--feature-group <name>] [--include-sequences] [--resume]
```

Собирает X/y/metadata/traceability, split index и preprocessing metadata.

## run-quality-checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Проверяет schema, empty artifacts, dtype consistency, class balance, label coverage и model-ready contracts.

## run-leakage-checks

```powershell
python manage.py stage-three run-leakage-checks --experiment-id <id> [--branch <branch>] [--role <role>] [--feature-group <name>]
```

Проверяет forbidden X columns, TEST leakage, preprocessing fit role, balancing policy и traceability chain.

## trace-artifact

```powershell
python manage.py stage-three trace-artifact <model_ready_artifact_id>
python manage.py stage-three trace-artifact --experiment-id <id>
```

Восстанавливает lineage:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset -> raw source
```

## final-report

```powershell
python manage.py stage-three final-report --experiment-id <id> [--branch <branch>]
```

Пишет RU/EN final report Task20 и выводит Stage Four readiness status.

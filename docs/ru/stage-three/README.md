# Stage Three

Stage Three преобразует результаты Stage Two из normalized Parquet в split-safe, leakage-safe и traceable model-ready artifacts для Stage Four.

Основная линия данных:

```text
raw -> normalized -> features -> model-ready -> training/evaluation
```

Stage Three закрывает только участок:

```text
normalized -> features -> model-ready
```

Обучение RF/XGBoost/CNN/LSTM, подбор гиперпараметров, threshold tuning, SHAP/XAI и итоговая экспериментальная оценка относятся к Stage Four.

## Документы

- [usage_guide.md](usage_guide.md) - порядок запуска Stage Three.
- [stage_three_commands.md](stage_three_commands.md) - справочник CLI-команд.
- [performance_tuning.md](performance_tuning.md) - runtime-профиль, RAM/GPU policy и безопасные настройки производительности.

## Минимальный DNS MVP path

1. Проверить готовность Stage Two для DNS TRAIN/VALIDATION/TEST.
2. Собрать и проверить feature catalog.
3. Извлечь DNS feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`.
4. Собрать `tree_unscaled` model-ready artifacts для `label_binary`.
5. При необходимости построить воспроизводимый DNS supervised 70/30 split через `rebalance-dns-supervised`.
6. Запустить quality checks.
7. Запустить leakage/traceability checks.
8. Сгенерировать final report.
9. Переходить к Stage Four только если final report показывает `READY_FOR_STAGE_FOUR`.

## Production path

После DNS MVP расширить Stage Three на Host/Network/Hybrid:

- добавить и прогнать Host/Network feature groups;
- включить sequence artifacts, если нужны CNN/LSTM/LSTM-like модели;
- использовать отдельные preprocessing profiles для tree/DL/linear моделей;
- прогнать quality/leakage/traceability checks для каждого production `experiment_id`;
- не смешивать TRAIN, VALIDATION и TEST;
- не fit-ить imputer/scaler/encoder на VALIDATION или TEST.

## Итоговый отчет

Команда:

```powershell
python manage.py stage-three final-report --experiment-id <id>
```

Отчеты пишутся в:

- `C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task20-stage-three-final-report-and-documentation.md`
- `C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task20-stage-three-final-report-and-documentation.md`

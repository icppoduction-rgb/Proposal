# Фактическое состояние репозитория, QA и gaps

Документ объединяет `repository_qa_section_3_8.md`, QA-блоки из `project_proposal_analysis.md` и ограничения из `functional_project_cheatsheet.md`. Его задача — отделить реализованное состояние репозитория от proposal-level планов.

## Scope анализа

Последняя repo-wide сверка: 2026-07-08. Подробный текущий срез entrypoints, CLI, Stage One/Two/Three, storage и тестов вынесен в [repository_analysis.md](repository_analysis.md).

Исходный QA документ фиксировал просмотр репозитория (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, конфиги). Ключевой вывод сохраняется:

> В текущем репозитории подтверждены этапы подготовки датасетов, Stage Two normalization и Stage Three feature/model-ready preparation. Обучение и оценка моделей остаются Stage Four.

## Что подтверждено текущей реализацией

| Область | Подтверждено |
| --- | --- |
| Stage One dataset preparation | Сканирование датасетов, назначение ролей, фильтрация host, сортировка по форматам, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS и Host обрабатываются отдельными ветками. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 в старом QA, 361670 total files по актуальной analysis-dataset сводке с 64 buckets. |
| Stage Two normalization | Реализованные CLI routes покрывают storage bootstrap, catalog ingestion, parser registry seed, parser coverage, mark-ready, normalization точного bucket, benchmark runs, splitting больших line-based files, DuckDB checks, leakage checks и traceability. |
| Stage Three feature/model-ready preparation | Реализован CLI `python manage.py stage-three ...` для readiness gate, feature catalog, runtime backend probe, feature extraction, label alignment, sequence build, model-ready build, quality checks, leakage/traceability checks и final report. |
| Stage Three reports | Task01-Task20 reports пишутся в `PATH_DATA_STORAGE/reports/{ru,en}/stage-three`; `final-report` явно сообщает `READY_FOR_STAGE_FOUR` или `NOT_READY_FOR_STAGE_FOUR`. |
| Current docs | Stage One/Stage Two/Stage Three architecture, normalization, parser strategy, labels, leakage, performance controls и traceability задокументированы в `analysis-dataset/`, `normalization/`, `stage-three/`, `code-documentation/`. |

## Что является proposal/планом, а не подтвержденной реализацией

| Область | Proposal-level утверждение | Gap |
| --- | --- | --- |
| Physical resampling strategy | SMOTE/undersampling как production default. | Stage Three поддерживает class balance reporting и TRAIN-only balancing constraints; SMOTE не должен быть default до отдельной проверки. |
| Random Forest / XGBoost | Baseline classifiers. | Параметры, training code и tuning не зафиксированы. |
| CNN | Deep learning branch for local feature patterns. | Архитектура не указана. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Stage Three может готовить sequence artifacts; модель LSTM, training config и evaluation остаются Stage Four. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Формула/веса/threshold не заданы. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны и не реализованы. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | Значение `k`, statistical tests, seeds и reports не зафиксированы. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware, Python/lib versions для ML stack не указаны; `requirements.txt` содержит только `python-dotenv` и `rich` без версий. |

## Текущие замечания по реализации

Сверено с кодом 2026-07-08:

- Stage Two routing находится в `scripts/stage_two/cli.py`; `config.manage_commands` является старым печатным списком команд и не полон для текущего Stage Two.
- `python manage.py stage-two --help` в текущем состоянии попадает в fallback и не должен использоваться как source of truth по командам.
- `normalize-format` и `benchmark-normalization` перед запуском применяют resource profiles и format-specific runtime policy. `normalize-all` получает общие runtime options, но не применяет per-format policy на уровне CLI route.
- Реализованные quality gates: parser reports, post-run validation для `normalize-format`, DuckDB checks, leakage checks и traceability lookup. Это проверки вокруг normalized/features/model-ready artifacts, а не полный ML experiment pipeline.
- Репозиторий подтверждает Stage Three CLI для feature extraction, DNS supervised rebalance, model-ready build, checks и final report. RF/XGBoost/CNN/LSTM training, SHAP analysis и evaluation reports остаются не реализованными в Stage Four.

## QA по разделам proposal 3.3-3.8

### Dataset Selection

| Вопрос | Ответ |
| --- | --- |
| Какие датасеты использовались? | DNS и Host datasets перечислены в [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md). |
| Есть ли total samples / class split / feature count? | Для большинства источников нет подтвержденных чисел. Для `CIC-Bell-DNS-2021` указано около 1,000,000 доменов и около 99% benign как утверждение документации. |
| Network и Host — отдельные датасеты? | Да, отдельные datasets и отдельные pipelines. |
| Host features симулировались из network? | В коде такой реализации не найдено; в proposal это только возможная feature-level simulation при отсутствии paired данных. |

### Data Preprocessing

| Вопрос | Ответ |
| --- | --- |
| Missing values | Реализованы Stage Three preprocessing utilities и reports; production readiness зависит от конкретного `experiment_id` и финальных checks. |
| Normalization/scaling | Scaling profiles и preprocessing metadata реализованы как Stage Three preparation layer. |
| Categorical encoding | Реализованы Stage Three encoding utilities; TEST не используется для fit. |
| Train/test split | Числовой split не задан; есть role-based strategy и плановая stratified k-fold CV. |

### Class Imbalance

Stage Three формирует class balance reports и class-weight metadata; physical resampling разрешается только для TRAIN и не является default для MVP DNS path.

### Model Architecture

| Модель | Состояние |
| --- | --- |
| Random Forest | Proposal-level; параметры/tuning не указаны. |
| XGBoost | Proposal-level; параметры/tuning не указаны. |
| CNN | Proposal-level; архитектура не указана. |
| LSTM | Proposal-level; есть только идея sequence-level binary classification. |

### Sequence Construction

| Вопрос | Состояние |
| --- | --- |
| Sequence length | Stage Three содержит sequence/window builder; production policy должна фиксироваться в experiment metadata. |
| Window step / overlap | Должны быть заданы в Stage Three sequence policy перед Stage Four training. |
| Multi-modal time alignment | Hybrid alignment остается production expansion area. |
| Labels for sequence windows | Stage Three поддерживает label policies; конкретная политика должна быть зафиксирована для experiment_id. |

### Decision Fusion

Proposal говорит о **late fusion** через агрегацию вероятностей classification и sequence components. Веса, формула и threshold policy не указаны.

### SHAP

Упоминается SHAP-based feature attribution. Не указано:

- TreeSHAP для RF/XGBoost;
- DeepSHAP для CNN/LSTM;
- KernelSHAP fallback;
- способ explainability для sequence windows.

### Experimental Environment

| Параметр | Состояние |
| --- | --- |
| Number of CV folds | Не указан. |
| Statistical tests | Не указаны. |
| Hardware | Не указан. |
| Software versions | ML stack не зафиксирован. |
| Random seed | Не указан. |

## Риски и рекомендации

| Риск | Где возникает | Последствие | Рекомендация |
| --- | --- | --- | --- |
| Host/network dataset incompatibility | Dataset strategy / hybrid architecture. | Нельзя доказать raw-level correlation. | Использовать feature-level integration, явно документировать assumptions. |
| TEST leakage | Feature extraction / model-ready artifacts. | Завышенная оценка качества. | Запретить TEST для training, fit preprocessing, feature selection, threshold tuning. |
| Label leakage | Filename/scenario/path fields. | Модель учит источник, а не поведение. | Исключать label/source/path/scenario fields из X. |
| Weak labels | Filename, IDS alert, scenario metadata. | Неверная supervised target разметка. | Использовать `label_status`, confidence и mapping rules. |
| Missing timestamps | TXT/trace/binary sources. | Неверные temporal features. | Использовать `timestamp=null`, `timestamp_type=missing` или event order; не подставлять current time. |
| Large files | PCAP, BSON, JSON, netflow, txt traces. | Memory/performance failures. | Streaming parsers, batch writes, DuckDB/Parquet checks. |
| Schema drift | Mixed CSV/JSON/log schemas. | Broken normalization/features. | Schema-aware parsers и per-format quality reports. |
| Explainability over proxy fields | SHAP / model-ready X. | Объяснения будут misleading. | Leakage checks перед SHAP, separate audit fields. |

## Follow-up tasks

1. Для каждого `experiment_id` прогонять `stage-three final-report` и не переходить в Stage Four без `READY_FOR_STAGE_FOUR`.
2. Расширить production Stage Three path на Host/Network/Hybrid feature groups после DNS MVP.
3. Зафиксировать production sequence window policy: length, step, overlap, label assignment, time alignment.
4. Добавить model configs для RF/XGBoost/CNN/LSTM в Stage Four.
5. Описать late fusion formula и threshold policy.
6. Выбрать SHAP variants по model family.
7. Добавить experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
8. Добавить Stage Four training/evaluation reports.

## Связанные документы

- [project_overview_and_research_context.md](project_overview_and_research_context.md)
- [repository_analysis.md](repository_analysis.md)
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](analysis-dataset/README.md)
- [normalization/README.md](normalization/README.md)
- [stage-three/README.md](stage-three/README.md)
- [code-documentation/README.md](code-documentation/README.md)

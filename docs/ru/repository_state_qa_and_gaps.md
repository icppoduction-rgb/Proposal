# Фактическое состояние репозитория, QA и gaps

Документ объединяет `repository_qa_section_3_8.md`, QA-блоки из `project_proposal_analysis.md` и ограничения из `functional_project_cheatsheet.md`. Его задача — отделить реализованное состояние репозитория от proposal-level планов.

## Scope анализа

Исходный QA документ фиксировал просмотр репозитория (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, конфиги). Ключевой вывод сохраняется:

> В текущем репозитории подтвержден этап подготовки датасетов, а не обучение/оценка моделей.

## Что подтверждено текущей реализацией

| Область | Подтверждено |
| --- | --- |
| Stage One dataset preparation | Сканирование датасетов, назначение ролей, фильтрация host, сортировка по форматам, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS и Host обрабатываются отдельными ветками. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 в старом QA, 361675 total files по актуальной analysis-dataset сводке с 66 buckets. |
| Current docs | Stage One/Stage Two architecture, normalization, parser strategy, labels, leakage и traceability задокументированы в `analysis-dataset/`, `normalization/`, `code-documentation/`. |

## Что является proposal/планом, а не подтвержденной реализацией

| Область | Proposal-level утверждение | Gap |
| --- | --- | --- |
| ML preprocessing | Missing value handling, scaling, categorical encoding. | В коде не подтверждены `MinMaxScaler`, `StandardScaler`, encoders или preprocessing fit pipeline. |
| Class imbalance | SMOTE/undersampling/class weights. | Реализация не найдена. |
| Random Forest / XGBoost | Baseline classifiers. | Параметры, training code и tuning не зафиксированы. |
| CNN | Deep learning branch for local feature patterns. | Архитектура не указана. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Sequence builder, step/overlap, alignment и model config не реализованы. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Формула/веса/threshold не заданы. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны и не реализованы. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | Значение `k`, statistical tests, seeds и reports не зафиксированы. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware, Python/lib versions для ML stack не указаны; `requirements.txt` содержит только `python-dotenv` и `rich` без версий. |

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
| Missing values | Реализация обработки model-feature пропусков не подтверждена. |
| Normalization/scaling | Не найдено. |
| Categorical encoding | Не найдено. |
| Train/test split | Числовой split не задан; есть role-based strategy и плановая stratified k-fold CV. |

### Class Imbalance

Методы SMOTE, undersampling, class weights или аналогичные механизмы не подтверждены кодом.

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
| Sequence length | Proposal указывает 50-100 событий. |
| Window step / overlap | Не задано. |
| Multi-modal time alignment | Явный алгоритм не найден. |
| Labels for sequence windows | План: label based on exfiltration activity within window; implementation не подтверждена. |

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

1. Зафиксировать `feature_catalog.yml/json` как machine-readable contract.
2. Реализовать Stage Two feature extraction layers по [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md).
3. Добавить preprocessing contracts: missing values, categorical encoding, scaling, fit/transform separation.
4. Добавить model configs для RF/XGBoost/CNN/LSTM.
5. Описать sequence window policy: length, step, overlap, label assignment, time alignment.
6. Описать late fusion formula и threshold policy.
7. Выбрать SHAP variants по model family.
8. Добавить experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
9. Расширить data quality reports: class balance, label coverage, timestamp coverage, schema drift, leakage.

## Связанные документы

- [project_overview_and_research_context.md](project_overview_and_research_context.md)
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](analysis-dataset/README.md)
- [normalization/README.md](normalization/README.md)
- [code-documentation/README.md](code-documentation/README.md)

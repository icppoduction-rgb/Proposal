# Индекс ключевой проектной документации

Этот индекс заменяет набор разрозненных документов верхнего уровня и показывает, куда перенесена ключевая информация по proposal, стратегиям датасетов, feature engineering и фактическому состоянию репозитория.

## Итоговая структура

| Документ | Назначение |
| --- | --- |
| [project_overview_and_research_context.md](project_overview_and_research_context.md) | Research context, proposal-level архитектура, вопросы, цели, methodology, scope, план и ограничения. |
| [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) | Единая стратегия DNS и Host датасетов с явным разделением `TRAIN` / `VALIDATION` / `TEST`. |
| [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) | Карта feature extraction, каталог групп признаков, schema requirements, leakage exclusions и приоритеты реализации. |
| [stage-three/README.md](stage-three/README.md) | Stage Three feature/model-ready preparation: usage guide, commands, performance tuning, MVP DNS path и production path. |
| [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) | Что подтверждено текущим кодом, что остается proposal/планом, QA по разделам 3.3-3.8, gaps и follow-up. |

## Объединенные старые документы

| Старый документ | Куда перенесено содержание |
| --- | --- |
| `project_proposal_analysis.md` | `project_overview_and_research_context.md`, `repository_state_qa_and_gaps.md`. |
| `functional_project_cheatsheet.md` | `project_overview_and_research_context.md`, `dataset_strategy_dns_host.md`, `feature_extraction_and_catalogue.md`. |
| `dns_dataset_strategy.md` | `dataset_strategy_dns_host.md`. |
| `host_datasets_analysis.md` | `dataset_strategy_dns_host.md`, `repository_state_qa_and_gaps.md`. |
| `dataset_feature_extraction_map.md` | `feature_extraction_and_catalogue.md`, `dataset_strategy_dns_host.md`. |
| `feature_catalogue_full.md` | `feature_extraction_and_catalogue.md`. |
| `repository_qa_section_3_8.md` | `repository_state_qa_and_gaps.md`. |

## Связанные актуальные разделы

- [analysis-dataset/README.md](analysis-dataset/README.md) — фактический Stage One анализ bucket/formats/readiness.
- [normalization/README.md](normalization/README.md) — Stage Two normalization guide.
- [stage-three/README.md](stage-three/README.md) — Stage Three feature extraction, preprocessing и model-ready guide.
- [code-documentation/README.md](code-documentation/README.md) — архитектура кода, CLI, Stage One/Stage Two, DB и parser strategy.

## Правила чтения

1. Для research proposal читать сначала [project_overview_and_research_context.md](project_overview_and_research_context.md).
2. Для выбора датасетов читать [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md).
3. Для реализации feature engineering читать [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md).
4. Для запуска Stage Three читать [stage-three/usage_guide.md](stage-three/usage_guide.md) и [stage-three/stage_three_commands.md](stage-three/stage_three_commands.md).
5. Для сверки с текущим кодом читать [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md).

## Архитектурные инварианты

- `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
- `TEST` не используется для training, fit preprocessing, feature selection или threshold tuning.
- DNS и Host логика разделены; объединение выполняется только на уровне normalized events, windows, features и traceability.
- Labels являются target/audit fields, а не input features.
- Отсутствие label не означает benign.
- Proposal-level идеи не считаются реализованными, пока они не подтверждены кодом, артефактами или Stage Two/Stage Three документацией.
- Stage Three artifacts считаются готовыми для Stage Four только после `final-report` со статусом `READY_FOR_STAGE_FOUR`.

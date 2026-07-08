# Storage

Документ описывает фактическое состояние `C:\Users\Public\PythonProjects\storage` на 2026-07-08 и его роль в пайплайне Proposal.

Связанный repo-wide анализ кода и CLI: `docs/ru/repository_analysis.md` и `docs/en/repository_analysis.md`.

## Назначение

`storage` является рабочим корнем для сгенерированных артефактов проекта, а не хранилищем исходных raw datasets:

- Parquet-слои `normalized`, `features`, `model_ready`;
- DuckDB-база для аналитических проверок;
- отчеты Stage One, Stage Two и Stage Three на русском и английском;
- временные данные ingestion, parser runs, normalization и Stage Three;
- runtime-конфигурация, схемы, логи, backup/quarantine зоны;
- инфраструктурные данные PostgreSQL и pgAdmin, если они используются локально.

Raw datasets должны оставаться отдельной зоной ответственности. `storage` хранит generated artifacts и metadata outputs; перенос или удаление файлов из `parquet` может сломать ссылки в PostgreSQL catalog и traceability.

## Верхнеуровневая структура

```text
C:\Users\Public\PythonProjects\storage\
  backups\
  config\
  duckdb\
  logs\
  parquet\
  pgadmin\
  postgres\
  quarantine\
  reports\
  schemas\
  temp_data\
```

## Основные слои данных

### `parquet/normalized`

Слой нормализованных событий Stage Two.

Найденные ветки:

- `dns`
- `host`
- `hybrid`
- `network`

Документированный шаблон пути:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Назначение: единый normalized event format после парсеров DNS/Host/Network/Hybrid. Этот слой является входом для Stage Three feature extraction.

### `parquet/features`

Слой feature artifacts Stage Three.

Найденные группы:

- `dns`
- `dns_entropy`
- `dns_features`
- `dns_lexical`
- `dns_temporal`
- `host`
- `host_eventlog_features`
- `host_metrics_features`
- `host_syscall`
- `host_syscall_features`
- `hybrid`
- `hybrid_features`
- `network`
- `network_flow_features`
- `sequence_features`

Документированный шаблон пути:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Назначение: признаки, извлеченные из normalized artifacts. Эти данные не должны смешивать `TRAIN`, `VALIDATION` и `TEST`.

### `parquet/model_ready`

Слой model-ready artifacts.

Найденные директории:

- `dns`
- `dns_rebalanced_70_30_v1`
- `exp001`
- `host`
- `hybrid`
- `labels`
- `network`
- `preprocessing`
- `sequences`
- `split_index`
- `tabular`

Документированный шаблон пути:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

Назначение: финальные таблицы, labels, split index, preprocessing artifacts и sequence artifacts для обучения и оценки моделей.

## DuckDB

Найдена локальная база:

```text
duckdb/proposal_analytics.duckdb
```

Размер на момент проверки: около `274432` байт.

Назначение: локальная аналитика поверх Parquet, quality checks и SQL-представления. DuckDB не является source of truth для catalog metadata; source of truth для metadata остается PostgreSQL catalog, а для больших таблиц - Parquet.

## Reports

Корень отчетов:

```text
reports/
  en/
  ru/
```

В `reports/ru` найдены группы:

- `leakage`
- `normalization`
- `parser`
- `quality`
- `schema_mismatch`
- `stage-one`
- `stage-two`
- `stage-three`

Типовые группы отчетов:

| Группа | Назначение |
| --- | --- |
| `stage-one` | анализ, сортировка и фильтрация исходных DNS/Host datasets |
| `stage-two` | normalization, parser runs, readiness, status reports |
| `stage-three` | feature extraction, model-ready builder, quality/leakage checks |
| `quality` | data quality и DuckDB analytics reports |
| `leakage` | проверки утечек между split/roles |
| `schema_mismatch` | расхождения схем |
| `parser` | coverage/status reports парсеров |
| `normalization` | отчеты нормализации |

В storage присутствует большое число `parser_run_*.json`, `.md`-отчетов и status artifacts. Их следует рассматривать как audit trail выполнения пайплайна, а не как конфигурацию.

## Temp Data

`temp_data` содержит временные и промежуточные файлы:

- Stage One JSON inventories и summaries;
- parser/normalization scratch data;
- Stage Two cleanup/orphan snapshots;
- Stage Three sample/runtime artifacts.

Данные из `temp_data` не должны использоваться как authoritative input для обучения без явной проверки происхождения. Для production-like воспроизводимости опирайтесь на зарегистрированные Parquet artifacts и catalog metadata.

## Config, Schemas, Logs, Backups

| Путь | Назначение |
| --- | --- |
| `config/` | runtime-конфигурация storage, например внешние mapping rules |
| `schemas/` | runtime copies/exports схем normalized/features/model-ready |
| `logs/` | runtime logs пайплайна |
| `backups/` | резервные копии metadata/config/catalog artifacts |
| `quarantine/` | зона для изолированных проблемных артефактов |
| `postgres/` | локальные данные PostgreSQL, если storage используется как volume root |
| `pgadmin/` | локальные данные pgAdmin, если используется локальный UI |

## Масштаб хранилища

Агрегированный срез по расширениям на момент проверки:

| Расширение | Количество |
| --- | ---: |
| `.json` | 1 448 136 |
| `.parquet` | 443 787 |
| без расширения | 1 529 |
| `.md` | 481 |
| `.log` | 19 |
| `.map` | 5 |
| `.conf` | 4 |
| `.init` | 3 |
| `.csv` | 2 |
| `.duckdb` | 1 |
| `.opts` | 1 |
| `.pid` | 1 |
| `.db` | 1 |

Из-за масштаба storage нецелесообразно документировать каждый файл вручную. Для поддержки нужно документировать контракты путей, роли директорий, правила очистки и команды проверки.

## Эксплуатационные правила

1. Не удалять `parquet/normalized`, `parquet/features` и `parquet/model_ready` вручную без синхронного обновления catalog metadata.
2. Не смешивать `TRAIN`, `VALIDATION` и `TEST`; `TEST` должен оставаться evaluation-only.
3. Не считать `temp_data` источником истины.
4. Не хранить секреты в `reports`, `logs`, `config` или Markdown-документации.
5. Перед очисткой больших директорий делать inventory: количество файлов, размер, дата последнего изменения, связь с parser/model-ready reports.
6. Для воспроизводимых проверок использовать report artifacts и catalog paths, а не случайные найденные файлы.

## Рекомендуемые проверки

Из корня репозитория:

```powershell
# Проверить наличие основных storage-директорий
Get-ChildItem C:\Users\Public\PythonProjects\storage -Directory

# Посмотреть распределение файлов по расширениям
Get-ChildItem C:\Users\Public\PythonProjects\storage -Recurse -File -ErrorAction SilentlyContinue |
  Group-Object Extension |
  Sort-Object Count -Descending |
  Select-Object Count, Name

# Проверить верхние Parquet-слои
Get-ChildItem C:\Users\Public\PythonProjects\storage\parquet -Directory

# Найти Stage Three model-ready отчеты
Get-ChildItem C:\Users\Public\PythonProjects\storage\reports\ru\stage-three -File
```

## Связанные документы

- `docs/ru/normalization/storage_architecture.md`
- `docs/ru/code-documentation/storage_architecture.md`
- `docs/ru/normalization/parquet_duckdb_artifacts.md`
- `docs/ru/stage-three/usage_guide.md`
- `docs/ru/stage-three/stage_three_commands.md`

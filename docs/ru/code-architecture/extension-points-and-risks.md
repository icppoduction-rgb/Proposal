# Точки расширения, ограничения и технический долг

## Точки расширения Stage One

| Что расширять | Где менять | Требования |
|---|---|---|
| Новый top-level handler service | `scripts/handlers/router_handler.py` | Добавить route и help/update docs. |
| Новый action для DNS анализа | `scripts/handlers/dns_analyze/router_dns.py`, новый `analyze_dns_*_dataset_handler.py` | Handler должен читать `sort-path-dns-file.json` и возвращать result, совместимый с `run_action.py`. |
| Новый action для host анализа | `scripts/handlers/host_analyze/router_host.py`, новый `analyze_host_*_dataset_handler.py` | Handler должен читать `sort-path-host-file.json` и сохранять summary/report. |
| Новая логика host-фильтрации | `filter_host_dataset_handler.py` | Сохранять контракт `filter_dataset-host-path-file.json` и `filter_dataset-host-file.json`. |
| Новый format bucket sorter | `sort_dns_dataset_handler.py` или `sort_host_dataset_handler.py` | Bucket name должен совпадать с ожиданиями save/analyze handlers и Stage Two scanner. |

## Точки расширения Stage Two parser pipeline

| Что расширять | Где менять | Минимальный контракт |
|---|---|---|
| Новый parser class | `scripts/stage_two/parsers/*` | Наследовать существующие parser contracts, возвращать `ParseResult` с normalized events/counters. |
| Новая parser registry запись | seed data, используемые `parser_registry/seed.py` | Указать parser name/version/module/class, branch, source_format, role, schema name/version, `is_active`. |
| Новая normalized schema | `schemas/normalized/*.json`, `normalization/schema_contracts.py` при необходимости | Зарегистрировать в `schema_versions`; parser registry должен ссылаться на нее. |
| Новая label rule | `label_mapping_rules` или config `label_mapping_rules.json` | Не смешивать роли; правило должно быть воспроизводимым. |
| Новые quality checks | `scripts/stage_two/quality/*` или `duckdb/service.py` | Записывать report в `data_quality_reports`. |
| Feature/model-ready stage | `features/*`, `model_ready/*` | Регистрировать catalog artifacts и сохранять traceability к normalized/raw. |

## Правила добавления нового Stage Two parser

1. Изучить Stage One analysis summary для нужного role/format bucket.
2. Убедиться, что `catalog-ingest` корректно определяет `branch`, `role`, `source_format` для файлов.
3. Реализовать parser class и покрыть edge cases: пустой файл, битая строка, неизвестная кодировка/формат, отсутствующая label/timestamp информация.
4. Добавить или обновить schema contract и зарегистрировать его в `schema_versions` через seed.
5. Добавить parser registry entry. Не ставить `is_active=true`, пока parser class фактически не реализован и не проверен.
6. Проверить resolver: он должен выбирать parser только для поддерживаемого branch/source_format/role.
7. Проверить normalization на ограниченном `limit` и убедиться, что создаются `parser_runs`, `normalized_artifacts` и Parquet.
8. Запустить readiness/quality checks, если окружение доступно.

## Обнаруженные расхождения старой документации с кодом

| Расхождение | Фактическая реализация |
|---|---|
| Старые docs описывали только `handlers` module. | `router_script.py` также поддерживает `stage-two`. |
| Старые docs не описывали `scripts/db`. | DB слой является обязательной частью Stage Two. |
| Старые docs не описывали Stage Two CLI. | `scripts/stage_two/cli.py` содержит production-facing commands. |
| Старые docs не фиксировали `schema_versions` как обязательный шаг. | Seed теперь обязан регистрировать normalized schema metadata. |
| Старые docs не отделяли planned parsers от active parsers. | Planned/unsupported parser entries должны быть inactive. |
| Часть старых RU docs была в поврежденной кодировке. | Документация переписана в UTF-8. |

## Ограничения и риски текущей реализации

| Риск | Влияние | Практическое действие |
|---|---|---|
| `manage.py` использует `parse_known_args()`. | Лишние CLI аргументы игнорируются. | Для строгого CI нужен явный parse/validation layer. |
| Unknown commands печатают help без явного failure. | Автоматизация может считать ошибочную команду успешной. | Возвращать non-zero exit code при неизвестной команде. |
| `PATH_FILTER_LOG` в `config.py` может быть tuple из-за trailing comma. | Потенциальная ошибка path handling в host filter. | Исправить config и добавить regression test. |
| Stage Two не имеет публичной команды mark-ready. | `normalize-*` может обработать 0 файлов после ingestion. | Добавить явный review/mark-ready workflow. |
| Feature/model-ready pipeline неполный как CLI. | Traceability chain до model-ready доступна только при использовании APIs/dry-run. | Реализовать отдельные Stage Two задачи для feature/model-ready сборки. |
| Host netflow/wls parser entries inactive. | Эти форматы не нормализуются Stage Two. | Реализовать parser или оставить documented inactive. |
| Stage One temp JSON не валидируется общей schema. | Разные handlers могут расходиться в полях summary. | Добавить JSON Schema для temporary artifacts, если они станут stable contract. |
| `readiness_check` может hash-ить catalog files. | На полном корпусе проверка может быть дорогой. | Добавить sampling/incremental режим при необходимости. |
| Stage One и Stage Two ingestion независимы. | Изменения в sorted tree не автоматически отражаются в catalog. | После изменения файлов запускать `catalog-ingest`. |

## Что не следует делать

- Не объявлять parser active, если class отсутствует или не поддерживает формат.
- Не создавать normalized/features/model-ready файлы без catalog registration.
- Не использовать TEST для fitted preprocessing или выбора параметров.
- Не полагаться на Stage One summary как на источник truth для Stage Two catalog; Stage Two catalog строится собственным scanner-ом.

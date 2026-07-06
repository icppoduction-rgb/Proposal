# Риски, ограничения и technical debt

## Известные ограничения

| Риск | Где возникает | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Fallback Host role в TEST | `HostDatasetHandler._detect_role` | файлы без role token попадут в TEST | проверить `host-path-file.json` | требовать явные role directories, добавить strict mode |
| Жестко заданный Host filter whitelist | `HostDatasetFilterHandler` | новые datasets/formats исключаются | причины в filter log | вынести rules в config с тестами |
| Статусы Stage One могут отставать от Stage Two parsers | analysis docs vs parser registry | формат помечен `NEEDS_CUSTOM_PARSER`, хотя parser уже есть | `parser-coverage` | обновлять analysis docs после parser work |
| Stage Four отсутствует | model training/evaluation layer | нельзя обучать/оценивать модели штатной командой проекта | ревью CLI routes и `docs/stage-three` final report | добавить отдельный Stage Four CLI после `READY_FOR_STAGE_FOUR` |
| Production Host/Network/Hybrid expansion неполный | Stage Three MVP path начинается с DNS | DNS MVP может быть готов раньше полного hybrid scope | `stage-three final-report`, feature group coverage | расширять Stage Three по branch/feature_group с `--resume` и checks |

## Gaps в parser layer

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Смешанные CSV schemas | DNS/Host CSV | failures при парсинге строк, partial artifacts | parser reports, `PARTIAL_SUCCESS` | schema-specific parsing, per-file schema hints |
| Смешанные JSON schemas | Host TRAIN/TEST JSON | failed rows или слабая нормализация | parser error samples | schema-aware dispatch и JSON flatten tests |
| Неоднозначность WLS/NetFlow | registry для `wls_day` использует `HostNetflowParser` | semantic mismatch, если WLS является JSON-lines | parser coverage + sample parse | выделить WLS parser или обновить registry |
| Производительность PCAP/PCAPNG | packet parser | медленная обработка, pressure на память/диск | runtime metrics, parser reports | packet sampling, `dns-only`, chunked streaming |
| Сложность BSON | sandbox BSON | descriptor/event mismatch | parser warnings | descriptor state tests, bounded raw previews |

## Риски leakage

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Labels попали в X | feature/model-ready build | model напрямую учит target | `run-leakage-checks` | `validate_x_columns`, strict excluded list |
| Source identity в X | source paths/event ids | model запоминает dataset/file | проверка forbidden columns | хранить traceability только в catalog/audit |
| TEST используется для fit/tuning | preprocessing/model code | невалидная evaluation | preprocessing fit check, review | enforcing TRAIN-only fit и CI checks |
| Filename label inference для TEST | изменения label resolver | загрязнение evaluation | unit tests | сохранять `label_hints_allowed(TEST)=False` |

## Риски labels

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Отсутствующий label трактуется как benign | downstream feature/model code | false negatives, contaminated labels | label distribution checks | сохранять `unlabeled` и фильтровать supervised samples |
| Weak labels используются как ground truth | IDS/scenario/filename | noisy training labels | проверять `label_status` | train/evaluate by label confidence/source |
| Conflicting labels игнорируются | resolver candidates | неверный target | counts по `conflicting_label` | блокировать или вручную разруливать conflicts |

## Риски timestamp

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Missing timestamp заменен текущим временем | parser implementation | invalid temporal features | review `timestamp_type`, tests | использовать `timestamp=null`, `timestamp_type=missing/event_order` |
| Relative time трактуется как absolute | syscall/BSON/logs | неверный ordering/windows | parser tests | сохранять `timestamp_type=relative` и `event_index` |
| Смешанный timezone parsing | logs/json/csv | смещенные windows | sample validation | нормализовать в UTC только известные absolute timestamps |

## Риски больших файлов

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Загрузка файла целиком | parsers/analyzers | исчерпание памяти | profiling, OOM | streaming readers, `parse_batches`, split-large-files |
| Слишком много Parquet parts | low max rows | filesystem overhead | artifact counts | настраивать `--max-output-part-rows` |
| Parallel workers на огромных файлах | `normalize-format --workers` | RAM/disk pressure | system monitoring | использовать workers=1, пока нет chunks |

## Schema drift

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Source schema изменилась | datasets | parser failures | `PARTIAL_SUCCESS`, schema mismatch | сохранять schema hints, обновлять parser tests |
| Normalized schema развивается | schema JSON + parsers | downstream mismatch | DuckDB required column checks | версионировать schemas и поддерживать migrations |
| Feature schema mismatch | feature artifacts | model-ready invalid | quality checks | валидировать feature contract до регистрации |

## Follow-up по technical debt

1. Добавить config-driven Host filter rules.
2. Добавить Stage Four CLI для training/evaluation только поверх `READY_FOR_STAGE_FOUR` artifacts.
3. Расширить Stage Three production path на Host/Network/Hybrid feature groups.
4. Добавить отдельный WLS parser, если текущий netflow mapping семантически недостаточен.
5. Уточнить schema-version lifecycle для feature/model-ready schemas в production migrations.
6. Добавить CI command для parser registry validation, Stage Three tests, leakage contract tests и docs link checks.

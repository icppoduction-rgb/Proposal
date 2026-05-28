# Отчёт: фильтрация Host-датасетов (этап 3)

## Краткое описание задачи
Реализован этап анализа и фильтрации Host-датасетов: из результатов первичного сканирования (`host-path-file.json`, `host-file.json`) отобраны только релевантные датасеты и файлы для `TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`.

## Какие файлы были добавлены или изменены
### Добавлены
- `scripts/handlers/filter_host_dataset_handler.py`
- `report/ru/host_dataset_filter_report.md`
- `report/en/host_dataset_filter_report.md`

### Изменены
- `manage.py`

## Какие JSON-файлы создаются
Файлы сохраняются в директорию `PATH_TEMP_DATA`:

- `filter-host-path-file.json`  
  Содержит пути к нужным Host-датасетам по ролям.
- `filter-host-file.json`  
  Содержит имена нужных файлов по ролям.

## Какие файлы были исключены
Исключение выполняется по причинам:

- датасет не соответствует роли из проектной стратегии (`dataset_not_allowed_for_role`);
- путь не относится к телеметрии/логам для `Maintainable Log Dataset` (`non_telemetry_path_for_maintainable_dataset`);
- нерелевантные расширения для обучения и feature engineering (например: `.pdf`, `.html`, `.rc`, `.ps1`, `.dmp`, `.webarchive`, `.res`, часть `.pcap`);
- служебные файлы macOS вида `._*` (`macos_resource_fork_file`).

### Сводка последнего запуска
- `kept_files_count`: `361646`
- `excluded_files_count`: `30438`

## Краткая логика фильтрации
1. Читаются `host-path-file.json` и `host-file.json` из `PATH_TEMP_DATA`.
2. Применяется строгая role-matrix датасетов из документации проекта:
   - `TRAIN`: `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset`
   - `VALIDATION`: `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets`
   - `TEST`: `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset`
   - `EXPERIMENTS`: `HDFS-Log-Dataset`
3. Для каждого датасета применяются dataset-aware правила по расширениям и пути:
   - сохраняются syscall/log/telemetry артефакты;
   - исключаются документация, скрипты окружения, бинарные и явно нерелевантные файлы.
4. Формируются и сохраняются:
   - `filter-host-path-file.json`
   - `filter-host-file.json`
5. Все исключения пишутся в `logs/filter.log`.

## Описание структуры логов
Файл: `logs/filter.log`  
Формат строки:

`timestamp | dataset_type=HOST | role=<ROLE> | dataset=<DATASET_NAME> | reason=<REASON> | path=<FULL_PATH>`

Лог содержит:
- путь исключённого файла;
- причину исключения;
- тип датасета (`HOST`);
- роль датасета.

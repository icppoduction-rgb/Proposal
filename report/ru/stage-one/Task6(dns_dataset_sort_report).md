# Отчёт: сортировка DNS-датасетов по форматам (этап 6)

## Описание задачи
Реализована сортировка DNS-датасетов по форматам файлов на основе входных JSON:
- `dns-file.json`
- `dns-path-file.json`

Файлы группируются по ролям (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`) и форматам в отдельной структуре внутри `PATH_DNS_DATASETS_FILTER`.

## Какие файлы были добавлены
- `scripts/handlers/sort_dns_dataset_handler.py`
- `report/ru/dns_dataset_sort_report.md`
- `report/en/dns_dataset_sort_report.md`

## Какие файлы были изменены
- `manage.py`

## Команда запуска
- `python manage.py dns dataset sort`

Дополнительно поддерживается alias-команда:
- `python manage.py dataset dns sort`

`manage.py` используется только как точка входа. Основная логика вынесена в `scripts/handlers/sort_dns_dataset_handler.py`.

## Описание структуры сортировки
Создаётся структура:

```text
PATH_DNS_DATASETS_FILTER/
  TRAIN/
    csv/
    pcap/
    pcap.csv/
  TEST/
    csv/
  VALIDATION/
    pcap/
    txt/
  EXPERIMENTS/
```

## Поддерживаемые форматы
Поддерживаются форматы:
- `csv`
- `pcap`
- `pcap.csv`
- `txt`

Если встречается нестандартный формат, используется fallback по расширению файла.

## Логика определения форматов
1. Если имя файла оканчивается на `.pcap.csv` -> группа `pcap.csv`.
2. Если имя файла оканчивается на `.pcap` -> группа `pcap`.
3. Если имя файла оканчивается на `.csv` -> группа `csv`.
4. Если имя файла оканчивается на `.txt` -> группа `txt`.
5. В остальных случаях используется `suffix` файла как имя группы.

## Безопасность и работа с исходными данными
- Исходные DNS-датасеты не изменяются.
- Файлы не перемещаются и не удаляются.
- Для размещения используется hardlink; при ошибке hardlink применяется безопасный fallback на `copy2`.
- При коллизии имён используется hash-суффикс, чтобы избежать перезаписи.

## Результат фактического запуска
Сводка сохранена в `PATH_TEMP_DATA/sort-dns-format-summary.json`.

Метрики последнего запуска:
- `created_links_count`: `0`
- `copied_files_count`: `0`
- `skipped_existing_count`: `35`
- `missing_source_count`: `0`
- `name_mismatch_count`: `0`

Это подтверждает идемпотентность: повторный запуск не дублирует и не перезаписывает уже отсортированные данные.

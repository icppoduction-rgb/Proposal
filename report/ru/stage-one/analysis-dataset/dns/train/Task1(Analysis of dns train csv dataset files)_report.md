# Отчёт по Task1: Analysis of dns train csv dataset files

## Описание задачи
Выполнен анализ `PATH_DNS_DATASETS_FILTER\TRAIN\csv` на основе `sort-path-dns-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_dns_train_csv_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-dns-train-csv-summary.json`
- `docs/ru/analysis-dataset/dns/train/csv.md`
- `docs/en/analysis-dataset/dns/train/csv.md`
- `docs/ru/analysis-dataset/dns/train/README.md`
- `docs/en/analysis-dataset/dns/train/README.md`
- `report/ru/stage-one/analysis-dataset/dns/train/Task1(Analysis of dns train csv dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/dns/train/Task1(Analysis of dns train csv dataset files)_report.md`

## Структура JSON
`sort-path-dns-file.json`: `role -> format -> list[path]`; bucket: `TRAIN.csv`.

## Логика анализа
Handler анализирует все CSV-файлы, читает ограниченное число строк на файл и фиксирует schema kind/class hint.

## Пример итогового JSON
```json
{
  "format": "csv",
  "role": "TRAIN",
  "scope": {
    "total_files_count": 8,
    "sampled_files_count": 8,
    "max_files_per_format": 30,
    "max_rows_per_file": 1000
  },
  "parsed_rows": 7996,
  "schema_kinds": {
    "dns_feature_table": 4,
    "domain_list": 3,
    "phishtank_url_feed": 1
  },
  "class_hints": {
    "benign": 2,
    "malware": 2,
    "phishing": 2,
    "spam": 2
  },
  "inconsistent_column_files": 4,
  "final_status": "PARTIALLY_SUPPORTED"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-dns-train-csv-summary.json`. Итоговый статус: `PARTIALLY_SUPPORTED`.

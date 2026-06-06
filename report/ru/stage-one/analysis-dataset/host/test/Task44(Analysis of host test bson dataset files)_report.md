# Отчёт по Task44: Analysis of host test bson dataset files

## Описание задачи
Выполнен анализ содержимого файлов `PATH_HOST_DATASETS_FILTER\TEST\bson` на основе путей из `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_bson_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-bson-summary.json`
- `docs/ru/analysis-dataset/host/test/bson.md`
- `docs/en/analysis-dataset/host/test/bson.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`

## Структура JSON
Источник `sort-path-host-file.json` имеет структуру `role -> format -> list[path]`. Для задачи использован bucket `TEST.bson`.

## Логика группировки путей
Handler читает только Host JSON, выбирает роль `TEST` и формат `bson`, сортирует пути, затем берёт равномерную выборку до 30 файлов. Для каждого файла читается не больше 2097152 байт и не больше 100 BSON-документов.

## Пример итогового JSON
```json
{
  "format": "bson",
  "role": "TEST",
  "scope": {
    "total_files_count": 9005,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_docs_per_file": 100,
    "max_bytes_per_file": 2097152,
    "total_sampled_bytes": 14878744
  },
  "parsed_document_count": 2325,
  "final_status": "NEEDS_CUSTOM_PARSER",
  "needs_custom_parser": true,
  "top_fields": [
    {
      "field": "I",
      "type": "int32",
      "observed_count": 2325,
      "example": "0"
    },
    {
      "field": "args",
      "type": "array",
      "observed_count": 2325,
      "example": "nested_array"
    },
    {
      "field": "flags_value.information_class.0",
      "type": "array",
      "observed_count": 2091,
      "example": "nested_array"
    },
    {
      "field": "flags_value.information_class.0.0",
      "type": "int32",
      "observed_count": 2091,
      "example": "0"
    },
    {
      "field": "flags_value.information_class.0.1",
      "type": "string",
      "observed_count": 2091,
      "example": "KeyValueBasicInformation"
    }
  ]
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-bson-summary.json`. Итоговый статус: `NEEDS_CUSTOM_PARSER`. Нужен отдельный BSON parser: `true`.

# JSON helper: `scripts.handlers.json_handler`

## Назначение

`JsonDataManager` является общим helper для чтения и записи JSON-файлов Stage One. Он используется handlers в `analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`.

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/json_handler/json_data.py` | Реальная реализация `JsonDataManager`. |
| `scripts/handlers/json_handler/json-data.py` | Thin wrapper/import для совместимости со старым именем файла. |

## API

| Метод | Вход | Выход | Поведение |
|---|---|---|---|
| `read(default=None)` | path, заданный в constructor | Python object из JSON или `default` | Возвращает `default`, если файл отсутствует. |
| `write(data)` | JSON-serializable object | `None` | Создает parent directory и пишет JSON в UTF-8. |

## Место в pipeline

`JsonDataManager` не содержит бизнес-логики. Он только обеспечивает единый способ работы с временными JSON-артефактами в `PATH_TEMP_DATA` и summary/report JSON, создаваемыми content-analysis handlers.

## Ограничения

- Helper не валидирует JSON Schema. Валидация структуры выполняется в конкретных handlers.
- Ошибки некорректного JSON не маскируются и пробрасываются вызывающему коду.

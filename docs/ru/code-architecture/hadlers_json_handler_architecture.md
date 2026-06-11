# Архитектура handlers: json_handler

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Место в общей цепочке](#3-место-в-общей-цепочке)
- [4. JsonDataManager](#4-jsondatamanager)
- [5. Цепочки вызовов](#5-цепочки-вызовов)
- [6. Контракт данных](#6-контракт-данных)
- [7. Ошибки и ограничения](#7-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/json_handler` содержит общий слой работы с JSON-файлами. Практически все service handlers используют `JsonDataManager` для чтения и записи промежуточных артефактов в `PATH_TEMP_DATA`.

Пакет не запускается напрямую через `manage.py`. Он является инфраструктурной зависимостью для других обработчиков.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `json_data.py` | Основная реализация `JsonDataManager`. |
| `json-data.py` | Совместимая обертка, реэкспортирует `JsonDataManager`. |
| `__init__.py` | Package marker. |

## 3. Место в общей цепочке

Типовой вызов:

```text
service handler
-> JsonDataManager(path)
-> read(default={}) | write(data) | update(data)
-> JSON-файл на диске
```

Примеры потребителей:

- `DNSDatasetHandler` пишет `dns-path-file.json`;
- `HostDatasetFilterHandler` читает `host-path-file.json`;
- `DNSDatasetSortHandler` пишет `sort-dns-format-summary.json`;
- content-analysis handlers пишут `analysis-*-summary.json`.

## 4. JsonDataManager

Файл:

- `scripts/handlers/json_handler/json_data.py`

### Методы

| Метод | Назначение |
|---|---|
| `__init__(file_path)` | Сохраняет путь к JSON-файлу как `Path`. |
| `ensure_directory()` | Создает родительскую директорию файла. |
| `exists()` | Проверяет, существует ли JSON-файл. |
| `create(initial_data=None, overwrite=False, indent=2)` | Создает JSON-файл, не перезаписывая существующий без `overwrite=True`. |
| `read(default=None)` | Читает JSON и возвращает dict. Если файла нет, возвращает `default` или `{}`. |
| `write(data, indent=2)` | Полностью перезаписывает JSON-файл словарем. |
| `update(new_data, indent=2)` | Читает текущий JSON, обновляет верхний уровень и записывает обратно. |

## 5. Цепочки вызовов

### Запись JSON

```text
handler method
-> JsonDataManager(output_path)
-> write(payload)
-> ensure_directory()
-> json.dump(payload, ensure_ascii=False, indent=2)
```

### Чтение JSON

```text
handler method
-> JsonDataManager(input_path)
-> read(default={})
-> file_path.open("r", encoding="utf-8")
-> json.load(...)
-> проверка isinstance(data, dict)
```

### Обновление JSON

```text
handler method
-> JsonDataManager(path).update(new_data)
-> read(default={})
-> current_data.update(new_data)
-> write(current_data)
```

## 6. Контракт данных

`JsonDataManager` ожидает, что верхний уровень JSON является объектом Python `dict`.

Корректный пример:

```json
{
  "TRAIN": [],
  "TEST": []
}
```

Некорректный пример:

```json
[
  "file1",
  "file2"
]
```

Если `read()` получает JSON-массив или другое значение верхнего уровня, метод выбрасывает `ValueError`.

## 7. Ошибки и ограничения

- `write()` принимает только `dict`; для других типов выбрасывает `TypeError`.
- `read()` не валидирует вложенную структуру, только верхний уровень.
- `update()` обновляет только верхний уровень словаря, без deep-merge.
- Атомарная запись через временный файл не используется. При сбое записи JSON может быть поврежден.
- `json-data.py` нужен только для совместимости с именем файла; основная реализация находится в `json_data.py`.

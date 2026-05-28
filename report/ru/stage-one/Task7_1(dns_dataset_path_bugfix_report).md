# Отчёт: исправление бага путей в dns-path-file.json

## Краткое описание
Исправлен баг в обработчике DNS-датасетов: файл `dns-path-file.json` содержал пути директорий вместо путей к конкретным файлам.

## Причина проблемы
В логике сборки `paths_by_role` в JSON добавлялся `current_path` (папка), а не путь `current_path / file_name`.

## Что исправлено
- Обновлён обработчик `DNSDatasetHandler`.
- Для каждого найденного файла теперь формируется и сохраняется полный путь к файлу.
- Формат `dns-file.json` не изменялся: в нём остаются только имена файлов.

## Изменённые файлы
- `scripts/handlers/dns_dataset_handler.py`
- `report/ru/dns_dataset_path_bugfix_report.md`
- `report/en/dns_dataset_path_bugfix_report.md`

## Как проверить
1. Запустить команду:
```bash
python manage.py dataset dns analyze
```
2. Открыть `PATH_TEMP_DATA/dns-path-file.json`.
3. Убедиться, что значения в ролях содержат полные пути до файлов (например, `...\\CSV_benign.csv`, `...\\benign.pcap`), а не только директории.

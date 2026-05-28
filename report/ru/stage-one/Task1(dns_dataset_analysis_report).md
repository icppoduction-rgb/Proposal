# Отчёт: анализ DNS-датасетов (этап 1)

## Краткое описание выполненной задачи
Реализован первый этап анализа DNS-датасетов: поиск директорий с файлами, определение ролей (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`), сбор путей датасетов и имён файлов, сохранение результата в JSON.

## Какие файлы были добавлены или изменены
### Добавлены
- `scripts/json_data.py`
- `scripts/json-data.py`
- `scripts/handlers/dns_dataset_handler.py`
- `report/ru/dns_dataset_analysis_report.md`
- `report/en/dns_dataset_analysis_report.md`

### Изменены
- `manage.py`

## Какие команды были добавлены в manage.py
Добавлена команда запуска анализа DNS-датасетов:

```bash
python manage.py dataset dns analyze
```

## Какие JSON-файлы создаются
- `dns-path-file.json` — пути к найденным DNS-датасетам по ролям.
- `dns-file.json` — имена файлов внутри DNS-датасетов по ролям.

Структура ролей в обоих JSON:
- `TRAIN`
- `TEST`
- `VALIDATION`
- `EXPERIMENTS`

## Где сохраняются результаты
Оба JSON-файла сохраняются в директорию из переменной окружения `PATH_TEMP_DATA`.
Если `PATH_TEMP_DATA` не задана, используется `temp_data` в корне проекта.

## Краткое описание логики работы скрипта
1. `manage.py` получает команду `dataset dns analyze` и вызывает `DNSDatasetHandler`.
2. Обработчик читает путь из `PATH_DNS_DATASETS` и рекурсивно сканирует файлы.
3. Для каждой директории с файлами определяется роль по ключевым токенам в пути.
4. Пути и имена файлов собираются по ролям с дедупликацией и сортировкой.
5. Результат сохраняется в `dns-path-file.json` и `dns-file.json` через `JsonDataManager`.

# Handler Router Refactor Plan

> **Статус:** Подготовительный этап — код проекта **не меняется**. Документ фиксирует анализ, выводы, риски и план будущего рефакторинга.

---

## Содержание

1. [Краткий вывод](#краткий-вывод)
2. [Ограничения текущего этапа](#ограничения-текущего-этапа)
3. [Результаты анализа](#результаты-анализа)
4. [Текущая архитектура](#текущая-архитектура)
5. [Текущие команды](#текущие-команды)
6. [Как вызываются handlers](#как-вызываются-handlers)
7. [Проблемы текущего подхода](#проблемы-текущего-подхода)
8. [Целевая архитектура](#целевая-архитектура)
9. [Модель CommandSpec](#модель-commandspec)
10. [Добавление нового handler в будущем](#добавление-нового-handler-в-будущем)
11. [Что можно удалить из manage.py позже](#что-можно-удалить-из-managepy-позже)
12. [План рефакторинга](#план-рефакторинга)
13. [Риски и ограничения](#риски-и-ограничения)
14. [Условия безопасной миграции](#условия-безопасной-миграции)
15. [Рекомендации по реализации](#рекомендации-по-реализации)
16. [Итоговая рекомендация](#итоговая-рекомендация)

---

## Краткий вывод

Лучший вариант для будущего рефакторинга: **сохранить текущий внешний формат команд** через `manage.py`, но вынести dispatch-логику из `manage.py` в router — `scripts/handlers/router.py`.

**CLI-контракт должен остаться совместимым:**

```bash
python manage.py <module> <service> <action>
```

**Примеры команд, которые должны продолжить работать:**

```bash
python manage.py host dataset analyze
python manage.py host dataset filter
python manage.py host dataset sort
python manage.py host dataset analyze-csv-content

python manage.py dataset dns analyze
python manage.py dns dataset sort
python manage.py dns dataset analyze-train-csv-content
```

**`manage.py` в целевом состоянии** — тонкая CLI-точка входа:

1. Загрузить env/config
2. Разобрать аргументы `module`, `service`, `action`
3. Создать контекст запуска
4. Передать управление в `HandlerRouter`

---

## Ограничения текущего этапа

> ⚠️ На текущем этапе **запрещено** выполнять следующие действия:

| # | Запрещённое действие |
|---|----------------------|
| 1 | Изменять `manage.py` |
| 2 | Удалять `case`-блоки |
| 3 | Удалять `import`-ы |
| 4 | Создавать `scripts/handlers/router.py` |
| 5 | Создавать `command_specs.py` |
| 6 | Создавать `result_printer.py` |
| 7 | Изменять handlers |
| 8 | Менять env/config |
| 9 | Менять команды запуска |
| 10 | Менять вывод приложения |
| 11 | Выполнять рефакторинг |

**Этап завершён**, когда документ содержит полное описание текущего состояния, проблем, плана, рисков и условий безопасной миграции.

---

## Результаты анализа

В рамках подготовительного анализа изучены:

- Структура корня репозитория
- Файл `manage.py`
- Директория `scripts/handlers`
- Существующие handler-файлы
- Способы вызова handlers из `manage.py`
- Текущие команды, запускающие handlers
- Повторяющиеся шаблоны и архитектурные ограничения

**Фактические наблюдения:**

| Метрика | Значение |
|---------|----------|
| Строк в `manage.py` | 1773 |
| Python-файлов в `scripts/handlers` | 74 (включая `__init__.py`) |
| Прямых `import` из `scripts.handlers` | 73 |
| `case`-блоков команд | 74 |

**Дополнительно:** большинство команд создаёт handler, вызывает один метод и печатает результат через `console.print`. Для content-analysis handlers повторяется почти идентичный шаблон: создание handler с `temp_data_path` и `project_root`, вызов `analyze_and_generate_docs()`, вывод полей `summary/doc/report/status`.

---

## Текущая архитектура

### Точка входа

```
manage.py
```

### Пакет handlers

```
scripts/handlers/
```

**Состав:**

| Группа | Файлы |
|--------|-------|
| Базовый анализ датасетов | `dns_dataset_handler.py`, `host_dataset_handler.py` |
| Host pipeline | `filter_host_dataset_handler.py`, `sort_host_dataset_handler.py`, `save_sort_host_path_handler.py` |
| DNS pipeline | `sort_dns_dataset_handler.py`, `save_sort_dns_path_handler.py` |
| Content-analysis handlers | Множество файлов для host/dns train, test, validation наборов |

### Роли manage.py (текущие)

`manage.py` одновременно выполняет:

1. Загрузку переменных окружения через `dotenv`
2. Определение `PROJECT_ROOT`
3. Формирование `PATH_*` переменных
4. Создание `argparse` parser
5. Прямой импорт всех handler-классов
6. Выбор команды через `match/case`
7. Создание нужного handler
8. Вызов нужного метода handler
9. Форматирование результата
10. Печать `help` со списком команд

---

## Текущие команды

### Служебная команда

```bash
python manage.py handler example work_example
```

### DNS dataset analysis

```bash
python manage.py dataset dns analyze
```

### Host dataset pipeline

```bash
python manage.py host dataset analyze
python manage.py host dataset filter
python manage.py host dataset sort
python manage.py host dataset save-paths
```

### Host train content-analysis

```bash
python manage.py host dataset analyze-csv-content
python manage.py host dataset analyze-auth-log-content
python manage.py host dataset analyze-cpu-log-content
python manage.py host dataset analyze-diskio-log-content
python manage.py host dataset analyze-filesystem-log-content
python manage.py host dataset analyze-fsstat-log-content
python manage.py host dataset analyze-ghc-content
python manage.py host dataset analyze-info-content
python manage.py host dataset analyze-journal-content
python manage.py host dataset analyze-journal-tilde-content
python manage.py host dataset analyze-json-content
python manage.py host dataset analyze-json-1-content
python manage.py host dataset analyze-load-log-content
python manage.py host dataset analyze-log-content
python manage.py host dataset analyze-log-1-content
python manage.py host dataset analyze-log-2-content
python manage.py host dataset analyze-log-3-content
python manage.py host dataset analyze-mail-info-1-content
python manage.py host dataset analyze-mail-warn-1-content
python manage.py host dataset analyze-mainlog-content
python manage.py host dataset analyze-mainlog-1-content
python manage.py host dataset analyze-mainlog-2-content
python manage.py host dataset analyze-mainlog-3-content
python manage.py host dataset analyze-memory-log-content
python manage.py host dataset analyze-messages-content
python manage.py host dataset analyze-messages-1-content
python manage.py host dataset analyze-netflow-ids-content
python manage.py host dataset analyze-network-log-content
python manage.py host dataset analyze-pcap-content
python manage.py host dataset analyze-process-log-content
python manage.py host dataset analyze-process-summary-log-content
python manage.py host dataset analyze-sc-content
python manage.py host dataset analyze-service-log-content
python manage.py host dataset analyze-socket-summary-log-content
python manage.py host dataset analyze-syslog-content
python manage.py host dataset analyze-syslog-1-content
python manage.py host dataset analyze-syslog-2-content
python manage.py host dataset analyze-syslog-3-content
python manage.py host dataset analyze-syslog-4-content
python manage.py host dataset analyze-syslog-log-content
python manage.py host dataset analyze-txt-content
python manage.py host dataset analyze-uptime-log-content
python manage.py host dataset analyze-xml-content
```

### Host test content-analysis

```bash
python manage.py host dataset analyze-test-bson-content
python manage.py host dataset analyze-test-csv-content
python manage.py host dataset analyze-test-json-content
python manage.py host dataset analyze-test-log-content
python manage.py host dataset analyze-test-netflow-day-content
python manage.py host dataset analyze-test-txt-content
python manage.py host dataset analyze-test-wls-day-content
```

### Host validation content-analysis

```bash
python manage.py host dataset analyze-validation-cap-content
python manage.py host dataset analyze-validation-csv-content
python manage.py host dataset analyze-validation-json-content
python manage.py host dataset analyze-validation-netflow-day-content
python manage.py host dataset analyze-validation-pcap-content
python manage.py host dataset analyze-validation-pcapng-content
python manage.py host dataset analyze-validation-txt-content
python manage.py host dataset analyze-validation-wls-day-content
```

### DNS dataset pipeline

```bash
python manage.py dns dataset sort
python manage.py dataset dns sort
python manage.py dns dataset save-paths
python manage.py dataset dns save-paths
```

### DNS content-analysis

```bash
python manage.py dns dataset analyze-train-csv-content
python manage.py dns dataset analyze-train-pcap-content
python manage.py dns dataset analyze-train-pcap-csv-content
python manage.py dns dataset analyze-test-csv-content
python manage.py dns dataset analyze-test-pcap-content
python manage.py dns dataset analyze-test-pcap-csv-content
python manage.py dns dataset analyze-validation-pcap-content
python manage.py dns dataset analyze-validation-txt-content
```

---

## Как вызываются handlers

### Общий шаблон в manage.py

```python
# 1. match/case определяет tuple
match (args.module, args.service, args.action):
    case ("host", "dataset", "analyze"):
        # 2. Создание handler
        handler = SomeHandler(...)
        # 3. Вызов метода
        result = handler.analyze_and_save()
        # 4. Вывод результата
        console.print(result.some_field)
```

### Основные методы handlers

| Метод | Назначение |
|-------|------------|
| `analyze_and_save()` | Первичный анализ host/dns датасетов |
| `filter_and_save()` | Фильтрация host датасетов |
| `sort_and_prepare()` | Сортировка host/dns датасетов |
| `export_paths()` | Сохранение путей отсортированных датасетов |
| `analyze_and_generate_docs()` | Content-analysis: генерация summary, документации, отчётов |

### Группы case-блоков в manage.py

1. `("handler", "example", "work_example")` — placeholder
2. `("dataset", "dns", "analyze")` — DNS dataset analysis
3. `("host", "dataset", "analyze|filter|sort|save-paths")` — Host pipeline
4. `("host", "dataset", "analyze-*-content")` — Host train content-analysis (42 команды)
5. `("host", "dataset", "analyze-test-*-content")` — Host test content-analysis (7 команд)
6. `("host", "dataset", "analyze-validation-*-content")` — Host validation content-analysis (8 команд)
7. `("dns", "dataset", "sort|save-paths")` + aliases — DNS pipeline
8. `("dns", "dataset", "analyze-*-content")` — DNS content-analysis (8 команд)
9. `case _` — ручной help-блок

> После внедрения router help желательно генерировать из registry, чтобы список команд не расходился с реальным dispatch.

> ⚠️ Удаление перечисленных case-блоков разрешено только после того, как router полностью покрывает текущие команды и это подтверждено проверками.

---

## Проблемы текущего подхода

| # | Проблема | Описание |
|---|----------|----------|
| 1 | **Дублирование dispatch-логики** | Для каждой новой команды повторяется один шаблон: `case`, создание handler, вызов метода, вывод результата, добавление в help |
| 2 | **Перегрузка `manage.py`** | Один файл отвечает за CLI, конфигурацию, маршрутизацию, создание handlers и форматирование результатов |
| 3 | **Сложность добавления handler** | Нужно менять `manage.py` в нескольких местах: `import`, `match/case`, `console.print`, `help` |
| 4 | **Нет единого механизма маршрутизации** | Command routing не является отдельным слоем. Нет registry с командами, aliases, factory, method_name |
| 5 | **Дублирование форматирования** | Поля `summary_json_file`, `docs_ru_file`, `docs_en_file`, `report_ru_file`, `report_en_file`, `total_files_count`, `sampled_files_count`, `status` выводятся вручную в каждом case-блоке |
| 6 | **Архитектурное ограничение** | При добавлении новых доменов (ml, feature extraction, normalization, training pipeline) `manage.py` будет расти и ухудшать поддерживаемость |
| 7 | **Риск несогласованности help** | Команда может быть добавлена в `match/case`, но забыта в `help`, и наоборот |
| 8 | **Прямые imports всех handlers** | Ошибка импорта в одном handler может мешать запуску любой другой команды |

---

## Целевая архитектура

### Поток вызова

```
manage.py → HandlerRouter → CommandSpec → Handler → ResultPrinter
```

`manage.py` **не должен знать** о конкретных handler-классах.

### Ответственность router

Router принимает `module`, `service`, `action` и:

1. Собирает ключ команды `(module, service, action)`
2. Находит `CommandSpec` в registry
3. Создаёт handler через factory
4. Вызывает указанный `method_name`
5. Передаёт результат в единый printer
6. При неизвестной команде выводит help
7. Поддерживает aliases текущих команд

### Тип ключа команды

```python
CommandKey = tuple[str, str, str]
```

**Примеры ключей:**

```python
("host", "dataset", "analyze")
("host", "dataset", "filter")
("dns", "dataset", "sort")
("dataset", "dns", "sort")   # alias для предыдущего
```

> Aliases должны быть **явными**: обе команды `dns dataset sort` и `dataset dns sort` должны вести к одному `CommandSpec`.

---

## Модель CommandSpec

### Поля CommandSpec

| Поле | Описание |
|------|----------|
| `keys` | Список CLI-ключей (для aliases) |
| `handler_factory` | Функция, создающая handler из контекста |
| `method_name` | Имя метода handler для вызова |
| `success_message` | Сообщение при успешном выполнении |
| `result_formatter` | Опционально: специальное форматирование результата |

### Поля HandlerContext

Контекст запуска хранит значения из `manage.py`:

| Поле | Источник |
|------|----------|
| `project_root` | `manage.py` |
| `path_temp_data` | `manage.py` |
| `path_host_datasets` | `manage.py` |
| `path_dns_datasets` | `manage.py` |
| `path_host_datasets_filter` | `manage.py` |
| `path_dns_datasets_filter` | `manage.py` |
| `path_filter_log` | `manage.py` |

---

## Добавление нового handler в будущем

После реализации router добавление нового handler — **локальное и предсказуемое**:

1. Создать handler в `scripts/handlers/` или в доменном подпакете
2. Убедиться, что handler имеет явный публичный метод запуска:
   - `analyze_and_save()`
   - `filter_and_save()`
   - `sort_and_prepare()`
   - `export_paths()`
   - `analyze_and_generate_docs()`
   - (или новый метод с понятным именем и документацией)
3. Вернуть результат как `dataclass` или стабильный объект
4. Добавить `CommandSpec` в registry
5. Указать один или несколько `keys` для CLI-совместимости
6. Указать `handler_factory`, принимающую `HandlerContext`
7. Указать `method_name`
8. Указать `success_message`
9. При необходимости добавить `formatter` для нестандартного результата
10. Добавить проверку команды в тестовый checklist

> ✅ После внедрения router новый handler **не требует** изменения большого `match/case` в `manage.py`.

---

## Что можно удалить из manage.py позже

> ⚠️ На текущем этапе ничего из `manage.py` удалять **нельзя**.

После успешной реализации router, переноса всех команд в registry и проверки совместимости можно рассмотреть удаление:

### 1. Прямые imports handler-классов

```python
from scripts.handlers.* import ...
```

Переедут в router/registry-модуль или доменные registry-модули.

### 2. Placeholder case

```python
("handler", "example", "work_example")
```

### 3. DNS dataset analysis case

```python
("dataset", "dns", "analyze")
```

### 4. Host dataset pipeline cases

```python
("host", "dataset", "analyze")
("host", "dataset", "filter")
("host", "dataset", "sort")
("host", "dataset", "save-paths")
```

### 5. Host train content-analysis cases (42 блока)

```python
("host", "dataset", "analyze-csv-content")
("host", "dataset", "analyze-auth-log-content")
("host", "dataset", "analyze-cpu-log-content")
("host", "dataset", "analyze-diskio-log-content")
("host", "dataset", "analyze-filesystem-log-content")
("host", "dataset", "analyze-fsstat-log-content")
("host", "dataset", "analyze-ghc-content")
("host", "dataset", "analyze-info-content")
("host", "dataset", "analyze-journal-content")
("host", "dataset", "analyze-journal-tilde-content")
("host", "dataset", "analyze-json-content")
("host", "dataset", "analyze-json-1-content")
("host", "dataset", "analyze-load-log-content")
("host", "dataset", "analyze-log-content")
("host", "dataset", "analyze-log-1-content")
("host", "dataset", "analyze-log-2-content")
("host", "dataset", "analyze-log-3-content")
("host", "dataset", "analyze-mail-info-1-content")
("host", "dataset", "analyze-mail-warn-1-content")
("host", "dataset", "analyze-mainlog-content")
("host", "dataset", "analyze-mainlog-1-content")
("host", "dataset", "analyze-mainlog-2-content")
("host", "dataset", "analyze-mainlog-3-content")
("host", "dataset", "analyze-memory-log-content")
("host", "dataset", "analyze-messages-content")
("host", "dataset", "analyze-messages-1-content")
("host", "dataset", "analyze-netflow-ids-content")
("host", "dataset", "analyze-network-log-content")
("host", "dataset", "analyze-pcap-content")
("host", "dataset", "analyze-process-log-content")
("host", "dataset", "analyze-process-summary-log-content")
("host", "dataset", "analyze-sc-content")
("host", "dataset", "analyze-service-log-content")
("host", "dataset", "analyze-socket-summary-log-content")
("host", "dataset", "analyze-syslog-content")
("host", "dataset", "analyze-syslog-1-content")
("host", "dataset", "analyze-syslog-2-content")
("host", "dataset", "analyze-syslog-3-content")
("host", "dataset", "analyze-syslog-4-content")
("host", "dataset", "analyze-syslog-log-content")
("host", "dataset", "analyze-txt-content")
("host", "dataset", "analyze-uptime-log-content")
("host", "dataset", "analyze-xml-content")
```

### 6. Host test content-analysis cases (7 блоков)

```python
("host", "dataset", "analyze-test-bson-content")
("host", "dataset", "analyze-test-csv-content")
("host", "dataset", "analyze-test-json-content")
("host", "dataset", "analyze-test-log-content")
("host", "dataset", "analyze-test-netflow-day-content")
("host", "dataset", "analyze-test-txt-content")
("host", "dataset", "analyze-test-wls-day-content")
```

### 7. Host validation content-analysis cases (8 блоков)

```python
("host", "dataset", "analyze-validation-cap-content")
("host", "dataset", "analyze-validation-csv-content")
("host", "dataset", "analyze-validation-json-content")
("host", "dataset", "analyze-validation-netflow-day-content")
("host", "dataset", "analyze-validation-pcap-content")
("host", "dataset", "analyze-validation-pcapng-content")
("host", "dataset", "analyze-validation-txt-content")
("host", "dataset", "analyze-validation-wls-day-content")
```

### 8. DNS dataset pipeline cases с aliases

```python
("dns", "dataset", "sort")
("dataset", "dns", "sort")
("dns", "dataset", "save-paths")
("dataset", "dns", "save-paths")
```

### 9. DNS content-analysis cases (8 блоков)

```python
("dns", "dataset", "analyze-train-csv-content")
("dns", "dataset", "analyze-train-pcap-content")
("dns", "dataset", "analyze-train-pcap-csv-content")
("dns", "dataset", "analyze-test-csv-content")
("dns", "dataset", "analyze-test-pcap-content")
("dns", "dataset", "analyze-test-pcap-csv-content")
("dns", "dataset", "analyze-validation-pcap-content")
("dns", "dataset", "analyze-validation-txt-content")
```

### 10. Ручной help-блок (`case _`)

После внедрения router help генерируется из registry.

---

## План рефакторинга

### Этап 1 — Подготовить router без удаления старой логики

- [ ] Создать `scripts/handlers/router.py`
- [ ] Описать `HandlerContext`
- [ ] Описать `CommandSpec`
- [ ] Реализовать `HandlerRouter`
- [ ] Добавить registry для нескольких низкорисковых команд
- [ ] Оставить текущий `match/case` в `manage.py` как fallback

### Этап 2 — Перенести базовые pipeline-команды

- [ ] `host dataset analyze`
- [ ] `host dataset filter`
- [ ] `host dataset sort`
- [ ] `host dataset save-paths`
- [ ] `dataset dns analyze`
- [ ] `dns/dataset sort` aliases
- [ ] `dns/dataset save-paths` aliases

### Этап 3 — Перенести content-analysis команды

- [ ] Host train content-analysis (42 команды)
- [ ] Host test content-analysis (7 команд)
- [ ] Host validation content-analysis (8 команд)
- [ ] DNS train/test/validation content-analysis (8 команд)
- [ ] Проверить, что все старые команды имеют соответствующий `CommandSpec`

### Этап 4 — Централизовать вывод результата

- [ ] Вынести общий `result_printer`
- [ ] Добавить стандартный dataclass-printer
- [ ] Для специальных результатов оставить возможность `custom formatter`
- [ ] Проверить, что вывод содержит все важные поля, которые сейчас печатает `manage.py`

### Этап 5 — Проверить совместимость

- [ ] Все текущие команды
- [ ] Aliases
- [ ] Unknown command / help
- [ ] env/config значения корректно передаются в handlers
- [ ] Результаты пишутся в те же файлы, что и раньше

### Этап 6 — Удалить старый dispatch из manage.py

> Только после успешной проверки этапа 5.

- [ ] Удалить прямые `import` handlers из `manage.py`
- [ ] Удалить большой `match/case`
- [ ] Оставить в `manage.py` только создание контекста и вызов `router.run(...)`
- [ ] Перенести help в router

---

## Риски и ограничения

| # | Риск | Описание |
|---|------|----------|
| 1 | **CLI-совместимость** | Все существующие команды должны продолжить работать с теми же `module/service/action` |
| 2 | **Потеря aliases** | `dns dataset sort` и `dataset dns sort` должны быть явно зарегистрированы как aliases одного действия |
| 3 | **Изменение формата вывода** | Если вывод парсят другие скрипты — нужно сохранить названия и порядок ключевых полей или явно согласовать изменение |
| 4 | **Избыточный импорт** | Простая явная registry может сохранить текущее поведение с импортом многих модулей. При необходимости — lazy imports внутри `handler_factory` |
| 5 | **Дублирование command keys** | Router должен проверять registry на дублирующиеся ключи при старте или в тестах |
| 6 | **Неполная миграция** | Временное существование двух источников dispatch-логики допустимо только как короткий миграционный этап |
| 7 | **Некорректные пути** | В текущей реализации встречаются Windows-style строки с backslash. Это отдельная проблема, не исправляется в рамках данной задачи |
| 8 | **Неявная auto-discovery** | На первом этапе не рекомендуется автоматически импортировать `scripts/handlers/*.py` через `importlib`. Явный registry безопаснее и проще для отладки |

---

## Условия безопасной миграции

Перед удалением старой dispatch-логики из `manage.py` должны быть выполнены все следующие условия:

- [ ] Все текущие команды зарегистрированы в router
- [ ] Все aliases зарегистрированы явно
- [ ] Есть проверка на duplicate command keys
- [ ] Есть проверка unknown command / help
- [ ] Есть список команд до/после миграции
- [ ] Для каждой команды подтверждено, что вызывается тот же handler и тот же метод
- [ ] Результирующие JSON/docs/report файлы формируются в тех же местах
- [ ] `manage.py` временно поддерживает fallback на старый `match/case` до завершения проверки
- [ ] Удаление старых case-блоков выполняется **отдельным этапом** после тестирования

---

## Рекомендации по реализации

1. **Сохранять текущий CLI-контракт.** Не менять форму `python manage.py <module> <service> <action>`.

2. **Использовать явный registry команд.** Это проще и безопаснее, чем decorator-based registry или автоматический `importlib` discovery на первом этапе.

3. **Поддерживать aliases через `keys` в `CommandSpec`.**

4. **Хранить env/config значения в `HandlerContext`.**

5. **Не заставлять `manage.py` импортировать конкретные handlers.**

6. **Сделать help производным от registry.**

7. **Для content-analysis handlers использовать общий dataclass-printer**, если нет специальных требований к выводу.

8. **Разделить registry по доменам только после того, как общий router заработает.** Например:
   ```
   scripts/handlers/host_commands.py
   scripts/handlers/dns_commands.py
   ```

9. **Не смешивать рефакторинг router с исправлением путей, кодировки, структуры handlers или бизнес-логики.**

---

## Итоговая рекомендация

Будущий рефакторинг должен быть **минимально инвазивным**:

1. Внешний формат команд — сохранить
2. `manage.py` — оставить точкой входа
3. Dispatch — перенести в `HandlerRouter`
4. Команды — описать через явный registry
5. Новые handlers — добавлять через `CommandSpec`
6. Старые case-блоки — удалить **только после** полной миграции и тестирования

Такой подход убирает перегрузку `manage.py`, снижает дублирование и создаёт понятный механизм расширения проекта без изменения текущего пользовательского интерфейса команд.
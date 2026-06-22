# Stage Two runtime/resource runbook

Документ описывает практические правила запуска Stage Two normalization для больших файлов.

## Главный принцип

Сначала добиться устойчивого выполнения без swap, потом повышать параллелизм.

Если CPU низкий, RAM 95-98%, а диск активен, процесс уперся не в CPU, а в память/подкачку или I/O. В такой ситуации увеличение `--workers` часто замедляет обработку.

## Что означает каждый параметр

`--limit`
: Лимит файлов из catalog, не строк внутри файла.

`--workers`
: Количество процессов. Параллелит файлы, а не строки одного файла.

`--batch-size`
: Сколько normalized events parser держит в памяти до передачи на запись. Основной регулятор RAM.

`--max-output-part-rows`
: Сколько строк писать в один Parquet part. Влияет на размер и количество output-файлов.

`--resume`
: Пытается продолжить существующий resumable parser_run и пропустить уже зарегистрированные parts. Если запуск был прерван до commit parser_run, продолжать может быть нечего.

`--packet-mode`
: Для packet captures. Значения: `packet-summary`, `dns-only`, `sample`.

## Профили запуска

### Ноутбук 16 GB RAM

Без split:

```powershell
python manage.py stage-two normalize-format --branch dns --role TEST --format csv --limit 1 --workers 1 --batch-size 10000 --max-output-part-rows 50000 --resume
```

После split line-based файла:

```powershell
python manage.py stage-two normalize-format --branch dns --role TEST --format csv --limit 4 --workers 2 --batch-size 10000 --max-output-part-rows 50000 --resume
```

Если RAM выше 14 GB или диск постоянно 100%, остановить и вернуться к `--workers 1`.

### Машина 64 GB RAM

```powershell
python manage.py stage-two normalize-format --branch host --role TEST --format txt --limit 1000 --workers 2 --batch-size 25000 --max-output-part-rows 50000 --resume
```

Можно пробовать `--workers 4` только если файлы уже split/chunked и RAM не уходит в swap.

### Машина 128 GB RAM

```powershell
python manage.py stage-two normalize-format --branch host --role TEST --format txt --limit 1000 --workers 4 --batch-size 50000 --max-output-part-rows 100000 --resume
```

Для большого количества маленьких файлов можно повышать `--workers`. Для нескольких очень больших файлов лучше сначала split.

## Когда применять split-large-files

Применять для line-based форматов:

- `csv`, `pcap.csv`
- `txt`
- `json`, если это JSON-lines, а не один большой JSON array/object
- `log`, `auth.log`, `syslog*`, `mainlog*`, `messages*`
- `ghc`, `sc`
- `netflow_day`, `netflow_ids`, `wls_day`
- metricbeat-like logs: `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log`

Не применять для:

- `pcap`, `pcapng`, `cap`
- `bson`
- JSON array/object, если весь файл является одним JSON-документом.

## Split workflow

Dry-run:

```powershell
python manage.py stage-two split-large-files --branch dns --role TEST --format csv --limit 1 --max-part-size-gb 2 --min-size-gb 1 --header no
```

Apply and register:

```powershell
python manage.py stage-two split-large-files --branch dns --role TEST --format csv --limit 1 --max-part-size-gb 2 --min-size-gb 1 --header no --apply --register
```

Normalize chunks:

```powershell
python manage.py stage-two normalize-format --branch dns --role TEST --format csv --limit 4 --workers 2 --batch-size 10000 --max-output-part-rows 50000 --resume
```

`--register` регистрирует chunks как `READY_FOR_PARSING`. Исходный большой файл по умолчанию переводится в `SKIPPED`, чтобы не обработать его повторно.

Если нужно оставить исходник в очереди, использовать `--keep-source-ready`, но это опасно: можно получить дубли.

## Header mode

`--header no`
: Для headerless CSV, например текущий `dns TEST csv`.

`--header yes`
: Для CSV с заголовком. Header будет повторен в каждом chunk.

`--header auto`
: Автоопределение через `csv.Sniffer`. Удобно, но для критичного запуска лучше явно указать `yes` или `no`.

## Как выбирать размер chunk

Для 16 GB RAM:

```text
--max-part-size-gb 1 или 2
```

Для 64 GB RAM:

```text
--max-part-size-gb 2 или 4
```

Для 128 GB RAM:

```text
--max-part-size-gb 4 или 8
```

Меньше chunk = больше файлов и лучше параллелизм, но больше overhead catalog/Parquet.
Больше chunk = меньше overhead, но хуже балансировка workers.

## Что смотреть во время запуска

В Task Manager:

- RAM ниже 80-85%: хорошо.
- RAM 95-98% и диск 100%: плохо, идет swap/I/O pressure.
- CPU 60-100% и RAM стабильна: нормальный режим.
- CPU низкий, диск высокий: узкое место I/O или swap.

В output команды:

- `selected`: сколько файлов выбрано.
- `processed`: сколько обработано.
- `normalized`: сколько успешно нормализовано.
- `failed`: сколько упало.
- `unsupported`: нет активного parser-а.

## Рекомендуемый порядок на дедлайн

1. Сначала обработать обязательные DNS/TEST/TRAIN/VALIDATION форматы.
2. Большие CSV/TXT/JSON-lines/log/netflow сначала split.
3. На 16 GB RAM не запускать `workers > 2`.
4. Packet captures запускать отдельно, не смешивать с тяжелыми CSV/TXT.
5. После каждого крупного блока запускать:

```powershell
python manage.py stage-two parser-coverage
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

## Быстрые признаки неправильного запуска

`--workers 16` на 16 GB RAM
: Почти гарантированный swap для больших файлов.

`--batch-size 100000` на 16 GB RAM
: Риск высокой RAM и PyArrow buffers.

`--limit 100` для одного файла
: Не ускоряет один файл. Это только лимит выбранных файлов.

Split без `--register`
: Chunks созданы на диске, но normalize-format их не увидит в catalog.

Split с `--keep-source-ready`
: Есть риск обработать и исходный файл, и chunks.

# Отчет об очистке datasets-new/host

**Дата:** 2026-05-16

---

## 1. Краткий вывод

В каталоге `datasets-new/host` были удалены лишние сконвертированные host datasets, которые относятся к расширенной, опциональной или экспериментальной валидации. Для дипломной работы оставлен минимально достаточный host-стек:

| Датасет | Назначение |
|:---|:---|
| **ADFA IDS** | Baseline HIDS training |
| **LID-DS 2021** | Syscall sequence modelling |
| **Maintainable Log Dataset** | Enterprise multi-stage log behaviour |

Такой набор соответствует минимальной обязательной конфигурации из `docs/ru/host_datasets_analysis.md` и закрывает основные задачи proposal: baseline HIDS, syscall sequence modelling и enterprise multi-stage log behaviour.

---

## 2. Почему была выполнена очистка

Документ `docs/ru/project_proposal_analysis.md` фиксирует несколько важных ограничений проекта:

- исследование должно быть воспроизводимым;
- публичные datasets должны быть явно выбраны и обоснованы;
- есть риск несовместимости host и network datasets;
- есть ограничения по времени, данным и вычислительным ресурсам;
- для дипломной работы не требуется хранить все возможные validation/test/experiment datasets.

> Поэтому было принято инженерное решение оставить только core datasets, которые необходимы для основной линии исследования, а крупные расширенные datasets удалить из `datasets-new/host`.

---

## 3. Оставленные datasets

---

### ADFA IDS

> **Причина:** Основной baseline dataset для Host-Based Intrusion Detection.

Нужен для первичного сравнения с классическими HIDS-подходами и обучения на normal/attack host traces.

---

### LID-DS 2021

> **Причина:** Основной dataset для syscall sequence modelling.

Нужен для LSTM/CNN-LSTM части проекта и анализа поведения процессов во времени.

---

### Maintainable Log Dataset

> **Причина:** Основной dataset для enterprise logs и multi-stage attack modelling.

Нужен, чтобы проект покрывал не только syscall-level поведение, но и log-level поведенческие паттерны.

---

## 4. Удаленные datasets

---

### Dynamic Malware Analysis Dataset

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 298 625 |
| Объем | ~41.49 GiB |

> **Причина удаления:** Это malware-driven validation dataset. Он полезен для расширенной проверки suspicious process behavior, но является опциональным для текущего дипломного scope и занимает самый большой объем.

---

### LID-DS 2019

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 6 502 |
| Объем | ~6.06 GiB |

> **Причина удаления:** Это cross-version validation dataset для CVE-based атак. Он полезен для дополнительной проверки переносимости модели, но минимальный дипломный стек уже содержит LID-DS 2021 как основной sequence dataset.

---

### Windows Event Log / OTRF Security Datasets

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 246 |
| Объем | ~246.11 MiB |

> **Причина удаления:** Это SOC-style Windows telemetry validation dataset. Он желателен для расширения практической SOC-валидации, но не обязателен для базовой реализации proposal.

---

### Unified Host + Network Dataset / LANL

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 5 |
| Объем | ~15.38 MiB |

> **Причина удаления:** Это hybrid host+network validation dataset. Он полезен для расширенной проверки feature-level fusion, но текущая задача состоит в сокращении объема host datasets до минимально нужного дипломного набора.

---

### LANL Dataset

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 5 |
| Объем | ~15.38 MiB |

> **Причина удаления:** Это enterprise user-host/authentication behaviour validation dataset. Он относится к desirable validation, но не входит в минимальную обязательную конфигурацию.

---

### ISOT Cloud IDS Dataset

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 3 |
| Объем | ~12.71 MiB |

> **Причина удаления:** Это cloud environment validation dataset. Он опционален и нужен только если проект отдельно доказывает переносимость на cloud workloads.

---

### HDFS Log Dataset

| Параметр | Значение |
|:---|:---|
| Удалено файлов | 6 |
| Объем | ~12.44 MiB |

> **Причина удаления:** Это experiments-only log anomaly dataset. Он не является security-focused host intrusion dataset и нужен только для дополнительных экспериментов по log anomaly detection.

---

## 5. Итог очистки

### До очистки

| Параметр | Значение |
|:---|:---|
| Файлов в `datasets-new/host` | 392 084 конвертированных JSON-файла |

### Удалено

| Параметр | Значение |
|:---|:---|
| Файлов | 305 392 |
| Объем | ~47.84 GiB |

### Осталось

| Параметр | Значение |
|:---|:---|
| Файлов | 86 692 |
| Объем | ~4.63 GiB |

---

### Финальное состояние по split

| Split | Файлов | Объем |
|:---:|---:|---:|
| `TRAIN` | 72 373 | ~3 083.34 MiB |
| `VALIDATION` | 10 799 | ~569.46 MiB |
| `TEST` | 3 520 | ~1 090.44 MiB |
| `EXPERIMENTS` | 0 | — |

---

## 6. Как проверить

### Dry-run проверка

```bash
python scripts/cleanup_host_datasets_new.py --root datasets-new/host --workers 16
```

**Ожидаемый результат после очистки:**

```
Deleted files: 0
```

---

### Тесты

```bash
python -m unittest discover -s tests -p "test_*.py"
```

**Ожидаемый результат:**

```
OK
```

# Host Dataset Strategy для проекта Host-Based Intrusion Detection и Hybrid IDS

## 1. Назначение документа

Документ фиксирует набор датасетов для обучения, валидации, тестирования и экспериментов в host-side части проекта по обнаружению вторжений, вредоносного поведения, аномалий пользователей и hybrid host + network activity.

Основная цель — не смешивать роли датасетов и использовать каждый набор данных по назначению:

- **TRAIN** — обучение модели на normal / attack host traces, syscall sequences и enterprise logs.
- **VALIDATION** — проверка устойчивости модели на других поколениях данных, user-host behavior и SOC telemetry.
- **TEST** — финальная проверка обобщающей способности модели на hybrid, cloud и malware-driven данных.
- **EXPERIMENTS** — быстрые эксперименты, log anomaly detection, synthetic augmentation и поиск дополнительных источников.

---

# 2. Обязательные датасеты

## 🥇 1. ADFA IDS

### Роль

**Основной baseline dataset для Host Intrusion Detection Systems.**

### Ссылка

<https://research.unsw.edu.au/projects/adfa-ids-datasets>

<https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download>

### Факт

ADFA IDS — классический benchmark для Host Intrusion Detection Systems.

### Содержит

- Linux system calls;
- Windows system calls;
- normal traces;
- attack traces.

### Для чего нужен

Используется как **baseline HIDS training dataset** для первичной проверки модели и сравнения с существующими research-подходами.

Основные задачи:

- baseline normal / attack host traces;
- первичная проверка модели;
- сравнимость с классическими HIDS-подходами;
- обучение на system call sequences.

### Подходящие модели

| Тип модели | Применение |
|---|---|
| Random Forest | базовая ML-модель |
| XGBoost | сильный baseline для табличных признаков |
| LSTM | sequence modelling по system call sequences |
| CNN | анализ локальных паттернов syscall-последовательностей |

### Почему критичен

ADFA — один из стандартных датасетов для HIDS. Без него трудно обосновать baseline и сравнимость с существующими research-подходами.

### Использование в проекте

```text
TRAIN:
- baseline HIDS training
- normal host traces
- attack host traces
- system call sequences
```

---

## 🥈 2. LID-DS 2021

### Роль

**Основной sequence dataset для host-based detection.**

### Ссылка

<https://github.com/LID-DS/LID-DS>

### Факт

LID-DS 2021 — современный dataset для Linux-based intrusion detection на основе system calls и сценариев атак.

### Содержит

- system calls;
- attack scenarios;
- normal behavior;
- labelled traces.

### Для чего нужен

Используется как **core sequence modelling dataset** для обучения моделей, которые анализируют поведение процессов во времени.

Основные задачи:

- syscall sequence modelling;
- обучение LSTM / GRU / CNN-LSTM моделей;
- анализ временных паттернов host behavior;
- обучение на normal и attack traces.

### Подходящие модели

| Тип модели | Применение |
|---|---|
| LSTM | анализ последовательностей system calls |
| GRU | более лёгкое sequence modelling |
| CNN-LSTM | локальные syscall-паттерны + временная динамика |
| Transformer-based models | моделирование длинных зависимостей в syscall sequences |

### Почему критичен

LID-DS 2021 лучше подходит для моделирования поведения во времени, чем простые табличные host logs. Это ключевой dataset для LSTM-части проекта.

### Использование в проекте

```text
TRAIN:
- syscall sequence modelling
- Linux host behavior
- attack scenarios
- labelled traces
```

---

## 🥉 3. Maintainable Log Dataset

### Роль

**Основной датасет для enterprise log behavior и multi-stage attack modelling.**

### Ссылка

<https://data.niaid.nih.gov/resources?id=zenodo_5789063>

### Факт

Maintainable Log Dataset содержит enterprise logs и multi-stage атаки, смоделированные через state machines.

### Содержит

- system logs;
- enterprise logs;
- 20 типов логов;
- multi-stage attack behavior.

### Для чего нужен

Используется для проверки behavioral modelling и detection multi-stage атак на log-level telemetry.

Основные задачи:

- anomaly detection;
- user / host behavior modelling;
- temporal pattern detection;
- feature-level fusion;
- проверка multi-stage attack behavior.

### Подходящие модели

| Тип модели | Применение |
|---|---|
| Random Forest | baseline по агрегированным log-признакам |
| XGBoost | сильный baseline для feature-level fusion |
| LSTM / GRU | temporal pattern detection |
| Autoencoder | anomaly detection по log-поведению |

### Почему критичен

System calls показывают низкоуровневое поведение процесса, но не всегда дают картину enterprise-атаки. Maintainable Log Dataset нужен, чтобы показать, что проект работает не только на syscall-level, но и на log-level behavior.

### Использование в проекте

```text
TRAIN:
- enterprise log behavior modelling
- multi-stage attack behavior
- temporal log patterns
- feature-level fusion
```

---

# 3. Дополнительные датасеты

## 🟡 4. LID-DS 2019

### Роль

**Validation dataset для CVE-based атак и cross-version проверки.**

### Ссылка

<https://fkie-cad.github.io/COMIDDS/content/datasets/lids_ds_2019/>

### Факт

LID-DS 2019 содержит CVE-based attack scenarios с system calls и параметрами.

### Содержит

- system calls;
- syscall parameters;
- labelled attacks;
- benign traces.

### Для чего нужен

Используется для validation и проверки устойчивости модели на другом поколении LID-DS.

Основной сценарий:

```text
TRAIN:
- LID-DS 2021

VALIDATION:
- LID-DS 2019
```

### Проверяет

- насколько модель переносится между LID-DS 2021 и LID-DS 2019;
- не переобучилась ли модель на конкретные attack traces;
- насколько хорошо работают syscall-level признаки;
- устойчивость к CVE-based attack scenarios.

### Почему важен

LID-DS 2019 даёт cross-dataset validation внутри одного семейства host-based datasets. Это помогает отделить реальное качество модели от переобучения на конкретные traces.

### Использование в проекте

```text
VALIDATION:
- cross-version validation
- CVE-based attack scenarios
- syscall parameters
- benign traces
```

---

## 🟡 5. LANL Dataset

### Роль

**Проверка enterprise authentication behavior и user-host anomalies.**

### Ссылка

<https://github.com/trenton3983/Cybersecurity-Datasets>

### Факт

Los Alamos National Lab dataset содержит enterprise authentication logs и user-computer events.

### Содержит

- authentication logs;
- user-computer events;
- multi-day activity;
- enterprise behavior.

### Для чего нужен

Используется для моделирования поведения пользователей и хостов в корпоративной среде.

### Проверяет

- lateral movement patterns;
- abnormal login behavior;
- user-host interaction anomalies;
- long-term behavioral deviations.

### Почему важен

LANL закрывает слабое место syscall datasets: они хорошо описывают процессы, но плохо описывают поведение пользователей и инфраструктуры.

### Использование в проекте

```text
VALIDATION:
- user-host behavior
- authentication behavior
- lateral movement patterns
- long-term behavioral deviations
```

---

## 🟡 6. Windows Event Log / OTRF Security Datasets

### Роль

**SOC-level validation на Windows host telemetry.**

### Ссылка

<https://github.com/OTRF/Security-Datasets>

### Факт

OTRF Security Datasets содержат Windows security logs, часто включающие Sysmon-based telemetry.

### Содержит

- Windows Event Logs;
- Sysmon events;
- process activity;
- security events.

### Для чего нужен

Используется для проверки модели на real SOC-style данных и Windows host behavior.

### Проверяет

- Windows host behavior;
- process creation events;
- suspicious parent-child process chains;
- event-based anomaly detection;
- применимость к SOC telemetry.

### Почему важен

ADFA и LID-DS больше ориентированы на syscall-level detection. Windows Event Logs позволяют добавить SOC-практичность и связать research с реальными security operations.

### Использование в проекте

```text
VALIDATION:
- SOC-style validation
- Windows host behavior
- Sysmon telemetry
- event-based anomaly detection
```

---

## 🟢 7. Unified Host + Network Dataset / LANL

### Роль

**Hybrid validation для host + network detection.**

### Ссылка

<https://github.com/trenton3983/Cybersecurity-Datasets>

### Факт

Unified Host + Network Dataset / LANL — редкий dataset, объединяющий host logs и network-level данные.

### Содержит

- host events;
- network events;
- authentication activity;
- multi-source telemetry.

### Для чего нужен

Используется для проверки hybrid-подхода и feature-level fusion между host telemetry и network telemetry.

### Проверяет

- насколько host-level признаки усиливают network-level detection;
- можно ли объединить host telemetry и network telemetry;
- насколько модель устойчива при multi-source input;
- применимость к SOC-style hybrid IDS архитектуре.

### Почему важен

Для proposal с hybrid IDS / exfiltration detection этот dataset особенно важен, потому что он ближе к реальной SOC-архитектуре.

### Использование в проекте

```text
TEST:
- hybrid host + network validation
- multi-source telemetry
- feature-level fusion
- SOC-style architecture check
```

---

## 🟢 8. ISOT Cloud IDS Dataset

### Роль

**Проверка модели в cloud environment.**

### Ссылка

<https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php>

### Факт

ISOT Cloud IDS Dataset содержит cloud environment telemetry: system logs, syscalls и performance metrics.

### Содержит

- system logs;
- syscalls;
- cloud performance metrics;
- cloud activity traces.

### Для чего нужен

Используется для проверки переносимости модели на cloud infrastructure.

### Проверяет

- переносимость модели на cloud infrastructure;
- устойчивость к другому типу host telemetry;
- detection в условиях cloud workloads;
- применимость не только к локальным машинам.

### Почему важен

Если проект заявляет применимость не только к локальным машинам, но и к современной инфраструктуре, cloud dataset усиливает аргументацию.

### Использование в проекте

```text
TEST:
- cloud environment validation
- cloud workloads
- cloud logs / syscalls
- performance metrics
```

---

## 🟢 9. Dynamic Malware Analysis Dataset

### Роль

**Проверка malware-driven host behavior.**

### Ссылка

<https://zenodo.org/record/1203289>

### Факт

Dynamic Malware Analysis Dataset предназначен для анализа поведения malware через kernel calls и user-level activity.

### Содержит

- kernel calls;
- user-level activity;
- malware behavior traces.

### Для чего нужен

Используется для расширения модели на malware-driven host behavior.

### Проверяет

- malware execution patterns;
- suspicious process behavior;
- признаки exfiltration-related activity;
- host-side malicious behavior.

### Почему важен

DNS exfiltration часто связан с malware или post-exploitation activity. Этот dataset помогает связать host behavior с потенциальной exfiltration-логикой.

### Использование в проекте

```text
TEST:
- malware-driven host behavior
- suspicious process behavior
- exfiltration-related host activity
- malicious behavior traces
```

---

## 🟢 10. HDFS Log Dataset

### Роль

**Дополнительный baseline для log anomaly detection.**

### Ссылка

<https://github.com/logpai/loghub>

### Факт

HDFS Log Dataset — классический log anomaly detection dataset.

### Содержит

- system logs;
- structured log sequences;
- anomaly labels.

### Для чего нужен

Используется для дополнительных экспериментов с log anomaly detection.

Подходит для:

- быстрых экспериментов;
- проверки log anomaly методов;
- feature engineering на structured log sequences;
- сравнения anomaly detection подходов.

### Ограничение

Это не security-focused dataset. Он полезен для проверки log anomaly методов, но не должен быть основным источником для host intrusion detection.

### Использование в проекте

```text
EXPERIMENTS:
- log anomaly experiments
- structured log sequences
- anomaly detection baseline
```

---

# 4. Правильное распределение ролей

| Этап | Датасет | Назначение |
|---|---|---|
| TRAIN | ADFA IDS | baseline HIDS training |
| TRAIN | LID-DS 2021 | основное sequence modelling обучение |
| TRAIN | Maintainable Log Dataset | enterprise log behavior modelling |
| VALIDATION | LID-DS 2019 | cross-version validation на CVE-based атаках |
| VALIDATION | LANL Dataset | проверка user / host behavior |
| VALIDATION | Windows Event Log / OTRF | SOC-style validation |
| TEST | Unified Host + Network Dataset / LANL | hybrid host + network test |
| TEST | ISOT Cloud IDS Dataset | cloud environment test |
| TEST | Dynamic Malware Analysis Dataset | malware behavior test |
| EXPERIMENTS | HDFS Log Dataset | log anomaly experiments |
| EXPERIMENTS | BGL Logs | non-security anomaly baseline |
| EXPERIMENTS | Syscall Dataset Generator | synthetic syscall augmentation |
| EXPERIMENTS | COMIDDS | поиск дополнительных datasets |

---

# 5. Правильная схема обучения

## TRAIN

```text
ADFA IDS
→ baseline normal / attack host traces
→ HIDS baseline
→ comparison with classic research approaches
```

```text
LID-DS 2021
→ syscall sequence modelling
→ Linux host behavior
→ LSTM / GRU / CNN-LSTM / Transformer models
```

```text
Maintainable Log Dataset
→ enterprise log behavior modelling
→ multi-stage attack behavior
→ feature-level fusion
```

## VALIDATION

```text
LID-DS 2019
→ CVE-based attack scenarios
→ cross-version validation
→ syscall-level robustness check
```

```text
LANL Dataset
→ user-host behavior
→ authentication behavior
→ lateral movement patterns
```

```text
Windows Event Logs / OTRF
→ SOC telemetry validation
→ Windows host behavior
→ Sysmon-style event analysis
```

## TEST

```text
Unified Host + Network Dataset / LANL
→ hybrid IDS validation
→ host + network correlation
→ multi-source telemetry test
```

```text
ISOT Cloud IDS Dataset
→ cloud environment validation
→ cloud logs / syscalls
→ cloud workload robustness
```

```text
Dynamic Malware Analysis Dataset
→ malware-driven host behavior
→ suspicious process behavior
→ exfiltration-related activity
```

## EXPERIMENTS

```text
HDFS Log Dataset
→ log anomaly experiments
→ structured log sequences
→ non-security anomaly baseline
```

```text
BGL Logs
→ non-security anomaly baseline
→ additional log anomaly experiments
```

```text
Syscall Dataset Generator
→ synthetic syscall augmentation
→ extra syscall traces
```

```text
COMIDDS
→ поиск дополнительных datasets
→ расширение набора validation / test данных
```

---

# 6. Итоговая логика использования

## Основная идея

Host-side часть проекта не должна опираться на один датасет, потому что разные источники покрывают разные уровни поведения:

```text
ADFA IDS даёт классический HIDS baseline.
LID-DS 2021 учит модель syscall sequence modelling.
Maintainable Log Dataset добавляет enterprise multi-stage behavior.
LID-DS 2019 проверяет переносимость внутри syscall-family datasets.
LANL проверяет user / authentication behavior.
Windows Event Logs / OTRF проверяет применимость к SOC telemetry.
Unified Host + Network Dataset проверяет hybrid host + network fusion.
ISOT Cloud IDS проверяет cloud environment.
Dynamic Malware Analysis Dataset проверяет malware-driven host behavior.
HDFS / BGL используются только для anomaly experiments.
```

## Критическая логика

Для host-based intrusion detection существует много датасетов, но большинство из них покрывают только один тип данных:

- system calls;
- logs;
- authentication events;
- malware traces;
- cloud telemetry;
- network + host events.

Один host dataset редко покрывает полный сценарий атаки:

```text
process behavior
+ user behavior
+ enterprise logs
+ network correlation
+ cloud environment
+ malware-driven behavior
```

Поэтому для host-side части проекта лучше использовать **feature-level fusion**, а не пытаться механически объединять raw logs, syscalls и authentication events в один общий датасет.

---

# 7. Минимальная обязательная конфигурация

Для серьёзного host-side proposal минимальный набор должен быть таким:

| Приоритет | Датасет | Статус |
|---|---|---|
| 1 | ADFA IDS | обязательно |
| 2 | LID-DS 2021 | обязательно |
| 3 | Maintainable Log Dataset | обязательно |
| 4 | LID-DS 2019 | желательно |
| 5 | LANL Dataset | желательно |
| 6 | Unified Host + Network Dataset / LANL | желательно |
| 7 | Windows Event Log / OTRF Security Datasets | желательно |
| 8 | ISOT Cloud IDS Dataset | опционально |
| 9 | Dynamic Malware Analysis Dataset | опционально |
| 10 | HDFS / BGL Logs | только experiments |

## Минимально достаточный стек

```text
ADFA IDS
LID-DS 2021
Maintainable Log Dataset
```

Без этих трёх источников host-side часть проекта будет недостаточно обоснованной.

## Оптимальный стек для proposal

```text
ADFA IDS
LID-DS 2021
LID-DS 2019
LANL Dataset
Maintainable Log Dataset
Unified Host + Network Dataset / LANL
```

Этот стек покрывает baseline HIDS, sequence modelling, validation, user-host behavior, enterprise multi-stage behavior и hybrid validation.

## Продвинутый стек

```text
ISOT Cloud IDS Dataset
Dynamic Malware Analysis Dataset
Windows Event Logs / OTRF
HDFS / BGL Logs
```

Этот стек усиливает cloud validation, malware behavior validation, SOC-style применимость и дополнительные anomaly experiments.

---

# 8. Краткий вывод

## Обязательные

1. **ADFA IDS** — baseline HIDS training и сравнимость с классическими research-подходами.
2. **LID-DS 2021** — основное syscall sequence modelling обучение.
3. **Maintainable Log Dataset** — enterprise log behavior и multi-stage attack modelling.

## Желательные

4. **LID-DS 2019** — cross-version validation на CVE-based атаках.
5. **LANL Dataset** — user / authentication behavior и lateral movement patterns.
6. **Windows Event Log / OTRF Security Datasets** — SOC-style validation.
7. **Unified Host + Network Dataset / LANL** — hybrid host + network validation.

## Дополнительные

8. **ISOT Cloud IDS Dataset** — cloud environment validation.
9. **Dynamic Malware Analysis Dataset** — malware-driven host behavior.
10. **HDFS / BGL Logs** — дополнительные log anomaly experiments.

## Финальная схема

```text
TRAIN:
- ADFA IDS
- LID-DS 2021
- Maintainable Log Dataset

VALIDATION:
- LID-DS 2019
- LANL Dataset
- Windows Event Logs / OTRF

TEST:
- Unified Host + Network Dataset / LANL
- ISOT Cloud IDS Dataset
- Dynamic Malware Analysis Dataset

EXPERIMENTS:
- HDFS Log Dataset
- BGL Logs
- Syscall Dataset Generator
- COMIDDS
```

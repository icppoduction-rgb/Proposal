# Анализ датасетов для Host-Based Intrusion Detection

## 1. Назначение документа

Документ систематизирует датасеты, которые можно использовать для разработки, обучения, валидации и тестирования host-side части IDS / hybrid IDS проекта.

Основной фокус:

- host-based intrusion detection;
- syscall-level sequence modelling;
- enterprise behavioral modelling;
- user / host behavior analytics;
- hybrid host + network validation;
- SOC-style telemetry validation.

---

## 2. Ключевой вывод

Для сильного proposal недостаточно одного host-based датасета.

Большинство доступных источников покрывают только один уровень поведения:

| Уровень | Что покрывает | Ограничение |
|---|---|---|
| System calls | Низкоуровневое поведение процессов | Слабо отражает user / enterprise context |
| Authentication logs | Поведение пользователей и хостов | Не показывает process-level активность |
| Enterprise logs | Multi-stage поведение в инфраструктуре | Требует feature engineering |
| Windows / Sysmon logs | SOC-style события | Часто зависит от конкретной конфигурации логирования |
| Host + Network telemetry | Hybrid IDS сценарии | Редкие и сложные для унификации |

**Оптимальная стратегия:** использовать стек датасетов и применять feature-level fusion, а не пытаться механически объединить raw syscalls, logs и authentication events в один общий датасет.

---

## 3. Рекомендуемый стек датасетов

### Минимально достаточный стек

| Датасет | Роль | Почему нужен |
|---|---|---|
| ADFA IDS | Baseline HIDS training | Даёт классическую benchmark-базу для сравнения |
| LID-DS 2021 | Sequence modelling | Основной датасет для syscall sequence models |
| Maintainable Log Dataset | Enterprise behavior modelling | Добавляет multi-stage log-level поведение |

Без этих трёх источников host-side часть проекта будет слабо обоснована.

### Оптимальный стек для proposal

| Этап | Датасеты | Назначение |
|---|---|---|
| Train | ADFA IDS, LID-DS 2021, Maintainable Log Dataset | Baseline, syscall sequence modelling, enterprise behavior modelling |
| Validation | LID-DS 2019, LANL, Windows Event Logs / OTRF | Cross-version validation, user-host behavior, SOC telemetry |
| Test | Unified Host + Network Dataset, ISOT Cloud IDS, Dynamic Malware Analysis Dataset | Hybrid IDS, cloud validation, malware-driven behavior |

### Продвинутый стек

| Датасет | Назначение |
|---|---|
| ISOT Cloud IDS | Проверка cloud-сценариев |
| Dynamic Malware Analysis Dataset | Расширение на malware-driven host behavior |
| Windows Event Logs / OTRF | SOC-level validation |
| HDFS / BGL | Дополнительные anomaly detection эксперименты |
| Syscall Dataset Generator | Synthetic syscall augmentation |
| COMIDDS | Поиск дополнительных host intrusion datasets |

---

## 4. Детальный анализ датасетов

## 4.1 ADFA IDS

**Роль:** основной baseline dataset для HIDS  
**Ссылка:** <https://research.unsw.edu.au/projects/adfa-ids-datasets>

### Описание

ADFA IDS — классический benchmark для Host Intrusion Detection Systems.

### Тип данных

- Linux system calls;
- Windows system calls;
- normal traces;
- attack traces.

### Для чего использовать

- baseline-обучение;
- первичная проверка модели;
- сравнение с существующими research-подходами.

### Подходящие модели

| Тип модели | Примеры |
|---|---|
| Classical ML | Random Forest, XGBoost |
| Deep Learning | LSTM, CNN |
| Sequence modelling | System call sequence models |

### Почему важен

ADFA является одним из стандартных источников для HIDS. Без него сложнее обосновать baseline и сопоставимость результатов с существующими исследованиями.

---

## 4.2 LID-DS 2021

**Роль:** основной sequence dataset для host-based detection  
**Ссылка:** <https://github.com/LID-DS/LID-DS>

### Описание

Современный Linux-based intrusion detection dataset на основе system calls и attack scenarios.

### Тип данных

- system calls;
- attack scenarios;
- normal behavior;
- labelled traces.

### Для чего использовать

- основное обучение sequence-моделей;
- моделирование поведения во времени;
- обучение LSTM / GRU / Transformer-based моделей.

### Подходящие модели

- LSTM;
- GRU;
- CNN-LSTM;
- Transformer-based sequence models.

### Почему критичен

LID-DS 2021 лучше подходит для temporal behavior modelling, чем простые табличные host logs. Это ключевой датасет для LSTM / sequence modelling части проекта.

---

## 4.3 LID-DS 2019

**Роль:** validation dataset для CVE-based атак  
**Ссылка:** <https://fkie-cad.github.io/COMIDDS/content/datasets/lids_ds_2019/>

### Описание

Содержит CVE-based attack scenarios, system calls и syscall parameters.

### Тип данных

- system calls;
- syscall parameters;
- labelled attacks;
- benign traces.

### Для чего использовать

- validation;
- проверка устойчивости модели на другом поколении LID-DS;
- cross-dataset validation внутри одного семейства host-based datasets.

### Что проверять

- переносимость модели между LID-DS 2021 и LID-DS 2019;
- отсутствие переобучения на конкретные attack traces;
- качество syscall-level признаков.

---

## 4.4 Maintainable Log Dataset

**Роль:** multi-stage enterprise behavior dataset  
**Ссылка:** <https://arxiv.org/abs/2203.08580>

### Описание

Dataset с enterprise logs и multi-stage атаками, смоделированными через state machines.

### Тип данных

- system logs;
- enterprise logs;
- 20 типов логов;
- multi-stage attack behavior.

### Для чего использовать

- behavioral modelling;
- detection multi-stage атак;
- log-level anomaly detection;
- temporal pattern detection;
- feature-level fusion.

### Почему критичен

System calls дают низкоуровневое представление процесса, но не всегда отражают enterprise attack flow. Maintainable Log Dataset помогает показать, что проект работает не только на syscall-level, но и на уровне enterprise behavior.

---

## 4.5 LANL Dataset

**Роль:** enterprise authentication behavior dataset  
**Ссылка:** <https://github.com/trenton3983/Cybersecurity-Datasets>

### Описание

Los Alamos National Lab dataset содержит enterprise authentication logs и user-computer events.

### Тип данных

- authentication logs;
- user-computer events;
- multi-day activity;
- enterprise behavior.

### Для чего использовать

- user behavior modelling;
- host behavior modelling;
- detection abnormal login behavior;
- анализ long-term behavioral deviations.

### Что проверять

- lateral movement patterns;
- abnormal login behavior;
- user-host interaction anomalies;
- long-term deviations.

### Почему важен

LANL закрывает ограничение syscall datasets: они хорошо описывают процессы, но слабо отражают поведение пользователей и инфраструктуры.

---

## 4.6 Unified Host + Network Dataset / LANL

**Роль:** hybrid validation dataset  
**Ссылка:** <https://github.com/trenton3983/Cybersecurity-Datasets>

### Описание

Редкий dataset, объединяющий host logs и network-level данные.

### Тип данных

- host events;
- network events;
- authentication activity;
- multi-source telemetry.

### Для чего использовать

- проверка hybrid IDS подхода;
- feature-level fusion;
- multi-source telemetry validation.

### Что проверять

- усиливают ли host-level признаки network-level detection;
- можно ли объединить host telemetry и network telemetry;
- устойчива ли модель при multi-source input.

### Почему критичен

Для proposal с hybrid IDS / exfiltration detection этот датасет особенно важен, потому что он ближе к реальной SOC-архитектуре.

---

## 4.7 ISOT Cloud IDS Dataset

**Роль:** cloud environment validation  
**Ссылка:** <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php>

### Описание

Dataset из cloud environment с system logs, syscalls и performance metrics.

### Тип данных

- system logs;
- syscalls;
- cloud performance metrics;
- cloud activity traces.

### Для чего использовать

- проверка модели в cloud-среде;
- оценка переносимости на cloud infrastructure;
- проверка устойчивости к cloud workloads.

### Почему важен

Если проект заявляет применимость не только к локальным машинам, но и к современной инфраструктуре, cloud dataset усиливает аргументацию.

---

## 4.8 Dynamic Malware Analysis Dataset

**Роль:** malware behavior extension  
**Ссылка:** <https://zenodo.org/record/1203289>

### Описание

Dataset для анализа поведения malware через kernel calls и user-level activity.

### Тип данных

- kernel calls;
- user-level activity;
- malware behavior traces.

### Для чего использовать

- расширение модели на malware-driven host behavior;
- анализ suspicious process behavior;
- проверка признаков exfiltration-related activity.

### Почему важен

DNS exfiltration часто связан с malware или post-exploitation activity. Этот датасет помогает связать host behavior с потенциальной exfiltration-логикой.

---

## 4.9 Windows Event Log / OTRF Security Datasets

**Роль:** SOC-level validation  
**Ссылка:** <https://github.com/OTRF/Security-Datasets>

### Описание

Набор Windows security logs, часто включающий Sysmon-based telemetry.

### Тип данных

- Windows Event Logs;
- Sysmon events;
- process activity;
- security events.

### Для чего использовать

- проверка модели на SOC-style данных;
- анализ Windows host behavior;
- event-based anomaly detection.

### Что проверять

- process creation events;
- suspicious parent-child process chains;
- event-based anomaly detection;
- применимость к реальным security operations.

### Почему важен

ADFA и LID-DS в основном ориентированы на syscall-level detection. Windows Event Logs добавляют практическую SOC-перспективу.

---

## 4.10 HDFS Log Dataset

**Роль:** anomaly detection baseline  
**Ссылка:** <https://github.com/logpai/loghub>

### Описание

Классический log anomaly detection dataset.

### Тип данных

- system logs;
- structured log sequences;
- anomaly labels.

### Для чего использовать

- дополнительные log anomaly detection эксперименты;
- сравнение методов последовательностного анализа логов;
- проверка general-purpose anomaly detection подходов.

### Ограничение

HDFS не является security-focused dataset. Он полезен как дополнительный baseline, но не должен быть основным источником для host intrusion detection.

---

## 5. Классификация по типу данных

| Тип данных | Датасеты | Основная роль |
|---|---|---|
| System Calls | ADFA IDS | Baseline HIDS |
| System Calls + Parameters | LID-DS 2019 / 2021 | Sequence modelling |
| Enterprise Logs | Maintainable Log Dataset | Behavioral modelling |
| Authentication Logs | LANL | User / host behavior |
| Host + Network | Unified LANL | Hybrid validation |
| Cloud Logs / Syscalls | ISOT Cloud IDS | Cloud validation |
| Malware Behavior | Dynamic Malware Analysis Dataset | Malware extension |
| Windows Logs | OTRF Security Datasets | SOC validation |
| Generic Logs | HDFS / BGL | Anomaly experiments |

---

## 6. Роли датасетов по этапам ML pipeline

## Train

| Датасет | Назначение |
|---|---|
| ADFA IDS | Baseline normal / attack host traces |
| LID-DS 2021 | Syscall sequence modelling |
| Maintainable Log Dataset | Enterprise log behavior modelling |

## Validation

| Датасет | Назначение |
|---|---|
| LID-DS 2019 | Проверка на CVE-based атаках |
| LANL | Проверка user-host behavior |
| Windows Event Logs / OTRF | Проверка применимости к SOC telemetry |

## Test

| Датасет | Назначение |
|---|---|
| Unified Host + Network Dataset | Проверка hybrid IDS |
| ISOT Cloud IDS | Проверка cloud-среды |
| Dynamic Malware Analysis Dataset | Проверка malware-driven host behavior |

## Experiments

| Датасет / источник | Назначение |
|---|---|
| HDFS Log Dataset | Log anomaly detection experiments |
| BGL logs | Non-security anomaly baseline |
| Syscall Dataset Generator | Synthetic syscall augmentation |
| COMIDDS | Поиск дополнительных datasets |

---

## 7. Рекомендуемая архитектура экспериментов

### 7.1 Baseline stage

Использовать ADFA IDS для первичного HIDS baseline:

- classical ML baseline;
- syscall frequency features;
- sequence-based baseline;
- comparison with existing research.

### 7.2 Sequence modelling stage

Использовать LID-DS 2021 как основной источник для temporal models:

- LSTM;
- GRU;
- CNN-LSTM;
- Transformer-based sequence modelling.

Затем валидировать на LID-DS 2019, чтобы проверить переносимость между версиями и сценариями атак.

### 7.3 Enterprise behavior stage

Использовать Maintainable Log Dataset и LANL:

- user-host behavior modelling;
- authentication anomaly detection;
- lateral movement detection;
- temporal behavioral deviations.

### 7.4 SOC telemetry stage

Использовать Windows Event Logs / OTRF:

- process creation analysis;
- parent-child process chain detection;
- Sysmon-like event modelling;
- event-based anomaly detection.

### 7.5 Hybrid validation stage

Использовать Unified Host + Network Dataset:

- host + network feature fusion;
- проверка вклада host telemetry;
- hybrid IDS validation;
- exfiltration-related detection logic.

---

## 8. Практическая рекомендация для proposal

### Основная формулировка

Для host-side части проекта рекомендуется использовать multi-dataset evaluation framework.

Он должен включать:

1. **ADFA IDS** — baseline host intrusion detection.
2. **LID-DS 2021** — основное sequence modelling обучение.
3. **LID-DS 2019** — cross-dataset validation.
4. **Maintainable Log Dataset** — enterprise multi-stage behavior.
5. **LANL** — user / authentication behavior.
6. **Windows Event Logs / OTRF** — SOC-style validation.
7. **Unified Host + Network Dataset** — hybrid validation.
8. **ISOT Cloud IDS** — cloud environment validation.
9. **Dynamic Malware Analysis Dataset** — malware-driven behavior extension.

### Почему это сильнее одного датасета

Один датасет не покрывает полный сценарий атаки:

```text
process behavior + user behavior + enterprise logs + network correlation
```

Поэтому проект должен быть построен вокруг нескольких источников данных и feature-level fusion.

---

## 9. Итоговая матрица приоритетов

| Приоритет | Датасет | Статус | Обоснование |
|---|---|---|---|
| Must-have | ADFA IDS | Train | Классический HIDS baseline |
| Must-have | LID-DS 2021 | Train | Основной syscall sequence dataset |
| Must-have | Maintainable Log Dataset | Train | Enterprise multi-stage behavior |
| High | LID-DS 2019 | Validation | Cross-version CVE-based validation |
| High | LANL | Validation | User / host behavior analytics |
| High | Windows Event Logs / OTRF | Validation | SOC-style host telemetry |
| High | Unified Host + Network Dataset | Test | Hybrid host + network evaluation |
| Medium | ISOT Cloud IDS | Test | Cloud workload validation |
| Medium | Dynamic Malware Analysis Dataset | Test | Malware behavior extension |
| Low / Experimental | HDFS / BGL | Experiments | Generic log anomaly baseline |

---

## 10. Финальный вывод

Для убедительного host-side proposal нужен не один универсальный датасет, а стек источников, каждый из которых закрывает отдельный слой поведения.

Рекомендуемая логика:

```text
ADFA + LID-DS
→ low-level host behavior

LANL
→ user / authentication behavior

Maintainable Log Dataset
→ enterprise multi-stage behavior

Windows Event Logs / OTRF
→ SOC-style host telemetry

Unified Host + Network Dataset
→ hybrid IDS validation
```

Главная методологическая рекомендация:

> Использовать feature-level fusion между источниками данных, а не объединять raw syscalls, logs и authentication events напрямую.

Такой подход делает proposal более реалистичным, исследовательски обоснованным и ближе к реальной SOC / enterprise IDS архитектуре.

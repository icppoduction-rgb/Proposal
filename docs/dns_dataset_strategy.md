# DNS Dataset Strategy для проекта обнаружения DNS Exfiltration и Tunneling

## 1. Назначение документа

Документ фиксирует набор датасетов для обучения, валидации, тестирования и экспериментов в проекте по обнаружению DNS data exfiltration и DNS tunneling.

Основная цель — не смешивать роли датасетов и использовать каждый набор данных по назначению:

- **TRAIN** — обучение модели на атаках и нормальном трафике.
- **VALIDATION** — контроль качества и ложных срабатываний.
- **TEST** — финальная проверка обобщающей способности модели.
- **EXPERIMENTS** — быстрые эксперименты, прототипирование и feature engineering.

---

# 2. Обязательные датасеты

## 🥇 1. CIC-Bell-DNS-EXF-2021

### Роль

**Основной датасет для обучения атакующего поведения.**

### Ссылка

<https://www.unb.ca/cic/datasets/dns-exf-2021.html>

### Факт

CIC-Bell-DNS-EXF-2021 специально создан для обнаружения:

- DNS data exfiltration;
- DNS tunneling;
- light attack scenarios;
- heavy attack scenarios.

### Содержит

- benign traffic;
- light attacks;
- heavy attacks;
- stateful признаки;
- stateless признаки;
- временные признаки, пригодные для sequence modeling.

### Для чего нужен

Используется как **core training dataset** для обучения модели обнаруживать DNS exfiltration и tunneling.

### Подходящие модели

| Тип модели | Применение |
|---|---|
| Random Forest | базовая ML-модель |
| XGBoost | сильный baseline для табличных признаков |
| CNN | анализ локальных паттернов признаков |
| LSTM | анализ временных окон и последовательностей |

### Почему критичен

Это ключевой датасет, потому что он:

- прямо моделирует DNS exfiltration scenarios;
- содержит разные уровни атак;
- поддерживает sequence modeling;
- подходит для LSTM за счёт time-window признаков.

### Использование в проекте

```text
TRAIN:
- attack class
- DNS exfiltration
- DNS tunneling
```

---

## 🥈 2. BCCC-CIC-Bell-DNS-2024

### Роль

**Финальная проверка модели и research-level benchmark.**

### Ссылка

<https://www.yorku.ca/research/bccc/>

### Факт

BCCC-CIC-Bell-DNS-2024 объединяет данные из:

- DNS-2021;
- EXF-2021.

Также добавляет расширенное пространство признаков и дополнительные типы атак.

### Содержит

- 6 типов атак;
- flow-based признаки;
- application-level признаки;
- 120 признаков;
- расширенный feature space.

### Для чего нужен

Используется для финального тестирования модели:

- проверка generalization;
- проверка устойчивости к новым данным;
- проверка работы на разных типах атак;
- выявление переобучения.

### Почему важен

Это наиболее современный и сложный датасет из списка. Его целесообразно использовать не для основного обучения, а как независимый тестовый benchmark.

### Использование в проекте

```text
TEST:
- final evaluation
- generalization check
- overfitting check
```

---

## 🥉 3. CIC-Bell-DNS-2021

### Роль

**Baseline нормального DNS-трафика и контроль ложных срабатываний.**

### Ссылка

<https://www.unb.ca/cic/datasets/dns-2021.html>

### Факт

CIC-Bell-DNS-2021 содержит около 1 млн доменов, при этом примерно 99% данных относятся к benign traffic.

### Содержит

- benign traffic;
- phishing;
- malware;
- spam;
- реалистичное распределение интернет-трафика.

### Для чего нужен

Датасет нужен для формирования понимания нормального поведения DNS-трафика.

Основные задачи:

- baseline нормального поведения;
- обучение benign class;
- контроль false positives;
- балансировка обучающей выборки;
- добавление real-world benign traffic.

### Почему важен

Без CIC-Bell-DNS-2021 модель будет слишком сильно ориентирована на атаки. Это приведёт к большому числу ложных срабатываний на реальном DNS-трафике.

### Использование в проекте

```text
TRAIN:
- benign class

VALIDATION:
- false positive control
- normal traffic behavior check
```

---

# 3. Дополнительные датасеты

## 🟡 4. Mendeley DNS Exfiltration Dataset

### Роль

**Проверка реалистичности и robustness.**

### Ссылка

<https://data.mendeley.com/datasets/c4n7fckkz3/3>

### Факт

Датасет содержит DNS exfiltration traffic и ближе к реальным условиям по сравнению с лабораторными наборами данных.

### Для чего нужен

Используется для проверки устойчивости модели к новым данным.

Основной сценарий:

```text
TRAIN:
- CIC datasets

TEST:
- Mendeley DNS Exfiltration Dataset
```

### Проверяет

- переносимость модели;
- устойчивость к новым паттернам;
- способность работать вне лабораторных условий;
- качество cross-dataset validation.

### Почему важен

Mendeley DNS Exfiltration Dataset показывает, насколько модель применима к данным, которые отличаются от обучающего распределения.

---

## 🟡 5. Kaggle DNS Tunneling Dataset

### Роль

**Быстрые эксперименты и прототипирование.**

### Ссылка

<https://www.kaggle.com/datasets/daumel/dns-tunneling-dataset>

### Факт

Датасет является синтетическим и содержит DNS tunneling traffic, сгенерированный несколькими tunneling-инструментами.

### Для чего нужен

Подходит для:

- быстрых экспериментов;
- feature engineering;
- первичного прототипирования;
- data augmentation;
- проверки идей до запуска на основных датасетах.

### Ограничение

Датасет синтетический, поэтому его результаты хуже переносятся на real-world traffic. Его не стоит использовать как главный источник истины для оценки качества модели.

### Использование в проекте

```text
EXPERIMENTS:
- quick tests
- feature engineering
- augmentation
```

---

# 4. Правильное распределение ролей

| Этап | Датасет | Назначение |
|---|---|---|
| TRAIN | CIC-Bell-DNS-EXF-2021 | обучение на attack class |
| TRAIN | CIC-Bell-DNS-2021 | обучение на benign class |
| VALIDATION | часть CIC-Bell-DNS-2021 | контроль false positives |
| TEST | BCCC-CIC-Bell-DNS-2024 | финальная проверка и generalization |
| TEST | Mendeley DNS Exfiltration Dataset | проверка реалистичности |
| EXPERIMENTS | Kaggle DNS Tunneling Dataset | быстрые эксперименты |

---

# 5. Правильная схема обучения

## TRAIN

```text
CIC-Bell-DNS-EXF-2021
→ attack class
→ DNS exfiltration
→ DNS tunneling
```

```text
CIC-Bell-DNS-2021
→ benign class
→ real-world normal DNS traffic
```

## VALIDATION

```text
Часть CIC-Bell-DNS-2021
→ validation split
→ false positives control
→ threshold tuning
```

## TEST

```text
BCCC-CIC-Bell-DNS-2024
→ final benchmark
→ generalization test
→ robustness against multiple attack types
```

```text
Mendeley DNS Exfiltration Dataset
→ cross-dataset validation
→ real-world pattern check
```

## EXPERIMENTS

```text
Kaggle DNS Tunneling Dataset
→ prototype
→ feature engineering
→ quick model comparison
```

---

# 6. Итоговая логика использования

## Основная идея

Модель должна учиться не только распознавать атаки, но и понимать нормальное поведение DNS-трафика.

Поэтому обучение строится так:

```text
EXF-2021 учит модель видеть атаки.
DNS-2021 учит модель понимать нормальный DNS-трафик.
BCCC-2024 проверяет, не переобучилась ли модель.
Mendeley проверяет применимость к более реалистичным данным.
Kaggle используется только для быстрых экспериментов.
```

---

# 7. Минимальная обязательная конфигурация

Для серьёзного проекта минимальный набор должен быть таким:

| Приоритет | Датасет | Статус |
|---|---|---|
| 1 | CIC-Bell-DNS-EXF-2021 | обязательно |
| 2 | CIC-Bell-DNS-2021 | обязательно |
| 3 | BCCC-CIC-Bell-DNS-2024 | обязательно |
| 4 | Mendeley DNS Exfiltration Dataset | желательно |
| 5 | Kaggle DNS Tunneling Dataset | опционально |

---

# 8. Краткий вывод

## Обязательные

1. **CIC-Bell-DNS-EXF-2021** — основное обучение атак.
2. **CIC-Bell-DNS-2021** — нормальный DNS-трафик и false positives.
3. **BCCC-CIC-Bell-DNS-2024** — финальный benchmark.

## Дополнительные

4. **Mendeley DNS Exfiltration Dataset** — реалистичность и cross-dataset validation.
5. **Kaggle DNS Tunneling Dataset** — быстрые эксперименты и augmentation.

## Финальная схема

```text
TRAIN:
- EXF-2021
- DNS-2021

VALIDATION:
- DNS-2021 split

TEST:
- BCCC-2024
- Mendeley DNS

EXPERIMENTS:
- Kaggle DNS
```

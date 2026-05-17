# Архитектура проекта: Behaviour-Driven Hybrid Learning для обнаружения утечки данных

> **Версия документа:** 1.0  
> **Дата:** 2026-05-17  
> **Проект:** Data Exfiltration Detection — ML Training Framework

---

## Содержание

1. [Обзор проекта](#1-обзор-проекта)
2. [Анализ датасетов](#2-анализ-датасетов)
3. [Архитектура системы](#3-архитектура-системы)
4. [Структура папок и файлов](#4-структура-папок-и-файлов)
5. [Компоненты системы](#5-компоненты-системы)
   - [5.1 Менеджер проекта — `manage.py`](#51-менеджер-проекта--managepy)
   - [5.2 Нормализация — `normalization/`](#52-нормализация--normalization)
   - [5.3 Обучение — `train/`](#53-обучение--train)
   - [5.4 Модели — `models/`](#54-модели--models)
6. [База данных — выбор и обоснование](#6-база-данных--выбор-и-обоснование)
7. [Многопоточность и асинхронность](#7-многопоточность-и-асинхронность)
8. [CLI — интерфейс командной строки](#8-cli--интерфейс-командной-строки)
9. [Процесс обучения в CLI](#9-процесс-обучения-в-cli)
10. [Поток данных — End-to-End](#10-поток-данных--end-to-end)
11. [ООП и принципы проектирования](#11-ооп-и-принципы-проектирования)
12. [Ответы на вопросы](#12-ответы-на-вопросы)

---

## 1. Обзор проекта

Проект реализует **гибридный ML/DL-фреймворк** для обнаружения эксфильтрации данных (data exfiltration detection). Система обучает ансамблевые и глубокие модели на двух типах телеметрии — сетевой (DNS) и хостовой (системные логи, системные вызовы) — и объединяет их предсказания через механизм late fusion.

### Ключевые компоненты модели

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID DETECTION FRAMEWORK                  │
├───────────────────┬────────────────────┬────────────────────────┤
│  Ensemble Layer   │   Deep Learning    │  Sequence Modelling    │
│  ─────────────── │  ──────────────── │  ────────────────────  │
│  Random Forest    │  CNN               │  LSTM                  │
│  XGBoost          │  (local patterns)  │  (temporal behavior)   │
│  (structured)     │                    │                        │
├───────────────────┴────────────────────┴────────────────────────┤
│                    LATE FUSION (вероятностная агрегация)        │
├─────────────────────────────────────────────────────────────────┤
│                    SHAP Explainability Layer                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Анализ датасетов

### 2.1 DNS-датасеты

**Источники:** CIC-Bell-DNS-EXF-2021, Mendeley-DNS-Exfiltration-Dataset

| Разбивка     | Файлов | Описание                                              |
|:-------------|:------:|:------------------------------------------------------|
| `TRAIN`      | 27     | Обучающие данные: benign + атаки (malware, phishing, spam, exfil) |
| `TEST`       | 1      | Тестовый датасет Mendeley (~8.25 GB, 10M+ записей)   |
| `VALIDATION` | 4      | PCAP-файлы DNS amplification attack + benign          |

#### Признаки (features)

**Stateful-признаки** (агрегированные по сессии, 27 столбцов):

| Группа признаков       | Примеры                                                            |
|:-----------------------|:-------------------------------------------------------------------|
| RR-частоты             | `A_frequency`, `NS_frequency`, `CNAME_frequency`, `MX_frequency`, `TXT_frequency`, `AAAA_frequency` |
| Энтропия имени         | `rr_name_entropy`, `rr_name_length`                               |
| Разнообразие           | `distinct_ns`, `distinct_ip`, `unique_country`, `unique_asn`, `distinct_domains` |
| TTL-статистика         | `unique_ttl`, `ttl_mean`, `ttl_variance`                          |
| Другое                 | `rr_type`, `rr_count`, `reverse_dns`, `a_records`                |

**Stateless-признаки** (пакетный уровень, 15 столбцов):

| Признак             | Описание                                           |
|:--------------------|:---------------------------------------------------|
| `timestamp`         | Временная метка запроса                            |
| `FQDN_count`        | Количество уникальных FQDN за период               |
| `subdomain_length`  | Длина субдомена                                    |
| `entropy`           | Энтропия Шеннона имени домена                      |
| `upper/lower/numeric` | Распределение символов                           |
| `labels`, `labels_max`, `labels_average` | Статистика DNS-меток            |
| `longest_word`      | Длина самого длинного слова                        |
| `sld`, `len`        | Second-Level Domain, общая длина                  |

**Классы DNS:**

```
benign                →  нормальный трафик
malware               →  DNS с малварью
phishing              →  фишинговые домены
spam                  →  спам-домены
exfiltration (audio, compressed, exe, image, text, video)  →  DNS-туннелинг по типу данных
```

---

### 2.2 Host-датасеты

**Источники:** ADFA IDS, LID-DS 2021, Maintainable Log Dataset

| Датасет                   | Файлов  | Размер    | Тип данных                              |
|:--------------------------|:-------:|:---------:|:----------------------------------------|
| ADFA IDS                  | 70,083  | 2.36 GB   | Последовательности системных вызовов    |
| LID-DS 2021               | 4,588   | 1.47 GB   | Системные вызовы + аномалии             |
| Maintainable Log Dataset  | 12,021  | 1.14 GB   | Системные логи, события                 |

**Формат данных хоста:**

```
{adjective}_{name}_{number}__{hash}.json
Пример: abundant_knuth_3979__5070f806466c.json
```

Каждый файл — JSON-обёртка над CSV/JSONL/binary/text данными с метаданными:  
`type`, `encoding`, `rows`, `columns`, `content[]`

---

## 3. Архитектура системы

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              manage.py (CLI Entry Point)                     │
│                   normalize | train | evaluate | export | info               │
└───────────┬──────────────────────────┬───────────────────────────────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────┐   ┌──────────────────────────────────────────────────┐
│   normalization/      │   │                   train/                         │
│   ─────────────────   │   │  ────────────────────────────────────────────    │
│  DNSNormalizer        │──▶│  TrainPipeline                                   │
│  HostNormalizer       │   │    │                                             │
│  FeatureEngineer      │   │    ├── EnsembleTrainer (RF, XGBoost)             │
│  SequenceBuilder      │   │    ├── CNNTrainer                                │
│  DataValidator        │   │    ├── LSTMTrainer                               │
└───────────┬───────────┘   │    ├── FusionLayer (late fusion)                 │
            │               │    └── SHAPExplainer                             │
            ▼               └────────────────────┬─────────────────────────────┘
┌───────────────────────┐                        │
│      DuckDB           │◀───────────────────────┘
│  ─────────────────    │
│  dns_features         │──────────────────────────────────┐
│  host_features        │                                  │
│  sequences            │                     ┌────────────▼──────────────┐
│  metadata             │                     │       models/             │
│  experiments          │                     │       ────────────────    │
└───────────────────────┘                     │       v1/                 │
                                              │       v2/                 │
                                              │       vN/                 │
                                              └───────────────────────────┘
```

---

## 4. Структура папок и файлов

```
Proposal/
│
├── .env                              # Конфигурация окружения (DB, пути, гиперпараметры)
├── manage.py                         # CLI-точка входа, управление всеми командами
│
├── normalization/                    # Нормализация и подготовка датасетов
│   ├── __init__.py
│   ├── base.py                       # Базовый класс BaseNormalizer
│   ├── dns_normalizer.py             # Нормализация DNS-датасетов
│   ├── host_normalizer.py            # Нормализация Host-датасетов
│   ├── feature_engineer.py           # Извлечение и инженерия признаков
│   ├── sequence_builder.py           # Построение временных последовательностей для LSTM
│   ├── data_validator.py             # Валидация качества данных
│   └── db_writer.py                  # Запись нормализованных данных в DuckDB
│
├── train/                            # Обучение моделей
│   ├── __init__.py
│   ├── pipeline.py                   # Основной TrainPipeline — оркестратор
│   ├── trainers/
│   │   ├── __init__.py
│   │   ├── base_trainer.py           # Абстрактный BaseTrainer
│   │   ├── ensemble_trainer.py       # Random Forest + XGBoost
│   │   ├── cnn_trainer.py            # CNN (локальные паттерны признаков)
│   │   └── lstm_trainer.py           # LSTM (последовательности поведения)
│   ├── fusion/
│   │   ├── __init__.py
│   │   └── late_fusion.py            # Агрегация вероятностей предсказаний
│   ├── explainability/
│   │   ├── __init__.py
│   │   └── shap_explainer.py         # SHAP-объяснимость для всех моделей
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── metrics.py                # Accuracy, Precision, Recall, F1, AUC, FPR
│   └── utils/
│       ├── __init__.py
│       ├── progress.py               # Rich-прогресс-бары и красивый CLI-вывод
│       ├── data_loader.py            # Загрузка данных из DuckDB / Parquet
│       └── checkpoint.py             # Сохранение и восстановление чекпоинтов
│
├── models/                           # Сохранённые обученные модели по версиям
│   ├── v1/
│   │   ├── random_forest.joblib
│   │   ├── xgboost.json
│   │   ├── cnn.pt
│   │   ├── lstm.pt
│   │   ├── fusion_weights.json
│   │   └── metadata.json             # Метаданные: датасет, метрики, гиперпараметры
│   ├── v2/
│   │   └── ...
│   └── vN/
│       └── ...
│
└── datasets-new/                     # Исходные датасеты (только чтение)
    ├── dns/
    │   ├── TRAIN/
    │   ├── TEST/
    │   └── VALIDATION/
    └── host/
        ├── TRAIN/
        ├── TEST/
        └── VALIDATION/
```

---

## 5. Компоненты системы

### 5.1 Менеджер проекта — `manage.py`

Единая точка входа для всех операций. Использует библиотеку **Click** для построения CLI-команд.

#### Доступные команды

```
python manage.py [КОМАНДА] [ОПЦИИ]

Команды:
  normalize   Нормализация и запись датасетов в БД
  train       Обучение моделей
  evaluate    Оценка обученной версии модели
  export      Экспорт модели в production-формат
  info        Информация о датасетах, моделях и БД
```

#### Примеры вызовов

```bash
# Нормализация всех датасетов
python manage.py normalize --source dns --split TRAIN --workers 8

# Обучение полного hybrid-фреймворка
python manage.py train --version v1 --model all --epochs 50 --batch-size 256

# Обучение только LSTM на host-данных
python manage.py train --version v1 --model lstm --source host --epochs 100

# Оценка версии v1 на тестовом датасете
python manage.py evaluate --version v1 --split TEST --explain

# Просмотр информации о доступных моделях
python manage.py info --models

# Экспорт модели v1 в ONNX
python manage.py export --version v1 --format onnx
```

---

### 5.2 Нормализация — `normalization/`

#### Класс `BaseNormalizer` (абстрактный)

```
BaseNormalizer
│
├── load(path) → DataFrame        # Загрузка сырых данных
├── validate() → ValidationReport # Проверка качества
├── normalize() → DataFrame       # Нормализация признаков
├── encode_labels() → Series      # Кодирование меток классов
└── save(db) → None               # Сохранение в DuckDB
```

#### Класс `DNSNormalizer(BaseNormalizer)`

| Этап            | Действие                                                              |
|:----------------|:----------------------------------------------------------------------|
| Загрузка        | Чтение JSON-файлов из `datasets-new/dns/`                            |
| Stateful        | Нормализация 27 статистических DNS-признаков                          |
| Stateless       | Временные признаки, энтропия, распределение символов                  |
| PCAP            | Извлечение packet-level признаков из raw PCAP                        |
| Метки           | `benign=0`, `malware=1`, `phishing=2`, `spam=3`, `exfiltration=4`   |
| Балансировка    | SMOTE или class-weighted loss при дисбалансе классов                  |

#### Класс `HostNormalizer(BaseNormalizer)`

| Этап            | Действие                                                              |
|:----------------|:----------------------------------------------------------------------|
| Загрузка        | Чтение JSON-обёрток из `datasets-new/host/`                          |
| ADFA IDS        | Системные вызовы → числовые ID → нормализованные последовательности  |
| LID-DS 2021     | Событийные последовательности с временными метками                    |
| Maintainable    | Парсинг log-строк, извлечение структурированных признаков             |
| Метки           | `benign=0`, `attack=1`                                               |

#### Класс `SequenceBuilder`

Строит временны́е последовательности для LSTM с использованием скользящего окна:

```
Входные данные:   [e1, e2, e3, ..., eN]   (отсортированные по времени события)

Sliding Window (размер окна = 64 события, шаг = 16):

  Sequence_1:  [e1,  e2,  ..., e64]   → label: benign/attack
  Sequence_2:  [e17, e18, ..., e80]   → label: benign/attack
  ...
  Sequence_K:  [eM-63, ..., eM]       → label: benign/attack

Выход:  sequences.h5 (HDF5-файл) или DuckDB blob
```

---

### 5.3 Обучение — `train/`

#### `TrainPipeline` — главный оркестратор

Запускает полный цикл обучения: загрузка данных → обучение моделей → fusion → оценка → сохранение.

```
TrainPipeline.run()
│
├── 1. DataLoader.load_from_db(split=TRAIN)
│       └── Параллельная загрузка DNS + Host из DuckDB
│
├── 2. [Параллельно] 
│       ├── EnsembleTrainer.fit(X_tabular)
│       ├── CNNTrainer.fit(X_tabular)
│       └── LSTMTrainer.fit(X_sequences)
│
├── 3. LateFusion.combine(predictions_ensemble, predictions_cnn, predictions_lstm)
│
├── 4. MetricsEvaluator.compute(y_true, y_pred_fused)
│
├── 5. SHAPExplainer.explain(model, X_sample)
│
└── 6. ModelRegistry.save(version, models, metrics, metadata)
```

#### `EnsembleTrainer`

| Модель        | Библиотека    | Особенности                                       |
|:--------------|:--------------|:--------------------------------------------------|
| Random Forest | scikit-learn  | Параллельное обучение через `n_jobs=-1`           |
| XGBoost       | xgboost       | GPU-ускорение, ранняя остановка, class_weight    |

#### `CNNTrainer`

- **Вход:** нормализованные признаки в виде 1D-тензора или 2D-матрицы признаков
- **Архитектура:** Conv1D → BatchNorm → MaxPool → Dropout → Linear → Sigmoid/Softmax
- **Фреймворк:** PyTorch
- **Обучение:** Async DataLoader, автоматический mixed precision (AMP)

#### `LSTMTrainer`

- **Вход:** последовательности событий из `SequenceBuilder` (размер окна: 50–100 событий)
- **Архитектура:** Embedding → LSTM (2 слоя) → Attention → Linear → Sigmoid
- **Задача:** Binary classification (benign vs exfiltration) на уровне последовательности
- **Фреймворк:** PyTorch с Gradient Clipping

#### `LateFusion`

Агрегирует вероятности трёх моделей во взвешенное итоговое предсказание:

```
P_final = w1 * P_ensemble + w2 * P_cnn + w3 * P_lstm

где w1 + w2 + w3 = 1
    Начальные веса: w1=0.4, w2=0.3, w3=0.3
    Оптимизация весов: по F1-score на валидационном наборе
```

#### `SHAPExplainer`

| Модель        | Метод SHAP                    | Назначение                        |
|:--------------|:------------------------------|:----------------------------------|
| Random Forest | TreeExplainer                 | Быстрый, точный для деревьев      |
| XGBoost       | TreeExplainer                 | Нативная поддержка               |
| CNN           | DeepExplainer / GradientSHAP  | Градиентная аппроксимация        |
| LSTM          | KernelSHAP (агрегированный)   | Объяснение агрегированных признаков |

---

### 5.4 Модели — `models/`

Каждая версия модели хранится в отдельной папке и содержит:

```
models/v1/
├── random_forest.joblib       # Сериализованная RF-модель (joblib)
├── xgboost.json               # XGBoost в нативном JSON-формате
├── cnn.pt                     # PyTorch state_dict для CNN
├── lstm.pt                    # PyTorch state_dict для LSTM
├── fusion_weights.json        # Веса late fusion агрегации
├── feature_scaler.joblib      # StandardScaler / MinMaxScaler
├── label_encoder.joblib       # LabelEncoder для меток
├── shap_summary.png           # SHAP summary plot
└── metadata.json              # Метаданные версии
```

**Формат `metadata.json`:**

```json
{
  "version": "v1",
  "created_at": "2026-05-17T12:00:00Z",
  "datasets": ["CIC-Bell-DNS-EXF-2021", "ADFA-IDS", "LID-DS-2021"],
  "hyperparameters": {
    "rf_n_estimators": 200,
    "xgb_max_depth": 6,
    "cnn_epochs": 50,
    "lstm_epochs": 100,
    "lstm_window_size": 64,
    "lstm_hidden_size": 128
  },
  "metrics": {
    "accuracy": 0.962,
    "precision": 0.951,
    "recall": 0.944,
    "f1_score": 0.947,
    "auc": 0.981,
    "fpr": 0.031
  },
  "fusion_weights": {"ensemble": 0.42, "cnn": 0.31, "lstm": 0.27}
}
```

---

## 6. База данных — выбор и обоснование

### Вопрос: Какую базу данных использовать для нормализованных данных?

### Рекомендация: **DuckDB** (основное хранилище) + **HDF5** (для последовательностей)

---

### 6.1 DuckDB — для табличных признаков

**DuckDB** — это встроенная аналитическая СУБД (column-oriented), идеально подходящая для ML-пайплайнов.

#### Почему DuckDB, а не альтернативы?

| Критерий                   | DuckDB ✅         | SQLite ❌         | PostgreSQL ⚠️     | Parquet-файлы ⚠️ |
|:---------------------------|:-----------------|:-----------------|:------------------|:-----------------|
| Встроенная (без сервера)   | ✅ Да            | ✅ Да            | ❌ Требует сервер | ✅ Да             |
| Колоночное хранение        | ✅ Да            | ❌ Нет           | ⚠️ Частично       | ✅ Да             |
| Скорость аналит. запросов  | ✅ Очень быстро  | ❌ Медленно      | ✅ Быстро         | ✅ Быстро         |
| Нативный Pandas/Arrow      | ✅ Да            | ⚠️ Через pandas  | ⚠️ Через psycopg2 | ✅ Да             |
| SQL-запросы                | ✅ Полный SQL     | ✅ Полный SQL    | ✅ Полный SQL     | ❌ Нет            |
| Конкурентная запись        | ⚠️ Один writer   | ❌ Плохо         | ✅ Отлично        | ❌ Нет            |
| Настройка                  | ✅ Zero-config   | ✅ Zero-config   | ❌ Сервер/конфиг  | ✅ Нет настройки  |
| Поддержка Parquet/CSV      | ✅ Нативная      | ❌ Нет           | ❌ Нет            | ✅ Да             |

**DuckDB = скорость + SQL + zero-config + нативная интеграция с Pandas/PyArrow**

#### Схема таблиц DuckDB

```sql
-- Нормализованные DNS stateful-признаки
CREATE TABLE dns_stateful_features (
    id          BIGINT PRIMARY KEY,
    source_file VARCHAR,
    split       VARCHAR,          -- TRAIN / TEST / VALIDATION
    label       VARCHAR,          -- benign, malware, phishing, spam, exfiltration_*
    label_id    INTEGER,
    rr          FLOAT,
    A_frequency FLOAT,
    NS_frequency FLOAT,
    entropy     FLOAT,
    -- ... остальные 27 признаков
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Нормализованные DNS stateless-признаки (временны́е)
CREATE TABLE dns_stateless_features (
    id               BIGINT PRIMARY KEY,
    source_file      VARCHAR,
    split            VARCHAR,
    label            VARCHAR,
    label_id         INTEGER,
    timestamp        TIMESTAMP,
    FQDN_count       FLOAT,
    subdomain_length FLOAT,
    entropy          FLOAT,
    -- ... остальные признаки
);

-- Нормализованные Host-признаки
CREATE TABLE host_features (
    id          BIGINT PRIMARY KEY,
    source_file VARCHAR,
    dataset     VARCHAR,          -- ADFA-IDS, LID-DS-2021, Maintainable
    split       VARCHAR,
    label       VARCHAR,
    label_id    INTEGER,
    -- агрегированные признаки системных вызовов
    syscall_count     FLOAT,
    unique_syscalls   FLOAT,
    entropy           FLOAT,
    -- ...
);

-- Метаданные экспериментов
CREATE TABLE experiments (
    id          BIGINT PRIMARY KEY,
    version     VARCHAR,          -- v1, v2, ...
    started_at  TIMESTAMP,
    finished_at TIMESTAMP,
    status      VARCHAR,
    config      JSON,
    metrics     JSON
);
```

---

### 6.2 HDF5 — для временны́х последовательностей LSTM

Файлы `.h5` хранят последовательности событий, которые LSTM читает через `torch.utils.data.Dataset`. HDF5 поддерживает хранение многомерных массивов с быстрой случайной выборкой — идеально для `DataLoader`.

```
sequences/
├── dns_sequences_train.h5     # Shape: (N_sequences, window_size, n_features)
├── host_sequences_train.h5
├── dns_sequences_val.h5
└── host_sequences_val.h5
```

---

### 6.3 Итоговая стратегия хранения

```
┌─────────────────────────────────────────────────────────────┐
│                    СТРАТЕГИЯ ХРАНЕНИЯ ДАННЫХ                │
├─────────────────────────┬───────────────────────────────────┤
│  Тип данных             │  Хранилище                        │
├─────────────────────────┼───────────────────────────────────┤
│  Нормализованные        │  DuckDB                           │
│  табличные признаки     │  (dns_stateful, host_features)    │
├─────────────────────────┼───────────────────────────────────┤
│  Временные              │  DuckDB                           │
│  stateless-признаки     │  (dns_stateless)                  │
├─────────────────────────┼───────────────────────────────────┤
│  LSTM-последовательности│  HDF5 (.h5)                       │
│  (sliding window)       │  (sequences/)                     │
├─────────────────────────┼───────────────────────────────────┤
│  Метаданные и логи      │  DuckDB                           │
│  экспериментов          │  (experiments)                    │
├─────────────────────────┼───────────────────────────────────┤
│  Сохранённые модели     │  Файловая система                 │
│                         │  (models/vN/)                     │
└─────────────────────────┴───────────────────────────────────┘
```

---

## 7. Многопоточность и асинхронность

### Где и как применяется

```
┌──────────────────────────────────────────────────────────────────────┐
│                      CONCURRENCY MAP                                 │
├───────────────────────┬──────────────────────────────────────────────┤
│  Этап                 │  Подход                                      │
├───────────────────────┼──────────────────────────────────────────────┤
│  Чтение JSON-файлов   │  concurrent.futures.ThreadPoolExecutor       │
│  датасетов (I/O)      │  (I/O-bound → потоки, не процессы)          │
├───────────────────────┼──────────────────────────────────────────────┤
│  Нормализация данных  │  concurrent.futures.ProcessPoolExecutor      │
│  (CPU-intensive)      │  (CPU-bound → процессы для GIL bypass)      │
├───────────────────────┼──────────────────────────────────────────────┤
│  RF / XGBoost         │  n_jobs=-1 (встроенная многопоточность)     │
│  обучение             │                                              │
├───────────────────────┼──────────────────────────────────────────────┤
│  CNN / LSTM DataLoader│  torch.utils.data.DataLoader(num_workers=N) │
│  (батчевая загрузка)  │  Предзагрузка батчей параллельно            │
├───────────────────────┼──────────────────────────────────────────────┤
│  Параллельное обучение│  asyncio + concurrent.futures               │
│  RF, XGBoost, CNN     │  Ensemble + CNN запускаются параллельно     │
│  (независимы)         │  LSTM запускается после, на их признаках    │
├───────────────────────┼──────────────────────────────────────────────┤
│  SHAP объяснения      │  multiprocessing на батчах данных           │
├───────────────────────┼──────────────────────────────────────────────┤
│  CLI прогресс-мониторинг│ asyncio + Rich live display               │
└───────────────────────┴──────────────────────────────────────────────┘
```

### Архитектура параллельного обучения

```
asyncio event loop
│
├── Task: EnsembleTrainer.fit()   ─── ProcessPool (n_jobs=-1)
│       └── RF + XGBoost параллельно
│
├── Task: CNNTrainer.fit()        ─── PyTorch DataLoader (workers=4)
│       └── GPU / CPU обучение
│
└── [После завершения выше]
    └── Task: LSTMTrainer.fit()   ─── PyTorch DataLoader (workers=4)
            └── Использует эмбеддинги из CNN/Ensemble как дополнит. признаки
```

---

## 8. CLI — интерфейс командной строки

### Команда `normalize`

```bash
python manage.py normalize [OPTIONS]

Options:
  --source TEXT     Источник: dns | host | all  [default: all]
  --split TEXT      Разбивка: TRAIN | TEST | VALIDATION | all  [default: all]
  --workers INT     Количество рабочих потоков  [default: 4]
  --chunk-size INT  Размер чанка при записи в БД  [default: 10000]
  --dry-run         Запуск без записи в БД (только валидация)
  --overwrite       Перезаписать существующие данные в БД
```

### Команда `train`

```bash
python manage.py train [OPTIONS]

Options:
  --version TEXT    Версия модели для сохранения (v1, v2, ...)  [required]
  --model TEXT      Модель: rf | xgb | cnn | lstm | ensemble | all  [default: all]
  --source TEXT     Источник данных: dns | host | all  [default: all]
  --split TEXT      Сплит для обучения  [default: TRAIN]
  --epochs INT      Количество эпох (CNN/LSTM)  [default: 50]
  --batch-size INT  Размер батча  [default: 256]
  --lr FLOAT        Learning rate  [default: 0.001]
  --workers INT     Потоки для DataLoader  [default: 4]
  --device TEXT     Устройство: cpu | cuda | mps  [default: auto]
  --val-split FLOAT Доля данных для валидации  [default: 0.2]
  --no-shap         Пропустить SHAP-объяснения после обучения
  --resume          Продолжить с последнего чекпоинта
```

### Команда `evaluate`

```bash
python manage.py evaluate [OPTIONS]

Options:
  --version TEXT    Версия модели  [required]
  --split TEXT      Сплит для оценки: TEST | VALIDATION  [default: TEST]
  --explain         Генерировать SHAP-объяснения
  --export-report   Сохранить отчёт в models/vN/report.json
  --ablation        Запустить ablation study (каждая модель отдельно)
```

---

## 9. Процесс обучения в CLI

Используется библиотека **Rich** для красивого отображения в терминале.

### Пример вывода в CLI при обучении

```
╔══════════════════════════════════════════════════════════════════════╗
║         BEHAVIOUR-DRIVEN HYBRID LEARNING FRAMEWORK v1.0            ║
║                  Training Pipeline — Version: v1                   ║
╚══════════════════════════════════════════════════════════════════════╝

 Phase 1 ─ Loading data from DuckDB
  ✓ DNS stateful features:    22,768 samples loaded
  ✓ DNS stateless features:   60,091 samples loaded
  ✓ Host features:           146,704 samples loaded
  ✓ LSTM sequences:           89,321 sequences (window=64)

 Phase 2 ─ Training Models [Parallel]
  ╔══════════════════════════════════════════════════════════════════╗
  ║  Random Forest  [████████████████████░░░░░░░░] 67%  ETA: 1m 24s ║
  ║  XGBoost        [████████████████████████████] 100% ✓ 2m 01s    ║
  ║  CNN            [████████████░░░░░░░░░░░░░░░░] 43%  ETA: 3m 55s ║
  ╚══════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────── XGBoost Results ──────────────────────┐
  │  Accuracy:  0.9714    Precision: 0.9682                          │
  │  Recall:    0.9601    F1-Score:  0.9641                          │
  │  AUC:       0.9887    FPR:       0.024                           │
  └──────────────────────────────────────────────────────────────────┘

 Phase 3 ─ LSTM Sequence Model
  Epoch  [1/50]  Loss: 0.6823  Acc: 0.5512  ████░░░░░░░░  2%
  Epoch [15/50]  Loss: 0.2241  Acc: 0.8934  ████████████  30%
  Epoch [50/50]  Loss: 0.0814  Acc: 0.9702  ████████████  100% ✓

 Phase 4 ─ Late Fusion Optimization
  Optimizing weights by F1-score on validation set...
  ✓ Optimal weights: RF=0.42  CNN=0.31  LSTM=0.27

 Phase 5 ─ SHAP Explainability
  Generating SHAP values for 500 samples...
  ✓ Top features: rr_name_entropy, subdomain_length, distinct_ns

 Phase 6 ─ Saving Model v1
  ✓ random_forest.joblib   saved
  ✓ xgboost.json           saved
  ✓ cnn.pt                 saved
  ✓ lstm.pt                saved
  ✓ fusion_weights.json    saved
  ✓ metadata.json          saved

╔══════════════════════════════════════════════════════════════════════╗
║                       FINAL RESULTS — v1                           ║
╠══════════════════════╦══════════════════════╦═══════════════════════╣
║  Accuracy:  0.9718   ║  Precision: 0.9701   ║  Recall:   0.9643    ║
║  F1-Score:  0.9672   ║  AUC:       0.9931   ║  FPR:      0.0198    ║
╚══════════════════════╩══════════════════════╩═══════════════════════╝
  Total training time: 14m 32s
```

---

## 10. Поток данных — End-to-End

```
RAW DATA (datasets-new/)
        │
        ▼
┌───────────────────┐
│  1. НОРМАЛИЗАЦИЯ  │
│                   │
│  DNS JSON files   │──► DNSNormalizer  ──► dns_stateful_features  (DuckDB)
│  Host JSON files  │──► HostNormalizer ──► host_features          (DuckDB)
│  PCAP files       │──► PCAPParser     ──► dns_stateless_features (DuckDB)
│  All events       │──► SequenceBuilder──► sequences_train.h5     (HDF5)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  2. ЗАГРУЗКА      │
│                   │
│  DuckDB SQL query │──► Pandas DataFrame  ──► Train/Val split
│  HDF5 dataset     │──► PyTorch Dataset   ──► DataLoader
└───────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│  3. ОБУЧЕНИЕ (параллельно)                                            │
│                                                                       │
│  EnsembleTrainer ──► RF model + XGBoost model + P(y|x) predictions   │
│  CNNTrainer      ──► CNN model               + P(y|x) predictions    │
│  LSTMTrainer     ──► LSTM model              + P(y|x) predictions    │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────┐
│  4. LATE FUSION   │
│                   │
│  P_final = w1*P_ensemble + w2*P_cnn + w3*P_lstm                      │
│  Optimization: argmax F1(w1, w2, w3) on validation set               │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  5. ОЦЕНКА        │
│                   │
│  Metrics: Accuracy, Precision, Recall, F1, AUC, FPR                  │
│  Ablation: каждая модель отдельно vs full hybrid                      │
│  Cross-validation: K-fold stratified                                  │
│  SHAP: feature attribution для интерпретации                          │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  6. СОХРАНЕНИЕ    │
│                   │
│  models/vN/       │ ── все артефакты модели + metadata.json
│  experiments (DB) │ ── лог эксперимента в DuckDB
└───────────────────┘
```

---

## 11. ООП и принципы проектирования

### Иерархия классов

```
BaseNormalizer (ABC)
├── DNSNormalizer
│   ├── StatefulDNSNormalizer
│   └── StatelessDNSNormalizer
└── HostNormalizer
    ├── ADFANormalizer
    ├── LIDDSNormalizer
    └── MaintainableLogNormalizer

BaseTrainer (ABC)
├── EnsembleTrainer
│   ├── RandomForestTrainer
│   └── XGBoostTrainer
├── CNNTrainer
└── LSTMTrainer

BaseEvaluator (ABC)
└── ClassificationEvaluator

BaseExplainer (ABC)
└── SHAPExplainer
    ├── TreeSHAPExplainer
    ├── DeepSHAPExplainer
    └── KernelSHAPExplainer
```

### Принципы SOLID применённые в проекте

| Принцип | Применение                                                                                |
|:--------|:------------------------------------------------------------------------------------------|
| **S**   | Каждый класс — одна ответственность: нормализатор нормализирует, тренер обучает          |
| **O**   | `BaseTrainer` открыт для расширения новыми моделями без изменения существующего кода      |
| **L**   | Любой `BaseTrainer` заменяем в `TrainPipeline` без поломки логики                        |
| **I**   | Интерфейсы `Normalizer`, `Trainer`, `Explainer` разделены — нет лишних зависимостей      |
| **D**   | `TrainPipeline` зависит от абстракций `BaseTrainer`, не от конкретных классов            |

### Обязательное документирование

Каждый класс, метод и функция содержат:

```python
class DNSNormalizer(BaseNormalizer):
    """
    Нормализатор DNS-датасетов.

    Обрабатывает JSON-файлы из datasets-new/dns/, извлекает
    stateful и stateless признаки, кодирует метки классов
    и записывает нормализованные данные в DuckDB.
    """

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализует raw DNS-признаки.

        Args:
            df: DataFrame с сырыми DNS-данными

        Returns:
            DataFrame с нормализованными признаками [0, 1]

        Raises:
            ValueError: если отсутствуют обязательные столбцы
        """
        ...
```

---

## 12. Ответы на вопросы

### Вопрос: Какую базу данных использовать для хранения нормализованных данных?

**Ответ: DuckDB для табличных данных + HDF5 для последовательностей**

#### Подробное обоснование

**DuckDB** — оптимальный выбор для этого проекта по следующим причинам:

1. **Zero-config** — не требует установки сервера. Один `.duckdb`-файл, и база готова к работе. Критично для воспроизводимости исследования.

2. **Колоночное хранение** — аналитические запросы вида `SELECT entropy, rr_name_entropy FROM dns_stateful WHERE label='exfiltration'` работают в 10–100× быстрее, чем в SQLite.

3. **Нативная интеграция с Pandas и PyArrow** — `duckdb.query("SELECT ...").df()` возвращает DataFrame без промежуточного копирования данных. Это ускоряет загрузку батчей при обучении.

4. **Поддержка Parquet** — можно экспортировать таблицы в `.parquet` для публичного воспроизведения без DuckDB.

5. **Полный SQL** — сложные запросы (JOIN, GROUP BY, window functions) без ORM-прослоек. Удобно для Feature Engineering прямо в SQL.

6. **Масштаб** — 4.97 GB нормализованных данных (хост) + DNS-данные. DuckDB эффективно обрабатывает десятки GB без нагрузки на RAM через lazy loading.

**HDF5 (h5py)** — для LSTM-последовательностей, потому что:
- Хранит трёхмерные массивы `(N, window_size, features)` нативно
- PyTorch `DataLoader` читает случайные батчи из HDF5 без загрузки всего файла в RAM
- Сжатие (gzip/lz4) уменьшает размер файлов последовательностей в 3–5×

#### Итог: почему не PostgreSQL?

PostgreSQL избыточен для исследовательского проекта — требует установки, настройки, управления пользователями. При этом не даёт преимуществ перед DuckDB для аналитических read-heavy рабочих нагрузок ML-обучения.

#### Итог: почему не просто Parquet-файлы?

Parquet не поддерживает SQL-запросы, индексы и транзакции. При сложной Feature Engineering (фильтрация, JOIN нескольких источников, агрегации) нужен SQL. DuckDB умеет читать Parquet напрямую, поэтому они совместимы.

---

### Резюме по выбору технологий

| Компонент          | Технология               | Обоснование                              |
|:-------------------|:-------------------------|:-----------------------------------------|
| CLI-менеджер       | Click + Rich             | Гибкие команды + красивый вывод          |
| Нормализация       | Pandas + DuckDB          | Скорость + SQL для Feature Engineering   |
| Последовательности | h5py (HDF5)              | Эффективное хранение 3D-массивов         |
| Ensemble ML        | scikit-learn + xgboost   | Зрелые библиотеки с параллельностью      |
| Deep Learning      | PyTorch                  | Гибкость, DataLoader, GPU-поддержка      |
| SHAP               | shap                     | Нативная поддержка всех типов моделей    |
| Прогресс в CLI     | Rich                     | Прогресс-бары, таблицы, цветной вывод    |
| Конфигурация       | python-dotenv (.env)     | Переменные окружения без хардкода        |
| Многопоточность    | concurrent.futures       | ThreadPool (I/O) + ProcessPool (CPU)     |
| Асинхронность      | asyncio                  | Параллельный запуск независимых тренеров |

---

*Документ подготовлен на основе анализа проектного предложения и датасетов: CIC-Bell-DNS-EXF-2021, Mendeley-DNS-Exfiltration-Dataset, ADFA IDS, LID-DS 2021, Maintainable Log Dataset.*

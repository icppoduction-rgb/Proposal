# Шпаргалка по функциональному проекту

## 1. Цель проекта
Спроектировать и оценить behaviour-driven гибридный ML-фреймворк для детекции многоэтапной эксфильтрации данных с объединением host-телеметрии, network-признаков, sequence modelling и explainability.

## 2. Основной исследовательский фокус
- Выделить кросс-доменные поведенческие индикаторы (host + network) для стадий эксфильтрации.
- Построить гибридную архитектуру, совмещающую классический ML и DL.
- Моделировать временную последовательность атаки, а не только event-level аномалии.
- Повысить интерпретируемость решений через SHAP.

## 3. Ядро архитектуры
- **Слой 1: Multi-source integration**: сбор, предобработка и нормализация host/network признаков в единое представление.
- **Слой 2: Hybrid ML/DL classification**: Random Forest, XGBoost, CNN для классификации benign/malicious на уровне событий/сэмплов.
- **Слой 3: Behavioural sequence modelling**: LSTM по упорядоченным поведенческим событиям.
- **Логика решения**: late fusion вероятностей классификатора и sequence-модели.

## 4. Стратегия датасетов
- Строго разделять роли: `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS`.
- Не смешивать DNS-логику и host-логику в одной ролевой таблице.
- Интеграцию разнородных источников делать на уровне признаков, а не через прямой raw-fusion логов.

## 5. Роли DNS-датасетов
| Роль | Датасет(ы) | Назначение |
|---|---|---|
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | Обучение attack-класса (DNS exfiltration/tunneling). |
| `TRAIN` | CIC-Bell-DNS-2021 | Обучение benign-класса (нормальное DNS-поведение). |
| `VALIDATION` | CIC-Bell-DNS-2021 split | Контроль false positives, настройка порога. |
| `TEST` | BCCC-CIC-Bell-DNS-2024 | Финальный benchmark, проверка generalization и overfitting. |
| `TEST` | Mendeley DNS Exfiltration | Проверка реалистичности и междатасетного переноса. |
| `EXPERIMENTS` | Kaggle DNS Tunneling | Быстрый прототипинг, feature-эксперименты, augmentation only. |

## 6. Роли host-датасетов
| Роль | Датасет(ы) | Назначение |
|---|---|---|
| `TRAIN` | ADFA IDS | Базовое HIDS-обучение. |
| `TRAIN` | LID-DS 2021 | Основное sequence-моделирование syscall. |
| `TRAIN` | Maintainable Log Dataset | Enterprise logs и моделирование multi-stage поведения. |
| `VALIDATION` | LID-DS 2019 | Cross-version/CVE валидация устойчивости. |
| `VALIDATION` | LANL | Валидация user-host/auth/lateral movement поведения. |
| `VALIDATION` | Windows Event Log / OTRF | SOC-ориентированная валидация Windows телеметрии. |
| `TEST` | Unified Host + Network / LANL | Гибридный host+network тест устойчивости. |
| `TEST` | ISOT Cloud IDS | Проверка переносимости в cloud-среду. |
| `TEST` | Dynamic Malware Analysis | Проверка malware-driven host поведения. |
| `EXPERIMENTS` | HDFS, BGL, Syscall Generator, COMIDDS | Вспомогательные эксперименты/augmentation/поиск датасетов. |

## 7. Фокус feature engineering
- Network-признаки: flow-статистики, распределения размера пакетов, inter-arrival timing, DNS entropy, частота коммуникаций.
- Host-признаки: частоты syscall, file-access entropy, process execution patterns, индикаторы использования привилегий.
- Использовать MITRE ATT&CK mapping как промежуточный слой согласования индикаторов стадий атаки.
- Валидировать важность признаков через SHAP.

## 8. Фокус sequence modelling
- Использовать LSTM для временных зависимостей многоэтапного поведения.
- Формировать упорядоченные последовательности через sliding windows.
- Целевой размер sequence: примерно 50-100 событий.
- Бинарная sequence-классификация: benign vs exfiltration.

## 9. Фокус explainability
- Основной XAI-метод: SHAP.
- Нужны global и local feature attribution.
- Качественная проверка: объяснения TP/FP по каждому CV-fold относительно MITRE-логики стадий.
- Количественная проверка: стабильность rank-order SHAP между CV-fold.

## 10. Приоритеты реализации
1. Зафиксировать доступ к датасетам и role-separated splits.
2. Реализовать feature engineering и ATT&CK-согласованную схему признаков.
3. Собрать baseline hybrid classifier (RF/XGBoost/CNN).
4. Интегрировать LSTM sequence-слой и late fusion.
5. Добавить SHAP-пайплайн и проверки качества объяснений.
6. Провести stratified k-fold CV, ablation и cross-dataset validation.

## 11. Ограничения проекта
- Таймлайн: 12 недель (май-август 2026), 5 фаз методологии.
- Только публичные benchmark-датасеты; без live traffic capture.
- Ограниченный стек моделей: RF, XGBoost, CNN, LSTM.
- Вне текущего scope: RL-компоненты, graph-based расширения, полностью unsupervised sequence modelling, крупномасштабный raw multi-dataset fusion.
- Ожидается class imbalance; ключевые метрики: precision/recall/F1 (+ AUC, FPR).

## 12. Чего не делать
- Не обучать модель на датасетах, отведённых под `TEST`.
- Не использовать синтетический Kaggle DNS tunneling как финальное доказательство качества.
- Не сливать DNS- и host-роль в один смешанный pipeline.
- Не закладываться на payload-inspection для encrypted каналов (в scope — metadata/behavioural подход).
- Не пропускать контроль false positives на benign-heavy распределениях.

## 13. Рекомендуемый порядок разработки
1. Зафиксировать инвентарь датасетов и role-matrix отдельно для DNS и host потоков.
2. Реализовать общие контракты предобработки и словари признаков.
3. Обучить baseline non-sequential модели и зафиксировать reference-метрики.
4. Добавить LSTM sequence-ветку и late-fusion слой принятия решения.
5. Интегрировать SHAP-отчёты (global/local + fold consistency checks).
6. Выполнить полный пакет оценки: stratified CV, ablation, cross-dataset generalization.
7. Зафиксировать воспроизводимые конфиги экспериментов и шаблоны отчётности.

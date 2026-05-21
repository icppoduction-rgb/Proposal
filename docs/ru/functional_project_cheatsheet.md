# Шпаргалка по функциональному проекту (гибридное обнаружение эксфильтрации)

## 1. Главный фокус (по proposal + dataset docs)
- Сделать **behavior-driven hybrid IDS** для обнаружения эксфильтрации данных.
- Объединять **сетевую и хостовую телеметрию** на уровне **признаков** (а не сырые логи в один массив).
- Ловить **многоэтапное развитие атаки** (recon -> staging -> exfiltration), а не только одиночные аномалии.
- Встроить объяснимость через **SHAP**, чтобы SOC-аналитик понимал причину алерта.

## 2. Что обязательно должно работать в MVP
- Сквозной pipeline: от загрузки датасетов до воспроизводимой оценки модели.
- Два уровня детекции:
  - классификация события/сэмпла (RF, XGBoost, CNN);
  - классификация последовательности (LSTM по sliding windows).
- Late fusion: объединение вероятностей классификатора и sequence-модуля.
- Оценка через stratified CV и отдельный контроль false positives.
- Воспроизводимые артефакты: метрики, модели, схема признаков, логи экспериментов.

## 3. Обязательная стратегия датасетов (роли не смешивать)

### DNS-ветка
- `TRAIN (атаки)`: CIC-Bell-DNS-EXF-2021
- `TRAIN/VALIDATION (benign + FP control)`: CIC-Bell-DNS-2021
- `TEST (финальный бенчмарк)`: BCCC-CIC-Bell-DNS-2024
- `TEST (реализм, cross-dataset)`: Mendeley DNS Exfiltration Dataset
- `Только EXPERIMENTS`: Kaggle DNS Tunneling (synthetic)

### Host-ветка
- `TRAIN`: ADFA IDS + LID-DS 2021 + Maintainable Log Dataset
- `VALIDATION`: LID-DS 2019 + LANL + OTRF Windows/Sysmon
- `TEST`: Unified Host+Network (LANL) + ISOT Cloud IDS + Dynamic Malware Analysis
- `Только EXPERIMENTS`: HDFS/BGL и synthetic generators

## 4. Архитектурные приоритеты для рабочего проекта
- Единая каноническая схема события для всех источников: время, actor/process, network context, label.
- Жесткие границы train/val/test по источнику и времени, чтобы убрать leakage.
- Раздельные генераторы признаков:
  - network features (flow stats, DNS entropy, inter-arrival, frequency);
  - host features (syscall distributions, process patterns, privilege indicators, file-access entropy).
- Sequence builder с фиксированными окнами (в proposal ориентир ~50-100 событий).
- Модуль explainability:
  - глобальный SHAP-рейтинг признаков;
  - локальные SHAP-объяснения для TP/FP кейсов;
  - проверка стабильности рангов между CV-фолдами.

## 5. Минимальный практический стек
- **Обязательные датасеты**:
  - DNS: EXF-2021 + DNS-2021 + BCCC-2024
  - Host: ADFA + LID-DS 2021 + Maintainable Log
- **Обязательные модели**:
  - RF/XGBoost как стабильные baseline
  - CNN для структурных паттернов
  - LSTM для временного поведения
- **Обязательные метрики**:
  - Precision, Recall, F1 как основные
  - FPR и AUC как контрольные

## 6. Риски, которые нужно закрыть заранее
- Несовместимость host/network датасетов -> feature-level integration + явная карта соответствия признаков.
- Дисбаланс классов -> взвешивание/сэмплинг и threshold tuning только на validation.
- Переобучение на одном семействе данных -> cross-dataset проверки (BCCC, Mendeley, LID-DS 2019, LANL).
- Ограничения по ресурсам -> сначала baseline-пайплайн, потом итерации CNN/LSTM.

## 7. Каркас выполнения на 12 недель (из proposal)
1. Phase 1: доступ к данным + feature engineering + ATT&CK mapping.
2. Phase 2: реализация hybrid classifier pipeline.
3. Phase 3: LSTM sequence module и интеграция.
4. Phase 4: интеграция SHAP и проверка качества интерпретации.
5. Phase 5: ablation + benchmark comparisons + финальная валидация.

## 8. Критерии готовности «функционального проекта»
- Полный воспроизводимый прогон от сырых данных до финального отчета.
- Документированная конфигурация ролей датасетов и политики сплитов.
- Сохраненные артефакты: модели, пороги, списки признаков, SHAP-сводки.
- Финальный отчет содержит:
  - метрики по каждому датасету;
  - анализ false positives;
  - ablation-таблицу (no-sequence vs sequence, no-host vs hybrid);
  - ограничения и следующий план итераций.

## 9. Привязка к структуре репозитория
- `manage.py`: оркестратор стадий (`prepare`, `train`, `eval`, `explain`, `report`).
- `scripts/`: идемпотентные скрипты подготовки данных, генерации признаков, обучения и оценки.
- `docs/en|ru`: синхронно поддерживать архитектурные решения, матрицу ролей датасетов и инструкции воспроизводимости.

# Анализ проектного предложения

---

## Краткое резюме

Документ представляет собой проектное предложение по теме **«Behaviour-driven hybrid learning for data exfiltration detection»**. Основная идея исследования — разработать гибридный ML/DL-фреймворк для обнаружения утечки данных, объединяющий сетевые признаки, host-level telemetry, поведенческое моделирование последовательностей и SHAP-объяснимость.

---

## Сильные стороны

| Аспект | Оценка |
|:---|:---|
| Актуальность темы | Data exfiltration, APT, insider threats, DNS tunnelling и encrypted traffic — существенные проблемы кибербезопасности |
| Исследовательский разрыв | Последовательно показаны ограниченность single-modality подходов и недостаток sequence modelling |
| Структура | Логична: Abstract → Background → Problem Statement → Research Questions → Aim/Objectives → Scope → Methodology → Plan |
| Методология | Design Science Research подходит для разработки и оценки detection framework |
| Ограничения | Явно зафиксированы по времени, данным и вычислительным ресурсам |
| Оценка | Указаны accuracy, precision, recall, F1-score, FPR, AUC, ablation study и cross-validation |

---

## Потенциальные слабые места

> **1. Риск недостаточной связности host и network datasets.**
> В тексте признается, что paired datasets могут отсутствовать, поэтому feature-level integration и simulation должны быть описаны максимально строго.

> **2. Требуется усилить воспроизводимость.**
> Желательно явно указать конкретные datasets, preprocessing steps, train/test split strategy и baseline models.

> **3. SHAP для LSTM/sequence component требует осторожности.**
> Нужно уточнить, будет ли использоваться KernelSHAP, DeepSHAP или объяснение агрегированных признаков.

> **4. Некоторые утверждения зависят от актуальности источников.**
> Библиографические ссылки не были отдельно проверены на существование и корректность DOI при конвертации.

> **5. Грамматика и академический стиль местами требуют редактуры.**
> Есть фразы, которые лучше переформулировать для более формального академического тона.

---

## Рекомендации по доработке

1. Добавить отдельную таблицу с выбранными datasets: название, тип телеметрии, классы, размер, источник, ограничения.
2. Четко описать механизм объединения host и network признаков, особенно если данные не являются парными.
3. Уточнить архитектуру late fusion: формула/правило агрегации вероятностей, веса компонентов, критерий выбора threshold.
4. Добавить baseline comparison: Random Forest only, XGBoost only, CNN only, LSTM only, hybrid without SHAP, full hybrid.
5. Уточнить, как будет оцениваться explainability: rank stability, case studies, alignment with MITRE ATT&CK tactics.
6. Проверить все ссылки DOI и библиографические данные перед финальной сдачей.

---

## Итоговая оценка

> Проектное предложение выглядит содержательно сильным и методологически последовательным. Главный риск — практическая реализация multi-source integration при отсутствии совместимых host/network датасетов. Если этот риск будет закрыт через четкую схему feature-level integration, прозрачные baseline experiments и воспроизводимый evaluation pipeline, работа будет выглядеть убедительно как академически, так и практически.

---
---

# ИНДИВИДУАЛЬНОЕ ЗАДАНИЕ 2 — ПРОЕКТНОЕ ПРЕДЛОЖЕНИЕ

| Поле | Значение |
|:---|:---|
| **Имя / TP Number** | Djumakhodjaeva Malika / TP099270 |
| **Intake Code** | APUMF2508CYS(PR) |
| **Module Code** | CT095-6-M-RMCE |
| **Module Title** | Research Methodology in Computing and Engineering |
| **Module Lecturer** | Dr. Murugananthan Velayutham |
| **Nominated Supervisor** | Dr. Jalil Md Desa |
| **Project Title** | Behaviour-driven hybrid learning for data exfiltration detection |
| **Date Assigned** | 6 февраля 2026 |
| **Date Completed** | 24 апреля 2026 |

---

# Аннотация

Эксфильтрация данных является одной из наиболее серьезных и сложных киберугроз для современных организаций, поскольку она часто скрыта, длительна и многоэтапна. Традиционные системы обнаружения вторжений демонстрируют существенные ограничения при выявлении сложных техник эксфильтрации, особенно когда злоумышленники используют зашифрованные каналы связи, insider threats и advanced persistent threats.

Хотя современные исследования активно применяют machine learning и deep learning для повышения качества обнаружения, большинство существующих систем используют только одну модальность данных: либо сетевой трафик, либо host-level telemetry. Кроме того, такие системы часто не моделируют последовательные поведенческие паттерны, характерные для постепенного развития атак эксфильтрации данных.

Данное предложение представляет **behaviour-driven hybrid machine learning framework**, предназначенный для устранения этих ограничений за счет интеграции host telemetry, анализа сетевого трафика и behavioural sequence modelling в единую архитектуру обнаружения. Предлагаемый framework объединяет классические ансамблевые методы, такие как Random Forest и XGBoost, компоненты CNN deep learning и LSTM-based behavioural sequence modelling для захвата как структурированных признаков, так и сложных временных зависимостей в multi-source security data.

Framework также будет интегрирован с explainable artificial intelligence technique, а именно SHAP-based feature attribution, чтобы повысить интерпретируемость решений обнаружения и поддержать рабочие процессы security analysts. Оценка framework будет выполнена на публично доступных cybersecurity benchmark datasets с использованием стандартных classification metrics.

Ожидаемый вклад исследования — улучшенный hybrid detection framework, расширяющий существующие подходы, усиливающий early detection capability для stealthy multi-stage exfiltration attacks и предоставляющий воспроизводимые результаты для дальнейших исследований в behavioural intrusion detection.

**Ключевые слова:** data exfiltration detection, hybrid deep learning, CNN, behavioural sequence modelling, LSTM, explainable artificial intelligence.

---

# Содержание

- Аннотация
- Список сокращений и терминов
- 1. Введение
- 2. Исследовательский контекст
- 3. Постановка проблемы
- 4. Исследовательские вопросы
- 5. Цель и задачи
- 6. Область исследования
- 7. Значимость исследования
- 8. Методология исследования
- 9. План исследования
- 10. Итоги
- Список источников

---

# Список сокращений и терминов

| Сокращение | Расшифровка |
|:---|:---|
| AUC | Area Under the ROC Curve |
| CNN | Convolutional Neural Network |
| DL | Deep Learning |
| DNS | Domain Name System |
| DSR | Design Science Research |
| GCN | Graph Convolutional Network |
| HTTPS | Hypertext Transfer Protocol Secure |
| IDS | Intrusion Detection System |
| LIME | Local Interpretable Model-Agnostic Explanations |
| LSTM | Long Short-Term Memory |
| ML | Machine Learning |
| RNN | Recurrent Neural Network |
| ROC | Receiver Operating Characteristic |
| SHAP | SHapley Additive exPlanations |
| TLS | Transport Layer Security |
| XAI | Explainable Artificial Intelligence |
| XGBoost | Extreme Gradient Boosting |

---

# 1. Введение

Быстрый рост цифровой инфраструктуры существенно изменил то, как организации управляют информацией и обмениваются ею. Большие объемы чувствительных данных проходят через cloud systems, enterprise networks и personal endpoint devices, которые стали основными средами обмена данными. Эти изменения дают значительные преимущества, но одновременно создают новые сложные security challenges, требующие более продвинутых технологий обнаружения.

Одной из наиболее серьезных угроз для организаций сегодня является **data exfiltration** — несанкционированная передача чувствительной информации из внутренних систем во внешние, контролируемые злоумышленником направления. В отличие от многих других cyberattacks, которые часто можно обнаружить сразу, data exfiltration обычно является скрытой, длительной и трудно заметной на ранних стадиях.

Современные злоумышленники используют разные способы сокрытия эксфильтрации, включая DNS tunneling, HTTPS/TLS channels, cloud services, encrypted communication и legitimate-looking traffic. В результате традиционные IDS, основанные на signatures или статических правилах, часто не способны выявить multi-stage exfiltration attacks, особенно когда поведение злоумышленника имитирует нормальную активность пользователя или системы.

В последние годы machine learning и deep learning стали активно использоваться для intrusion detection. Classical ML models, такие как Random Forest и XGBoost, хорошо работают со структурированными признаками, а deep learning approaches, такие как CNN и LSTM, способны выявлять сложные паттерны и temporal dependencies. Однако многие существующие решения используют только один источник данных, например network traffic или host logs, и не объединяют multi-source telemetry в единую detection architecture.

Это исследование направлено на разработку **behaviour-driven hybrid learning framework** для обнаружения data exfiltration. Framework объединит network-level features, host-level telemetry, behavioural sequence modelling и explainability, чтобы улучшить качество обнаружения и сделать решения модели более понятными для security analysts.

---

# 2. Исследовательский контекст

Data exfiltration остается одной из ключевых проблем cybersecurity, поскольку атаки этого типа часто являются скрытыми, многоэтапными и направленными на выведение чувствительной информации из защищенной среды. Такие атаки могут выполняться внешними злоумышленниками, insider threats или malware, уже закрепившимся внутри инфраструктуры.

Традиционные IDS обычно ориентированы на network signatures, known attack patterns или threshold-based rules. Эти подходы эффективны против известных атак, но плохо работают с novel attacks, encrypted channels и low-and-slow exfiltration. Современные атаки могут маскироваться под обычный DNS, HTTPS или cloud traffic, что снижает эффективность классических rule-based методов.

Исследования в области ML/DL показывают, что automated classification models могут повысить качество обнаружения. Random Forest и XGBoost часто применяются к tabular security features и дают сильные baseline results. CNN может выделять локальные feature patterns, а LSTM подходит для modelling temporal sequences и multi-stage behavior. Тем не менее single-model и single-modality approaches остаются ограниченными, потому что data exfiltration проявляется одновременно на network и host levels.

Host telemetry может включать process activity, system calls, user actions, authentication behavior и log events. Network telemetry может включать DNS queries, flow statistics, packet-level features, connection metadata и encrypted traffic indicators. Отдельно эти источники дают неполную картину атаки. Их объединение на feature level может дать более устойчивое и информативное представление о поведении.

Еще одной важной проблемой является **explainability**. Security analysts должны понимать, почему модель классифицировала событие как exfiltration или benign. Без интерпретируемости ML/DL-модели трудно использовать в operational SOC workflows. SHAP, LIME и другие XAI-методы помогают объяснить вклад признаков в решение модели, но их применение к hybrid and sequence-based IDS требует аккуратной методологии.

---

# 3. Постановка проблемы

Существующие подходы к обнаружению data exfiltration имеют несколько ограничений.

**Во-первых**, многие решения используют **single-modality telemetry**. Network-based approaches анализируют traffic patterns, DNS queries или flow features, но могут не видеть host-side behavior, например suspicious process activity, unusual file access или abnormal user actions. Host-based approaches, наоборот, могут видеть локальное поведение системы, но не всегда связывают его с network-level exfiltration channels.

**Во-вторых**, многие detection systems **недостаточно моделируют temporal behavior**. Data exfiltration часто развивается постепенно: reconnaissance, staging, compression, encryption, channel establishment и data transfer могут происходить в разные моменты времени. Простая tabular classification может пропустить такие sequential patterns.

**В-третьих**, многие ML/DL approaches **остаются недостаточно объяснимыми**. Даже если модель показывает высокую accuracy, security analysts должны понимать, какие признаки или события привели к решению. Без explainability сложно доверять модели, расследовать incidents и интегрировать результаты в SOC workflows.

**В-четвертых**, существует **практический риск несовместимости datasets**. Публичные cybersecurity datasets часто собираются в разных условиях, используют разные форматы и не всегда содержат paired host/network telemetry. Поэтому multi-source integration должна быть реализована строго, воспроизводимо и с четкими ограничениями.

> Следовательно, существует необходимость в hybrid detection framework, который объединяет host and network features, моделирует behavioural sequences и предоставляет explainable outputs.

---

# 4. Исследовательские вопросы

**RQ1. Какие cross-domain features из host telemetry и network traffic наиболее релевантны для обнаружения data exfiltration attacks в host and network environments?**

Этот вопрос направлен на выявление признаков, связывающих host-side behavior и network-level activity.

**RQ2. Как hybrid ML/DL architecture может повысить detection accuracy и robustness по сравнению с single-model approaches?**

Этот вопрос исследует, как объединение ensemble ML, CNN и LSTM может улучшить качество обнаружения.

**RQ3. Как behavioural sequence modelling может помочь обнаруживать multi-stage data exfiltration attack patterns?**

Этот вопрос фокусируется на temporal dependencies и последовательном развитии атак.

**RQ4. Как explainable AI methods могут повысить interpretability detection decisions и поддержать incident investigation?**

Этот вопрос рассматривает применение SHAP-based explanations для анализа решений модели.

---

# 5. Цель и задачи

## 5.1 Цель

Цель исследования — разработать и оценить **behaviour-driven hybrid machine learning framework** для обнаружения data exfiltration, объединяющий host telemetry, network traffic features, behavioural sequence modelling и explainable AI.

## 5.2 Задачи

1. Определить релевантные host-level и network-level features для обнаружения data exfiltration.
2. Спроектировать hybrid ML/DL detection architecture, объединяющую classical ensemble models, CNN и LSTM-based sequence modelling.
3. Реализовать behavioural sequence modelling component для выявления temporal attack patterns.
4. Интегрировать SHAP-based explainability для интерпретации решений модели.
5. Оценить framework на publicly available cybersecurity benchmark datasets с использованием standard classification metrics.

---

# 6. Область исследования

## 6.1 Фокус обнаружения

Исследование фокусируется на data exfiltration attacks, включая DNS tunneling, encrypted communication channels, insider-related exfiltration behavior и multi-stage exfiltration patterns.

## 6.2 Источники данных

Планируется использовать publicly available cybersecurity benchmark datasets, содержащие network traffic, DNS data, host logs, system calls и related telemetry. Если fully paired host/network datasets недоступны, integration будет выполняться на feature level с явным описанием ограничений.

## 6.3 Machine Learning Techniques

Framework будет использовать:

- Random Forest;
- XGBoost;
- CNN;
- LSTM;
- late fusion / feature-level fusion;
- SHAP-based explainability.

## 6.4 Behavioural Sequence Modelling

Behavioural sequence modelling будет использоваться для анализа ordered event sequences, построенных из host и network telemetry. Основной подход — **LSTM**, поскольку он подходит для временных зависимостей и multi-stage behavior.

## 6.5 Explainability

Explainability будет реализована через **SHAP-based feature attribution**. Объяснения будут использоваться для анализа вклада признаков в решения модели и для поддержки security analyst workflows.

## 6.6 Evaluation

Оценка будет выполняться с использованием accuracy, precision, recall, F1-score, false positive rate, AUC, cross-validation и ablation study.

## 6.7 Geographical and Organizational Scope

Исследование не ограничивается конкретной организацией или географическим регионом. Оно использует publicly available datasets и не включает live traffic capture или доступ к реальным organizational systems.

---

# 7. Значимость исследования

## 7.1 Решение важной cybersecurity-проблемы

Data exfiltration является критической угрозой, потому что она связана с утечкой чувствительной информации, финансовыми потерями, regulatory risks и damage to organizational reputation. Улучшение раннего обнаружения таких атак имеет практическую значимость для организаций и SOC teams.

## 7.2 Развитие state of the art в detection frameworks

Исследование развивает существующие IDS approaches за счет объединения host telemetry, network features, hybrid ML/DL classification и behavioural sequence modelling. Такой подход может повысить robustness по сравнению с single-modality systems.

## 7.3 Улучшение раннего обнаружения multi-stage attacks

Моделирование последовательностей позволяет выявлять не только отдельные suspicious events, но и patterns, которые проявляются во времени. Это особенно важно для stealthy exfiltration attacks.

## 7.4 Поддержка cybersecurity research community

Использование публичных datasets, воспроизводимой методологии и стандартных metrics позволит другим исследователям сравнивать результаты и развивать предложенный framework.

---

# 8. Методология исследования

## 8.1 Research Design and Approach

Исследование будет выполнено в рамках **Design Science Research**, поскольку его основной результат — разработка и оценка artifact в виде hybrid detection framework. Методология включает identification of problem, design and development, demonstration, evaluation и communication.

---

## 8.2 Phase 1: Feature Identification and Dataset Preparation

Первая фаза направлена на выявление behavioural indicators и подготовку datasets.

### 8.2.1 Dataset Selection

Будут выбраны публичные benchmark datasets, содержащие network, DNS и host telemetry. Для каждого dataset будут зафиксированы data type, labels, classes, size, limitations и preprocessing requirements.

### 8.2.2 Feature Engineering

Feature engineering будет включать извлечение DNS features, flow features, host activity indicators, system-call features, log-based features и temporal aggregation features. Там, где возможно, признаки будут сопоставлены с MITRE ATT&CK tactics and techniques.

---

## 8.3 Phase 2: Hybrid Framework Design

Вторая фаза будет посвящена проектированию hybrid framework.

### 8.3.1 Framework Architecture

Framework будет включать три основных слоя:

| Слой | Назначение |
|:---|:---|
| **Multi-source data integration layer** | Объединяет host и network telemetry на feature level |
| **Hybrid ML/DL classification layer** | Использует Random Forest, XGBoost и CNN для анализа structured and local feature patterns |
| **Behavioural sequence modelling layer** | Использует LSTM для анализа temporal relationships и multi-stage attack behavior |

Выходы classification и sequence modelling components будут объединяться через **late fusion**. Вероятности предсказаний будут агрегироваться для получения финального classification decision.

---

## 8.4 Phase 3: Behavioural Sequence Modelling

Третья фаза направлена на разработку behavioural sequence modelling component.

LSTM будет использовать ordered sequences of behavioural events, полученные из host и network telemetry. Event sequences будут строиться через sliding time windows. Каждая sequence будет состоять из фиксированного числа событий (например, **50–100 events per sequence**), а labels будут назначаться на основе наличия exfiltration activity внутри окна.

Модель будет выполнять **binary classification** на уровне sequence: benign vs exfiltration.

---

## 8.5 Phase 4: Explainability Integration

Четвертая фаза включает интеграцию explainable artificial intelligence techniques.

Основной техникой будет **SHAP**. SHAP-based explanations будут анализироваться для selected detection cases, включая true positives и false positives. Качественная оценка будет проверять, дают ли explanations осмысленные insights о behavioural patterns. Количественная оценка будет использовать rank-order consistency across cross-validation folds для проверки стабильности explanations.

---

## 8.6 Phase 5: Evaluation and Validation

Пятая фаза включает систематическую экспериментальную оценку proposed framework.

### 8.6.1 Evaluation Metrics

Для оценки будут использоваться:

| Метрика | Назначение |
|:---|:---|
| accuracy | общая точность классификации |
| precision | точность предсказания класса атаки |
| recall | полнота обнаружения атак |
| F1-score | основная метрика при class imbalance |
| false positive rate | контроль ложных срабатываний |
| AUC | оценка discriminative capability |

Поскольку cybersecurity datasets часто имеют class imbalance, precision, recall и F1-score будут рассматриваться как **основные метрики**. AUC будет использоваться для оценки discriminative capability.

Также будут выполнены:

- ablation study full hybrid framework vs individual components;
- comparison with baseline models;
- cross-validation;
- при возможности — comparison with published state-of-the-art approaches.

### 8.6.2 Ethical Considerations

Исследование использует только publicly available benchmark datasets. Личные данные не собираются и не обрабатываются. Live network traffic capture не выполняется, реальные organizational systems не мониторятся. Поэтому исследование имеет **низкий ethical risk**.

---

# 9. План исследования

Исследование запланировано на **12 недель** с мая 2026 по август 2026. План организован вокруг пяти методологических фаз.

## 9.1 Research Timeline Overview

Задачи распределяются по фазам: dataset preparation, framework design, sequence modelling, explainability integration, evaluation and validation, report writing.

## 9.2 Phase Descriptions and Key Milestones

| Phase | Milestone | Key Deliverable | Success Criterion | Target Date |
|:---|:---|:---|:---|:---:|
| **Phase 1** — Feature identification and dataset preparation | Datasets accessed and features extracted | Preprocessed feature dataset with MITRE ATT&CK mappings | datasets loaded, cleaned, feature-engineered and documented | May 15 |
| **Phase 2** — Hybrid framework design | Functional classification pipeline implemented | Hybrid detection framework prototype | baseline classification performance achieved on at least one dataset | June 12 |
| **Phase 3** — Behavioural sequence modelling | LSTM sequence model integrated | Integrated LSTM sequence modelling component | temporal event sequences captured and integrated into ensemble layer | July 3 |
| **Phase 4** — Explainability integration | SHAP module integrated | SHAP explanation module | SHAP values generated and validated against known attack sequences | July 24 |
| **Phase 5** — Evaluation and validation | Experiments completed | Experimental results report | framework outperforms at least one baseline on F1-score and AUC; ablation study complete | August 14 |
| **Report writing** | Final report submitted | Completed research report and slides | report finalized and proofread | August 28 |

---

### 9.2.1 Phase 1 — Feature Identification and Dataset Preparation

Фаза включает literature review, выбор benchmark datasets, feature engineering из host и network telemetry и MITRE ATT&CK tactic mapping. Основной deliverable — documented feature engineering report.

### 9.2.2 Phase 2 — Hybrid Framework Design and Implementation

Фаза включает design of multi-source integration layer, hybrid ML/DL classification architecture, implementation of framework components и baseline models for comparison.

### 9.2.3 Phase 3 — Behavioural Sequence Modelling

Фаза включает разработку LSTM-based sequence modelling component и интеграцию sequence modelling layer в broader hybrid framework.

### 9.2.4 Phase 4 — Explainability Integration

Фаза включает integration of SHAP-based explainability и design of sequence-aware explanation outputs.

### 9.2.5 Phase 5 — Evaluation and Validation

Фаза включает cross-validation experiments, ablation studies, baseline comparisons и cross-dataset generalizability evaluation.

### 9.2.6 Report Writing and Defence Preparation

Фаза включает непрерывное написание глав, review and revisions, подготовку к oral defence и финальную submission.

---

## 9.3 Risk and Contingency Planning

| Risk | Likelihood | Impact | Mitigation |
|:---|:---:|:---:|:---|
| Dataset incompatibility between host and network sources | Medium | High | использовать feature-level integration и synthetic host behaviour simulation для согласования heterogeneous datasets |
| Computational resource constraints limiting deep learning training | Medium | Medium | использовать cloud-based computing resources, например Google Colab или Kaggle; оптимизировать model complexity |
| Underperformance of sequence modelling component | Low | Medium | перейти к simpler temporal aggregation features; скорректировать scope of Objective 3 |
| Timeline delays due to integration complexity | Medium | Medium | сохранить buffer weeks для revisions; приоритизировать core objectives O1-O3 |

---

# 10. Итоги

Проектное предложение описывает исследование, направленное на устранение четко сформулированного gap в области data exfiltration detection. Существующие detection systems — network-based, host-based, predictive или hybrid — часто ограничены reliance on single-modality telemetry и неспособностью моделировать sequential behavioural patterns, характерные для multi-stage exfiltration attacks.

В ответ на этот gap предлагается **behaviour-driven hybrid machine learning framework**, объединяющий три ключевых компонента:

| Компонент | Назначение |
|:---|:---|
| Multi-source data integration layer | Объединяет host и network telemetry |
| Hybrid ML/DL classification layer | Ensemble methods + deep learning architecture |
| Behavioural sequence modelling layer | LSTM-based sequence analysis |

SHAP-based explainability будет добавлена для повышения interpretability of detection decisions.

Исследование направляется **четырьмя research questions**, связанными с cross-domain feature identification, hybrid architecture design, behavioural sequence modelling и explainability integration. Эти вопросы сопоставлены с конкретными objectives, каждый из которых представляет проверяемую единицу работы.

Использование publicly available benchmark datasets ограничивает scope, повышает ethical compliance и поддерживает reproducibility. 12-недельный план исследования разделен на пять methodological phases с понятными milestones и risk mitigation strategies.

Значимость исследования имеет как академическое, так и практическое измерение:
- **Академически:** развивает existing hybrid detection architectures через behavioural sequence modelling и multi-source feature integration.
- **Практически:** может улучшить early detection of stealthy multi-stage attacks и повысить interpretability для security operations teams.

> В заключение, proposed framework представляет своевременный и обоснованный вклад в cybersecurity, напрямую addressing limitations of existing approaches и responding to emerging research priorities in multi-source telemetry integration, behavioural modelling and explainable intrusion detection.

---

# Список источников

Açıkgözoglu, E. (2024). Comparison Of Machine Learning Algorithms For Detection Of Data Exfiltration Over DNS. *Yalvaç Akademi Dergisi*, *9*(2), 61-70. https://doi.org/10.57120/yalvac.1507402

Almuhanna, R., & Dardouri, S. (2025). A deep learning/machine learning approach for anomaly based network intrusion detection. *Frontiers in Artificial Intelligence*, *8*, 1625891. https://doi.org/10.3389/frai.2025.1625891

Balogun, S. A., Ijiga, O. M., Okika, N., Enyejo, L. A., & Agbo, O. J. (2025). Machine Learning-Based Detection of SQL Injection and Data Exfiltration Through Behavioral Profiling of Relational Query Patterns. *International Journal of Innovative Science and Research Technology*, 49-63. https://doi.org/10.38124/ijisrt/25aug324

Cai, X., Zhang, H., Ahmed, C. M., & Koide, H. (2025). Detecting advanced persistent threat exfiltration with ensemble deep learning tree models and novel detection metrics. *IEEE Access*, *13*, 81803-81822. https://doi.org/10.1109/access.2025.3567772

Chen, Z., Simsek, M., Kantarci, B., Bagheri, M., & Djukic, P. (2024). Machine learning-enabled hybrid intrusion detection system with host data transformation and an advanced two-stage classifier. *Computer Networks*, *250*, 110576. https://doi.org/10.1016/j.comnet.2024.110576

Chinnasamy, R., Subramanian, M., Easwaramoorthy, S. V., & Cho, J. (2025). Deep learning-driven methods for network-based intrusion detection systems: A systematic review. *ICT Express*, *11*(1), 181-215. https://doi.org/10.1016/j.icte.2025.01.005

Hakim, A. R., Ramli, K., Salman, M., Pranggono, B., & Agustina, E. R. (2024). ARKAIV: Predicting data exfiltration using supervised machine learning based on tactics mapping from threat reports and event logs. *IEEE Access*, *13*, 28381-28397. https://doi.org/10.1109/access.2024.3524502

Hanintya, D. L., Sukarno, P., & Wardana, A. A. (2025). Comparing Explainable AI Framework: Study case on detection of DNS exfiltration attach using neural network. *Procedia Computer Science*, *269*, 1022-1032. https://doi.org/10.1016/j.procs.2025.09.044

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75-105. https://doi.org/10.2307/25148625

Hozouri, A., Mirzaei, A., & Effatparvar, M. (2025). A comprehensive survey on intrusion detection systems with advances in machine learning, deep learning and emerging cybersecurity challenges. *Discover Artificial Intelligence*, *5*(1). https://doi.org/10.1007/s44163-025-00578-1

Kamal, H., & Mashaly, M. (2025). Robust intrusion detection system using an improved hybrid deep learning model for binary and Multi-Class classification in IoT networks. *Technologies*, *13*(3), 102. https://doi.org/10.3390/technologies13030102

Kuppuraju, S. Y., Ojha, S. S., & Kumar, M. (2025). Real-Time detection of data exfiltration using deep learning in edge computing systems. *International Journal of Innovative Research in Computer Science & Technology*, *13*(2), 6-13. https://doi.org/10.55524/ijircst.2025.13.2.2

Ofori, H. K., Bell-Dzide, K., Brown-Acquaye, W. L., Lempogo, F., Frimpong, S. O., Agbehadji, I. E., & Millham, R. C. (2025). Application of machine learning and deep learning techniques for enhanced insider threat detection in cybersecurity: Bibliometric review. *Symmetry*, *17*(10), 1704. https://doi.org/10.3390/sym17101704

Potluri, S. (2024). A Deep Learning-Driven framework for detecting anomalous data breaches in distributed cloud storage infrastructures. *International Journal of Artificial Intelligence Data Science and Machine Learning*, *5*(3). https://doi.org/10.63282/3050-9262.ijaidsml-v5i3p109

Qutqut, M. H., Ahmed, A., Taqi, M. K., Abimanyu, J., Ajes, E. T., & Alhaj, F. (2026). A comparative evaluation of SnORt and Suricata for detecting data exfiltration tunnels in cloud environments. *Journal of Cybersecurity and Privacy*, *6*(1), 17. https://doi.org/10.3390/jcp6010017

Sammour, M., Othman, M. F. I., Hassan, A., Bhais, O., & Talib, M. S. (2026). Advanced DNS tunneling detection: a hybrid reinforcement learning and metaheuristic approach. *Frontiers in Computer Science*, *7*. https://doi.org/10.3389/fcomp.2025.1728980

Singh, P. R. N., & Siddalingaiah, N. (2025). Permission-level risk profiling and anomaly detection in IoT using machine learning. *International Journal of Information Technology*. https://doi.org/10.1007/s41870-025-02977-0

Thomas, R., Yerima, S. Y., Alkharoossi, S. K., Alkhoori, M. M., & Ahmed, A. (2025). DNS Exfiltration Attack and Dataset Generation for Machine Learning-Based Detection. *3rd International Conference on Cyber Resilience ICCR2025*, 1-6. https://doi.org/10.1109/iccr67387.2025.11292120

Yumlembam, R., Issac, B., Jacob, S. M., Yang, L., & Krishnan, D. (2025). Insider Threat Detection Using GCN and Bi-LSTM with Explicit and Implicit Graph Representations. *arXiv (Cornell University)*. https://doi.org/10.48550/arxiv.2512.18483

Zuppelli, M., Guarascio, M., Caviglione, L., & Liguori, A. (2024). No Country for Leaking Containers: Detecting Exfiltration of Secrets Through AI and Syscalls. *ARES 24: Proceedings of the 19th International Conference on Availability, Reliability and Security*, 1-8. https://doi.org/10.1145/3664476.3670884

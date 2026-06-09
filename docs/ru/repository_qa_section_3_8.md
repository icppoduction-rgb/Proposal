# Ответы по репозиторию (разделы 3.3-3.8)

Область анализа: просмотрены все файлы репозитория (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, конфиги проекта).  
Важный контекст: в текущем репозитории реализован этап подготовки датасетов, а не обучение/оценка моделей.

---

## 1. Dataset Selection (Section 3.3)

**Вопрос:** Какие конкретно датасеты использовались?  
**Ответ:** По фактически обработанным путям в `temp_data`:
- DNS:
  - `CIC-Bell-DNS-2021` (TRAIN + VALIDATION)
  - `CIC-Bell-DNS-EXF-2021` (TRAIN)
  - `Mendeley-DNS-Exfiltration-Dataset` (TEST)
- Host:
  - TRAIN: `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset`
  - VALIDATION: `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets`
  - TEST: `Dynamic-Malware-Analysis-Dataset`, `ISOT-Cloud-IDS-Dataset`, `Unified-Host-Network-Dataset -LANL`

**Вопрос:** Для каждого датасета: сколько всего сэмплов, benign vs malicious, сколько признаков?  
**Ответ:** Полных чисел в репозитории нет. Подтверждаемые значения:
- `CIC-Bell-DNS-2021`: около 1,000,000 доменов, около 99% benign (утверждение из документации).
- Для остальных датасетов в репозитории не указаны: total samples / class split / feature count.

**Вопрос:** Были отдельные датасеты для network и host или один?  
**Ответ:** Используются отдельные датасеты и отдельные пайплайны (`dns` и `host` обрабатываются независимо).

**Вопрос:** Если host-признаки симулировались/выводились из network, что именно сделано?  
**Ответ:** Реализации такой симуляции/вывода в коде не найдено. Есть только формулировка в proposal, что feature-level simulation может применяться при отсутствии парных host/network данных.

---

## 2. Data Preprocessing (Section 3.4.1)

**Вопрос:** Как обрабатывались missing values?  
**Ответ:** Реализация обработки пропусков для модельных признаков отсутствует.

**Вопрос:** Какая нормализация использовалась?  
**Ответ:** Нормализация/скейлинг не реализованы (`MinMaxScaler`, `StandardScaler` и т.д. не найдены).

**Вопрос:** Как кодировались категориальные признаки?  
**Ответ:** Реализация кодирования категориальных признаков не найдена.

**Вопрос:** Какой train/test split или только cross-validation?  
**Ответ:** Числовой train/test split в коде не задан. В документах указана планируемая stratified k-fold cross-validation, но без конкретного числа фолдов/конфига.

---

## 3. Class Imbalance (Section 3.4.3)

**Вопрос:** Применялись SMOTE/undersampling/class weights или другое?  
**Ответ:** Реализации методов борьбы с дисбалансом классов не найдено.

---

## 4. Model Architecture Details (Sections 3.5.2 and 3.5.3)

**Вопрос:** Параметры/tuning для Random Forest?  
**Ответ:** Не указаны в коде и конфигурациях экспериментов.

**Вопрос:** Параметры/tuning для XGBoost?  
**Ответ:** Не указаны.

**Вопрос:** Детали архитектуры CNN?  
**Ответ:** Не указаны.

**Вопрос:** Детали LSTM (layers/units/dropout/optimizer и т.д.)?  
**Ответ:** Не указаны. Есть только proposal-уровень: LSTM для sequence-level binary classification.

---

## 5. Sequence Construction (Section 3.6)

**Вопрос:** Сколько событий в последовательности?  
**Ответ:** В proposal указано плановое значение 50-100 событий на последовательность. В коде фактическая реализация отсутствует.

**Вопрос:** Размер шага окна / overlap?  
**Ответ:** Не задано.

**Вопрос:** Как выравнивались события разных модальностей по времени?  
**Ответ:** Явного алгоритма выравнивания в коде не найдено.

---

## 6. Decision Fusion (Section 3.5.4)

**Вопрос:** Точный механизм fusion?  
**Ответ:** На уровне proposal: late fusion через агрегацию вероятностей classification и sequence-компонентов.

**Вопрос:** Если веса, как они определялись?  
**Ответ:** Не указано.

---

## 7. SHAP Variants (Section 3.7)

**Вопрос:** TreeSHAP для RF/XGBoost?  
**Ответ:** Не указано.

**Вопрос:** DeepSHAP/KernelSHAP для CNN/LSTM?  
**Ответ:** Не указано. Упоминается только общий SHAP-based feature attribution.

---

## 8. Experimental Environment (Section 3.8)

**Вопрос:** Сколько фолдов cross-validation?  
**Ответ:** Упомянута stratified k-fold cross-validation, но конкретное `k` не задано.

**Вопрос:** Какие statistical significance tests использовались?  
**Ответ:** Не указаны (paired t-test/Wilcoxon не найдены).

**Вопрос:** Hardware (CPU/GPU/RAM)?
**Ответ:** Не указано. В документации есть только общий комментарий, что при необходимости можно использовать облачные ресурсы (например Colab/Kaggle).

**Вопрос:** Software версии (Python/libs)?  
**Ответ:** Для ML-стека не указаны. В `requirements.txt` только:
- `python-dotenv`
- `rich`
Версии не зафиксированы, ML-библиотеки не перечислены.

**Вопрос:** Random seed для воспроизводимости?  
**Ответ:** Не указан.

---

## Дополнительные факты по текущей реализации (dataset preparation stage)

**Вопрос:** Что реально реализовано в текущем коде?  
**Ответ:** Сканирование датасетов, assignment ролей, фильтрация host, сортировка по форматам, экспорт путей в JSON.

**Вопрос:** Какие объёмы подтверждены артефактами репозитория?  
**Ответ:**
- DNS sorted/exported files: 35 (`temp_data/sort-path-dns-file-summary.json`)
- Host filtered kept file paths: 361,646 (`PATH_REPORT/en/stage-one/Task3...` и `temp_data/sort-path-host-file-summary.json`)

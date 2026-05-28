# Стратегия DNS-датасетов (текущий scope)

## 1. Назначение
Документ фиксирует DNS-датасеты, которые фактически используются в проекте.

Текущий DNS scope:
- `TRAIN`: обучение на атакующем и benign-поведении
- `VALIDATION`: контроль false positives
- `TEST`: независимая проверка реалистичности и переносимости
- DNS `EXPERIMENTS`: не используются

## 2. Активные DNS-датасеты

### 2.1 CIC-Bell-DNS-EXF-2021
Роль: `TRAIN` (attack-class behavior)

Использование:
- паттерны DNS exfiltration / tunneling
- извлечение табличных и временных признаков для classifier + sequence-ветки

Ссылка: <https://www.unb.ca/cic/datasets/dns-exf-2021.html>

### 2.2 CIC-Bell-DNS-2021
Роль: `TRAIN` + `VALIDATION` (benign baseline и контроль FP)

Использование:
- baseline нормального DNS-поведения
- балансировка benign-класса
- калибровка ложных срабатываний

Ссылка: <https://www.unb.ca/cic/datasets/dns-2021.html>

### 2.3 Mendeley DNS Exfiltration Dataset
Роль: `TEST` (внешняя проверка реалистичности/generalization)

Использование:
- независимая валидация на данных со сдвигом распределения
- проверка переносимости и устойчивости

Ссылка: <https://data.mendeley.com/datasets/c4n7fckkz3/3>

## 3. Матрица ролей (текущее состояние)

| Роль | Датасет | Назначение |
|---|---|---|
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | обучение атакующим паттернам |
| `TRAIN` | CIC-Bell-DNS-2021 | обучение нормальному DNS-поведению |
| `VALIDATION` | split CIC-Bell-DNS-2021 | контроль false positives и настройка порога |
| `TEST` | Mendeley DNS Exfiltration Dataset | проверка междатасетной переносимости |

## 4. Схема использования

```text
TRAIN:
  - CIC-Bell-DNS-EXF-2021
  - CIC-Bell-DNS-2021

VALIDATION:
  - split CIC-Bell-DNS-2021

TEST:
  - Mendeley DNS Exfiltration Dataset
```

## 5. Ограничение scope
В DNS-ветке используются только перечисленные выше датасеты.

## 6. Краткий вывод
Обязательные и активные DNS-источники:
1. `CIC-Bell-DNS-EXF-2021`
2. `CIC-Bell-DNS-2021`
3. `Mendeley DNS Exfiltration Dataset`

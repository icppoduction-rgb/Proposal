# Анализ формата: ghc

## 1. Назначение
`ghc` в `TRAIN` содержит текстовые trace-последовательности вида `<module>+0x<offset>` для анализа поведения процессов host.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | ghc |
| Варианты расширения | `.ghc`, `.GHC` |
| DNS | нет |
| Host | да |
| Роли | TRAIN |
| Количество файлов | 56158 |

## 3. Примеры файлов
```text
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-0.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-1.GHC
C:\Users\Public\PythonProjects\storages\datasets-filter\host\TRAIN\ghc\S1-1-Full_1040-10.GHC
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | space |
| Кодировка | utf-8 (30) |
| Вложенная структура | нет |
| Sample-файлов проанализировано | 30 |
| Sample-строк проанализировано | 30 |
| Token count | 6000 |
| Valid trace tokens | 6000 |

## 5. Содержательная структура
Данные представляют последовательности trace-токенов, похожих на stack frame адреса:
- имя модуля (`kernel32.dll`);
- смещение в hex-формате (`0xb50b`);
- порядок токенов внутри строки как sequence-поведение.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| trace.token | string | исходный токен trace | `kernel32.dll+0xb50b` |
| trace.module | string | имя модуля/библиотеки | `kernel32.dll` |
| trace.offset_hex | string | смещение в hex | `0xb50b` |
| filename.scenario_tag | string | сценарный префикс имени файла | `S1-1-Full` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | partially |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | not present |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты модулей (`top_modules_detected`);
- n-grams trace-токенов;
- переходы между модулями;
- длина trace-последовательности;
- распределение offset по модулям.

### Network / hybrid-признаки
- корреляция trace-последовательностей с process/network событиями по общему host и времени из внешних источников.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | count: 0 |
| Повреждённые файлы | нет | parse errors: 0 |
| Missing values | нет | invalid tokens: 0 |
| Нестабильная структура | нет | non-trace tokens exist |
| Смешанные схемы | нет | includes tokens outside `<module>+0x<hex>` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | NEEDS_CUSTOM_PARSER |
| Нужен отдельный парсер | да |
| Приоритет обработки | high |

## 12. Вывод
`TRAIN/ghc` пригоден для этапа feature extraction только через отдельный специализированный parser.
Статистика токенов на файл (sample): min=200.0, max=200.0, avg=200.0.

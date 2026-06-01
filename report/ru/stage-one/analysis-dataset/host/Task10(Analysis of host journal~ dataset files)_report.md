# РћС‚С‡С‘С‚: Task10 (Analysis of host journal~ dataset files)

## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё
Р РµР°Р»РёР·РѕРІР°РЅ РѕС‚РґРµР»СЊРЅС‹Р№ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° С„РѕСЂРјР°С‚Р° `TRAIN/journal~` РЅР° РѕСЃРЅРѕРІРµ `temp_data/sort-path-host-file.json` СЃ РіРµРЅРµСЂР°С†РёРµР№ РґРѕРєСѓРјРµРЅС‚Р°С†РёРё RU/EN.

## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹/РёР·РјРµРЅРµРЅС‹
- `scripts/handlers/analyze_host_journal_tilde_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/journal~.md`
- `docs/en/analysis-dataset/host/journal~.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `temp_data/analysis-host-journal-tilde-summary.json`

## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON
- Р±РёРЅР°СЂРЅР°СЏ СЃРёРіРЅР°С‚СѓСЂР°: `LPKSHHRH`
- С‚РёРї: Р±РёРЅР°СЂРЅС‹Р№ container
- СЃС‚Р°С‚СѓСЃ РїСЂРёРіРѕРґРЅРѕСЃС‚Рё: `NEEDS_CUSTOM_PARSER`

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. РЎС‡РёС‚С‹РІР°РµС‚СЃСЏ `sort-path-host-file.json`.
2. Р’С‹Р±РёСЂР°РµС‚СЃСЏ bucket: `TRAIN -> journal~`.
3. РџР°СЂР°Р»Р»РµР»СЊРЅРѕ С‡РёС‚Р°РµС‚СЃСЏ `sort-path-dns-file.json` РґР»СЏ РІР°Р»РёРґР°С†РёРё РєРѕРЅС‚РµРєСЃС‚Р° DNS/Host Р±РµР· СЃРјРµС€РёРІР°РЅРёСЏ РґР°РЅРЅС‹С….
4. Р”Р»СЏ Р°РЅР°Р»РёР·Р° Р±РµСЂС‘С‚СЃСЏ РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sample С„Р°Р№Р»РѕРІ Рё С‚РѕР»СЊРєРѕ Р±РµР·РѕРїР°СЃРЅС‹Р№ header sample bytes.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "journal~",
    "total_files_count": 1,
    "sampled_files_count": 1,
    "max_files_per_format": 30
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "journal~",
    "dns_formats_detected_count": 3
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Р РµР·СѓР»СЊС‚Р°С‚
- Р’СЃРµРіРѕ С„Р°Р№Р»РѕРІ С„РѕСЂРјР°С‚Р°: `1`.
- Sample-С„Р°Р№Р»РѕРІ РїСЂРѕР°РЅР°Р»РёР·РёСЂРѕРІР°РЅРѕ: `1`.
- РС‚РѕРіРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ: `NEEDS_CUSTOM_PARSER`.

## РђСЂС‚РµС„Р°РєС‚С‹
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-journal-tilde-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\journal~.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\journal~.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`

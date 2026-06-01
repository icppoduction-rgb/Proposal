# РћС‚С‡С‘С‚: Task12 (Analysis of host json-1 dataset files)

## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё
РџРµСЂРµРґРµР»Р°РЅ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° `TRAIN/json-1` СЃ РіРµРЅРµСЂР°С†РёРµР№ RU/EN-РґРѕРєСѓРјРµРЅС‚Р°С†РёРё Рё РѕР±РЅРѕРІР»РµРЅРёРµРј README РёРЅРґРµРєСЃРѕРІ.

## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹ РёР»Рё РёР·РјРµРЅРµРЅС‹
- `scripts/handlers/analyze_host_json_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/json.md`
- `docs/en/analysis-dataset/host/json.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task12(Analysis of host json-1 dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task12(Analysis of host json-1 dataset files)_report.md`
- `temp_data/analysis-host-json-summary.json`

## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON
- json_document: `0`
- json_lines: `1`
- unparsed: `0`

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. Р—Р°РіСЂСѓР¶РµРЅ `sort-path-host-file.json`.
2. Р’С‹Р±СЂР°РЅ bucket `TRAIN -> json`.
3. РџСЂРёРјРµРЅРµРЅР° СЂР°РІРЅРѕРјРµСЂРЅР°СЏ РІС‹Р±РѕСЂРєР° С„Р°Р№Р»РѕРІ РїРѕ РІСЃРµРјСѓ РґРёР°РїР°Р·РѕРЅСѓ РёРјРµРЅ.
4. Р”Р»СЏ РєР°Р¶РґРѕРіРѕ sample-С„Р°Р№Р»Р° РІС‹РїРѕР»РЅРµРЅ Р°РЅР°Р»РёР· РєР°Рє `json document`, Р·Р°С‚РµРј fallback РІ `json-lines`.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "json-1",
    "total_files_count": 1,
    "sampled_files_count": 1,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 1,
      "unparsed": 0
    }
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-json-1-summary.json`

# РћС‚С‡С‘С‚: Task29 (Analysis of host pcap dataset files)

## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё
РџРµСЂРµРґРµР»Р°РЅ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° `TRAIN/pcap` СЃ РіРµРЅРµСЂР°С†РёРµР№ RU/EN-РґРѕРєСѓРјРµРЅС‚Р°С†РёРё Рё РѕР±РЅРѕРІР»РµРЅРёРµРј README РёРЅРґРµРєСЃРѕРІ.

## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹ РёР»Рё РёР·РјРµРЅРµРЅС‹
- `scripts/handlers/analyze_host_pcap_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/pcap.md`
- `docs/en/analysis-dataset/host/pcap.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`
- `temp_data/analysis-host-pcap-summary.json`

## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON
- json_document: `0`
- json_lines: `0`
- unparsed: `0`

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. Р—Р°РіСЂСѓР¶РµРЅ `sort-path-host-file.json`.
2. Р’С‹Р±СЂР°РЅ bucket `TRAIN -> pcap`.
3. РџСЂРёРјРµРЅРµРЅР° СЂР°РІРЅРѕРјРµСЂРЅР°СЏ РІС‹Р±РѕСЂРєР° С„Р°Р№Р»РѕРІ РїРѕ РІСЃРµРјСѓ РґРёР°РїР°Р·РѕРЅСѓ РёРјРµРЅ.
4. Р”Р»СЏ РєР°Р¶РґРѕРіРѕ sample-С„Р°Р№Р»Р° РІС‹РїРѕР»РЅРµРЅ Р°РЅР°Р»РёР· РєР°Рє `json document`, Р·Р°С‚РµРј fallback РІ `json-lines`.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "pcap",
    "total_files_count": 15,
    "sampled_files_count": 15,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 0,
      "raw_text": 15,
      "unparsed": 0
    }
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-pcap-summary.json`

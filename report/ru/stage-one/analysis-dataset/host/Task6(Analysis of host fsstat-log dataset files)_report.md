# РћС‚С‡С‘С‚: Task6 (Analysis of host fsstat-log dataset files)

## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё
Р РµР°Р»РёР·РѕРІР°РЅ РѕС‚РґРµР»СЊРЅС‹Р№ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° С„РѕСЂРјР°С‚Р° `TRAIN/fsstat.log` РЅР° РѕСЃРЅРѕРІРµ `temp_data/sort-path-host-file.json` СЃ РіРµРЅРµСЂР°С†РёРµР№ РґРѕРєСѓРјРµРЅС‚Р°С†РёРё РЅР° RU/EN.

## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹/РёР·РјРµРЅРµРЅС‹
- `scripts/handlers/analyze_host_fsstat_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/fsstat.log.md`
- `docs/en/analysis-dataset/host/fsstat.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `temp_data/analysis-host-fsstat-log-summary.json`

## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON
- top-level keys: metricset, agent, tags, host, @version, system, @timestamp, service, event, ecs
- dataset: `system.fsstat`
- РІР»РѕР¶РµРЅРЅС‹Рµ РїРѕР»СЏ: `system.fsstat.count/total_files/total_size.used/total_size.free/total_size.total`.

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. РЎС‡РёС‚С‹РІР°РµС‚СЃСЏ `sort-path-host-file.json`.
2. Р’С‹Р±РёСЂР°РµС‚СЃСЏ bucket: `TRAIN -> fsstat.log`.
3. РџР°СЂР°Р»Р»РµР»СЊРЅРѕ С‡РёС‚Р°РµС‚СЃСЏ `sort-path-dns-file.json` РґР»СЏ РІР°Р»РёРґР°С†РёРё РєРѕРЅС‚РµРєСЃС‚Р° DNS/Host Р±РµР· СЃРјРµС€РёРІР°РЅРёСЏ РґР°РЅРЅС‹С….
4. Р”Р»СЏ Р°РЅР°Р»РёР·Р° Р±РµСЂС‘С‚СЃСЏ РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sample С„Р°Р№Р»РѕРІ Рё СЃС‚СЂРѕРє.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "fsstat.log",
    "total_files_count": 12,
    "sampled_files_count": 12,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "fsstat.log",
    "dns_formats_detected_count": 3
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Р РµР·СѓР»СЊС‚Р°С‚
- Р’СЃРµРіРѕ С„Р°Р№Р»РѕРІ С„РѕСЂРјР°С‚Р°: `12`.
- Sample-С„Р°Р№Р»РѕРІ РїСЂРѕР°РЅР°Р»РёР·РёСЂРѕРІР°РЅРѕ: `12`.
- РС‚РѕРіРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ: `READY_FOR_FEATURE_EXTRACTION`.

## РђСЂС‚РµС„Р°РєС‚С‹
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-fsstat-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\fsstat.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\fsstat.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`

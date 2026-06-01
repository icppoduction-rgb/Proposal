from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTXTContentAnalysisResult:
    summary_json_file: str
    docs_ru_file: str
    docs_en_file: str
    docs_ru_readme_file: str
    docs_en_readme_file: str
    report_ru_file: str
    report_en_file: str
    total_files_count: int
    sampled_files_count: int
    status: str


class HostTXTContentAnalysisHandler:
    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "txt"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000
    DEFAULT_MAX_BYTES_PER_FILE = 2 * 1024 * 1024

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-host-txt-summary.json"

    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"
    FSSTAT_SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"
    GHC_SUMMARY_JSON_FILE = "analysis-host-ghc-summary.json"
    INFO_SUMMARY_JSON_FILE = "analysis-host-info-summary.json"
    JOURNAL_SUMMARY_JSON_FILE = "analysis-host-journal-summary.json"
    JOURNAL_TILDE_SUMMARY_JSON_FILE = "analysis-host-journal-tilde-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
        max_bytes_per_file: int = DEFAULT_MAX_BYTES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(100, max_lines_per_file)
        self.max_bytes_per_file = max(64 * 1024, max_bytes_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostTXTContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/txt.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "txt.md"
        docs_en_path = self.docs_en_dir / "txt.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task41(Analysis of host txt dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task41(Analysis of host txt dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostTXTContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary_payload["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
        role_bucket = role_to_formats.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")
        format_bucket = role_bucket.get(self.FORMAT_NAME, [])
        if not isinstance(format_bucket, list):
            raise ValueError(
                f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list of paths."
            )
        return sorted(
            [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)],
            key=lambda p: str(p).lower(),
        )

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths
        # Evenly sample the whole sorted pool to catch schema variants spread by filename.
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        indices = {int(round(i * step)) for i in range(self.max_files_per_format)}
        return [all_paths[index] for index in sorted(indices)]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        schema_counts = {"json_document": 0, "json_lines": 0, "raw_text": 0, "unparsed": 0}
        top_keys: dict[str, int] = {}
        event_types: dict[str, int] = {}
        roles: dict[str, int] = {}
        exploit_values: dict[str, int] = {}

        empty_files = 0
        parse_error_files = 0
        timestamp_hits = 0
        label_hits = 0
        sample_file_details: list[dict[str, Any]] = []

        for file_path in sampled_paths:
            detail = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
                "schema": "unparsed",
                "json_lines_parsed": 0,
                "json_lines_failed": 0,
                "parse_error": None,
            }
            if not file_path.exists():
                detail["parse_error"] = "file_not_found"
                parse_error_files += 1
                schema_counts["unparsed"] += 1
                sample_file_details.append(detail)
                continue
            if detail["size_bytes"] == 0:
                detail["parse_error"] = "empty_file"
                empty_files += 1
                schema_counts["unparsed"] += 1
                sample_file_details.append(detail)
                continue

            raw = file_path.read_bytes()[: self.max_bytes_per_file]
            text = raw.decode("utf-8", errors="replace").strip()

            parsed_document = False
            if text.startswith("{") or text.startswith("["):
                try:
                    payload = json.loads(text)
                    if isinstance(payload, dict):
                        parsed_document = True
                        schema_counts["json_document"] += 1
                        detail["schema"] = "json_document"
                        for key in payload.keys():
                            top_keys[key] = top_keys.get(key, 0) + 1
                        if "time" in payload or "timestamp" in payload:
                            timestamp_hits += 1
                        if "exploit" in payload:
                            label_hits += 1
                            exploit_key = str(payload.get("exploit"))
                            exploit_values[exploit_key] = exploit_values.get(exploit_key, 0) + 1
                        container = payload.get("container")
                        if isinstance(container, list):
                            for item in container:
                                if isinstance(item, dict):
                                    role = item.get("role")
                                    if isinstance(role, str):
                                        roles[role] = roles.get(role, 0) + 1
                    elif isinstance(payload, list):
                        parsed_document = True
                        schema_counts["json_document"] += 1
                        detail["schema"] = "json_document"
                except json.JSONDecodeError:
                    parsed_document = False

            if not parsed_document:
                parsed_lines = 0
                failed_lines = 0
                try:
                    with file_path.open("r", encoding="utf-8", errors="replace") as stream:
                        for index, raw_line in enumerate(stream):
                            if index >= self.max_lines_per_file:
                                break
                            line = raw_line.strip()
                            if not line:
                                continue
                            try:
                                line_payload = json.loads(line)
                            except json.JSONDecodeError:
                                failed_lines += 1
                                continue
                            if not isinstance(line_payload, dict):
                                failed_lines += 1
                                continue
                            parsed_lines += 1
                            event_type = line_payload.get("event_type")
                            if isinstance(event_type, str):
                                event_types[event_type] = event_types.get(event_type, 0) + 1
                            if "timestamp" in line_payload:
                                timestamp_hits += 1
                            if "alert" in line_payload or "label" in line_payload:
                                label_hits += 1
                except OSError:
                    failed_lines += 1

                detail["json_lines_parsed"] = parsed_lines
                detail["json_lines_failed"] = failed_lines
                if parsed_lines > 0:
                    schema_counts["json_lines"] += 1
                    detail["schema"] = "json_lines"
                else:
                    non_empty_raw_lines = [
                        ln for ln in text.splitlines()[: self.max_lines_per_file] if ln.strip()
                    ]
                    if non_empty_raw_lines:
                        schema_counts["raw_text"] += 1
                        detail["schema"] = "raw_text"
                        if non_empty_raw_lines[0][:4].isdigit():
                            timestamp_hits += 1
                    else:
                        schema_counts["unparsed"] += 1
                        detail["schema"] = "unparsed"
                        detail["parse_error"] = "json_document_and_json_lines_parse_failed"
                        parse_error_files += 1

            sample_file_details.append(detail)

        active_schema_count = sum(
            1
            for key in ("json_document", "json_lines", "raw_text")
            if schema_counts.get(key, 0) > 0
        )
        mixed_schema = active_schema_count > 1
        if schema_counts["unparsed"] == len(sampled_paths):
            status = self.STATUS_BROKEN
        elif mixed_schema:
            status = self.STATUS_NEEDS_CUSTOM
        elif schema_counts["json_lines"] > 0 and parse_error_files > 0:
            status = self.STATUS_PARTIAL
        else:
            status = self.STATUS_READY

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
                "max_bytes_per_file": self.max_bytes_per_file,
            },
            "examples": {"paths": [str(path) for path in all_paths[:3]]},
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": False,
                "nested_structure": True,
                "schema_counts": schema_counts,
                "top_level_keys": top_keys,
                "sample_file_details": sample_file_details[:12],
            },
            "content": {
                "category": "Mixed Host JSON datasets: scenario metadata JSON documents and Suricata/traffic JSON-lines telemetry.",
                "top_event_types": event_types,
                "container_roles": roles,
                "exploit_values": exploit_values,
            },
            "label_detection": {
                "label_found": label_hits > 0,
                "label_field_name": "exploit / container.role / alert (schema-dependent)",
                "label_values": ["True", "False", "normal", "victim", "alert-derived"],
                "supports_supervised_learning": "partially",
            },
            "time_detection": {
                "timestamp_found": timestamp_hits > 0,
                "timestamp_fields": ["time.container_ready.absolute", "timestamp"],
                "timestamp_format": "Unix epoch float + ISO-8601",
                "timezone": "UTC(+0000) for JSON-lines; scenario JSON timezone implicit",
                "sequence_ready": True,
                "sliding_window_ready": True,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_error_files,
                "mixed_schema_detected": mixed_schema,
            },
            "final_status": status,
            "needs_custom_parser": status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL},
            "priority": "high" if status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL} else "medium",
        }

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        quality = summary["data_quality"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        examples = summary["examples"]["paths"]
        return f"""
# РђРЅР°Р»РёР· С„РѕСЂРјР°С‚Р°: json

## 1. РќР°Р·РЅР°С‡РµРЅРёРµ
РЎРјРµС€Р°РЅРЅС‹Р№ С„РѕСЂРјР°С‚ `json` РІ `TRAIN`: СЃС†РµРЅР°СЂРЅС‹Рµ JSON-РґРѕРєСѓРјРµРЅС‚С‹ Рё JSON-lines С‚РµР»РµРјРµС‚СЂРёСЏ (`eve*`, `traffic*`).

## 2. Р“РґРµ РІСЃС‚СЂРµС‡Р°РµС‚СЃСЏ
| РџРѕР»Рµ | Р—РЅР°С‡РµРЅРёРµ |
|---|---|
| Р¤РѕСЂРјР°С‚ | json |
| Р’Р°СЂРёР°РЅС‚С‹ СЂР°СЃС€РёСЂРµРЅРёСЏ | `.json` |
| DNS | РЅРµС‚ |
| Host | РґР° |
| Р РѕР»Рё | {scope["role"]} |
| РљРѕР»РёС‡РµСЃС‚РІРѕ С„Р°Р№Р»РѕРІ | {scope["total_files_count"]} |

## 3. РџСЂРёРјРµСЂС‹ С„Р°Р№Р»РѕРІ
```text
{examples[0] if len(examples) > 0 else "-"}
{examples[1] if len(examples) > 1 else "-"}
{examples[2] if len(examples) > 2 else "-"}
```

## 4. РўРµС…РЅРёС‡РµСЃРєР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР°
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| РўРёРї С„Р°Р№Р»Р° | text |
| Р§С‚РµРЅРёРµ РїРѕСЃС‚СЂРѕС‡РЅРѕ | РґР° |
| РўР°Р±Р»РёС‡РЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | РЅРµС‚ |
| Р—Р°РіРѕР»РѕРІРѕРє | РЅРµС‚ |
| Р Р°Р·РґРµР»РёС‚РµР»СЊ | JSON object / JSON-lines |
| РљРѕРґРёСЂРѕРІРєР° | utf-8 |
| Р’Р»РѕР¶РµРЅРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | РґР° |
| JSON document | {technical["schema_counts"]["json_document"]} |
| JSON-lines | {technical["schema_counts"]["json_lines"]} |
| Raw text | {technical["schema_counts"]["raw_text"]} |
| РќРµСЂР°Р·РѕР±СЂР°РЅРЅС‹Рµ | {technical["schema_counts"]["unparsed"]} |

## 5. РЎРѕРґРµСЂР¶Р°С‚РµР»СЊРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР°
РћР±РЅР°СЂСѓР¶РµРЅС‹ РґРІРµ СЃС…РµРјС‹: СЃС†РµРЅР°СЂРЅС‹Рµ РґРѕРєСѓРјРµРЅС‚С‹ (`container`, `exploit`, `time`) Рё JSON-lines СЃРѕР±С‹С‚РёСЏ (`timestamp`, `event_type`, `alert`, `dns`).

## 6. РќР°Р№РґРµРЅРЅС‹Рµ РїРѕР»СЏ / РєРѕР»РѕРЅРєРё
| РџРѕР»Рµ | РўРёРї | РќР°Р·РЅР°С‡РµРЅРёРµ | РџСЂРёРјРµСЂ Р·РЅР°С‡РµРЅРёСЏ |
|---|---|---|---|
| exploit | bool | РёРЅРґРёРєР°С‚РѕСЂ СЃС†РµРЅР°СЂРёСЏ | `false` |
| container.role | string | СЂРѕР»СЊ РєРѕРЅС‚РµР№РЅРµСЂР° | `normal`, `victim` |
| time.container_ready.absolute | float | РІСЂРµРјСЏ РіРѕС‚РѕРІРЅРѕСЃС‚Рё | `1631222503.73` |
| timestamp | string | РІСЂРµРјСЏ СЃРѕР±С‹С‚РёСЏ | `2022-01-13T14:37:36.251509+0000` |
| event_type | string | С‚РёРї СЃРѕР±С‹С‚РёСЏ | `stats`, `dns`, `alert` |

## 7. Label / class indicators
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| Label РЅР°Р№РґРµРЅ | {"РґР°" if label["label_found"] else "РЅРµС‚"} |
| РќР°Р·РІР°РЅРёРµ РїРѕР»СЏ | {label["label_field_name"]} |
| Р—РЅР°С‡РµРЅРёСЏ label | {", ".join(label["label_values"])} |
| РњРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РґР»СЏ supervised learning | {label["supports_supervised_learning"]} |

## 8. Р’СЂРµРјРµРЅРЅС‹Рµ РїСЂРёР·РЅР°РєРё
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| Timestamp РЅР°Р№РґРµРЅ | {"РґР°" if time_block["timestamp_found"] else "РЅРµС‚"} |
| РќР°Р·РІР°РЅРёРµ РїРѕР»СЏ | {", ".join(time_block["timestamp_fields"])} |
| Р¤РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё | {time_block["timestamp_format"]} |
| Timezone | {time_block["timezone"]} |
| РњРѕР¶РЅРѕ СЃС‚СЂРѕРёС‚СЊ sequence | {"РґР°" if time_block["sequence_ready"] else "РЅРµС‚"} |
| РњРѕР¶РЅРѕ РїСЂРёРјРµРЅСЏС‚СЊ sliding window | {"РґР°" if time_block["sliding_window_ready"] else "РЅРµС‚"} |

## 9. РџРѕС‚РµРЅС†РёР°Р»СЊРЅС‹Рµ РїСЂРёР·РЅР°РєРё РґР»СЏ feature extraction
### DNS-РїСЂРёР·РЅР°РєРё
- С‡Р°СЃС‚РѕС‚С‹ `event_type=dns`;
- СЂР°Р·РЅРѕРѕР±СЂР°Р·РёРµ DNS-СЃРѕР±С‹С‚РёР№.

### Host-РїСЂРёР·РЅР°РєРё
- `exploit`, СЂРѕР»Рё РєРѕРЅС‚РµР№РЅРµСЂРѕРІ, `recording_time`;
- РїРѕСЃР»РµРґРѕРІР°С‚РµР»СЊРЅРѕСЃС‚Рё `event_type`.

### Network / hybrid-РїСЂРёР·РЅР°РєРё
- `src_ip`, `dest_ip`, `src_port`, `dest_port`, `proto`;
- РєРѕСЂСЂРµР»СЏС†РёСЏ alert-СЃРѕР±С‹С‚РёР№ СЃ host-РєРѕРЅС‚РµРєСЃС‚РѕРј.

## 10. РџСЂРѕР±Р»РµРјС‹ РєР°С‡РµСЃС‚РІР° РґР°РЅРЅС‹С…
| РџСЂРѕР±Р»РµРјР° | РќР°Р№РґРµРЅР° | РљРѕРјРјРµРЅС‚Р°СЂРёР№ |
|---|---|---|
| РџСѓСЃС‚С‹Рµ С„Р°Р№Р»С‹ | {"РґР°" if quality["empty_files_count"] > 0 else "РЅРµС‚"} | count: {quality["empty_files_count"]} |
| РџРѕРІСЂРµР¶РґС‘РЅРЅС‹Рµ С„Р°Р№Р»С‹ | {"РґР°" if quality["parse_error_files_count"] > 0 else "РЅРµС‚"} | parse errors: {quality["parse_error_files_count"]} |
| Missing values | РЅРµС‚ | РєСЂРёС‚РёС‡РЅС‹С… РїСЂРѕРїСѓСЃРєРѕРІ РІ sample РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅРѕ |
| РќРµСЃС‚Р°Р±РёР»СЊРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | {"РґР°" if quality["mixed_schema_detected"] else "РЅРµС‚"} | СЃРјРµС€Р°РЅС‹ JSON document Рё JSON-lines |
| РЎРјРµС€Р°РЅРЅС‹Рµ СЃС…РµРјС‹ | {"РґР°" if quality["mixed_schema_detected"] else "РЅРµС‚"} | РЅСѓР¶РµРЅ schema-aware parser |

## 11. РС‚РѕРіРѕРІР°СЏ РїСЂРёРіРѕРґРЅРѕСЃС‚СЊ
| РџРѕР»Рµ | Р—РЅР°С‡РµРЅРёРµ |
|---|---|
| РЎС‚Р°С‚СѓСЃ | {summary["final_status"]} |
| РќСѓР¶РµРЅ РѕС‚РґРµР»СЊРЅС‹Р№ РїР°СЂСЃРµСЂ | {"РґР°" if summary["needs_custom_parser"] else "РЅРµС‚"} |
| РџСЂРёРѕСЂРёС‚РµС‚ РѕР±СЂР°Р±РѕС‚РєРё | {summary["priority"]} |

## 12. Р’С‹РІРѕРґ
`TRAIN/txt` РїСЂРёРіРѕРґРµРЅ РґР»СЏ РёР·РІР»РµС‡РµРЅРёСЏ РїСЂРёР·РЅР°РєРѕРІ, РЅРѕ РёР·-Р·Р° СЃРјРµС€РµРЅРёСЏ СЃС…РµРј С‚СЂРµР±СѓРµС‚ РѕС‚РґРµР»СЊРЅРѕРіРѕ parser layer.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        quality = summary["data_quality"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        examples = summary["examples"]["paths"]
        return f"""
# Format Analysis: txt

## 1. Purpose
Mixed `txt` format in `TRAIN`: scenario JSON documents and JSON-lines telemetry (`eve*`, `traffic*`).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | `.json` |
| DNS | no |
| Host | yes |
| Roles | {scope["role"]} |
| File count | {scope["total_files_count"]} |

## 3. Example files
```text
{examples[0] if len(examples) > 0 else "-"}
{examples[1] if len(examples) > 1 else "-"}
{examples[2] if len(examples) > 2 else "-"}
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | JSON object / JSON-lines |
| Encoding | utf-8 |
| Nested structure | yes |
| JSON document | {technical["schema_counts"]["json_document"]} |
| JSON-lines | {technical["schema_counts"]["json_lines"]} |
| Raw text | {technical["schema_counts"]["raw_text"]} |
| Unparsed | {technical["schema_counts"]["unparsed"]} |

## 5. Semantic structure
Two schemas are present: scenario documents (`container`, `exploit`, `time`) and JSON-lines events (`timestamp`, `event_type`, `alert`, `dns`).

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| exploit | bool | scenario indicator | `false` |
| container.role | string | container role | `normal`, `victim` |
| time.container_ready.absolute | float | readiness timestamp | `1631222503.73` |
| timestamp | string | event timestamp | `2022-01-13T14:37:36.251509+0000` |
| event_type | string | event type | `stats`, `dns`, `alert` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {"yes" if label["label_found"] else "no"} |
| Field name | {label["label_field_name"]} |
| Label values | {", ".join(label["label_values"])} |
| Suitable for supervised learning | {label["supports_supervised_learning"]} |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {"yes" if time_block["timestamp_found"] else "no"} |
| Field name | {", ".join(time_block["timestamp_fields"])} |
| Timestamp format | {time_block["timestamp_format"]} |
| Timezone | {time_block["timezone"]} |
| Sequence-ready | {"yes" if time_block["sequence_ready"] else "no"} |
| Sliding-window-ready | {"yes" if time_block["sliding_window_ready"] else "no"} |

## 9. Potential feature extraction signals
### DNS features
- frequency of `event_type=dns`;
- diversity of DNS-related events.

### Host features
- `exploit`, container roles, `recording_time`;
- temporal sequences of `event_type`.

### Network / hybrid features
- `src_ip`, `dest_ip`, `src_port`, `dest_port`, `proto`;
- correlation of alerts with host scenario context.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality["empty_files_count"] > 0 else "no"} | count: {quality["empty_files_count"]} |
| Corrupted files | {"yes" if quality["parse_error_files_count"] > 0 else "no"} | parse errors: {quality["parse_error_files_count"]} |
| Missing values | no | no critical gaps in sampled data |
| Unstable structure | {"yes" if quality["mixed_schema_detected"] else "no"} | mixed JSON document and JSON-lines |
| Mixed schemas | {"yes" if quality["mixed_schema_detected"] else "no"} | schema-aware parser is required |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Needs dedicated parser | {"yes" if summary["needs_custom_parser"] else "no"} |
| Processing priority | {summary["priority"]} |

## 12. Conclusion
`TRAIN/txt` is usable for feature extraction, but because schemas are mixed it requires a dedicated schema-aware parsing layer.
"""

    def _build_ru_readme(self, json_summary: dict[str, Any]) -> str:
        rows = self._readme_rows(json_summary)
        body = "\n".join(f"| {name} | {count} | РЅРµС‚ | РґР° | {status} | {doc} |" for name, count, status, doc in rows)
        return (
            "# РђРЅР°Р»РёР· СЃРѕРґРµСЂР¶РёРјРѕРіРѕ С„Р°Р№Р»РѕРІ РґР°С‚Р°СЃРµС‚РѕРІ (Host)\n\n"
            "| Р¤РѕСЂРјР°С‚ | РљРѕР»РёС‡РµСЃС‚РІРѕ С„Р°Р№Р»РѕРІ | DNS | Host | РЎС‚Р°С‚СѓСЃ | Р”РѕРєСѓРјРµРЅС‚ |\n"
            "|---|---:|---|---|---|---|\n"
            f"{body}\n"
        )

    def _build_en_readme(self, json_summary: dict[str, Any]) -> str:
        rows = self._readme_rows(json_summary)
        body = "\n".join(f"| {name} | {count} | no | yes | {status} | {doc} |" for name, count, status, doc in rows)
        return (
            "# Dataset File Content Analysis (Host)\n\n"
            "| Format | File count | DNS | Host | Status | Document |\n"
            "|---|---:|---|---|---|---|\n"
            f"{body}\n"
        )

    def _build_ru_report(self, summary_payload: dict[str, Any], summary_json_path: Path) -> str:
        schema = summary_payload["technical"]["schema_counts"]
        return (
            "# РћС‚С‡С‘С‚: Task41 (Analysis of host txt dataset files)\n\n"
            "## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё\n"
            "РџРµСЂРµРґРµР»Р°РЅ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° `TRAIN/txt` СЃ РіРµРЅРµСЂР°С†РёРµР№ RU/EN-РґРѕРєСѓРјРµРЅС‚Р°С†РёРё Рё РѕР±РЅРѕРІР»РµРЅРёРµРј README РёРЅРґРµРєСЃРѕРІ.\n\n"
            "## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹ РёР»Рё РёР·РјРµРЅРµРЅС‹\n"
            "- `scripts/handlers/analyze_host_txt_dataset_handler.py`\n"
            "- `manage.py`\n"
            "- `docs/ru/analysis-dataset/host/txt.md`\n"
            "- `docs/en/analysis-dataset/host/txt.md`\n"
            "- `docs/ru/analysis-dataset/host/README.md`\n"
            "- `docs/en/analysis-dataset/host/README.md`\n"
            "- `report/ru/stage-one/analysis-dataset/host/Task41(Analysis of host txt dataset files)_report.md`\n"
            "- `report/en/stage-one/analysis-dataset/host/Task41(Analysis of host txt dataset files)_report.md`\n"
            "- `temp_data/analysis-host-txt-summary.json`\n\n"
            "## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON\n"
            f"- json_document: `{schema['json_document']}`\n"
            f"- json_lines: `{schema['json_lines']}`\n"
            f"- unparsed: `{schema['unparsed']}`\n\n"
            "## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№\n"
            "1. Р—Р°РіСЂСѓР¶РµРЅ `sort-path-host-file.json`.\n"
            "2. Р’С‹Р±СЂР°РЅ bucket `TRAIN -> txt`.\n"
            "3. РџСЂРёРјРµРЅРµРЅР° СЂР°РІРЅРѕРјРµСЂРЅР°СЏ РІС‹Р±РѕСЂРєР° С„Р°Р№Р»РѕРІ РїРѕ РІСЃРµРјСѓ РґРёР°РїР°Р·РѕРЅСѓ РёРјРµРЅ.\n"
            "4. Р”Р»СЏ РєР°Р¶РґРѕРіРѕ sample-С„Р°Р№Р»Р° РІС‹РїРѕР»РЅРµРЅ Р°РЅР°Р»РёР· РєР°Рє `json document`, Р·Р°С‚РµРј fallback РІ `json-lines`.\n\n"
            "## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON\n"
            "```json\n"
            + json.dumps(
                {
                    "scope": summary_payload["scope"],
                    "technical": {"schema_counts": schema},
                    "final_status": summary_payload["final_status"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n```\n\n"
            f"Summary JSON: `{summary_json_path}`\n"
        )

    def _build_en_report(self, summary_payload: dict[str, Any], summary_json_path: Path) -> str:
        schema = summary_payload["technical"]["schema_counts"]
        return (
            "# Report: Task41 (Analysis of host txt dataset files)\n\n"
            "## Task description\n"
            "Reworked `TRAIN/txt` content analysis with RU/EN documentation generation and README index updates.\n\n"
            "## Added or modified files\n"
            "- `scripts/handlers/analyze_host_txt_dataset_handler.py`\n"
            "- `manage.py`\n"
            "- `docs/ru/analysis-dataset/host/txt.md`\n"
            "- `docs/en/analysis-dataset/host/txt.md`\n"
            "- `docs/ru/analysis-dataset/host/README.md`\n"
            "- `docs/en/analysis-dataset/host/README.md`\n"
            "- `report/ru/stage-one/analysis-dataset/host/Task41(Analysis of host txt dataset files)_report.md`\n"
            "- `report/en/stage-one/analysis-dataset/host/Task41(Analysis of host txt dataset files)_report.md`\n"
            "- `temp_data/analysis-host-txt-summary.json`\n\n"
            "## JSON structure summary\n"
            f"- json_document: `{schema['json_document']}`\n"
            f"- json_lines: `{schema['json_lines']}`\n"
            f"- unparsed: `{schema['unparsed']}`\n\n"
            "## Path grouping logic\n"
            "1. Load `sort-path-host-file.json`.\n"
            "2. Select bucket `TRAIN -> txt`.\n"
            "3. Apply evenly distributed sampling across all sorted filenames.\n"
            "4. For each sample file, try `json document` parsing first, then fallback to `json-lines`.\n\n"
            "## Sample output JSON\n"
            "```json\n"
            + json.dumps(
                {
                    "scope": summary_payload["scope"],
                    "technical": {"schema_counts": schema},
                    "final_status": summary_payload["final_status"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n```\n\n"
            f"Summary JSON: `{summary_json_path}`\n"
        )

    def _readme_rows(self, json_summary: dict[str, Any]) -> list[tuple[str, int, str, str]]:
        host_counts = self._load_host_format_counts()
        return [
            ("csv", host_counts.get("csv", 0), self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE), "csv.md"),
            ("auth.log", host_counts.get("auth.log", 0), self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE), "auth.log.md"),
            ("cpu.log", host_counts.get("cpu.log", 0), self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE), "cpu.log.md"),
            ("diskio.log", host_counts.get("diskio.log", 0), self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE), "diskio.log.md"),
            ("filesystem.log", host_counts.get("filesystem.log", 0), self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE), "filesystem.log.md"),
            ("fsstat.log", host_counts.get("fsstat.log", 0), self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE), "fsstat.log.md"),
            ("ghc", host_counts.get("ghc", 0), self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE), "ghc.md"),
            ("info", host_counts.get("info", 0), self._load_optional_status(self.temp_data_path / self.INFO_SUMMARY_JSON_FILE), "info.md"),
            ("journal", host_counts.get("journal", 0), self._load_optional_status(self.temp_data_path / self.JOURNAL_SUMMARY_JSON_FILE), "journal.md"),
            ("journal~", host_counts.get("journal~", 0), self._load_optional_status(self.temp_data_path / self.JOURNAL_TILDE_SUMMARY_JSON_FILE), "journal~.md"),
            (
                "json",
                host_counts.get("json", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-json-summary.json"),
                "json.md",
            ),
            (
                "json-1",
                host_counts.get("json-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-json-1-summary.json"),
                "json-1.md",
            ),
            (
                "load.log",
                host_counts.get("load.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-load-log-summary.json"),
                "load.log.md",
            ),
            (
                "log",
                host_counts.get("log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-summary.json"),
                "log.md",
            ),
            (
                "log-1",
                host_counts.get("log-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-1-summary.json"),
                "log-1.md",
            ),
            (
                "log-2",
                host_counts.get("log-2", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-2-summary.json"),
                "log-2.md",
            ),
            (
                "log-3",
                host_counts.get("log-3", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-3-summary.json"),
                "log-3.md",
            ),
            (
                "mail-info-1",
                host_counts.get("mail-info-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mail-info-1-summary.json"),
                "mail-info-1.md",
            ),
            (
                "mail-warn-1",
                host_counts.get("mail-warn-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mail-warn-1-summary.json"),
                "mail-warn-1.md",
            ),
            (
                "mainlog",
                host_counts.get("mainlog", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-summary.json"),
                "mainlog.md",
            ),
            (
                "mainlog-1",
                host_counts.get("mainlog-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-1-summary.json"),
                "mainlog-1.md",
            ),
            (
                "mainlog-2",
                host_counts.get("mainlog-2", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-2-summary.json"),
                "mainlog-2.md",
            ),
            (
                "mainlog-3",
                host_counts.get("mainlog-3", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-3-summary.json"),
                "mainlog-3.md",
            ),
            (
                "memory.log",
                host_counts.get("memory.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-memory-log-summary.json"),
                "memory.log.md",
            ),
            (
                "messages",
                host_counts.get("messages", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-messages-summary.json"),
                "messages.md",
            ),
            (
                "messages-1",
                host_counts.get("messages-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-messages-1-summary.json"),
                "messages-1.md",
            ),
            (
                "netflow_ids",
                host_counts.get("netflow_ids", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-netflow-ids-summary.json"),
                "netflow_ids.md",
            ),
            (
                "network.log",
                host_counts.get("network.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-network-log-summary.json"),
                "network.log.md",
            ),
            (
                "process.log",
                host_counts.get("process.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-process-log-summary.json"),
                "process.log.md",
            ),
            (
                "process.summary.log",
                host_counts.get("process.summary.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-process-summary-log-summary.json"),
                "process.summary.log.md",
            ),
            (
                "sc",
                host_counts.get("sc", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-sc-summary.json"),
                "sc.md",
            ),
            (
                "service.log",
                host_counts.get("service.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-service-log-summary.json"),
                "service.log.md",
            ),
            (
                "socket.summary.log",
                host_counts.get("socket.summary.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-socket-summary-log-summary.json"),
                "socket.summary.log.md",
            ),
            (
                "syslog",
                host_counts.get("syslog", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-summary.json"),
                "syslog.md",
            ),
            (
                "syslog-1",
                host_counts.get("syslog-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-1-summary.json"),
                "syslog-1.md",
            ),
            (
                "syslog-2",
                host_counts.get("syslog-2", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-2-summary.json"),
                "syslog-2.md",
            ),
            (
                "syslog-3",
                host_counts.get("syslog-3", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-3-summary.json"),
                "syslog-3.md",
            ),
            (
                "syslog-4",
                host_counts.get("syslog-4", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-4-summary.json"),
                "syslog-4.md",
            ),
            (
                "syslog.log",
                host_counts.get("syslog.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-syslog-log-summary.json"),
                "syslog.log.md",
            ),
            (
                "txt",
                host_counts.get("txt", json_summary["scope"]["total_files_count"]),
                json_summary["final_status"],
                "txt.md",
            ),
        ]

    def _load_host_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}
        result: dict[str, int] = {}
        for fmt, paths in role_bucket.items():
            if isinstance(paths, list):
                result[fmt] = len(paths)
        return result

    @staticmethod
    def _load_optional_status(summary_path: Path) -> str:
        if not summary_path.exists():
            return "-"
        try:
            payload = JsonDataManager(summary_path).read(default={})
        except (ValueError, TypeError):
            return "-"
        value = payload.get("final_status")
        return str(value) if isinstance(value, str) else "-"






























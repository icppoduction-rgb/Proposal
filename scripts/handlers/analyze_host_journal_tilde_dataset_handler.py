from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostJournalTildeContentAnalysisResult:
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


class HostJournalTildeContentAnalysisHandler:
    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "journal~"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    MAX_HEADER_BYTES = 4096

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-host-journal-tilde-summary.json"

    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"
    FSSTAT_SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"
    GHC_SUMMARY_JSON_FILE = "analysis-host-ghc-summary.json"
    INFO_SUMMARY_JSON_FILE = "analysis-host-info-summary.json"
    JOURNAL_SUMMARY_JSON_FILE = "analysis-host-journal-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_UNSUPPORTED = "UNSUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    SYSTEMD_JOURNAL_SIGNATURE = b"LPKSHHRH"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostJournalTildeContentAnalysisResult:
        host_role_to_formats = self._read_host_source_json()
        all_paths = self._extract_journal_paths(host_role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/journal~.")

        sampled_paths = self._select_sample_paths(all_paths)
        dns_format_counts = self._read_dns_format_counts()
        summary_payload = self._build_summary(all_paths, sampled_paths, dns_format_counts)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "journal~.md"
        docs_en_path = self.docs_en_dir / "journal~.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task10(Analysis of host journal~ dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task10(Analysis of host journal~ dataset files)_report.md"

        status = str(summary_payload["final_status"])

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(
            report_ru_path,
            self._build_ru_report(
                summary_payload=summary_payload,
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                total_files_count=len(all_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )
        self._write_text_file(
            report_en_path,
            self._build_en_report(
                summary_payload=summary_payload,
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                total_files_count=len(all_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )

        return HostJournalTildeContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=status,
        )

    def _read_host_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_journal_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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

    def _read_dns_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.DNS_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        train_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(train_bucket, dict):
            return {}
        result: dict[str, int] = {}
        for format_name, paths in train_bucket.items():
            if isinstance(paths, list):
                result[str(format_name)] = len(paths)
        return result

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths
        return all_paths[: self.max_files_per_format]

    def _build_summary(
        self,
        all_paths: list[Path],
        sampled_paths: list[Path],
        dns_format_counts: dict[str, int],
    ) -> dict[str, Any]:
        sample_file_details: list[dict[str, Any]] = []

        empty_files = 0
        parse_error_files = 0
        systemd_signature_files = 0
        binary_like_files = 0
        text_like_files = 0

        header_signatures: dict[str, int] = {}
        size_values: list[float] = []
        printable_ratios: list[float] = []

        for file_path in sampled_paths:
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "header_signature_hex": "",
                "systemd_journal_signature": False,
                "printable_ratio": 0.0,
                "parse_error": None,
            }

            if not file_path.exists():
                file_info["parse_error"] = "file_not_found"
                parse_error_files += 1
                sample_file_details.append(file_info)
                continue

            file_info["size_bytes"] = file_path.stat().st_size
            size_values.append(float(file_info["size_bytes"]))
            if file_info["size_bytes"] == 0:
                file_info["parse_error"] = "empty_file"
                empty_files += 1
                sample_file_details.append(file_info)
                continue

            try:
                raw = file_path.read_bytes()[: self.MAX_HEADER_BYTES]
            except OSError as error:
                file_info["parse_error"] = f"read_error:{error.__class__.__name__}"
                parse_error_files += 1
                sample_file_details.append(file_info)
                continue

            signature = raw[:8]
            signature_hex = signature.hex()
            file_info["header_signature_hex"] = signature_hex
            header_signatures[signature_hex] = header_signatures.get(signature_hex, 0) + 1

            is_systemd_journal = signature == self.SYSTEMD_JOURNAL_SIGNATURE
            file_info["systemd_journal_signature"] = is_systemd_journal
            if is_systemd_journal:
                systemd_signature_files += 1

            printable = 0
            for byte in raw:
                if 32 <= byte <= 126 or byte in (9, 10, 13):
                    printable += 1
            printable_ratio = printable / len(raw) if raw else 0.0
            file_info["printable_ratio"] = printable_ratio
            printable_ratios.append(printable_ratio)

            if printable_ratio < 0.7:
                binary_like_files += 1
            else:
                text_like_files += 1

            sample_file_details.append(file_info)

        if not sampled_paths or (empty_files + parse_error_files) == len(sampled_paths):
            status = self.STATUS_BROKEN
        elif systemd_signature_files > 0:
            status = self.STATUS_NEEDS_CUSTOM
        elif binary_like_files > 0 and text_like_files > 0:
            status = self.STATUS_PARTIAL
        elif binary_like_files > 0:
            status = self.STATUS_UNSUPPORTED
        else:
            status = self.STATUS_READY

        needs_custom_parser = status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL}

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
            },
            "path_grouping": {
                "source_json_host": self.HOST_INPUT_JSON_FILE,
                "source_json_dns": self.DNS_INPUT_JSON_FILE,
                "host_role_bucket": self.ROLE_NAME,
                "host_format_bucket": self.FORMAT_NAME,
                "dns_formats_detected_count": len(dns_format_counts),
            },
            "examples": {"paths": [str(path) for path in all_paths[:3]]},
            "technical": {
                "file_type": "binary",
                "line_by_line_readable": False,
                "tabular_structure": False,
                "nested_structure": True,
                "systemd_signature_files": systemd_signature_files,
                "binary_like_files": binary_like_files,
                "text_like_files": text_like_files,
                "header_signatures": header_signatures,
                "sample_file_details": sample_file_details[:12],
            },
            "content": {
                "category": (
                    "Binary systemd journal container data. Requires specialized tooling "
                    "(journalctl/systemd libraries) for record extraction."
                ),
                "size_bytes_stats": self._stats(size_values),
                "printable_ratio_stats": self._stats(printable_ratios),
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": [],
                "supports_supervised_learning": "no",
                "notes": "Labels are not directly present in binary journal container bytes.",
            },
            "time_detection": {
                "timestamp_found": False,
                "timestamp_fields": [],
                "timestamp_format": "not directly readable",
                "timezone": "unknown",
                "sequence_ready": False,
                "sliding_window_ready": False,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_error_files,
                "mixed_schema_detected": binary_like_files > 0 and text_like_files > 0,
            },
            "final_status": status,
            "needs_custom_parser": needs_custom_parser,
            "priority": "high" if needs_custom_parser else "medium",
        }

    @staticmethod
    def _stats(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"min": None, "max": None, "avg": None}
        return {"min": min(values), "max": max(values), "avg": sum(values) / len(values)}

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]

        return f"""
# РђРЅР°Р»РёР· С„РѕСЂРјР°С‚Р°: journal~

## 1. РќР°Р·РЅР°С‡РµРЅРёРµ
`journal~` РІ `TRAIN` РїСЂРµРґСЃС‚Р°РІР»РµРЅ Р±РёРЅР°СЂРЅС‹Рј РєРѕРЅС‚РµР№РЅРµСЂРѕРј systemd journal Рё С‚СЂРµР±СѓРµС‚ РѕС‚РґРµР»СЊРЅРѕРіРѕ РїР°СЂСЃРµСЂР° РґР»СЏ РёР·РІР»РµС‡РµРЅРёСЏ СЃРѕР±С‹С‚РёР№.

## 2. Р“РґРµ РІСЃС‚СЂРµС‡Р°РµС‚СЃСЏ
| РџРѕР»Рµ | Р—РЅР°С‡РµРЅРёРµ |
|---|---|
| Р¤РѕСЂРјР°С‚ | journal~ |
| Р’Р°СЂРёР°РЅС‚С‹ СЂР°СЃС€РёСЂРµРЅРёСЏ | `.journal~` |
| DNS | РЅРµС‚ |
| Host | РґР° |
| Р РѕР»Рё | {scope['role']} |
| РљРѕР»РёС‡РµСЃС‚РІРѕ С„Р°Р№Р»РѕРІ | {scope['total_files_count']} |

## 3. РџСЂРёРјРµСЂС‹ С„Р°Р№Р»РѕРІ
```text
{examples[0] if len(examples) > 0 else '-'}
{examples[1] if len(examples) > 1 else '-'}
{examples[2] if len(examples) > 2 else '-'}
```

## 4. РўРµС…РЅРёС‡РµСЃРєР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР°
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| РўРёРї С„Р°Р№Р»Р° | binary |
| Р§С‚РµРЅРёРµ РїРѕСЃС‚СЂРѕС‡РЅРѕ | РЅРµС‚ |
| РўР°Р±Р»РёС‡РЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | РЅРµС‚ |
| Р—Р°РіРѕР»РѕРІРѕРє | РµСЃС‚СЊ Р±РёРЅР°СЂРЅР°СЏ СЃРёРіРЅР°С‚СѓСЂР° |
| Р Р°Р·РґРµР»РёС‚РµР»СЊ | none |
| РљРѕРґРёСЂРѕРІРєР° | unknown (container bytes) |
| Р’Р»РѕР¶РµРЅРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | РґР° |
| Sample-С„Р°Р№Р»РѕРІ РїСЂРѕР°РЅР°Р»РёР·РёСЂРѕРІР°РЅРѕ | {scope['sampled_files_count']} |
| Р¤Р°Р№Р»РѕРІ СЃ СЃРёРіРЅР°С‚СѓСЂРѕР№ `LPKSHHRH` | {technical['systemd_signature_files']} |

## 5. РЎРѕРґРµСЂР¶Р°С‚РµР»СЊРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР°
Р¤РѕСЂРјР°С‚ РїРѕС…РѕР¶ РЅР° РєРѕРЅС‚РµР№РЅРµСЂ systemd journal: РґР°РЅРЅС‹Рµ С…СЂР°РЅСЏС‚СЃСЏ Р±РёРЅР°СЂРЅРѕ Рё РЅРµ РїСЂРµРґРЅР°Р·РЅР°С‡РµРЅС‹ РґР»СЏ РїСЂСЏРјРѕРіРѕ С‚РµРєСЃС‚РѕРІРѕРіРѕ С‡С‚РµРЅРёСЏ.

## 6. РќР°Р№РґРµРЅРЅС‹Рµ РїРѕР»СЏ / РєРѕР»РѕРЅРєРё
| РџРѕР»Рµ | РўРёРї | РќР°Р·РЅР°С‡РµРЅРёРµ | РџСЂРёРјРµСЂ Р·РЅР°С‡РµРЅРёСЏ |
|---|---|---|---|
| header_signature_hex | string | СЃРёРіРЅР°С‚СѓСЂР° РїРµСЂРІС‹С… 8 Р±Р°Р№С‚ | `4c504b5348485248` |
| size_bytes | integer | СЂР°Р·РјРµСЂ С„Р°Р№Р»Р° | `16777216` |
| printable_ratio | float | РґРѕР»СЏ РїРµС‡Р°С‚РЅС‹С… Р±Р°Р№С‚ РІ sample-header | `0.12` |

## 7. Label / class indicators
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| Label РЅР°Р№РґРµРЅ | {'РґР°' if label['label_found'] else 'РЅРµС‚'} |
| РќР°Р·РІР°РЅРёРµ РїРѕР»СЏ | {label['label_field_name']} |
| Р—РЅР°С‡РµРЅРёСЏ label | - |
| РњРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РґР»СЏ supervised learning | {label['supports_supervised_learning']} |

## 8. Р’СЂРµРјРµРЅРЅС‹Рµ РїСЂРёР·РЅР°РєРё
| РџСЂРѕРІРµСЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| Timestamp РЅР°Р№РґРµРЅ | {'РґР°' if time_block['timestamp_found'] else 'РЅРµС‚'} |
| РќР°Р·РІР°РЅРёРµ РїРѕР»СЏ | - |
| Р¤РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё | {time_block['timestamp_format']} |
| РњРѕР¶РЅРѕ СЃС‚СЂРѕРёС‚СЊ sequence | {'РґР°' if time_block['sequence_ready'] else 'РЅРµС‚'} |
| РњРѕР¶РЅРѕ РїСЂРёРјРµРЅСЏС‚СЊ sliding window | {'РґР°' if time_block['sliding_window_ready'] else 'РЅРµС‚'} |

## 9. РџРѕС‚РµРЅС†РёР°Р»СЊРЅС‹Рµ РїСЂРёР·РЅР°РєРё РґР»СЏ feature extraction
### DNS-РїСЂРёР·РЅР°РєРё
- РЅРµ РїСЂРёРјРµРЅРёРјРѕ РЅР° СЌС‚Р°РїРµ СЃС‹СЂРѕРіРѕ Р±РёРЅР°СЂРЅРѕРіРѕ С‡С‚РµРЅРёСЏ.

### Host-РїСЂРёР·РЅР°РєРё
- РѕР±СЉС‘Рј Р¶СѓСЂРЅР°Р»Р° Рё С‚РµРјРї СЂРѕСЃС‚Р°;
- РєРѕР»РёС‡РµСЃС‚РІРѕ Р·Р°РїРёСЃРµР№ Рё С‚РёРїС‹ СЃРѕР±С‹С‚РёР№ РїРѕСЃР»Рµ РїР°СЂСЃРёРЅРіР° `journalctl`.

### Network / hybrid-РїСЂРёР·РЅР°РєРё
- РєРѕСЂСЂРµР»СЏС†РёСЏ РёР·РІР»РµС‡С‘РЅРЅС‹С… journal-СЃРѕР±С‹С‚РёР№ СЃ СЃРµС‚РµРІС‹РјРё/РїСЂРѕС†РµСЃСЃРЅС‹РјРё Р»РѕРіР°РјРё РїРѕСЃР»Рµ РЅРѕСЂРјР°Р»РёР·Р°С†РёРё.

## 10. РџСЂРѕР±Р»РµРјС‹ РєР°С‡РµСЃС‚РІР° РґР°РЅРЅС‹С…
| РџСЂРѕР±Р»РµРјР° | РќР°Р№РґРµРЅР° | РљРѕРјРјРµРЅС‚Р°СЂРёР№ |
|---|---|---|
| РџСѓСЃС‚С‹Рµ С„Р°Р№Р»С‹ | {'РґР°' if quality['empty_files_count'] > 0 else 'РЅРµС‚'} | count: {quality['empty_files_count']} |
| РџРѕРІСЂРµР¶РґС‘РЅРЅС‹Рµ С„Р°Р№Р»С‹ | {'РґР°' if quality['parse_error_files_count'] > 0 else 'РЅРµС‚'} | parse/read errors: {quality['parse_error_files_count']} |
| Missing values | РЅРµС‚ | РєРѕРЅС‚РµР№РЅРµСЂРЅС‹Р№ Р±РёРЅР°СЂРЅС‹Р№ С„РѕСЂРјР°С‚ |
| РќРµСЃС‚Р°Р±РёР»СЊРЅР°СЏ СЃС‚СЂСѓРєС‚СѓСЂР° | {'РґР°' if quality['mixed_schema_detected'] else 'РЅРµС‚'} | СЃРјРµС€РµРЅРёРµ Р±РёРЅР°СЂРЅС‹С… Рё text-like С„Р°Р№Р»РѕРІ |
| РЎРјРµС€Р°РЅРЅС‹Рµ СЃС…РµРјС‹ | {'РґР°' if quality['mixed_schema_detected'] else 'РЅРµС‚'} | binary_like={technical['binary_like_files']}, text_like={technical['text_like_files']} |

## 11. РС‚РѕРіРѕРІР°СЏ РїСЂРёРіРѕРґРЅРѕСЃС‚СЊ
| РџРѕР»Рµ | Р—РЅР°С‡РµРЅРёРµ |
|---|---|
| РЎС‚Р°С‚СѓСЃ | {summary['final_status']} |
| РќСѓР¶РµРЅ РѕС‚РґРµР»СЊРЅС‹Р№ РїР°СЂСЃРµСЂ | {'РґР°' if summary['needs_custom_parser'] else 'РЅРµС‚'} |
| РџСЂРёРѕСЂРёС‚РµС‚ РѕР±СЂР°Р±РѕС‚РєРё | {summary['priority']} |

## 12. Р’С‹РІРѕРґ
`TRAIN/journal~` РЅРµ РґРѕР»Р¶РµРЅ РѕР±СЂР°Р±Р°С‚С‹РІР°С‚СЊСЃСЏ РєР°Рє РѕР±С‹С‡РЅС‹Р№ С‚РµРєСЃС‚РѕРІС‹Р№ Р»РѕРі. Р”Р»СЏ РєРѕСЂСЂРµРєС‚РЅРѕРіРѕ РёР·РІР»РµС‡РµРЅРёСЏ РїСЂРёР·РЅР°РєРѕРІ РЅСѓР¶РµРЅ РѕС‚РґРµР»СЊРЅС‹Р№ parser/toolchain РґР»СЏ systemd journal.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]

        return f"""
# Format Analysis: journal~

## 1. Purpose
`journal~` in `TRAIN` is a binary systemd journal container and requires a dedicated parser to extract events.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | journal~ |
| Extension variants | `.journal~` |
| DNS | no |
| Host | yes |
| Roles | {scope['role']} |
| File count | {scope['total_files_count']} |

## 3. Example files
```text
{examples[0] if len(examples) > 0 else '-'}
{examples[1] if len(examples) > 1 else '-'}
{examples[2] if len(examples) > 2 else '-'}
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | binary signature present |
| Delimiter | none |
| Encoding | unknown (container bytes) |
| Nested structure | yes |
| Sampled files | {scope['sampled_files_count']} |
| Files with `LPKSHHRH` signature | {technical['systemd_signature_files']} |

## 5. Semantic structure
The format matches a systemd journal-like binary container. Direct text parsing is not reliable.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| header_signature_hex | string | first 8-byte signature | `4c504b5348485248` |
| size_bytes | integer | file size | `16777216` |
| printable_ratio | float | printable bytes ratio in sampled header | `0.12` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {'yes' if label['label_found'] else 'no'} |
| Field name | {label['label_field_name']} |
| Label values | - |
| Suitable for supervised learning | {label['supports_supervised_learning']} |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {'yes' if time_block['timestamp_found'] else 'no'} |
| Field name | - |
| Timestamp format | {time_block['timestamp_format']} |
| Sequence-ready | {'yes' if time_block['sequence_ready'] else 'no'} |
| Sliding-window-ready | {'yes' if time_block['sliding_window_ready'] else 'no'} |

## 9. Potential feature extraction signals
### DNS features
- not applicable at raw binary stage.

### Host features
- journal size and growth pace;
- entry count and event families after `journalctl` parsing.

### Network / hybrid features
- correlation of extracted journal events with network/process logs after normalization.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {'yes' if quality['empty_files_count'] > 0 else 'no'} | count: {quality['empty_files_count']} |
| Corrupted files | {'yes' if quality['parse_error_files_count'] > 0 else 'no'} | parse/read errors: {quality['parse_error_files_count']} |
| Missing values | no | binary container format |
| Unstable structure | {'yes' if quality['mixed_schema_detected'] else 'no'} | binary and text-like files mixed |
| Mixed schemas | {'yes' if quality['mixed_schema_detected'] else 'no'} | binary_like={technical['binary_like_files']}, text_like={technical['text_like_files']} |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {'yes' if summary['needs_custom_parser'] else 'no'} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/journal~` should not be handled as a plain text log. A dedicated parser/toolchain for systemd journal is required for reliable feature extraction.
"""

    def _build_ru_readme(self, journal_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", 0)
        info_count = host_counts.get("info", 0)
        journal_count = host_counts.get("journal", 0)
        journal_tilde_count = host_counts.get("journal~", journal_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE)
        info_status = self._load_optional_status(self.temp_data_path / self.INFO_SUMMARY_JSON_FILE)
        journal_status = self._load_optional_status(self.temp_data_path / self.JOURNAL_SUMMARY_JSON_FILE)
        journal_tilde_status = journal_summary["final_status"]

        return f"""
# Р С’Р Р…Р В°Р В»Р С‘Р В· РЎРѓР С•Р Т‘Р ВµРЎР‚Р В¶Р С‘Р СР С•Р С–Р С• РЎвЂћР В°Р в„–Р В»Р С•Р Р† Р Т‘Р В°РЎвЂљР В°РЎРѓР ВµРЎвЂљР С•Р Р† (Host)

| Р В¤Р С•РЎР‚Р СР В°РЎвЂљ | Р С™Р С•Р В»Р С‘РЎвЂЎР ВµРЎРѓРЎвЂљР Р†Р С• РЎвЂћР В°Р в„–Р В»Р С•Р Р† | DNS | Host | Р РЋРЎвЂљР В°РЎвЂљРЎС“РЎРѓ | Р вЂќР С•Р С”РЎС“Р СР ВµР Р…РЎвЂљ |
|---|---:|---|---|---|---|
| csv | {csv_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {csv_status} | csv.md |
| auth.log | {auth_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {fsstat_status} | fsstat.log.md |
| ghc | {ghc_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {ghc_status} | ghc.md |
| info | {info_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {info_status} | info.md |
| journal | {journal_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {journal_status} | journal.md |
| journal~ | {journal_tilde_count} | Р Р…Р ВµРЎвЂљ | Р Т‘Р В° | {journal_tilde_status} | journal~.md |
"""

    def _build_en_readme(self, journal_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", 0)
        info_count = host_counts.get("info", 0)
        journal_count = host_counts.get("journal", 0)
        journal_tilde_count = host_counts.get("journal~", journal_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE)
        info_status = self._load_optional_status(self.temp_data_path / self.INFO_SUMMARY_JSON_FILE)
        journal_status = self._load_optional_status(self.temp_data_path / self.JOURNAL_SUMMARY_JSON_FILE)
        journal_tilde_status = journal_summary["final_status"]

        return f"""
# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | {csv_count} | no | yes | {csv_status} | csv.md |
| auth.log | {auth_count} | no | yes | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | no | yes | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | no | yes | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | no | yes | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | no | yes | {fsstat_status} | fsstat.log.md |
| ghc | {ghc_count} | no | yes | {ghc_status} | ghc.md |
| info | {info_count} | no | yes | {info_status} | info.md |
| journal | {journal_count} | no | yes | {journal_status} | journal.md |
| journal~ | {journal_tilde_count} | no | yes | {journal_tilde_status} | journal~.md |
"""

    def _build_ru_report(
        self,
        summary_payload: dict[str, Any],
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        json_structure_sample = {
            "scope": summary_payload["scope"],
            "path_grouping": summary_payload["path_grouping"],
            "final_status": summary_payload["final_status"],
        }
        json_structure_text = json.dumps(json_structure_sample, ensure_ascii=False, indent=2)

        return f"""
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
- СЃС‚Р°С‚СѓСЃ РїСЂРёРіРѕРґРЅРѕСЃС‚Рё: `{summary_payload['final_status']}`

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. РЎС‡РёС‚С‹РІР°РµС‚СЃСЏ `sort-path-host-file.json`.
2. Р’С‹Р±РёСЂР°РµС‚СЃСЏ bucket: `TRAIN -> journal~`.
3. РџР°СЂР°Р»Р»РµР»СЊРЅРѕ С‡РёС‚Р°РµС‚СЃСЏ `sort-path-dns-file.json` РґР»СЏ РІР°Р»РёРґР°С†РёРё РєРѕРЅС‚РµРєСЃС‚Р° DNS/Host Р±РµР· СЃРјРµС€РёРІР°РЅРёСЏ РґР°РЅРЅС‹С….
4. Р”Р»СЏ Р°РЅР°Р»РёР·Р° Р±РµСЂС‘С‚СЃСЏ РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sample С„Р°Р№Р»РѕРІ Рё С‚РѕР»СЊРєРѕ Р±РµР·РѕРїР°СЃРЅС‹Р№ header sample bytes.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{json_structure_text}
```

## Р РµР·СѓР»СЊС‚Р°С‚
- Р’СЃРµРіРѕ С„Р°Р№Р»РѕРІ С„РѕСЂРјР°С‚Р°: `{total_files_count}`.
- Sample-С„Р°Р№Р»РѕРІ РїСЂРѕР°РЅР°Р»РёР·РёСЂРѕРІР°РЅРѕ: `{sampled_files_count}`.
- РС‚РѕРіРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ: `{status}`.

## РђСЂС‚РµС„Р°РєС‚С‹
- Summary JSON: `{summary_json_path}`
- RU doc: `{docs_ru_path}`
- EN doc: `{docs_en_path}`
- RU README: `{docs_ru_readme_path}`
- EN README: `{docs_en_readme_path}`
"""

    def _build_en_report(
        self,
        summary_payload: dict[str, Any],
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        json_structure_sample = {
            "scope": summary_payload["scope"],
            "path_grouping": summary_payload["path_grouping"],
            "final_status": summary_payload["final_status"],
        }
        json_structure_text = json.dumps(json_structure_sample, ensure_ascii=False, indent=2)

        return f"""
# Report: Task10 (Analysis of host journal~ dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/journal~` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_journal_tilde_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/journal~.md`
- `docs/en/analysis-dataset/host/journal~.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `temp_data/analysis-host-journal-tilde-summary.json`

## JSON structure description
- binary signature: `LPKSHHRH`
- type: binary container
- suitability status: `{summary_payload['final_status']}`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> journal~`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples and safe header bytes.

## Sample of resulting JSON
```json
{json_structure_text}
```

## Result
- Total format files: `{total_files_count}`.
- Sampled files analyzed: `{sampled_files_count}`.
- Final status: `{status}`.

## Artifacts
- Summary JSON: `{summary_json_path}`
- RU doc: `{docs_ru_path}`
- EN doc: `{docs_en_path}`
- RU README: `{docs_ru_readme_path}`
- EN README: `{docs_en_readme_path}`
"""

    def _load_host_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}

        counts: dict[str, int] = {}
        for format_name, paths in role_bucket.items():
            if isinstance(paths, list):
                counts[format_name] = len(paths)
        return counts

    @staticmethod
    def _load_optional_status(summary_path: Path) -> str:
        if not summary_path.exists():
            return "-"
        try:
            payload = JsonDataManager(summary_path).read(default={})
        except (ValueError, TypeError):
            return "-"
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"


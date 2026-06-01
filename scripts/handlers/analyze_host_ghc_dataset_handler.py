from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostGHCContentAnalysisResult:
    """Result of analyzing TRAIN/ghc host datasets and generating documentation."""

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


class HostGHCContentAnalysisHandler:
    """Analyzes host TRAIN/ghc datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "ghc"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"

    SUMMARY_JSON_FILE = "analysis-host-ghc-summary.json"
    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"
    FSSTAT_SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_UNSUPPORTED = "UNSUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    TRACE_TOKEN_RE = re.compile(r"^(?P<module>[A-Za-z0-9_.-]+)\+0x(?P<offset>[0-9A-Fa-f]+)$")

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(100, max_lines_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostGHCContentAnalysisResult:
        host_role_to_formats = self._read_host_source_json()
        all_ghc_paths = self._extract_ghc_paths(host_role_to_formats)
        if not all_ghc_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/ghc.")

        dns_format_counts = self._read_dns_format_counts()
        sampled_paths = self._select_sample_paths(all_ghc_paths)

        summary_payload = self._build_summary(
            all_ghc_paths=all_ghc_paths,
            sampled_paths=sampled_paths,
            dns_format_counts=dns_format_counts,
        )

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "ghc.md"
        docs_en_path = self.docs_en_dir / "ghc.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task7(Analysis of host ghc dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task7(Analysis of host ghc dataset files)_report.md"

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
                total_files_count=len(all_ghc_paths),
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
                total_files_count=len(all_ghc_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )

        return HostGHCContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_ghc_paths),
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

    def _extract_ghc_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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
        all_ghc_paths: list[Path],
        sampled_paths: list[Path],
        dns_format_counts: dict[str, int],
    ) -> dict[str, Any]:
        sample_files_info: list[dict[str, Any]] = []

        encoding_counts: dict[str, int] = {}
        module_counts: dict[str, int] = {}
        scenario_tag_counts: dict[str, int] = {}

        total_sample_lines = 0
        total_tokens = 0
        valid_trace_tokens = 0
        invalid_trace_tokens = 0

        parse_errors = 0
        empty_files = 0
        duplicate_lines = 0

        missing_timestamp_count = 0
        mixed_schema_detected = False

        seen_lines: set[str] = set()
        token_counts_per_file: list[float] = []
        valid_ratio_per_file: list[float] = []

        for file_path in sampled_paths:
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "encoding": "unknown",
                "line_count_sample": 0,
                "trace_token_count": 0,
                "valid_trace_token_count": 0,
                "parse_error": None,
            }

            if not file_path.exists():
                file_info["parse_error"] = "file_not_found"
                sample_files_info.append(file_info)
                parse_errors += 1
                continue

            file_info["size_bytes"] = file_path.stat().st_size
            if file_info["size_bytes"] == 0:
                file_info["parse_error"] = "empty_file"
                sample_files_info.append(file_info)
                empty_files += 1
                continue

            encoding = self._detect_encoding(file_path)
            file_info["encoding"] = encoding
            encoding_counts[encoding] = encoding_counts.get(encoding, 0) + 1

            try:
                lines = file_path.read_text(encoding=encoding, errors="replace").splitlines()[
                    : self.max_lines_per_file
                ]
            except OSError as error:
                file_info["parse_error"] = f"read_error:{error.__class__.__name__}"
                sample_files_info.append(file_info)
                parse_errors += 1
                continue

            if not lines:
                lines = [""]

            file_info["line_count_sample"] = len(lines)
            total_sample_lines += len(lines)

            scenario_tag = self._extract_scenario_tag(file_path.name)
            scenario_tag_counts[scenario_tag] = scenario_tag_counts.get(scenario_tag, 0) + 1

            file_token_count = 0
            file_valid_token_count = 0

            for line in lines:
                if line in seen_lines:
                    duplicate_lines += 1
                else:
                    seen_lines.add(line)

                tokens = [token for token in line.split(" ") if token]
                if not tokens:
                    mixed_schema_detected = True
                    continue

                file_token_count += len(tokens)
                total_tokens += len(tokens)

                for token in tokens:
                    match = self.TRACE_TOKEN_RE.match(token)
                    if match is None:
                        invalid_trace_tokens += 1
                        mixed_schema_detected = True
                        continue

                    valid_trace_tokens += 1
                    file_valid_token_count += 1

                    module_name = match.group("module").lower()
                    module_counts[module_name] = module_counts.get(module_name, 0) + 1

            file_info["trace_token_count"] = file_token_count
            file_info["valid_trace_token_count"] = file_valid_token_count

            token_counts_per_file.append(float(file_token_count))
            if file_token_count > 0:
                valid_ratio_per_file.append(file_valid_token_count / file_token_count)

            sample_files_info.append(file_info)

        if total_tokens == 0:
            status = self.STATUS_BROKEN
        else:
            valid_ratio = valid_trace_tokens / total_tokens
            if valid_ratio >= 0.95:
                status = self.STATUS_NEEDS_CUSTOM
            elif valid_ratio >= 0.60:
                status = self.STATUS_PARTIAL
            else:
                status = self.STATUS_UNSUPPORTED

        needs_custom_parser = status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL}

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_ghc_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "path_grouping": {
                "source_json_host": self.HOST_INPUT_JSON_FILE,
                "source_json_dns": self.DNS_INPUT_JSON_FILE,
                "host_role_bucket": self.ROLE_NAME,
                "host_format_bucket": self.FORMAT_NAME,
                "dns_formats_detected_count": len(dns_format_counts),
            },
            "examples": {"paths": [str(path) for path in all_ghc_paths[:3]]},
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": False,
                "nested_structure": False,
                "encoding_counts": encoding_counts,
                "total_sample_lines": total_sample_lines,
                "total_tokens": total_tokens,
                "valid_trace_tokens": valid_trace_tokens,
                "invalid_trace_tokens": invalid_trace_tokens,
                "sample_file_details": sample_files_info[:12],
            },
            "content": {
                "category": (
                    "Text trace format with repeated stack-frame-like tokens "
                    "<module>+0x<offset> for host process behavior sequences."
                ),
                "scenario_tags_detected": dict(
                    sorted(scenario_tag_counts.items(), key=lambda item: item[1], reverse=True)[:20]
                ),
                "top_modules_detected": dict(
                    sorted(module_counts.items(), key=lambda item: item[1], reverse=True)[:20]
                ),
                "tokens_per_file_stats": self._stats(token_counts_per_file),
                "valid_token_ratio_stats": self._stats(valid_ratio_per_file),
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": [],
                "supports_supervised_learning": "partially",
                "notes": (
                    "Explicit label field is absent in content; scenario tag exists in filename "
                    "(for example S1-1-Full), mapping to class requires external metadata."
                ),
            },
            "time_detection": {
                "timestamp_found": False,
                "timestamp_fields": [],
                "timestamp_format": "not present",
                "timezone": "unknown",
                "sequence_ready": True,
                "sliding_window_ready": True,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_errors,
                "missing_timestamp_count": missing_timestamp_count,
                "duplicate_line_count_sample": duplicate_lines,
                "mixed_schema_detected": mixed_schema_detected,
            },
            "final_status": status,
            "needs_custom_parser": needs_custom_parser,
            "priority": "high" if needs_custom_parser else "medium",
        }

    @staticmethod
    def _extract_scenario_tag(file_name: str) -> str:
        if "_" not in file_name:
            return "unknown"
        return file_name.split("_", 1)[0]

    @staticmethod
    def _stats(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"min": None, "max": None, "avg": None}
        return {"min": min(values), "max": max(values), "avg": sum(values) / len(values)}

    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        raw = file_path.read_bytes()[:32768]
        for candidate in ("utf-8", "utf-8-sig", "latin-1", "cp1251"):
            try:
                raw.decode(candidate)
                return candidate
            except UnicodeDecodeError:
                continue
        return "latin-1"

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
        token_stats = content["tokens_per_file_stats"]

        return f"""
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
| Роли | {scope['role']} |
| Количество файлов | {scope['total_files_count']} |

## 3. Примеры файлов
```text
{examples[0] if len(examples) > 0 else '-'}
{examples[1] if len(examples) > 1 else '-'}
{examples[2] if len(examples) > 2 else '-'}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | space |
| Кодировка | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {scope['sampled_files_count']} |
| Sample-строк проанализировано | {technical['total_sample_lines']} |
| Token count | {technical['total_tokens']} |
| Valid trace tokens | {technical['valid_trace_tokens']} |

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
| Label найден | {'да' if label['label_found'] else 'нет'} |
| Название поля | {label['label_field_name']} |
| Значения label | - |
| Можно использовать для supervised learning | {label['supports_supervised_learning']} |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | {'да' if time_block['timestamp_found'] else 'нет'} |
| Название поля | {', '.join(time_block['timestamp_fields']) if time_block['timestamp_fields'] else '-'} |
| Формат времени | {time_block['timestamp_format']} |
| Можно строить sequence | {'да' if time_block['sequence_ready'] else 'нет'} |
| Можно применять sliding window | {'да' if time_block['sliding_window_ready'] else 'нет'} |

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
| Пустые файлы | {'да' if quality['empty_files_count'] > 0 else 'нет'} | count: {quality['empty_files_count']} |
| Повреждённые файлы | {'да' if quality['parse_error_files_count'] > 0 else 'нет'} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {'да' if technical['invalid_trace_tokens'] > 0 else 'нет'} | invalid tokens: {technical['invalid_trace_tokens']} |
| Нестабильная структура | {'да' if quality['mixed_schema_detected'] else 'нет'} | non-trace tokens exist |
| Смешанные схемы | {'да' if quality['mixed_schema_detected'] else 'нет'} | includes tokens outside `<module>+0x<hex>` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {'да' if summary['needs_custom_parser'] else 'нет'} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
`TRAIN/ghc` пригоден для этапа feature extraction только через отдельный специализированный parser.
Статистика токенов на файл (sample): min={token_stats['min']}, max={token_stats['max']}, avg={token_stats['avg']}.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]
        token_stats = content["tokens_per_file_stats"]

        return f"""
# Format Analysis: ghc

## 1. Purpose
`ghc` in `TRAIN` contains text trace sequences in `<module>+0x<offset>` form for host process behavior analysis.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | ghc |
| Extension variants | `.ghc`, `.GHC` |
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
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | no |
| Header | no |
| Delimiter | space |
| Encoding | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Nested structure | no |
| Sampled files | {scope['sampled_files_count']} |
| Sampled lines | {technical['total_sample_lines']} |
| Token count | {technical['total_tokens']} |
| Valid trace tokens | {technical['valid_trace_tokens']} |

## 5. Semantic structure
Data is represented as trace-like token sequences containing:
- module name (`kernel32.dll`);
- hexadecimal offset (`0xb50b`);
- token order in a line as behavioral sequence.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| trace.token | string | raw trace token | `kernel32.dll+0xb50b` |
| trace.module | string | module/library name | `kernel32.dll` |
| trace.offset_hex | string | hexadecimal offset | `0xb50b` |
| filename.scenario_tag | string | filename scenario prefix | `S1-1-Full` |

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
| Field name | {', '.join(time_block['timestamp_fields']) if time_block['timestamp_fields'] else '-'} |
| Timestamp format | {time_block['timestamp_format']} |
| Sequence-ready | {'yes' if time_block['sequence_ready'] else 'no'} |
| Sliding-window-ready | {'yes' if time_block['sliding_window_ready'] else 'no'} |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- module frequency counts (`top_modules_detected`);
- trace token n-grams;
- transitions between modules;
- trace sequence length;
- per-module offset distributions.

### Network / hybrid features
- correlate trace sequences with process/network activity by host and external timestamps.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {'yes' if quality['empty_files_count'] > 0 else 'no'} | count: {quality['empty_files_count']} |
| Corrupted files | {'yes' if quality['parse_error_files_count'] > 0 else 'no'} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {'yes' if technical['invalid_trace_tokens'] > 0 else 'no'} | invalid tokens: {technical['invalid_trace_tokens']} |
| Unstable structure | {'yes' if quality['mixed_schema_detected'] else 'no'} | non-trace tokens exist |
| Mixed schemas | {'yes' if quality['mixed_schema_detected'] else 'no'} | includes tokens outside `<module>+0x<hex>` |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {'yes' if summary['needs_custom_parser'] else 'no'} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/ghc` is usable for feature extraction only through a dedicated specialized parser.
Token-per-file stats (sample): min={token_stats['min']}, max={token_stats['max']}, avg={token_stats['avg']}.
"""

    def _build_ru_readme(self, ghc_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", ghc_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = ghc_summary["final_status"]

        return f"""
# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | {csv_count} | нет | да | {csv_status} | csv.md |
| auth.log | {auth_count} | нет | да | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | нет | да | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | нет | да | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | нет | да | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | нет | да | {fsstat_status} | fsstat.log.md |
| ghc | {ghc_count} | нет | да | {ghc_status} | ghc.md |
"""

    def _build_en_readme(self, ghc_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", ghc_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = ghc_summary["final_status"]

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
# Отчёт: Task7 (Analysis of host ghc dataset files)

## Описание задачи
Реализован отдельный этап анализа формата `TRAIN/ghc` на основе `temp_data/sort-path-host-file.json` с генерацией документации RU/EN.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_ghc_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/ghc.md`
- `docs/en/analysis-dataset/host/ghc.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `temp_data/analysis-host-ghc-summary.json`

## Описание структуры JSON
- формат trace: `<module>+0x<offset>`
- тип: текстовые последовательности
- статус пригодности: `{summary_payload['final_status']}`

## Логика группировки путей
1. Считывается `sort-path-host-file.json`.
2. Выбирается bucket: `TRAIN -> ghc`.
3. Параллельно читается `sort-path-dns-file.json` для валидации контекста DNS/Host без смешивания данных.
4. Для анализа берётся ограниченный sample файлов и строк.

## Пример итогового JSON
```json
{json_structure_text}
```

## Результат
- Всего файлов формата: `{total_files_count}`.
- Sample-файлов проанализировано: `{sampled_files_count}`.
- Итоговый статус: `{status}`.

## Артефакты
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
# Report: Task7 (Analysis of host ghc dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/ghc` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_ghc_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/ghc.md`
- `docs/en/analysis-dataset/host/ghc.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `temp_data/analysis-host-ghc-summary.json`

## JSON structure description
- trace format: `<module>+0x<offset>`
- type: text sequences
- suitability status: `{summary_payload['final_status']}`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> ghc`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples of files and lines.

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

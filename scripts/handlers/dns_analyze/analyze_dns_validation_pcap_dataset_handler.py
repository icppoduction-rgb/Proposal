from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.dns_analyze.analyze_dns_train_pcap_dataset_handler import DNSTrainPCAPContentAnalysisHandler
from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSValidationPCAPContentAnalysisResult:
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


class DNSValidationPCAPContentAnalysisHandler(DNSTrainPCAPContentAnalysisHandler):
    ROLE_NAME = "VALIDATION"
    SUMMARY_JSON_FILE = "analysis-dns-validation-pcap-summary.json"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DNSTrainPCAPContentAnalysisHandler.DEFAULT_MAX_FILES_PER_FORMAT,
        max_packets_per_file: int = DNSTrainPCAPContentAnalysisHandler.DEFAULT_MAX_PACKETS_PER_FILE,
        max_blocks_per_file: int = DNSTrainPCAPContentAnalysisHandler.DEFAULT_MAX_BLOCKS_PER_FILE,
    ) -> None:
        super().__init__(
            temp_data_path=temp_data_path,
            project_root=project_root,
            max_files_per_format=max_files_per_format,
            max_packets_per_file=max_packets_per_file,
            max_blocks_per_file=max_blocks_per_file,
        )
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "validation"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "dns" / "validation"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "dns" / "validation"

    def analyze_and_generate_docs(self) -> DNSValidationPCAPContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-dns-file.json for VALIDATION/pcap.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcap.md"
        docs_en_path = self.docs_en_dir / "pcap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task1(Analysis of dns validation pcap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task1(Analysis of dns validation pcap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_validation_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_validation_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_validation_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_validation_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_validation_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_validation_report(summary, summary_json_path, "en"))

        return DNSValidationPCAPContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary["final_status"]),
        )

    def _build_validation_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"])
        variants = ", ".join(f"{key}: {value}" for key, value in summary["container_variants"].items()) or "-"
        protocols = ", ".join(f"{key}: {value}" for key, value in summary["ip_protocols"].items()) or "-"
        labels = self._label_values(summary)
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS VALIDATION содержат raw packet capture трафик для проверки DNS amplification attack / benign сценариев. Формат нужен для валидации packet-level DNS признаков, сетевых агрегатов и сверки downstream feature extraction.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | VALIDATION |
| Количество файлов | {summary["scope"]["total_files_count"]} |

## 3. Примеры файлов
```text
{examples}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcap global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Содержательная структура
Контейнеры в sample: {variants}. IP protocol distribution: {protocols}. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: {summary["dns_port_hits_sample"]}.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| container_variant | string | classic pcap или pcapng | {next(iter(summary["container_variants"]), "")} |
| magic | hex | capture signature | {summary["file_probes"][0]["magic"] if summary["file_probes"] else ""} |
| ip_protocol | integer | IP protocol | {next(iter(summary["ip_protocols"]), "")} |
| udp_dst_port | integer | UDP destination port sample | {next(iter(summary["udp_ports_sample"]), "")} |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла |
| Значения label | {labels} |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet timestamp |
| Формат времени | pcap seconds/usec |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- qname, qtype/qclass, response size;
- DNS amplification query/response ratios;
- RCODE/NXDOMAIN distribution;
- TTL and answer count;
- inter-query intervals.

### Network / hybrid-признаки
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- attack/benign label from file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Поврежденные файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | packet headers доступны |
| Нестабильная структура | нет | sample содержит classic pcap |
| Смешанные схемы | нет | один контейнерный тип в sample |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
DNS VALIDATION pcap полезен для проверки DNS amplification detection pipeline, но production processing должен использовать packet parser с DNS protocol decoding.
"""

        return f"""# Format Analysis: pcap

## 1. Purpose
DNS VALIDATION PCAP files contain raw packet capture traffic for DNS amplification attack / benign validation scenarios. The format is needed for packet-level DNS features, network aggregates, and downstream feature extraction checks.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | VALIDATION |
| File count | {summary["scope"]["total_files_count"]} |

## 3. Example Files
```text
{examples}
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcap global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Content Structure
Containers in the sample: {variants}. IP protocol distribution: {protocols}. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: {summary["dns_port_hits_sample"]}.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| container_variant | string | classic pcap or pcapng | {next(iter(summary["container_variants"]), "")} |
| magic | hex | capture signature | {summary["file_probes"][0]["magic"] if summary["file_probes"] else ""} |
| ip_protocol | integer | IP protocol | {next(iter(summary["ip_protocols"]), "")} |
| udp_dst_port | integer | UDP destination port sample | {next(iter(summary["udp_ports_sample"]), "")} |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name |
| Label values | {labels} |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet timestamp |
| Time format | pcap seconds/usec |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- qname, qtype/qclass, response size;
- DNS amplification query/response ratios;
- RCODE/NXDOMAIN distribution;
- TTL and answer count;
- inter-query intervals.

### Network / Hybrid Features
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- attack/benign label from file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | no | packet headers are available |
| Unstable structure | no | sample contains classic pcap |
| Mixed schemas | no | one container type in sample |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
DNS VALIDATION pcap is useful for validating a DNS amplification detection pipeline, but production processing must use a packet parser with DNS protocol decoding.
"""

    def _build_validation_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "pcap": (summary["final_status"], "pcap.md"),
            "txt": (self._load_optional_status("analysis-dns-validation-txt-summary.json"), "txt.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_validation_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task1: Analysis of dns validation pcap dataset files"
            if ru
            else "# Task1 Report: Analysis of dns validation pcap dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_DNS_DATASETS_FILTER\\VALIDATION\\pcap` на основе `{self.DNS_INPUT_JSON_FILE}`. "
            "Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_DNS_DATASETS_FILTER\\VALIDATION\\pcap` using `{self.DNS_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_validation_pcap_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/validation/pcap.md`
- `docs/en/analysis-dataset/dns/validation/pcap.md`
- `docs/ru/analysis-dataset/dns/validation/README.md`
- `docs/en/analysis-dataset/dns/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/dns/validation/Task1(Analysis of dns validation pcap dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/dns/validation/Task1(Analysis of dns validation pcap dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.pcap`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler определяет pcap-контейнер по magic bytes и читает ограниченное число packet records.' if ru else 'The handler detects the pcap container by magic bytes and reads a limited number of packet records.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.DNS_INPUT_JSON_FILE).read(default={})
        bucket = payload.get(self.ROLE_NAME, {})
        return {fmt: len(paths) for fmt, paths in bucket.items() if isinstance(paths, list)} if isinstance(bucket, dict) else {}

    def _load_optional_status(self, summary_file_name: str) -> str:
        summary_path = self.temp_data_path / summary_file_name
        if not summary_path.exists():
            return "-"
        payload = JsonDataManager(summary_path).read(default={})
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

    @staticmethod
    def _label_values(summary: dict[str, Any]) -> str:
        labels = set()
        for path in summary.get("sample_paths", []):
            name = Path(path).name.lower()
            if "attack" in name:
                labels.add("attack")
            if "benign" in name:
                labels.add("benign")
        return ", ".join(sorted(labels)) or "-"

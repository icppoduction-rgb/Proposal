from __future__ import annotations

import argparse
import os
import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


# В datasets-new/host лежат уже сконвертированные JSON-файлы. Имя исходного
# датасета хранится в data.metadata.dataset, поэтому очистка идет по этому
# метаданному полю, а не по имени файла.
DATASET_PATTERN = re.compile(rb'"dataset"\s*:\s*"((?:\\.|[^"\\])*)"')
DEFAULT_METADATA_READ_BYTES = 4 * 1024
DEFAULT_WORKERS = max(1, min(os.cpu_count() or 1, 16))
HOST_SPLITS = ("TRAIN", "VALIDATION", "TEST", "EXPERIMENTS")


# Минимальный стек из docs/ru/host_datasets_analysis.md, достаточный для
# дипломного proposal: baseline HIDS, syscall sequence modelling и enterprise
# multi-stage logs. Остальные host-наборы остаются расширенной/опциональной
# валидацией и создают основной объем данных.
MINIMAL_DIPLOMA_DATASETS: set[str] = {
    "ADFA IDS",
    "LID-DS 2021",
    "Maintainable Log Dataset",
}


REMOVAL_REASONS: dict[str, str] = {
    "LID-DS 2019": "cross-version validation; полезен, но не обязателен для минимального дипломного scope",
    "LANL Dataset": "enterprise user-host validation; крупный desirable dataset, не входит в минимальный стек",
    "Windows-Event-Log -OTRF-Security-Datasets": "SOC-style Windows validation; desirable, но не обязателен",
    "Unified-Host-Network-Dataset -LANL": "hybrid host+network validation; полезен для расширенной оценки, но слишком крупный для текущего scope",
    "ISOT-Cloud-IDS-Dataset": "cloud validation; optional dataset",
    "Dynamic-Malware-Analysis-Dataset": "malware-driven validation; optional и самый объемный dataset",
    "HDFS-Log-Dataset": "experiments-only log anomaly dataset; не security-focused baseline",
}


@dataclass(frozen=True)
class FileDecision:
    """Решение по одному converted JSON-файлу."""

    path: Path
    dataset: str | None
    size_bytes: int
    keep: bool
    reason: str


@dataclass(frozen=True)
class DatasetStats:
    """Агрегированная статистика по одному исходному датасету."""

    files: int = 0
    size_bytes: int = 0


@dataclass(frozen=True)
class CleanupResult:
    """Итог dry-run или apply-запуска."""

    root: Path
    keep_datasets: set[str]
    scanned_files: int
    kept_files: int
    deleted_files: int
    kept_bytes: int
    deleted_bytes: int
    unknown_metadata_files: int
    deleted_paths: list[Path]
    kept_by_dataset: dict[str, DatasetStats]
    deleted_by_dataset: dict[str, DatasetStats]


def format_bytes(size: int) -> str:
    """Форматирует байты в читаемый CLI-вид."""

    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} TiB"


def decode_json_string(raw_value: bytes) -> str:
    """Декодирует JSON-строку из regex-группы без полного чтения файла."""

    # json.loads ожидает полноценную JSON-строку с кавычками. Такой способ
    # корректно обрабатывает escaped-символы в имени датасета.
    return json.loads(b'"' + raw_value + b'"')


def read_dataset_metadata(path: Path, read_bytes: int = DEFAULT_METADATA_READ_BYTES) -> str | None:
    """Извлекает data.metadata.dataset из начала converted JSON-файла."""

    with path.open("rb") as file:
        prefix = file.read(read_bytes)

    match = DATASET_PATTERN.search(prefix)
    if not match:
        return None

    return decode_json_string(match.group(1))


def iter_host_json_files(root: Path) -> list[Path]:
    """Возвращает только файлы datasets-new/host/<split>/*.json."""

    files: list[Path] = []

    for split in HOST_SPLITS:
        split_dir = root / split
        if not split_dir.exists():
            continue
        if not split_dir.is_dir():
            raise NotADirectoryError(f"Host split path is not a directory: {split_dir}")

        # Текущий host-конвертер пишет плоскую структуру split/*.json. glob()
        # заметно быстрее rglob() на сотнях тысяч файлов.
        files.extend(path for path in split_dir.glob("*.json") if path.is_file())

    return files


def ensure_safe_delete_path(path: Path, root: Path) -> Path:
    """Проверяет, что удаляется файл внутри datasets-new/host/<split>/."""

    resolved_root = root.resolve()
    resolved_path = path.resolve()
    relative_path = resolved_path.relative_to(resolved_root)

    if not resolved_path.is_file():
        raise ValueError(f"Refusing to delete non-file path: {resolved_path}")

    if len(relative_path.parts) < 2 or relative_path.parts[0] not in HOST_SPLITS:
        raise ValueError(f"Refusing to delete path outside known host splits: {resolved_path}")

    return resolved_path


def build_decision(path: Path, keep_datasets: set[str], read_bytes: int) -> FileDecision:
    """Строит keep/delete-решение для одного converted JSON-файла."""

    dataset = read_dataset_metadata(path, read_bytes=read_bytes)
    size_bytes = path.stat().st_size

    if dataset is None:
        # Неизвестные файлы безопаснее оставить: это защищает от удаления
        # поврежденного или нового формата без явного анализа.
        return FileDecision(
            path=path,
            dataset=None,
            size_bytes=size_bytes,
            keep=True,
            reason="dataset metadata not found",
        )

    if dataset in keep_datasets:
        return FileDecision(
            path=path,
            dataset=dataset,
            size_bytes=size_bytes,
            keep=True,
            reason="minimal diploma dataset",
        )

    return FileDecision(
        path=path,
        dataset=dataset,
        size_bytes=size_bytes,
        keep=False,
        reason=REMOVAL_REASONS.get(dataset, "not selected for minimal diploma dataset stack"),
    )


def build_decisions(
    root: Path,
    keep_datasets: set[str],
    *,
    read_bytes: int = DEFAULT_METADATA_READ_BYTES,
    workers: int = DEFAULT_WORKERS,
) -> list[FileDecision]:
    """Строит решения keep/delete для всех converted JSON-файлов."""

    files = iter_host_json_files(root)

    if workers <= 1:
        return [
            build_decision(path=path, keep_datasets=keep_datasets, read_bytes=read_bytes)
            for path in files
        ]

    decisions: list[FileDecision] = []

    # Чтение маленького префикса у сотен тысяч файлов является IO-bound задачей,
    # поэтому ограниченный ThreadPool ускоряет dry-run и apply без лишней памяти.
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                build_decision,
                path,
                keep_datasets,
                read_bytes,
            )
            for path in files
        ]

        for future in as_completed(futures):
            decisions.append(future.result())

    return decisions


def add_stat(stats: dict[str, list[int]], dataset: str, size_bytes: int) -> None:
    """Добавляет один файл в агрегированную статистику."""

    stats[dataset][0] += 1
    stats[dataset][1] += size_bytes


def freeze_stats(stats: dict[str, list[int]]) -> dict[str, DatasetStats]:
    """Преобразует mutable-счетчики в dataclass-структуры для отчета."""

    return {
        dataset: DatasetStats(files=values[0], size_bytes=values[1])
        for dataset, values in sorted(stats.items(), key=lambda item: item[0])
    }


def cleanup_host_datasets_new(
    root: str | Path,
    keep_datasets: set[str] | None = None,
    *,
    dry_run: bool = True,
    read_bytes: int = DEFAULT_METADATA_READ_BYTES,
    workers: int = DEFAULT_WORKERS,
) -> CleanupResult:
    """Удаляет из datasets-new/host converted JSON-файлы невыбранных датасетов."""

    root_path = Path(root).resolve()
    selected_datasets = set(keep_datasets or MINIMAL_DIPLOMA_DATASETS)

    if not root_path.exists():
        raise FileNotFoundError(f"datasets-new/host directory not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"datasets-new/host path is not a directory: {root_path}")

    decisions = build_decisions(
        root=root_path,
        keep_datasets=selected_datasets,
        read_bytes=read_bytes,
        workers=workers,
    )
    kept_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    deleted_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    deleted_paths: list[Path] = []
    kept_files = 0
    deleted_files = 0
    kept_bytes = 0
    deleted_bytes = 0
    unknown_metadata_files = 0

    for decision in decisions:
        dataset_key = decision.dataset or "<unknown>"

        if decision.keep:
            kept_files += 1
            kept_bytes += decision.size_bytes
            add_stat(kept_stats, dataset_key, decision.size_bytes)
            if decision.dataset is None:
                unknown_metadata_files += 1
            continue

        deleted_files += 1
        deleted_bytes += decision.size_bytes
        add_stat(deleted_stats, dataset_key, decision.size_bytes)
        deleted_paths.append(decision.path)

        if not dry_run:
            safe_path = ensure_safe_delete_path(decision.path, root_path)
            safe_path.unlink()

    return CleanupResult(
        root=root_path,
        keep_datasets=selected_datasets,
        scanned_files=len(decisions),
        kept_files=kept_files,
        deleted_files=deleted_files,
        kept_bytes=kept_bytes,
        deleted_bytes=deleted_bytes,
        unknown_metadata_files=unknown_metadata_files,
        deleted_paths=deleted_paths,
        kept_by_dataset=freeze_stats(kept_stats),
        deleted_by_dataset=freeze_stats(deleted_stats),
    )


def write_cleanup_report(result: CleanupResult, report_path: Path, *, dry_run: bool) -> None:
    """Записывает машинно-читаемый отчет рядом с datasets-new/host."""

    payload = {
        "mode": "dry-run" if dry_run else "apply",
        "root": str(result.root),
        "keep_datasets": sorted(result.keep_datasets),
        "scanned_files": result.scanned_files,
        "kept_files": result.kept_files,
        "deleted_files": result.deleted_files,
        "kept_bytes": result.kept_bytes,
        "deleted_bytes": result.deleted_bytes,
        "unknown_metadata_files": result.unknown_metadata_files,
        "kept_by_dataset": {
            dataset: {"files": stats.files, "size_bytes": stats.size_bytes}
            for dataset, stats in result.kept_by_dataset.items()
        },
        "deleted_by_dataset": {
            dataset: {
                "files": stats.files,
                "size_bytes": stats.size_bytes,
                "reason": REMOVAL_REASONS.get(dataset, "not selected for minimal diploma dataset stack"),
            }
            for dataset, stats in result.deleted_by_dataset.items()
        },
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def print_result(result: CleanupResult, *, dry_run: bool) -> None:
    """Печатает краткий отчет для ручной проверки."""

    mode = "DRY-RUN" if dry_run else "APPLY"

    print(f"Mode: {mode}")
    print(f"Root: {result.root}")
    print(f"Keep datasets: {', '.join(sorted(result.keep_datasets))}")
    print(f"Scanned files: {result.scanned_files}")
    print(f"Kept files: {result.kept_files} ({format_bytes(result.kept_bytes)})")
    print(f"Deleted files: {result.deleted_files} ({format_bytes(result.deleted_bytes)})")
    print(f"Unknown metadata files kept: {result.unknown_metadata_files}")

    print("Deleted by dataset:")
    if not result.deleted_by_dataset:
        print(" - none")
    for dataset, stats in sorted(
        result.deleted_by_dataset.items(),
        key=lambda item: item[1].size_bytes,
        reverse=True,
    ):
        reason = REMOVAL_REASONS.get(dataset, "not selected for minimal diploma dataset stack")
        print(f" - {dataset}: files={stats.files}, size={format_bytes(stats.size_bytes)}, reason={reason}")

    if dry_run:
        print("Files were not deleted. Re-run with --apply to delete.")


def parse_args() -> argparse.Namespace:
    """Парсит CLI-аргументы cleanup-скрипта."""

    parser = argparse.ArgumentParser(
        description="Clean unnecessary converted host datasets under datasets-new/host."
    )
    parser.add_argument(
        "--root",
        default=r"datasets-new\host",
        help="Path to datasets-new/host. Default: datasets-new\\host",
    )
    parser.add_argument(
        "--keep-dataset",
        action="append",
        default=[],
        help="Additional dataset name to keep. Can be passed multiple times.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete files. Without this flag the script runs in dry-run mode.",
    )
    parser.add_argument(
        "--report",
        default="cleanup_summary.json",
        help="Report filename or path. Relative paths are created under --root.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of metadata reader threads. Default: {DEFAULT_WORKERS}",
    )
    parser.add_argument(
        "--metadata-read-bytes",
        type=int,
        default=DEFAULT_METADATA_READ_BYTES,
        help=f"Bytes read from each JSON file to find metadata.dataset. Default: {DEFAULT_METADATA_READ_BYTES}",
    )
    return parser.parse_args()


def main() -> None:
    """Точка входа для запуска из командной строки."""

    args = parse_args()
    root = Path(args.root)
    keep_datasets = MINIMAL_DIPLOMA_DATASETS | set(args.keep_dataset)
    dry_run = not args.apply

    result = cleanup_host_datasets_new(
        root=root,
        keep_datasets=keep_datasets,
        dry_run=dry_run,
        read_bytes=args.metadata_read_bytes,
        workers=args.workers,
    )
    print_result(result, dry_run=dry_run)

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path
    write_cleanup_report(result=result, report_path=report_path, dry_run=dry_run)
    print(f"Report: {report_path.resolve()}")


if __name__ == "__main__":
    main()

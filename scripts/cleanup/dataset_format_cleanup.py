from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from scripts.workdatasets.dataset_processing import collect_processed_extensions, write_processed_dataset_json
from scripts.json_data import JsonData


SNIFF_BYTES = 8192

TEXT_READABLE_EXTENSIONS: set[str] = {
    ".0",
    ".1",
    ".2",
    ".3",
    ".4",
    ".5",
    ".7",
    ".8",
    ".access",
    ".acm",
    ".alias",
    ".allow",
    ".atd",
    ".bak",
    ".bashrc",
    ".blacklist",
    ".cache",
    ".cfg",
    ".client",
    ".cnf",
    ".com",
    ".com_add_aggi_up",
    ".com_add_and_delete_aggi_up",
    ".com_change_ipv4",
    ".com_change_ipv4_post_up",
    ".com_change_ipv4_pre_up",
    ".com_change_ipv6",
    ".com_change_ipv6_post_up",
    ".com_change_ipv6_pre_up",
    ".com_change_method",
    ".com_revert",
    ".com_set_aggi_and_eth0_mtu",
    ".com_set_aggi_slaves",
    ".commit",
    ".commitmeta",
    ".conf",
    ".config",
    ".control",
    ".csv",
    ".dat",
    ".default",
    ".defaults",
    ".defs",
    ".delta",
    ".deny",
    ".desktop",
    ".dhclient",
    ".dirmeta",
    ".dirtree",
    ".disabled",
    ".dist",
    ".dtd",
    ".example",
    ".ext",
    ".fallback",
    ".filez",
    ".flatpakref",
    ".flatpakrepo",
    ".gen",
    ".ghc",
    ".hcl",
    ".html",
    ".idx",
    ".inc",
    ".info",
    ".ini",
    ".init",
    ".initial_md5sum",
    ".inventory",
    ".iscsi",
    ".j2",
    ".ja",
    ".jfc",
    ".json",
    ".jsonnet",
    ".kmap",
    ".ldif",
    ".list",
    ".load",
    ".local",
    ".lock",
    ".log",
    ".lxc-start",
    ".man",
    ".map",
    ".md",
    ".mime",
    ".mysqld",
    ".net",
    ".netflow_ids",
    ".options",
    ".order",
    ".org",
    ".override",
    ".path",
    ".pcapng",
    ".php",
    ".plymouth",
    ".policy",
    ".prev",
    ".profile",
    ".properties",
    ".ps1",
    ".psf",
    ".pub",
    ".py",
    ".rb",
    ".rc",
    ".real",
    ".res",
    ".rst",
    ".rsyslogd",
    ".rules",
    ".sc",
    ".security",
    ".service",
    ".sh",
    ".socket",
    ".spec",
    ".sql",
    ".subr",
    ".svg",
    ".sysctl",
    ".target",
    ".tcpdump",
    ".template",
    ".test_no_changes",
    ".tf",
    ".timer",
    ".tiny",
    ".tmpl",
    ".txt",
    ".types",
    ".ubuntu",
    ".v4",
    ".vga",
    ".webarchive",
    ".xml",
    ".xsd",
    ".yaml",
    ".yml",
}

BINARY_READABLE_EXTENSIONS: set[str] = {
    ".bson",
    ".cap",
    ".certs",
    ".crt",
    ".csr",
    ".dmp",
    ".docx",
    ".eps",
    ".exe",
    ".gpg",
    ".gpg~",
    ".gz",
    ".iso",
    ".journal",
    ".journal~",
    ".jpg",
    ".key",
    ".keystore",
    ".npz",
    ".odt",
    ".p12",
    ".pcap",
    ".pcapng",
    ".pdf",
    ".pem",
    ".png",
    ".pptx",
    ".pyc",
    ".sig",
    ".xlsx",
}


@dataclass(frozen=True)
class FileDecision:
    """
    Описывает решение по одному файлу: оставить его или удалить как нечитаемый.
    """

    path: Path
    size: int
    extension: str
    dataset_key: str
    keep: bool
    reason: str


@dataclass(frozen=True)
class DatasetFormatCleanupResult:
    """
    Хранит итог очистки форматов для CLI-отчета и последующей проверки.
    """

    total_files: int
    total_bytes: int
    kept_files: int
    kept_bytes: int
    deleted_files: int
    deleted_bytes: int
    missing_files: int
    deleted_paths: list[Path]
    processed_path_file: Path
    processed_extensions_file: Path
    top_deleted_extensions: list[tuple[str, int, int]]
    top_deleted_datasets: list[tuple[str, int, int]]


def read_processed_dataset_paths(path_file: str | Path) -> dict[str, dict[str, list[str]]]:
    """
    Читает processed JSON с путями датасетов и проверяет ожидаемый формат.
    """

    data = JsonData(path_file).read(default={})

    if not isinstance(data, dict):
        raise TypeError(f"Processed JSON должен быть объектом: {path_file}")

    for domain, splits in data.items():
        if not isinstance(domain, str) or not isinstance(splits, dict):
            raise TypeError("Ожидается структура {domain: {split: [paths...]}}")

        for split, paths in splits.items():
            if not isinstance(split, str) or not isinstance(paths, list):
                raise TypeError("Ожидается структура {domain: {split: [paths...]}}")

            if not all(isinstance(path, str) for path in paths):
                raise TypeError("Все пути в processed JSON должны быть строками")

    return data


def read_file_sample(path: Path, sample_size: int = SNIFF_BYTES) -> bytes:
    """
    Читает только первые байты файла, чтобы не загружать крупные датасеты в память.
    """

    with path.open("rb") as file:
        return file.read(sample_size)


def is_text_like(sample: bytes) -> bool:
    """
    Проверяет, похож ли файл на потоковый текст, пригодный для чтения Python.
    """

    if not sample:
        return True

    null_ratio = sample.count(b"\x00") / len(sample)
    if null_ratio > 0.05:
        return False

    for encoding in ("utf-8-sig", "utf-16", "cp1251"):
        try:
            text = sample.decode(encoding)
        except UnicodeDecodeError:
            continue

        if not text:
            return True

        control_chars = sum(
            1
            for char in text
            if ord(char) < 32 and char not in "\r\n\t\f\b"
        )

        return control_chars / len(text) < 0.10

    return False


def has_supported_magic(sample: bytes) -> bool:
    """
    Определяет известные бинарные форматы, для которых есть Python-парсеры.
    """

    magic_prefixes = (
        b"\x7fELF",
        b"MZ",
        b"%PDF",
        b"PK\x03\x04",
        b"\x1f\x8b",
        b"\x89PNG\r\n\x1a\n",
        b"\xff\xd8\xff",
        b"SQLite format 3\x00",
        b"\xd4\xc3\xb2\xa1",
        b"\xa1\xb2\xc3\xd4",
        b"\x0a\x0d\x0d\x0a",
        b"\xcf\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
    )

    return any(sample.startswith(prefix) for prefix in magic_prefixes)


def is_rotated_pcap(path: Path) -> bool:
    """
    Распознает файлы вида log.pcap.<timestamp>, где реальный формат задает середина имени.
    """

    return ".pcap." in path.name.lower()


def get_dataset_key(path: Path) -> str:
    """
    Возвращает ключ датасета в формате domain/split/dataset для агрегированного отчета.
    """

    parts = path.parts

    for domain in ("dns", "host"):
        try:
            index = parts.index(domain)
        except ValueError:
            continue

        if index + 2 < len(parts):
            return "/".join(parts[index:index + 3])

    return "<unknown>"


def classify_file(path: Path) -> FileDecision:
    """
    Классифицирует файл как читаемый или нечитаемый без полного чтения содержимого.
    """

    extension = path.suffix.lower() or "<none>"
    size = path.stat().st_size

    if path.suffix.lower() in TEXT_READABLE_EXTENSIONS:
        return FileDecision(
            path=path,
            size=size,
            extension=extension,
            dataset_key=get_dataset_key(path),
            keep=True,
            reason="readable extension",
        )

    if path.suffix.lower() in BINARY_READABLE_EXTENSIONS or is_rotated_pcap(path):
        return FileDecision(
            path=path,
            size=size,
            extension=extension,
            dataset_key=get_dataset_key(path),
            keep=True,
            reason="readable by Python ecosystem",
        )

    sample = read_file_sample(path)

    if is_text_like(sample):
        return FileDecision(
            path=path,
            size=size,
            extension=extension,
            dataset_key=get_dataset_key(path),
            keep=True,
            reason="text-like stream",
        )

    if has_supported_magic(sample):
        return FileDecision(
            path=path,
            size=size,
            extension=extension,
            dataset_key=get_dataset_key(path),
            keep=True,
            reason="supported magic signature",
        )

    return FileDecision(
        path=path,
        size=size,
        extension=extension,
        dataset_key=get_dataset_key(path),
        keep=False,
        reason="unknown binary format",
    )


def ensure_file_inside_datasets(path: Path, datasets_root: str | Path) -> Path:
    """
    Проверяет, что удаляемый файл расположен внутри datasets и не является директорией.
    """

    root_path = Path(datasets_root).resolve()
    resolved_path = path.resolve()
    resolved_path.relative_to(root_path)

    if not resolved_path.is_file():
        raise ValueError(f"Удалять можно только файлы внутри datasets: {path}")

    return resolved_path


def build_cleanup_summary(
    deleted_decisions: list[FileDecision],
) -> tuple[list[tuple[str, int, int]], list[tuple[str, int, int]]]:
    """
    Собирает top-списки удаляемых расширений и датасетов по размеру.
    """

    by_extension: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_dataset: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for decision in deleted_decisions:
        by_extension[decision.extension][0] += 1
        by_extension[decision.extension][1] += decision.size
        by_dataset[decision.dataset_key][0] += 1
        by_dataset[decision.dataset_key][1] += decision.size

    top_extensions = sorted(
        ((extension, values[0], values[1]) for extension, values in by_extension.items()),
        key=lambda item: item[2],
        reverse=True,
    )[:20]
    top_datasets = sorted(
        ((dataset, values[0], values[1]) for dataset, values in by_dataset.items()),
        key=lambda item: item[2],
        reverse=True,
    )[:20]

    return top_extensions, top_datasets


def cleanup_unreadable_dataset_files(
    datasets_root: str | Path,
    processed_path_file: str | Path,
    processed_extensions_file: str | Path,
    *,
    dry_run: bool = False,
) -> DatasetFormatCleanupResult:
    """
    Удаляет нечитаемые файлы из datasets и обновляет processed JSON после очистки.
    """

    dataset_paths = read_processed_dataset_paths(processed_path_file)
    kept_paths: dict[str, dict[str, list[str]]] = {}
    deleted_decisions: list[FileDecision] = []
    missing_files = 0
    total_files = 0
    total_bytes = 0
    kept_files = 0
    kept_bytes = 0

    for domain, splits in dataset_paths.items():
        kept_paths[domain] = {}

        for split, paths in splits.items():
            kept_paths[domain][split] = []

            for file_path in paths:
                path = Path(file_path)

                if not path.exists():
                    missing_files += 1
                    continue

                decision = classify_file(path)
                total_files += 1
                total_bytes += decision.size

                if decision.keep:
                    kept_files += 1
                    kept_bytes += decision.size
                    kept_paths[domain][split].append(file_path)
                else:
                    deleted_decisions.append(decision)

    deleted_paths = [decision.path for decision in deleted_decisions]

    if not dry_run:
        for path in deleted_paths:
            safe_path = ensure_file_inside_datasets(path, datasets_root)
            safe_path.unlink()

        processed_extensions = collect_processed_extensions(kept_paths)
        write_processed_dataset_json(
            processed_paths=kept_paths,
            processed_extensions=processed_extensions,
            processed_path_file=processed_path_file,
            processed_extensions_file=processed_extensions_file,
        )

    top_extensions, top_datasets = build_cleanup_summary(deleted_decisions)
    deleted_bytes = sum(decision.size for decision in deleted_decisions)

    return DatasetFormatCleanupResult(
        total_files=total_files,
        total_bytes=total_bytes,
        kept_files=kept_files,
        kept_bytes=kept_bytes,
        deleted_files=len(deleted_decisions),
        deleted_bytes=deleted_bytes,
        missing_files=missing_files,
        deleted_paths=deleted_paths,
        processed_path_file=Path(processed_path_file),
        processed_extensions_file=Path(processed_extensions_file),
        top_deleted_extensions=top_extensions,
        top_deleted_datasets=top_datasets,
    )


def format_bytes(size: int) -> str:
    """
    Форматирует размер в человекочитаемом виде для CLI-отчета.
    """

    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} TiB"


def print_cleanup_result(result: DatasetFormatCleanupResult, *, dry_run: bool) -> None:
    """
    Печатает отчет по dry-run или примененной очистке нечитаемых форматов.
    """

    mode = "DRY-RUN" if dry_run else "APPLY"

    print(f"Mode: {mode}")
    print(f"Total files before: {result.total_files}")
    print(f"Total size before: {format_bytes(result.total_bytes)}")
    print(f"Kept files: {result.kept_files}")
    print(f"Kept size: {format_bytes(result.kept_bytes)}")
    print(f"Deleted files: {result.deleted_files}")
    print(f"Deleted size: {format_bytes(result.deleted_bytes)}")
    print(f"Missing files skipped: {result.missing_files}")

    print("Top deleted extensions by size:")
    if result.top_deleted_extensions:
        for extension, count, size in result.top_deleted_extensions:
            print(f" - {extension}: files={count}, size={format_bytes(size)}")
    else:
        print(" - none")

    print("Top deleted datasets by size:")
    if result.top_deleted_datasets:
        for dataset, count, size in result.top_deleted_datasets:
            print(f" - {dataset}: files={count}, size={format_bytes(size)}")
    else:
        print(" - none")

    if dry_run:
        print("JSON files were not updated. Files were not deleted.")
    else:
        print(f"Updated: {result.processed_path_file}")
        print(f"Updated: {result.processed_extensions_file}")

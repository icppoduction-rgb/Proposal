"""Dataset file discovery and metadata inference."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.db.models.constants import ACTIVE_DATASET_ROLE_VALUES, BRANCH_VALUES
from scripts.stage_two.catalog_exclusions import is_excluded_raw_bucket


KNOWN_SOURCE_FORMATS: tuple[str, ...] = (
    "process.summary.log",
    "socket.summary.log",
    "mail-info-1",
    "mail-warn-1",
    "netflow_day",
    "wls_day",
    "pcap.csv",
    "auth.log",
    "cpu.log",
    "diskio.log",
    "filesystem.log",
    "fsstat.log",
    "load.log",
    "memory.log",
    "network.log",
    "process.log",
    "service.log",
    "syslog.log",
    "uptime.log",
    "journal~",
    "json-1",
    "log-1",
    "log-2",
    "log-3",
    "mainlog-1",
    "mainlog-2",
    "mainlog-3",
    "messages-1",
    "syslog-1",
    "syslog-2",
    "syslog-3",
    "syslog-4",
    "mainlog",
    "messages",
    "netflow_ids",
    "pcapng",
    "pcap",
    "cap",
    "bson",
    "csv",
    "ghc",
    "info",
    "journal",
    "json",
    "log",
    "sc",
    "syslog",
    "txt",
    "xml",
)
SUPPORTED_SOURCE_FORMATS: frozenset[str] = frozenset(KNOWN_SOURCE_FORMATS)
SOURCE_FORMAT_MATCH_PRIORITY: tuple[str, ...] = tuple(
    sorted(KNOWN_SOURCE_FORMATS, key=lambda value: (-len(value), value))
)
SOURCE_FORMAT_BY_LOWER: dict[str, str] = {
    source_format.lower(): source_format for source_format in KNOWN_SOURCE_FORMATS
}


@dataclass(frozen=True)
class DatasetFileCandidate:
    """File discovered for catalog ingestion."""

    path: Path
    root_path: Path
    relative_path: Path
    dataset_name: str
    dataset_slug: str
    branch: str
    role: str
    source_format: str


class DatasetFileScanner:
    """Scan dataset roots and infer catalog metadata from paths."""

    def scan(self, root_path: str | Path) -> list[DatasetFileCandidate]:
        """Return file candidates under a root path."""
        root = Path(root_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Dataset root does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Dataset root is not a directory: {root}")

        candidates: list[DatasetFileCandidate] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            branch = self.infer_branch(relative, root)
            role = self.infer_role(relative)
            if role is None:
                continue
            source_format = self.infer_source_format(path, relative_path=relative)
            if is_excluded_raw_bucket(
                branch=branch,
                role=role,
                source_format=source_format,
                relative_path=relative,
            ):
                continue
            dataset_name = self.infer_dataset_name(relative, branch, role, source_format)
            candidates.append(
                DatasetFileCandidate(
                    path=path,
                    root_path=root,
                    relative_path=relative,
                    dataset_name=dataset_name,
                    dataset_slug=slugify(dataset_name),
                    branch=branch,
                    role=role,
                    source_format=source_format,
                )
            )
        return candidates

    def infer_branch(self, relative_path: Path, root_path: Path) -> str:
        """Infer branch from a relative path or root path."""
        parts = [part.lower() for part in (*root_path.parts, *relative_path.parts)]
        for branch in BRANCH_VALUES:
            if branch in parts:
                return branch
        return "hybrid"

    def infer_role(self, relative_path: Path) -> str | None:
        """Infer an active TRAIN/VALIDATION/TEST role from path parts."""
        upper_parts = [part.upper() for part in relative_path.parts]
        for role in ACTIVE_DATASET_ROLE_VALUES:
            if role in upper_parts:
                return role
        return None

    def infer_source_format(self, path: Path, relative_path: Path | None = None) -> str:
        """Infer the Stage Two source_format value from bucket context or file name."""
        bucket_source_format = self.infer_bucket_source_format(relative_path)
        if bucket_source_format:
            return bucket_source_format

        return self.infer_file_source_format(path)

    def infer_bucket_source_format(self, relative_path: Path | None) -> str | None:
        """Infer source_format from a sorted tree role/format bucket."""
        if relative_path is None:
            return None

        parts = list(relative_path.parts)
        if len(parts) < 3:
            return None

        upper_parts = [part.upper() for part in parts]
        role_index = next(
            (
                index
                for index, part in enumerate(upper_parts[:-1])
                if part in ACTIVE_DATASET_ROLE_VALUES
            ),
            None,
        )
        if role_index is None:
            return None

        for part in parts[role_index + 1 : -1]:
            source_format = SOURCE_FORMAT_BY_LOWER.get(part.lower())
            if source_format:
                return source_format
        return None

    def infer_file_source_format(self, path: Path) -> str:
        """Infer source_format from a raw file name using compound-name priority."""
        name = path.name.lower()
        for source_format in SOURCE_FORMAT_MATCH_PRIORITY:
            if name == source_format or name.endswith(f".{source_format}"):
                return source_format
        suffix = path.suffix.lower().lstrip(".")
        return suffix or "unknown"

    def infer_dataset_name(
        self,
        relative_path: Path,
        branch: str,
        role: str,
        source_format: str,
    ) -> str:
        """Infer a stable dataset name from path context."""
        parts = list(relative_path.parts[:-1])
        lower_parts = [part.lower() for part in parts]
        upper_parts = [part.upper() for part in parts]

        start = lower_parts.index(branch) + 1 if branch in lower_parts else 0
        end = upper_parts.index(role) if role in upper_parts else len(parts)
        dataset_parts = [
            part
            for part in parts[start:end]
            if part.lower() not in SUPPORTED_SOURCE_FORMATS
            and part.upper() not in ACTIVE_DATASET_ROLE_VALUES
        ]
        if dataset_parts:
            return dataset_parts[0]
        return f"{branch}_{role.lower()}_{source_format}"


def slugify(value: str) -> str:
    """Return a lowercase slug safe for catalog natural keys."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown-dataset"

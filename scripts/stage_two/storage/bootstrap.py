"""Idempotent filesystem bootstrap for Stage Two generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BRANCHES: tuple[str, ...] = ("dns", "host", "network", "hybrid")
ROLES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST")
FEATURE_GROUPS: tuple[str, ...] = (
    "dns_features",
    "host_syscall_features",
    "host_eventlog_features",
    "host_metrics_features",
    "network_flow_features",
    "hybrid_features",
    "sequence_features",
)
MODEL_READY_TYPES: tuple[str, ...] = (
    "tabular",
    "labels",
    "sequences",
    "preprocessing",
    "split_index",
)
REPORT_GROUPS: tuple[str, ...] = (
    "parser",
    "normalization",
    "quality",
    "leakage",
    "schema_mismatch",
)


@dataclass(frozen=True)
class StorageBootstrapResult:
    """Result of a Stage Two storage bootstrap run."""

    root: Path
    created: tuple[Path, ...]
    existing: tuple[Path, ...]


class StorageBootstrapper:
    """Create the Stage Two storage directory tree without deleting content."""

    def __init__(self, storage_root: str | Path) -> None:
        """Initialize the bootstrapper with PATH_DATA_STORAGE."""
        self.storage_root = Path(storage_root).expanduser()
        if not str(self.storage_root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured before bootstrapping storage.")

    def bootstrap(self) -> StorageBootstrapResult:
        """Create all required directories idempotently and return a summary."""
        created: list[Path] = []
        existing: list[Path] = []

        for relative_path in self.required_relative_paths():
            path = self.storage_root / relative_path
            if path.exists():
                existing.append(path)
                continue
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)

        return StorageBootstrapResult(
            root=self.storage_root,
            created=tuple(created),
            existing=tuple(existing),
        )

    @classmethod
    def required_relative_paths(cls) -> tuple[Path, ...]:
        """Return the required Stage Two storage paths relative to PATH_DATA_STORAGE."""
        paths: list[Path] = [
            Path("postgres"),
            Path("pgadmin"),
            Path("parquet") / "normalized",
            Path("parquet") / "features",
            Path("parquet") / "model_ready",
            Path("duckdb") / "sql",
            Path("duckdb") / "exports",
            Path("logs") / "stage-two",
            Path("backups") / "postgres_catalog",
            Path("backups") / "metadata_exports",
            Path("temp_data") / "ingestion",
            Path("temp_data") / "parser_runs",
            Path("temp_data") / "normalization",
            Path("temp_data") / "duckdb",
            Path("schemas") / "normalized",
            Path("schemas") / "features",
            Path("schemas") / "model_ready",
            Path("config"),
        ]

        paths.extend(cls._parquet_paths())
        paths.extend(cls._report_paths())
        return tuple(dict.fromkeys(paths))

    @staticmethod
    def _parquet_paths() -> list[Path]:
        paths: list[Path] = []
        for branch in BRANCHES:
            for role in ROLES:
                paths.append(Path("parquet") / "normalized" / branch / role)
        for feature_group in FEATURE_GROUPS:
            paths.append(Path("parquet") / "features" / feature_group)
        for artifact_type in MODEL_READY_TYPES:
            paths.append(Path("parquet") / "model_ready" / artifact_type)
        return paths

    @staticmethod
    def _report_paths() -> list[Path]:
        paths: list[Path] = []
        for language in ("ru", "en"):
            paths.append(Path("reports") / language / "stage-two")
            for group in REPORT_GROUPS:
                paths.append(Path("reports") / language / "stage-two" / group)
                paths.append(Path("reports") / language / group)
        return paths


def bootstrap_stage_two_storage(path_data_storage: str | Path | None = None) -> StorageBootstrapResult:
    """Bootstrap Stage Two storage using an explicit path or project configuration."""
    if path_data_storage is None:
        from config import PATH_DATA_STORAGE

        path_data_storage = PATH_DATA_STORAGE

    return StorageBootstrapper(path_data_storage).bootstrap()

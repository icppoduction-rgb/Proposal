"""Idempotent filesystem bootstrap for Stage Three generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import (
    PARQUET_FEATURES_RELATIVE,
    PARQUET_MODEL_READY_RELATIVE,
)


BRANCHES: tuple[str, ...] = ("dns", "host", "network", "hybrid")
ROLES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST")

REPORTS_RU_STAGE_THREE_RELATIVE = "reports/ru/stage-three"
REPORTS_EN_STAGE_THREE_RELATIVE = "reports/en/stage-three"
LOGS_STAGE_THREE_RELATIVE = "logs/stage-three"
TEMP_DATA_STAGE_THREE_RELATIVE = "temp_data/stage_three"


@dataclass(frozen=True)
class StageThreeStorageBootstrapResult:
    """Result of a Stage Three storage bootstrap run."""

    root: Path
    created: tuple[Path, ...]
    existing: tuple[Path, ...]
    skipped: tuple[Path, ...]

    @property
    def counters(self) -> dict[str, int]:
        """Return create/exist/skip counts for CLI and report consumers."""
        return {
            "created": len(self.created),
            "existing": len(self.existing),
            "skipped": len(self.skipped),
        }


class StageThreeStorageBootstrapper:
    """Create the Stage Three storage directory tree without touching files."""

    def __init__(self, storage_root: str | Path) -> None:
        """Initialize the bootstrapper with PATH_DATA_STORAGE."""
        self.storage_root = Path(storage_root).expanduser()
        if not str(self.storage_root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured before bootstrapping Stage Three storage.")

    def bootstrap(self) -> StageThreeStorageBootstrapResult:
        """Create all required directories idempotently and return a summary."""
        created: list[Path] = []
        existing: list[Path] = []
        skipped: list[Path] = []

        for relative_path in self.required_relative_paths():
            path = self.storage_root / relative_path
            if path.exists():
                if path.is_dir():
                    existing.append(path)
                else:
                    skipped.append(path)
                continue
            try:
                path.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                skipped.append(path)
                continue
            created.append(path)

        return StageThreeStorageBootstrapResult(
            root=self.storage_root,
            created=tuple(created),
            existing=tuple(existing),
            skipped=tuple(skipped),
        )

    @classmethod
    def required_relative_paths(cls) -> tuple[Path, ...]:
        """Return required Stage Three storage paths relative to PATH_DATA_STORAGE."""
        paths: list[Path] = [
            Path(REPORTS_RU_STAGE_THREE_RELATIVE),
            Path(REPORTS_EN_STAGE_THREE_RELATIVE),
            Path(LOGS_STAGE_THREE_RELATIVE),
            Path(TEMP_DATA_STAGE_THREE_RELATIVE),
            Path(PARQUET_FEATURES_RELATIVE),
            Path(PARQUET_MODEL_READY_RELATIVE),
        ]
        paths.extend(cls._role_aware_paths(Path(PARQUET_FEATURES_RELATIVE)))
        paths.extend(cls._role_aware_paths(Path(PARQUET_MODEL_READY_RELATIVE)))
        return tuple(dict.fromkeys(paths))

    @staticmethod
    def _role_aware_paths(root: Path) -> list[Path]:
        paths: list[Path] = []
        for branch in BRANCHES:
            for role in ROLES:
                paths.append(root / branch / role)
        return paths


def bootstrap_stage_three_storage(
    path_data_storage: str | Path | None = None,
) -> StageThreeStorageBootstrapResult:
    """Bootstrap Stage Three storage using an explicit path or project configuration."""
    if path_data_storage is None:
        from config import PATH_DATA_STORAGE

        path_data_storage = PATH_DATA_STORAGE

    return StageThreeStorageBootstrapper(path_data_storage).bootstrap()

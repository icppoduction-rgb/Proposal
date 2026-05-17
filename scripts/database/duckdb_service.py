import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


class DuckDBServiceError(RuntimeError):
    """Raised when DuckDB Docker Compose configuration is invalid."""


@dataclass(frozen=True)
class DuckDBDockerConfig:
    project_root: Path
    compose_file: Path
    env_file: Path
    data_path: Path
    database: str


def build_duckdb_config(
    *,
    project_root: Path,
    data_path_value: str | None,
    database: str | None,
    compose_file: Path | None = None,
    env_file: Path | None = None,
) -> DuckDBDockerConfig:
    root = project_root.resolve()
    resolved_compose_file = compose_file or root / "databases" / "duckdb" / "docker-compose.yml"
    resolved_env_file = env_file or root / ".env"

    if not resolved_compose_file.is_file():
        raise DuckDBServiceError(f"DuckDB compose file not found: {resolved_compose_file}")
    if not resolved_env_file.is_file():
        raise DuckDBServiceError(f"Environment file not found: {resolved_env_file}")

    data_path = resolve_data_path(data_path_value, root)
    db_name = validate_database_name(database)

    return DuckDBDockerConfig(
        project_root=root,
        compose_file=resolved_compose_file.resolve(),
        env_file=resolved_env_file.resolve(),
        data_path=data_path,
        database=db_name,
    )


def resolve_data_path(value: str | None, project_root: Path) -> Path:
    if value is None or not value.strip():
        raise DuckDBServiceError("DUCKDB_DATA_PATH is not set")

    path = Path(value.strip())
    if not path.is_absolute():
        path = project_root / path

    return path.resolve()


def validate_database_name(value: str | None) -> str:
    if value is None or not value.strip():
        raise DuckDBServiceError("DUCKDB_DATABASE is not set")

    database = value.strip()
    path = Path(database)
    if path.is_absolute() or path.name != database or database in {".", ".."}:
        raise DuckDBServiceError("DUCKDB_DATABASE must be a file name, for example proposal.duckdb")

    return database


def build_compose_command(config: DuckDBDockerConfig, compose_args: Sequence[str]) -> list[str]:
    return [
        *detect_compose_command(),
        "--env-file",
        str(config.env_file),
        "-f",
        str(config.compose_file),
        *compose_args,
    ]


def detect_compose_command() -> list[str]:
    if shutil.which("docker"):
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    raise DuckDBServiceError("Docker Compose is not available: install Docker with Compose plugin")


def compose_environment(config: DuckDBDockerConfig, base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["DUCKDB_DATA_PATH"] = str(config.data_path)
    env["DUCKDB_DATABASE"] = config.database
    return env


def run_duckdb_compose(config: DuckDBDockerConfig, compose_args: Sequence[str]) -> None:
    command = build_compose_command(config, compose_args)
    subprocess.run(
        command,
        cwd=config.project_root,
        env=compose_environment(config),
        check=True,
    )


def start_duckdb(config: DuckDBDockerConfig) -> None:
    config.data_path.mkdir(parents=True, exist_ok=True)
    run_duckdb_compose(config, ["up", "-d"])


def stop_duckdb(config: DuckDBDockerConfig) -> None:
    run_duckdb_compose(config, ["down"])


def restart_duckdb(config: DuckDBDockerConfig) -> None:
    config.data_path.mkdir(parents=True, exist_ok=True)
    run_duckdb_compose(config, ["down"])
    run_duckdb_compose(config, ["up", "-d"])


def show_duckdb_status(config: DuckDBDockerConfig) -> None:
    run_duckdb_compose(config, ["ps"])


def show_duckdb_logs(config: DuckDBDockerConfig) -> None:
    run_duckdb_compose(config, ["logs", "--tail", "100", "duckdb"])

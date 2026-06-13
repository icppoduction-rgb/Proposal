"""Configuration helpers for the Stage Two PostgreSQL catalog."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabaseSettings:
    """Immutable SQLAlchemy database settings loaded from the environment."""

    database_url: str
    echo_sql: bool = False
    pool_pre_ping: bool = True


def load_database_settings(
    database_url: str | None = None,
    *,
    echo_sql: bool | None = None,
    pool_pre_ping: bool | None = None,
) -> DatabaseSettings:
    """Load database settings from explicit overrides or the process environment."""
    _load_project_dotenv()

    resolved_database_url = database_url or os.getenv("DATABASE_URL", "")
    if not resolved_database_url.strip():
        raise ValueError("DATABASE_URL must be configured in the environment or .env file.")

    return DatabaseSettings(
        database_url=resolved_database_url,
        echo_sql=_env_bool("SQLALCHEMY_ECHO_SQL", False) if echo_sql is None else echo_sql,
        pool_pre_ping=_env_bool("SQLALCHEMY_POOL_PRE_PING", True)
        if pool_pre_ping is None
        else pool_pre_ping,
    )


def _load_project_dotenv() -> None:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

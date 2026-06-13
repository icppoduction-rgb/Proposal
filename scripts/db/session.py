"""SQLAlchemy engine, session factory, and transaction scope helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from scripts.db.config import DatabaseSettings, load_database_settings


def get_engine(settings: DatabaseSettings | None = None) -> Engine:
    """Create a SQLAlchemy engine from database settings."""
    resolved_settings = settings or load_database_settings()
    return create_engine(
        resolved_settings.database_url,
        echo=resolved_settings.echo_sql,
        pool_pre_ping=resolved_settings.pool_pre_ping,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured SQLAlchemy session factory."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(
    session_factory: sessionmaker[Session] | None = None,
    *,
    settings: DatabaseSettings | None = None,
) -> Iterator[Session]:
    """Provide a transactional session scope with rollback on exceptions."""
    factory = session_factory or create_session_factory(get_engine(settings))
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

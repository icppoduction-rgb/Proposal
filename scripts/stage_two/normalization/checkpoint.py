"""Catalog checkpoint helpers for long-running normalization jobs."""

from __future__ import annotations

from sqlalchemy.orm import Session


def checkpoint_catalog_session(session: Session) -> None:
    """Persist a durable catalog checkpoint without breaking nested test transactions."""
    if session.in_nested_transaction():
        session.flush()
        return
    session.commit()

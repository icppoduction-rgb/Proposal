"""Base repository abstraction for catalog repositories."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Base class for repositories that operate on an existing Session."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        """Initialize the repository with an externally managed session."""
        self.session = session

    def add(self, entity: ModelT) -> ModelT:
        """Add an entity to the session and flush it without committing."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def get(self, entity_id: int) -> ModelT | None:
        """Return one entity by primary key or None."""
        return self.session.get(self.model, entity_id)

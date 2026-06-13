"""Streaming hash helper for raw dataset files."""

from __future__ import annotations

import hashlib
from pathlib import Path


class FileHashService:
    """Calculate file hashes without loading full files into memory."""

    def __init__(self, chunk_size: int = 1024 * 1024) -> None:
        """Initialize the hasher with a bounded read chunk size."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def sha256(self, path: str | Path) -> str:
        """Return the SHA-256 hex digest for a file."""
        digest = hashlib.sha256()
        with Path(path).open("rb") as file:
            for chunk in iter(lambda: file.read(self.chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()

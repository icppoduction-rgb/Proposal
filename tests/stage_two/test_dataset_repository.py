from __future__ import annotations

import hashlib
import unittest
from typing import Any, cast

from scripts.db.models import Dataset
from scripts.db.repositories.dataset_repository import DatasetRepository


class DatasetRepositorySlugCollisionTest(unittest.TestCase):
    def test_unique_slug_returns_original_when_slug_is_unused(self) -> None:
        repo = DatasetRepository(cast(Any, object()))
        repo.get_by_slug_branch_role = lambda slug, branch, role: None  # type: ignore[method-assign]

        result = repo._unique_slug_for_dataset(
            name="host_train_gpg",
            slug="host-train-gpg",
            branch="host",
            role="TRAIN",
        )

        self.assertEqual(result, "host-train-gpg")

    def test_unique_slug_adds_deterministic_suffix_on_collision(self) -> None:
        existing = Dataset(
            name="host_train_gpg",
            slug="host-train-gpg",
            branch="host",
            role="TRAIN",
        )
        repo = DatasetRepository(cast(Any, object()))
        repo.get_by_slug_branch_role = (  # type: ignore[method-assign]
            lambda slug, branch, role: existing if slug == "host-train-gpg" else None
        )

        result = repo._unique_slug_for_dataset(
            name="host_train_gpg~",
            slug="host-train-gpg",
            branch="host",
            role="TRAIN",
        )

        expected_digest = hashlib.sha1("host_train_gpg~".encode("utf-8")).hexdigest()[:8]
        self.assertEqual(result, f"host-train-gpg-{expected_digest}")

    def test_unique_slug_increments_when_digest_slug_also_exists(self) -> None:
        name = "host_train_gpg~"
        digest_slug = f"host-train-gpg-{hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}"
        existing_by_slug = {
            "host-train-gpg": Dataset(
                name="host_train_gpg",
                slug="host-train-gpg",
                branch="host",
                role="TRAIN",
            ),
            digest_slug: Dataset(
                name="other_dataset",
                slug=digest_slug,
                branch="host",
                role="TRAIN",
            ),
        }
        repo = DatasetRepository(cast(Any, object()))
        repo.get_by_slug_branch_role = (  # type: ignore[method-assign]
            lambda slug, branch, role: existing_by_slug.get(slug)
        )

        result = repo._unique_slug_for_dataset(
            name=name,
            slug="host-train-gpg",
            branch="host",
            role="TRAIN",
        )

        self.assertEqual(result, f"{digest_slug}-2")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from scripts.stage_two.catalog_exclusions import is_excluded_raw_bucket


class CatalogExclusionTest(unittest.TestCase):
    def test_excludes_host_validation_wls_day_raw_bucket(self) -> None:
        self.assertTrue(
            is_excluded_raw_bucket(
                branch="host",
                role="VALIDATION",
                source_format="wls_day",
                relative_path="host\\VALIDATION\\wls_day\\wls_day-01",
            )
        )

    def test_excludes_host_test_duplicate_raw_buckets(self) -> None:
        for source_format in ("netflow_day", "wls_day"):
            with self.subTest(source_format=source_format):
                self.assertTrue(
                    is_excluded_raw_bucket(
                        branch="host",
                        role="TEST",
                        source_format=source_format,
                        relative_path=f"host\\TEST\\{source_format}\\{source_format}-01",
                    )
                )

    def test_does_not_exclude_registered_chunks(self) -> None:
        self.assertFalse(
            is_excluded_raw_bucket(
                branch="host",
                role="VALIDATION",
                source_format="wls_day",
                relative_path="chunked\\host\\VALIDATION\\wls_day\\wls_day-01.parts\\wls_day-01.part-000001",
            )
        )

    def test_does_not_exclude_other_roles_or_formats(self) -> None:
        self.assertFalse(
            is_excluded_raw_bucket(
                branch="host",
                role="TRAIN",
                source_format="wls_day",
                relative_path="host\\TRAIN\\wls_day\\wls_day-01",
            )
        )
        self.assertFalse(
            is_excluded_raw_bucket(
                branch="host",
                role="VALIDATION",
                source_format="netflow_day",
                relative_path="host\\VALIDATION\\netflow_day\\netflow_day-01",
            )
        )


if __name__ == "__main__":
    unittest.main()

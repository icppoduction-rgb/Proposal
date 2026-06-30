from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage_two.labels import LabelResolver, label_hints_allowed
from scripts.stage_two.parsers.base import ParserContext


class LabelResolverTest(unittest.TestCase):
    def test_test_role_ignores_implicit_embedded_ids_and_filename_hints(self) -> None:
        resolver = LabelResolver(config_path=None, enable_filename_heuristics=True)
        context = _context(
            role="TEST",
            source_file_path="/datasets/dns/test/malicious_attack_sample.csv",
        )

        fields = resolver.resolve(
            {
                "label": "1",
                "attack_cat": "malware",
                "rule": {"alert": "alert"},
                "query_domain": "example.org",
            },
            context,
        )

        self.assertFalse(label_hints_allowed(context))
        self.assertEqual(fields["label_binary"], None)
        self.assertEqual(fields["label_source"], "none")
        self.assertEqual(fields["label_status"], "unlabeled")

    def test_train_embedded_label_resolves_as_explicit_label(self) -> None:
        resolver = LabelResolver(config_path=None, enable_filename_heuristics=False)

        fields = resolver.resolve({"label": "malicious"}, _context(role="TRAIN"))

        self.assertEqual(fields["label_binary"], 1)
        self.assertEqual(fields["label_source"], "embedded_column")
        self.assertEqual(fields["label_status"], "explicit_label")

    def test_test_role_allows_explicit_label_mapping_rule(self) -> None:
        resolver = LabelResolver(
            config_path=None,
            enable_filename_heuristics=True,
            config_rules=[
                {
                    "rule_uid": "test-explicit-external-label",
                    "branch": "dns",
                    "role": "TEST",
                    "source_format": "csv",
                    "source_field": "verified_label",
                    "source_value_pattern": "^malicious$",
                    "label_binary": 1,
                    "label_family": "malware",
                    "label_subtype": "external",
                    "label_source": "external_label_file",
                    "label_status": "explicit_label",
                    "label_confidence": 1.0,
                    "priority": 1,
                }
            ],
        )

        fields = resolver.resolve(
            {"label": "0", "verified_label": "malicious"},
            _context(role="TEST", source_file_path="/datasets/dns/test/benign_name.csv"),
        )

        self.assertEqual(fields["label_binary"], 1)
        self.assertEqual(fields["label_family"], "malware")
        self.assertEqual(fields["label_source"], "external_label_file")
        self.assertEqual(fields["label_status"], "explicit_label")
        self.assertEqual(fields["label_mapping_rule_id"], "test-explicit-external-label")

    def test_absent_label_is_unlabeled_not_benign(self) -> None:
        resolver = LabelResolver(config_path=None, enable_filename_heuristics=False)

        fields = resolver.resolve({"query_domain": "unknown.example"}, _context(role="TRAIN"))

        self.assertEqual(fields["label_binary"], None)
        self.assertEqual(fields["label_family"], None)
        self.assertEqual(fields["label_source"], "none")
        self.assertEqual(fields["label_status"], "unlabeled")
        self.assertEqual(fields["label_confidence"], None)

    def test_rules_are_loaded_once_per_context(self) -> None:
        resolver = LabelResolver(config_path=Path("label-rules.json"), enable_filename_heuristics=False)
        context = _context(role="TRAIN")

        with patch("scripts.stage_two.labels.resolver.load_config_rules", return_value=[]) as load_rules:
            resolver.resolve({"query_domain": "one.example"}, context)
            resolver.resolve({"query_domain": "two.example"}, context)

        self.assertEqual(load_rules.call_count, 1)


def _context(
    *,
    role: str,
    source_file_path: str = "/datasets/dns/train/sample.csv",
) -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="dns-dataset",
        dataset_role=role,
        branch="dns",
        source_format="csv",
        source_file_path=source_file_path,
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()

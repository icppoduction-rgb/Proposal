from __future__ import annotations

import unittest

from scripts.stage_two.execution.format_policy import FormatRuntimeFacts, resolve_format_policy
from scripts.stage_two.normalization.options import NormalizationOptions


class FormatPolicyTest(unittest.TestCase):
    def test_txt_uses_syscall_trace_policy(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(),
            FormatRuntimeFacts(
                branch="host",
                role="TEST",
                source_format="txt",
                file_count=100,
                total_size_bytes=2 * 1024 * 1024 * 1024,
            ),
        )

        self.assertEqual(decision.policy_name, "syscall_trace")
        self.assertEqual(decision.options.workers, 6)
        self.assertEqual(decision.options.batch_size, 100_000)
        self.assertEqual(decision.options.max_output_part_rows, 200_000)
        self.assertEqual(decision.options.engine, "cpu")
        self.assertTrue(any("syscall trace" in warning for warning in decision.warnings))

    def test_csv_uses_csv_netflow_policy(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(),
            FormatRuntimeFacts(branch="dns", role="TRAIN", source_format="csv", file_count=10, total_size_bytes=100),
        )

        self.assertEqual(decision.policy_name, "csv_netflow")
        self.assertEqual(decision.options.workers, 10)
        self.assertEqual(decision.options.batch_size, 200_000)
        self.assertEqual(decision.options.max_output_part_rows, 500_000)

    def test_json_uses_moderate_workers(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(),
            FormatRuntimeFacts(
                branch="host",
                role="TRAIN",
                source_format="json",
                file_count=2,
                total_size_bytes=600 * 1024 * 1024,
            ),
        )

        self.assertEqual(decision.policy_name, "json")
        self.assertEqual(decision.options.workers, 8)
        self.assertEqual(decision.options.batch_size, 150_000)
        self.assertTrue(any("large JSON" in warning for warning in decision.warnings))

    def test_wls_day_uses_eventlog_policy(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(),
            FormatRuntimeFacts(
                branch="host",
                role="VALIDATION",
                source_format="wls_day",
                file_count=3,
                total_size_bytes=45 * 1024 * 1024 * 1024,
            ),
        )

        self.assertEqual(decision.policy_name, "wls_eventlog")
        self.assertEqual(decision.options.workers, 8)
        self.assertEqual(decision.options.batch_size, 100_000)
        self.assertEqual(decision.options.max_output_part_rows, 100_000)
        self.assertTrue(any("150 MB" in warning for warning in decision.warnings))

    def test_bson_caps_workers_and_part_rows(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(workers=14, batch_size=300_000, max_output_part_rows=750_000),
            FormatRuntimeFacts(branch="host", role="TEST", source_format="bson", file_count=1, total_size_bytes=100),
        )

        self.assertEqual(decision.policy_name, "bson")
        self.assertEqual(decision.options.workers, 3)
        self.assertEqual(decision.options.batch_size, 75_000)
        self.assertEqual(decision.options.max_output_part_rows, 200_000)
        self.assertTrue(any("BSON" in warning for warning in decision.warnings))

    def test_pcap_caps_workers_and_defaults_packet_summary(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(workers=14, packet_mode="dns-only"),
            FormatRuntimeFacts(branch="dns", role="TRAIN", source_format="pcap", file_count=3, total_size_bytes=100),
        )

        self.assertEqual(decision.policy_name, "packet_capture")
        self.assertEqual(decision.options.workers, 3)
        self.assertEqual(decision.options.packet_batch_size, 50_000)
        self.assertEqual(decision.options.max_output_part_rows, 100_000)
        self.assertEqual(decision.options.packet_mode, "packet-summary")

    def test_explicit_cli_overrides_are_not_replaced_by_policy(self) -> None:
        decision = resolve_format_policy(
            NormalizationOptions(
                workers=6,
                batch_size=123_000,
                max_output_part_rows=321_000,
                packet_mode="dns-only",
                engine="auto",
            ),
            FormatRuntimeFacts(branch="dns", role="TRAIN", source_format="pcap", file_count=3, total_size_bytes=100),
            explicit_overrides={"workers", "batch_size", "max_output_part_rows", "packet_mode", "engine"},
        )

        self.assertEqual(decision.options.workers, 6)
        self.assertEqual(decision.options.batch_size, 123_000)
        self.assertEqual(decision.options.max_output_part_rows, 321_000)
        self.assertEqual(decision.options.packet_mode, "dns-only")
        self.assertEqual(decision.options.engine, "auto")
        self.assertTrue(any("reserved" in warning for warning in decision.warnings))


if __name__ == "__main__":
    unittest.main()

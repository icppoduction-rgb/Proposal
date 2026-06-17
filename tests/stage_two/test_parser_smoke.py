from __future__ import annotations

import unittest

from scripts.stage_two.parser_smoke import EXPECTED_PARSER_SMOKE_GROUPS, run_parser_smokes


class ParserSmokeRunnerTest(unittest.TestCase):
    def test_direct_parser_smokes_cover_every_parser_group(self) -> None:
        summaries = run_parser_smokes()

        groups = {summary.group for summary in summaries}
        self.assertEqual(groups, set(EXPECTED_PARSER_SMOKE_GROUPS))
        for summary in summaries:
            self.assertGreater(summary.rows_read, 0, summary.group)
            self.assertGreater(summary.rows_parsed, 0, summary.group)
            self.assertIn(summary.parser_run_status, {"SUCCESS", "PARTIAL_SUCCESS"}, summary.group)
            self.assertIn(summary.file_status, {"PARSED", "PARTIALLY_PARSED"}, summary.group)


if __name__ == "__main__":
    unittest.main()

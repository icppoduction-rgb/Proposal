from __future__ import annotations

import unittest

from scripts.stage_two.parser_input_smoke import EXPECTED_INPUT_SMOKE_CASES, run_parser_input_smokes


class ParserInputSmokeRunnerTest(unittest.TestCase):
    def test_encoded_compressed_input_smokes_cover_expected_cases(self) -> None:
        summaries = run_parser_input_smokes()

        cases = {summary.case for summary in summaries}
        self.assertEqual(cases, set(EXPECTED_INPUT_SMOKE_CASES))
        for summary in summaries:
            self.assertTrue(summary.raw_hash_unchanged, summary.case)
            self.assertIn(summary.status, {"PARSED", "WARNING"}, summary.case)

        negative_cases = {summary.case for summary in summaries if summary.status == "WARNING"}
        self.assertEqual(negative_cases, {"invalid_base64", "oversized_base64"})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from scripts.simulate_safari_chat_docx_v100 import NO_NOVELTY_EXTENSION, PRIMARY_M, run


class SafariChatDocxFullSaturationV100Tests(unittest.TestCase):
    """Run the exact Safari M + M+100 contract before expensive historical CI."""

    def test_exact_release_saturation_reaches_no_novelty(self):
        result = run(PRIMARY_M, NO_NOVELTY_EXTENSION)
        self.assertEqual(result.get("status"), "PASS")
        self.assertEqual(result.get("one_to_M_cases"), PRIMARY_M)
        self.assertEqual(result.get("M_plus_100_cases"), NO_NOVELTY_EXTENSION)
        self.assertTrue(result.get("no_novelty_after_M"))
        self.assertEqual(result.get("novel_categories_after_M"), [])


if __name__ == "__main__":
    unittest.main()

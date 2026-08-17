from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.simulate_safari_chat_docx_v100 import FAMILIES, _scenario


class SafariChatDocxSmokeV100Tests(unittest.TestCase):
    """Fail-fast coverage for every Safari delivery mutation family.

    The heavy 100 + M+100 saturation remains authoritative for no-novelty;
    this smoke layer makes a family-level contract regression observable in the
    normal unit matrix before the expensive historical simulations start.
    """

    def test_every_primary_family_matches_expected_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for ordinal, (family, _expected_pass, _expected_category) in enumerate(FAMILIES, start=1):
                with self.subTest(ordinal=ordinal, family=family):
                    result = _scenario(root, ordinal, extension=False)
                    self.assertEqual(result["family"], family)


if __name__ == "__main__":
    unittest.main()

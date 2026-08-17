from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.simulate_safari_chat_docx_v100 import FAMILIES, _scenario


class SafariChatDocxNoNoveltySmokeV100Tests(unittest.TestCase):
    """Fail fast on the M+100 browser-context extension before heavy CI."""

    def test_extension_cycle_introduces_no_new_delivery_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = [_scenario(root, ordinal, extension=False) for ordinal in range(1, len(FAMILIES) + 1)]
            learned = set().union(*(set(item["categories"]) for item in primary))

            start = 101
            extension = [
                _scenario(root, ordinal, extension=True)
                for ordinal in range(start, start + len(FAMILIES))
            ]
            extension_categories = set().union(*(set(item["categories"]) for item in extension))
            novel = sorted(extension_categories - learned)
            self.assertEqual(novel, [], f"M+100 smoke produced novel delivery classes: {novel}")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.simulate_safari_chat_docx_v100 import main


class SafariChatDocxCliV100Tests(unittest.TestCase):
    """Exercise the exact CLI path used by the heavy GitHub Actions step."""

    def test_cli_100_plus_100_writes_pass_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "safari-chat-docx-v100.json"
            rc = main([
                "--cases", "100",
                "--no-novelty", "100",
                "--json-out", str(output),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(output.is_file())
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("status"), "PASS")
            self.assertTrue(receipt.get("no_novelty_after_M"))
            self.assertEqual(receipt.get("total_cases"), 200)


if __name__ == "__main__":
    unittest.main()

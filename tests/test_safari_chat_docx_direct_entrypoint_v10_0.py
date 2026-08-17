from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_safari_chat_docx_v100.py"


class SafariChatDocxDirectEntrypointV100Tests(unittest.TestCase):
    """The release simulation must work when GitHub Actions executes the file directly."""

    def test_direct_script_execution_bootstraps_repository_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "safari-chat-docx-v100.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases", "100",
                    "--no-novelty", "100",
                    "--json-out", str(output),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout[-5000:])
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("status"), "PASS")
            self.assertTrue(receipt.get("no_novelty_after_M"))
            self.assertEqual(receipt.get("total_cases"), 200)


if __name__ == "__main__":
    unittest.main()

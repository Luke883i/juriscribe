from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_universal_artifacts_v100.py"


class UniversalArtifactDirectEntrypointV100Tests(unittest.TestCase):
    """The universal v0.10 saturation must work when CI executes the file directly."""

    def test_direct_script_execution_bootstraps_repository_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "universal-artifact-v100.json"
            workspace = Path(tmp) / "workspace"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases", "100",
                    "--no-novelty", "100",
                    "--out-root", str(workspace),
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

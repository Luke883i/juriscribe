import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from juriscribe.dashboard_persistence import verify_persistent_dashboard
from juriscribe.pipeline_v9 import persist_session
from juriscribe.session import Workspace


class PersistentDashboardV98Tests(unittest.TestCase):
    def _state(self, root: str):
        ws = Workspace(root, "SES-dashboard")
        state = ws.initialize(
            "Mandato persistente distintivo",
            runtime={"workspace_base": str(ws.base.resolve()), "capabilities": {}},
            admission={},
            persist=False,
        )
        return ws, state

    def test_dashboard_persists_and_advances_generation_after_real_state_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws, state = self._state(tmp)
            path = persist_session(ws, state, trigger="initialize")
            first = ws.load()
            first_bytes = path.read_bytes()
            self.assertEqual(first.dashboard_persistence["generation"], 1)
            self.assertEqual(first.dashboard_persistence["last_trigger"], "initialize")
            self.assertTrue(verify_persistent_dashboard(first, path)[0])
            self.assertIn("Mandato persistente distintivo", path.read_text(encoding="utf-8"))

            state = ws.load()
            state.epistemic_units = [{
                "id": "U-PERSIST",
                "kind": "RULE",
                "text": "Regola epistemica realmente persistita in dashboard",
                "material": True,
                "status": "VERIFIED",
            }]
            path2 = persist_session(ws, state, trigger="semantic-mining")
            second = ws.load()
            second_bytes = path2.read_bytes()
            self.assertEqual(path, path2)
            self.assertEqual(second.dashboard_persistence["generation"], 2)
            self.assertEqual(second.dashboard_persistence["last_trigger"], "semantic-mining")
            self.assertNotEqual(first_bytes, second_bytes)
            self.assertIn("Regola epistemica realmente persistita in dashboard", second_bytes.decode("utf-8"))
            ok, errors, report = verify_persistent_dashboard(second, path2)
            self.assertTrue(ok, errors)
            self.assertEqual(report["missing_public_leaf_count"], 0)

            ledger = ws.ledger_dir / "dashboard-generations.jsonl"
            rows = ledger.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(rows), 2)

    def test_failed_render_preserves_previous_dashboard_and_persisted_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws, state = self._state(tmp)
            path = persist_session(ws, state, trigger="initialize")
            before = path.read_bytes()
            before_state = ws.load()
            self.assertEqual(before_state.dashboard_persistence["generation"], 1)

            state = ws.load()
            state.epistemic_units = [{"id": "U-FAIL", "kind": "RULE", "text": "Mutazione non committabile", "material": True}]
            with patch("juriscribe.dashboard_persistence.render_session_dashboard", side_effect=RuntimeError("render failure")):
                with self.assertRaises(RuntimeError):
                    persist_session(ws, state, trigger="semantic-mining")

            self.assertEqual(path.read_bytes(), before)
            reloaded = ws.load()
            self.assertEqual(reloaded.dashboard_persistence["generation"], 1)
            self.assertNotIn("Mutazione non committabile", path.read_text(encoding="utf-8"))
            self.assertTrue(verify_persistent_dashboard(reloaded, path)[0])

    def test_explicit_dashboard_refresh_is_a_new_persistent_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws, state = self._state(tmp)
            path = persist_session(ws, state, trigger="initialize")
            first_digest = ws.load().dashboard_persistence["html_sha256"]
            state = ws.load()
            persist_session(ws, state, trigger="dashboard")
            reloaded = ws.load()
            self.assertEqual(reloaded.dashboard_persistence["generation"], 2)
            self.assertEqual(reloaded.dashboard_persistence["last_trigger"], "dashboard")
            self.assertEqual(reloaded.dashboard_persistence["html_sha256"], first_digest)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from juriscribe.convergence import ConvergenceMonitor
from juriscribe.dashboard import render_session_dashboard
from juriscribe.epistemic import EpistemicUnit, Relation, contradiction_pairs
from juriscribe.pipeline import initialize


class KernelTests(unittest.TestCase):
    def test_semantic_saturation_requires_1000_clean_probes(self):
        monitor = ConvergenceMonitor()
        for _ in range(999):
            self.assertFalse(monitor.semantic_probe(False, False))
        self.assertTrue(monitor.semantic_probe(False, False))
        self.assertFalse(monitor.semantic_probe(True, False))

    def test_epistemic_unit_validation(self):
        unit = EpistemicUnit("EU-1", "CLAIM", "Una proposizione", "SRC-1")
        self.assertEqual(unit.record()["kind"], "CLAIM")

    def test_contradiction_deduplicated(self):
        relations = [
            Relation("A", "CONTRADICTS", "B").record(),
            Relation("B", "CONTRADICTS", "A").record(),
        ]
        self.assertEqual(contradiction_pairs(relations), [("A", "B")])

    def test_dashboard_is_session_specific(self):
        state = {
            "session_id": "SES-test",
            "phase": "STRATEGY",
            "request": {"raw": "Scrivi il capitolo 3", "summary": "Scrivi il capitolo 3", "atoms": [{"text": "capitolo 3"}]},
            "sources": [{"summary": "Capitolo 1"}, {"summary": "Capitolo 2"}],
            "epistemic_units": [], "contradictions": [], "dod": [], "editorial_actions": [], "artifacts": [],
            "strategy": {"summary": "Collegare i capitoli precedenti", "methods": ["analisi relazionale"]},
            "metrics": {"semantic_no_novelty_streak": 12, "strategy_no_improvement_streak": 4, "simulations_run": 50, "simulation_failures": 0}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = render_session_dashboard(state, Path(tmp) / "dash.html")
            text = path.read_text(encoding="utf-8")
            self.assertIn("Scrivi il capitolo 3", text)
            self.assertIn("Capitolo 1", text)
            self.assertNotIn("principi generali di juriscribe", text.lower())

    def test_initialize_materializes_dashboard_and_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = initialize("Riorganizza il capitolo", root=tmp, session_id="SES-x")
            self.assertTrue((base / "state.json").exists())
            self.assertTrue((base / "artifacts" / "session-dashboard.html").exists())
            state = json.loads((base / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["request"]["raw"], "Riorganizza il capitolo")


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from juriscribe.convergence import ConvergenceMonitor, completion_gate
from juriscribe.mining import deep_mine, mine_style, compare_style
from juriscribe.orchestrator import mine_and_prepare, apply_setup, freeze_dods
from juriscribe.pipeline import initialize
from juriscribe.session import Workspace
from juriscribe.setup import propose_setup, accept_setup, parameter_dods
from juriscribe.sources import SourceRecord, ClaimRecord, validate_claim, assess_dominance

SAMPLE = """CAPITOLO I - Legalità e tecnica\n\nAnzitutto, il problema non consiste nel contrapporre decisione umana e tecnica. Il punto è stabilire quali condizioni rendano controllabile l'uso della tecnica nell'esercizio del potere. Tuttavia, l'opacità non coincide sempre con illegittimità; essa diviene giuridicamente rilevante quando impedisce la ricostruzione dei criteri decisionali.\n\nNe consegue che la motivazione non può ridursi alla mera esposizione dell'esito. Essa deve rendere intelligibile il percorso, salvo i limiti imposti da segreti tutelati e da esigenze proporzionate. Pertanto, la conoscibilità funzionale costituisce una condizione del controllo.\n"""

class RuntimeV2Tests(unittest.TestCase):
    def test_deep_mining_extracts_style(self):
        result = deep_mine(SAMPLE, source_id="SRC-1", chapter="I")
        self.assertGreater(result["surface"]["word_count"], 40)
        self.assertEqual(result["style"]["register"], "saggistico-argomentativo")
        self.assertIn("tuttavia", result["style"]["dominant_connectors"])

    def test_setup_is_minimal_and_recommended(self):
        proposal = propose_setup(deep_mine(SAMPLE, source_id="SRC-1"), {"raw": "Scrivi il capitolo II"})
        self.assertEqual(proposal["simple_options"], ["ACCETTA CONSIGLIATI", "MODIFICA"])
        self.assertEqual(len(proposal["parameters"]), 4)

    def test_user_parameters_become_blocking_dods(self):
        proposal = propose_setup(deep_mine(SAMPLE, source_id="SRC-1"), {"raw":"Scrivi il capitolo II"})
        accepted = accept_setup(proposal, {"length_words": [1800, 2200]})
        dods = parameter_dods(accepted)
        self.assertEqual(len(dods), 4)
        self.assertTrue(all(d["blocking"] for d in dods))
        self.assertEqual([d for d in dods if d["parameter"] == "length_words"][0]["expected"], [1800, 2200])

    def test_reflection_requires_100_clean_iterations(self):
        monitor = ConvergenceMonitor()
        for _ in range(99): self.assertFalse(monitor.reflection_probe(False))
        self.assertTrue(monitor.reflection_probe(False))
        self.assertFalse(monitor.reflection_probe(True))

    def test_completion_requires_10000_no_novelty_and_all_dod_done(self):
        dods = [{"id":"D1","status":"DONE","blocking":True}]
        self.assertFalse(completion_gate(dods, {"dod_no_novelty_streak":9999}, [])["eligible"])
        self.assertTrue(completion_gate(dods, {"dod_no_novelty_streak":10000}, [])["eligible"])

    def test_open_contradiction_blocks_completion(self):
        result = completion_gate([{"id":"D1","status":"DONE","blocking":True}], {"dod_no_novelty_streak":10000}, [{"id":"C1","status":"OPEN","blocking":True}])
        self.assertFalse(result["eligible"])

    def test_strong_inference_needs_premises_bridge_falsifier(self):
        source = SourceRecord("S1","Norma","https://example.test","primary_law",direct_read=True).record()
        premise = ClaimRecord("C1","Premessa","direct","scope",support_source_ids=("S1",),status="SUPPORTED").record()
        inference = ClaimRecord("C2","Inferenza","strong_inference","scope",premise_claim_ids=("C1",),inference_bridge="Se C1, allora plausibilmente C2 nel perimetro dichiarato",falsifier="Una fonte primaria contraria",status="INFERRED").record()
        ok, errors = validate_claim(inference,[source],[premise,inference]); self.assertTrue(ok, errors)
        broken = dict(inference); broken["falsifier"] = ""; ok, _ = validate_claim(broken,[source],[premise,broken]); self.assertFalse(ok)

    def test_dominance_never_from_single_source(self):
        source = SourceRecord("S1","Commento","https://example.test","leading_treatise",court_or_author="A",direct_read=True).record()
        self.assertEqual(assess_dominance("tesi", [source])["status"], "DOMINANCE_NOT_ESTABLISHED")

    def test_dominance_requires_independent_verified_authorities(self):
        sources = [
            SourceRecord("S1","A","u1","leading_treatise",court_or_author="A",direct_read=True).record(),
            SourceRecord("S2","B","u2","peer_reviewed_doctrine",court_or_author="B",direct_read=True).record(),
            SourceRecord("S3","C","u3","supreme_court",court_or_author="Court",direct_read=True).record(),
        ]
        self.assertEqual(assess_dominance("tesi", sources)["status"], "SUPPORTED_DOMINANT")

    def test_style_compare_is_auditable(self):
        comparison = compare_style(mine_style(SAMPLE).record(), SAMPLE)
        self.assertEqual(comparison["mean_relative_deviation"], 0.0)
        self.assertTrue(comparison["register_match"])

    def test_orchestrator_blocks_generation_until_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES"); state = ws.initialize("Scrivi il capitolo II")
            mine_and_prepare(state, SAMPLE, source_id="SRC1", chapter="I"); self.assertEqual(state.phase, "USER_SETUP_REQUIRED")
            apply_setup(state); self.assertEqual(state.phase, "DOD_DEFINITION")
            freeze_dods(state, [{"id":"DOD-CONTENT","kind":"CONTENT","status":"OPEN","blocking":True}]); self.assertEqual(state.phase, "DOD_FROZEN")

    def test_initialize_accepts_host_capability_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = initialize("Scrivi", root=tmp, session_id="SES", host_capabilities={"WEB_RESEARCH":"AVAILABLE","DOCX_WRITE":"AVAILABLE"})
            state = json.loads((base / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["runtime"]["capabilities"]["WEB_RESEARCH"], "AVAILABLE")
            self.assertEqual(state["runtime"]["capabilities"]["DOCX_WRITE"], "AVAILABLE")

if __name__ == "__main__": unittest.main()

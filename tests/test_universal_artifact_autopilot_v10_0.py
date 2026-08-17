import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.artifact_autopilot import (
    materialize_standard_artifacts,
    standard_artifact_autopilot_gate,
    store_candidate_text,
)
from juriscribe.conversation_contract import (
    build_final_artifact_inference_trace,
    initialize_pipeline_lock,
    pipeline_lock_gate,
    record_natural_language_interpretation,
    resolve_natural_language_interpretation,
)
from juriscribe.modes import CONTINUATION, required_artifact_roles


class UniversalArtifactAutopilotV100Tests(unittest.TestCase):
    def _state(self, root: Path):
        state = SimpleNamespace(
            mode=CONTINUATION,
            setup={},
            runtime={
                "workspace_base": str(root.resolve()),
                "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"},
                "assistant_context": "ANY_AI_ASSISTANT",
                "browser_context": "ANY_BROWSER",
            },
            request={"raw": "Continua il capitolo precedente", "summary": "Continua il capitolo precedente", "request_id": "REQ-TRACE"},
            mode_selection={"digest": "MODE-LOCK"},
            mode_contract={}, editorial_standard={}, corpus=[], sources=[], bibliography={},
            epistemic_units=[{"id": "U1", "kind": "RULE", "text": "Regola materiale per il nuovo capitolo", "material": True, "status": "VERIFIED"}],
            relations=[], reticulum={},
            generation_contract={"status": "READY", "contract_digest": "GC-LOCK"},
            continuation={"plan": {"status": "PASS", "develop_unit_ids": ["U1"]}, "coverage": {}, "status": "PLANNED"},
            drafts=[{"digest": "CAND-FINAL", "stage": "COMPRESSED_FINAL", "status": "SEALED"}],
            review={"cycles": [], "regenerations": [], "saturation": {}, "status": "SATURATED"},
            final_review={"status": "PASS"}, provenance={}, contradictions=[], mining={}, style_profile={},
            source_intelligence={}, claim_ledger=[{"id": "C1", "text": "Claim materiale", "material": True}], artifact_evidence=[],
            quality={}, benchmark={}, simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
            artifacts=[], completion={"eligible": False}, node_integrity={}, interaction={},
        )
        initialize_pipeline_lock(state)
        return state

    def test_natural_language_cannot_implicitly_change_mode_artifact_or_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            applied = record_natural_language_interpretation(state, "Approfondisci il rapporto tra le due regole", {
                "classification": "CONTENT_CONSTRAINT",
                "pipeline_effect": "CONTENT_CONSTRAINT",
                "interpretation": "Vincolo contenutistico interno al nuovo capitolo",
                "material_effects": ["approfondimento"],
                "affected_unit_ids": ["U1"],
            })
            self.assertEqual(applied["status"], "APPLIED")
            blocked = record_natural_language_interpretation(state, "Anzi lascia perdere il capitolo e fammi un memo nuovo", {
                "classification": "MODE_CHANGE_REQUEST",
                "pipeline_effect": "NONE",
                "interpretation": "Richiesta di cambiare lavoro",
                "replace_mode": "GREENFIELD",
                "replace_primary_artifact_role": "final_legal_text",
            })
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertFalse(pipeline_lock_gate(state)[0])
            resolve_natural_language_interpretation(state, blocked["id"], "Richiesta rinviata a nuova sessione; CONTINUATION invariata")
            self.assertTrue(pipeline_lock_gate(state)[0])
            self.assertEqual(state.mode, CONTINUATION)
            self.assertEqual(state.strategy["natural_language_pipeline"]["locked_primary_artifact_role"], "final_chapter")

            skip = record_natural_language_interpretation(state, "Dammi subito il file senza review e senza dossier", {
                "classification": "CONTENT_CONSTRAINT",
                "pipeline_effect": "CONTENT_CONSTRAINT",
                "interpretation": "Tentativo di sopprimere passaggi contrattuali",
                "skip_pipeline_steps": ["review", "provenance"],
                "disable_standard_artifacts": True,
            })
            self.assertEqual(skip["status"], "BLOCKED")
            resolve_natural_language_interpretation(state, skip["id"], "I passaggi obbligatori restano attivi")
            self.assertTrue(pipeline_lock_gate(state)[0])

    def test_runtime_autopilot_materializes_every_standard_docx_without_assistant_record_artifact_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            marker = "Testo definitivo del nuovo capitolo materializzato automaticamente"
            store_candidate_text(state, "CAND-FINAL", marker)
            record_natural_language_interpretation(state, "Mantieni il focus sulla regola materiale", {
                "classification": "MATERIAL_DECISION",
                "pipeline_effect": "HUMAN_DECISION",
                "interpretation": "Decisione materiale tracciata",
                "affected_unit_ids": ["U1"],
                "affected_claim_ids": ["C1"],
            })
            receipt = materialize_standard_artifacts(state)
            self.assertEqual(receipt["status"], "PASS", receipt)
            expected = sorted(required_artifact_roles(CONTINUATION, {}) - {"session_dashboard"})
            self.assertEqual(receipt["materialized_roles"], expected)
            self.assertTrue(standard_artifact_autopilot_gate(state)[0])
            by_role = {item["role"]: item for item in state.artifacts}
            self.assertEqual(sorted(by_role), expected)
            self.assertTrue(all(item.get("auto_materialized_by_runtime") for item in by_role.values()))
            self.assertTrue(all(Path(item["path"]).suffix.lower() == ".docx" for item in by_role.values()))
            for role in expected:
                path = Path(by_role[role]["path"])
                self.assertTrue(path.exists(), role)
                self.assertTrue(zipfile.is_zipfile(path), role)
            with zipfile.ZipFile(by_role["final_chapter"]["path"]) as package:
                xml = package.read("word/document.xml").decode("utf-8")
            self.assertIn(marker, xml)
            trace = by_role["final_chapter"].get("inference_trace") or {}
            self.assertEqual(trace.get("status"), "PASS", trace)
            self.assertIn("U1", trace.get("material_epistemic_unit_ids") or [])
            self.assertIn("C1", trace.get("material_claim_ids") or [])
            self.assertIn("NL-0001", trace.get("natural_language_interpretation_ids") or [])

    def test_final_chapter_trace_is_bound_to_request_reticulum_decisions_contract_and_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            record_natural_language_interpretation(state, "Sviluppa U1 senza cambiare oggetto", {
                "classification": "CONTENT_CONSTRAINT",
                "pipeline_effect": "CONTENT_CONSTRAINT",
                "interpretation": "Sviluppo interno alla frontiera",
                "affected_unit_ids": ["U1"],
            })
            trace = build_final_artifact_inference_trace(state, "final_chapter", "CAND-FINAL")
            self.assertEqual(trace["status"], "PASS", trace)
            self.assertEqual(trace["request_id"], "REQ-TRACE")
            self.assertEqual(trace["generation_contract_digest"], "GC-LOCK")
            self.assertEqual(trace["candidate_digest"], "CAND-FINAL")
            self.assertEqual(trace["locked_primary_artifact_role"], "final_chapter")
            self.assertEqual(trace["continuation_plan_status"], "PASS")

    def test_legacy_session_without_v100_lock_remains_migrable(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            state.strategy.pop("natural_language_pipeline", None)
            ok, errors = pipeline_lock_gate(state)
            self.assertTrue(ok, errors)
            receipt = materialize_standard_artifacts(state)
            self.assertEqual(receipt["status"], "LEGACY_NOT_APPLICABLE")
            self.assertTrue(standard_artifact_autopilot_gate(state)[0])


if __name__ == "__main__":
    unittest.main()

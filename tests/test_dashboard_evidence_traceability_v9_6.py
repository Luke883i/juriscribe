import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from juriscribe import dashboard
from juriscribe.chat_delivery import dashboard_attachment_isolation_report
from juriscribe.dashboard_v9 import dashboard_state_digest
from juriscribe.editorial_artifacts import build_dashboard_inference_view
from juriscribe.evidence_traceability import (
    build_dashboard_evidence_coverage,
    build_evidence_traceability,
    build_user_artifact_index,
    evidence_traceability_gate,
)


class DashboardEvidenceTraceabilityV96Tests(unittest.TestCase):
    def _state(self):
        workspace = "/tmp/juriscribe-v96/SES-test"
        roles = ["final_legal_text", "evidence_dossier", "source_register", "inference_register", "transformation_ledger"]
        artifacts = [
            {"id": role, "role": role, "path": f"{workspace}/artifacts/{role}.docx", "readback": "PASS", "required": True, "delivery_class": "ATTACH"}
            for role in roles
        ] + [{"id": "integrity", "role": "session_integrity", "path": f"{workspace}/session.integrity.json", "readback": "PASS", "required": False, "delivery_class": "INTERNAL"}]
        return SimpleNamespace(
            request={"raw": "Analizza la proporzionalita", "summary": "Analisi completa della proporzionalita"},
            mode="GREENFIELD", mode_selection={}, mode_contract={},
            editorial_standard={"document_type": "LEGAL_MONOGRAPH", "audience": "giuristi", "mode_adjustments": ["esplicitare i limiti"], "rules": {"stable_terminology": True}},
            corpus=[], sources=[{"id": "S1", "title": "Corte costituzionale", "source_type": "constitutional_court", "court_or_author": "Corte costituzionale", "jurisdiction": "Italia", "date": "2025-01-15"}], bibliography={},
            epistemic_units=[{"id": "C1", "kind": "RULE", "text": "La misura deve essere necessaria.", "status": "VERIFIED", "material": True}, {"id": "I1", "kind": "INFERENCE", "text": "La necessita richiede il confronto con alternative.", "status": "INFERRED", "material": True}],
            relations=[{"source": "C1", "predicate": "SUPPORTS", "target": "I1", "rationale": "Premessa del passaggio inferenziale."}], reticulum={}, generation_contract={}, continuation={}, drafts=[],
            review={"cycles": [], "regenerations": [], "saturation": {}, "status": "SATURATED"}, final_review={},
            provenance={"entries": [{"id": "C1", "kind": "CLAIM", "proposition": "La misura deve essere necessaria.", "evidence_refs": ["S1"], "artifact_locators": ["§ 1.2"]}, {"id": "I1", "kind": "INFERENCE", "proposition": "La necessita richiede il confronto con alternative.", "premise_ids": ["C1"], "evidence_refs": ["S1"], "inference_bridge": "Necessita implica assenza di alternative equivalenti meno restrittive.", "artifact_locators": ["§ 2.1"]}]},
            contradictions=[], mining={}, style_profile={}, setup={"accepted": {"document_type": "LEGAL_MONOGRAPH", "audience": "giuristi"}}, source_intelligence={},
            claim_ledger=[{"id": "C1", "text": "La misura deve essere necessaria.", "claim_type": "legal_rule", "support_source_ids": ["S1"], "status": "VERIFIED", "material": True, "source_evidence": [{"source_id": "S1", "pinpoint": "p. 12", "proposition": "Necessita come requisito autonomo."}]}, {"id": "I1", "text": "La necessita richiede il confronto con alternative.", "claim_type": "strong_inference", "support_source_ids": ["S1"], "premise_claim_ids": ["C1"], "inference_bridge": "Necessita implica confronto tra mezzi equivalenti.", "status": "INFERRED", "material": True}],
            artifact_evidence=[
                {"evidence_id": "EV-1", "claim_id": "C1", "artifact_locator": "§ 1.2", "source_ids": ["S1"], "pinpoints": ["p. 12"], "status": "VERIFIED", "artifact_role": "final_legal_text", "evidence_kind": "prova normativa", "nota_editoriale": "La citazione sostiene il nucleo della regola."},
                {"claim_id": "I1", "artifact_locator": "§ 2.1", "source_ids": ["S1"], "pinpoints": ["p. 13"], "status": "INFERRED"},
            ],
            quality={}, benchmark={}, simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
            phase="VALIDATING", interaction={}, completion={"eligible": True}, node_integrity={}, runtime={"workspace_base": workspace}, artifacts=artifacts,
        )

    def _render(self, state):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-dashboard.html"
            dashboard.render_session_dashboard(state, path)
            return path.read_text(encoding="utf-8")

    def test_artifact_evidence_projection_is_exhaustive_and_contextual(self):
        state = self._state()
        trace = build_evidence_traceability(state)
        self.assertEqual(trace["copertura"]["evidenze_registrate"], 2)
        self.assertEqual(trace["copertura"]["evidenze_proiettate"], 2)
        first = trace["records"][0]
        self.assertEqual(first["riferimento_evidenza"], "EV-1")
        self.assertEqual(first["proposizione"], "La misura deve essere necessaria.")
        self.assertEqual(first["fonti_richiamate"][0]["riferimento_fonte"], "S1")
        self.assertEqual(first["pinpoint_registrati"], ["p. 12"])
        self.assertEqual(first["artefatto_dichiarato"]["titolo"], "Testo giuridico finale")
        self.assertEqual(first["attributi_ulteriori"]["nota_editoriale"], "La citazione sostiene il nucleo della regola.")
        self.assertTrue(evidence_traceability_gate(state)[0])

    def test_traceability_gate_rejects_broken_references_without_hiding_them(self):
        state = self._state()
        state.artifact_evidence.append({"claim_id": "MISSING", "artifact_locator": "", "source_ids": ["S-MISSING"], "artifact_role": "missing_role", "status": "OPEN"})
        ok, errors = evidence_traceability_gate(state)
        self.assertFalse(ok)
        self.assertTrue(any("claim" in error for error in errors))
        self.assertTrue(any("source" in error for error in errors))
        self.assertTrue(any("artifact" in error for error in errors))
        trace = build_evidence_traceability(state)
        self.assertEqual(trace["copertura"]["evidenze_registrate"], trace["copertura"]["evidenze_proiettate"])

    def test_user_artifact_index_is_complete_but_not_technical(self):
        state = self._state()
        index = build_user_artifact_index(state)
        roles = {item["ruolo"] for item in index["records"]}
        self.assertEqual(roles, {"final_legal_text", "evidence_dossier", "source_register", "inference_register", "transformation_ledger"})
        self.assertNotIn("session_integrity", roles)
        final = next(item for item in index["records"] if item["ruolo"] == "final_legal_text")
        self.assertEqual(final["richiamo"], "./final_legal_text.docx")
        text = repr(index)
        for forbidden in ("/tmp/juriscribe-v96", "sha256", "readback", "workspace_base", "session.integrity.json"):
            self.assertNotIn(forbidden, text)

    def test_dashboard_shows_compressed_outcome_and_full_trace_without_document_links(self):
        state = self._state()
        aggregate = build_dashboard_inference_view(state)
        coverage = build_dashboard_evidence_coverage(state, aggregate)
        html = self._render(state)
        body = html.split("<body>", 1)[1].split("</body>", 1)[0]
        for token in ("Esito complessivo", "Indice degli artefatti", "Registro di tracciabilita delle evidenze di artefatto", "EV-1", "La citazione sostiene il nucleo della regola."):
            self.assertIn(token, body)
        self.assertIn(coverage["esito_complessivo"]["sintesi_compressa"][0], body)
        self.assertIn("chat-tail-delivery-summary", body)
        self.assertIn("allegati in formato DOCX in coda alla sessione-chat", body)
        isolation = dashboard_attachment_isolation_report(html)
        self.assertEqual(isolation["status"], "PASS", isolation["errors"])
        self.assertEqual(isolation["docx_link_count"], 0)
        self.assertEqual(isolation["download_anchor_count"], 0)
        self.assertNotIn('href="./final_legal_text.docx"', body)
        self.assertNotIn("Apri artefatto", body)
        for forbidden in ("/tmp/juriscribe-v96", "sha256", "readback", "workspace_base", "session.integrity.json"):
            self.assertNotIn(forbidden, body)

    def test_dashboard_digest_binds_artifact_evidence_changes(self):
        state = self._state()
        before = dashboard_state_digest(state)
        state.artifact_evidence[0]["pinpoints"] = ["p. 99"]
        after = dashboard_state_digest(state)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()

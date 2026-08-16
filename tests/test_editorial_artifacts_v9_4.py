import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from juriscribe.dashboard_v9 import render_session_dashboard
from juriscribe.editorial_artifacts import (
    DOSSIER_ROLES,
    PROFILE_ID,
    build_dashboard_inference_view,
    build_editorial_artifact_views,
    semantic_projection_digest,
)
from juriscribe import semantic_delivery


class LegalHumanisticArtifactV94Tests(unittest.TestCase):
    def _state(self):
        return SimpleNamespace(
            request={"raw": "Analisi della proporzionalita", "summary": "Analisi giuridica della proporzionalita e dei suoi limiti"},
            mode="GREENFIELD",
            mode_selection={}, mode_contract={},
            editorial_standard={
                "document_type": "LEGAL_MONOGRAPH",
                "audience": "giuristi, studiosi e redazioni giuridiche",
                "mode_adjustments": ["rendere espliciti scope e confini interpretativi"],
                "rules": {"stable_terminology": True, "authority_and_counterauthority": True, "formal_register": True},
            },
            corpus=[],
            sources=[{
                "id": "S-COST", "title": "Corte costituzionale, sentenza esemplificativa",
                "source_type": "constitutional_court", "jurisdiction": "Italia",
                "court_or_author": "Corte costituzionale", "date": "2025-01-15",
                "direct_read": True, "verified_at": "2026-08-16T12:00:00+00:00",
                "role": "autorita di controllo", "notes": "Verificata nel suo perimetro decisorio",
                "bibliography_entry": "Corte cost., sent. 15 gennaio 2025", "url": "https://example.invalid/cost",
            }, {
                "id": "S-COUNTER", "title": "Orientamento contrario",
                "source_type": "leading_treatise", "jurisdiction": "Italia",
                "court_or_author": "Autore critico", "date": "2024",
                "direct_read": True, "verified_at": "2026-08-16T12:05:00+00:00",
                "role": "controautorita", "notes": "counter authority: contesta l'estensione del test",
            }],
            bibliography={},
            epistemic_units=[
                {"id": "C1", "kind": "RULE", "text": "Il controllo richiede adeguatezza e necessita.", "source_id": "S-COST", "source_locator": "p. 12", "status": "VERIFIED", "material": True},
                {"id": "I1", "kind": "INFERENCE", "text": "La necessita esige la considerazione di alternative meno restrittive.", "source_id": "S-COST", "source_locator": "p. 13", "status": "INFERRED", "material": True},
                {"id": "Q1", "kind": "QUALIFICATION", "text": "L'intensita del controllo varia con il contesto normativo.", "source_id": "S-COST", "source_locator": "p. 14", "status": "VERIFIED", "material": True},
            ],
            relations=[
                {"source": "Q1", "predicate": "QUALIFIES", "target": "I1", "rationale": "Evita di universalizzare il test."},
                {"source": "I1", "predicate": "CONTRADICTS", "target": "Q1", "rationale": "Tensione interpretativa da esplicitare, non occultare."},
            ],
            reticulum={}, generation_contract={}, continuation={}, drafts=[],
            review={
                "cycles": [{"cycle": 1, "findings": [{
                    "id": "F1", "criterion": "COUNTERAUTHORITY", "severity": "MAJOR",
                    "message": "La controautorita deve essere discussa nel corpo del testo.",
                    "proposed_action": "Integrare l'obiezione e delimitare la tesi.",
                    "epistemic_unit_ids": ["I1"], "source_ids": ["S-COUNTER"],
                    "artifact_locator": "§ 2.3", "status": "ADDRESSED",
                }]}],
                "regenerations": [{
                    "cycle": 1, "addressed_finding_ids": ["F1"],
                    "preserved_required_unit_ids": ["C1", "I1", "Q1"],
                    "lost_required_unit_ids": [], "introduced_material_unit_ids": [],
                    "degradation_flags": [], "status": "PASS",
                }],
                "saturation": {}, "status": "SATURATED",
            },
            final_review={
                "evidence": [{"criterion": "LEGAL_AUTHORITY", "status": "PASS", "locator": "Evidence dossier / C1", "rationale": "Autorita primaria e controautorita sono state distinte."}],
                "consequence_probes": [{"id": "P1", "proposition": "La tesi non e assoluta.", "downstream_effect": "La conclusione resta qualificata dal contesto.", "evidence_ref": "Q1", "status": "PASS"}],
                "status": "PASS",
            },
            provenance={"entries": [
                {"id": "C1", "kind": "CLAIM", "proposition": "Il controllo richiede adeguatezza e necessita.", "rationale": "La proposizione e direttamente attestata.", "disposition": "IN_FINAL", "evidence_refs": ["S-COST"], "artifact_locators": ["§ 1.2"]},
                {"id": "I1", "kind": "INFERENCE", "proposition": "La necessita richiede alternative meno restrittive.", "rationale": "La conclusione deriva dalla funzione del requisito di necessita.", "disposition": "IN_FINAL", "evidence_refs": ["S-COST"], "premise_ids": ["C1"], "inference_bridge": "Se una misura e necessaria solo in assenza di alternative equivalenti, le alternative devono essere vagliate.", "falsifier": "Esistenza di una disciplina che escluda il confronto con alternative.", "artifact_locators": ["§ 2.2"]},
                {"id": "REGEN-1", "kind": "TRANSFORMATION", "proposition": "Integrazione della controautorita.", "rationale": "Evitare una rappresentazione unilaterale del quadro interpretativo.", "disposition": "IN_FINAL", "artifact_locators": ["§ 2.3"]},
            ]},
            contradictions=[], mining={}, style_profile={},
            setup={"accepted": {"audience": "giuristi, studiosi e redazioni giuridiche", "document_type": "LEGAL_MONOGRAPH"}},
            source_intelligence={},
            claim_ledger=[
                {"id": "C1", "text": "Il controllo richiede adeguatezza e necessita.", "claim_type": "legal_rule", "scope": "controllo di proporzionalita", "support_source_ids": ["S-COST"], "premise_claim_ids": [], "status": "VERIFIED", "material": True, "source_evidence": [{"source_id": "S-COST", "pinpoint": "p. 12", "proposition": "Adeguatezza e necessita sono passaggi distinti."}]},
                {"id": "I1", "text": "La necessita esige alternative meno restrittive.", "claim_type": "strong_inference", "scope": "necessita", "support_source_ids": ["S-COST"], "premise_claim_ids": ["C1"], "inference_bridge": "Dalla necessita segue il confronto tra mezzi equivalenti.", "falsifier": "Regola speciale che renda irrilevanti le alternative.", "status": "INFERRED", "material": True, "source_evidence": [{"source_id": "S-COST", "pinpoint": "p. 13", "proposition": "La necessita implica assenza di misure equivalenti meno restrittive."}]},
            ],
            artifact_evidence=[{"claim_id": "C1", "artifact_locator": "§ 1.2", "source_ids": ["S-COST"]}],
            quality={}, benchmark={}, simulations={},
            compression={"before_words": 1200, "after_words": 1040, "preserved_unit_ids": ["C1", "I1", "Q1"], "lost_required_unit_ids": [], "added_material_unit_ids": [], "post_compression_recheck": "PASS", "status": "PASS"},
            limits=[], strategy={}, dod=[],
            editorial_actions=[{"kind": "terminologia", "summary": "Uniformata la nozione di necessita.", "rationale": "Evitare oscillazioni concettuali.", "status": "DONE"}],
            reflection={}, metrics={}, phase="VALIDATING", interaction={}, completion={}, node_integrity={}, runtime={}, artifacts=[],
        )

    def test_four_dossiers_share_rich_legal_humanistic_projection(self):
        state = self._state()
        views = build_editorial_artifact_views(state)
        self.assertEqual(tuple(views), DOSSIER_ROLES)
        self.assertIn("proposizione", views["evidence_dossier"]["records"][0])
        self.assertIn("carattere_autorita", views["source_register"]["records"][0])
        inference = next(item for item in views["inference_register"]["records"] if item["riferimento"] == "I1")
        self.assertEqual(inference["premesse"][0]["contenuto"], "Il controllo richiede adeguatezza e necessita.")
        self.assertIn("ponte_inferenziale", inference)
        self.assertIn("condizione_di_confutazione", inference)
        transformations = views["transformation_ledger"]["records"]
        self.assertTrue(any(item.get("finding_affrontati") == ["F1"] for item in transformations))
        self.assertTrue(any(item.get("natura") == "prova delle conseguenze logiche" for item in transformations))

    def test_dashboard_contains_every_dossier_value_and_no_technical_body(self):
        state = self._state()
        aggregate = build_dashboard_inference_view(state)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-dashboard.html"
            render_session_dashboard(state, path)
            html = path.read_text(encoding="utf-8")
        body = html.split("<body>", 1)[1].split("</body>", 1)[0]
        self.assertIn('name="juriscribe-state-digest"', html)
        for role in DOSSIER_ROLES:
            view = aggregate[role]
            self.assertIn(view["titolo"], body)
            self.assertIn(view["finalita"], body)
            for record in view["records"]:
                for value in self._leaf_strings(record):
                    self.assertIn(value, body, (role, value))
        forbidden = [
            "session.integrity.json", "Mode digest", "Editorial digest", "Dashboard state digest",
            "sha256", "workspace_base", "DOCX_WRITE", "DOCX_READBACK", "readback", "Integrita tecnica",
        ]
        for token in forbidden:
            self.assertNotIn(token, body)

    def _leaf_strings(self, value):
        if isinstance(value, dict):
            for item in value.values(): yield from self._leaf_strings(item)
        elif isinstance(value, (list, tuple)):
            for item in value: yield from self._leaf_strings(item)
        elif value not in (None, ""):
            yield str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")

    def test_new_dossier_registration_is_semantically_sealed(self):
        state = self._state()
        record = {"id": "evidence", "role": "evidence_dossier", "path": "evidence_dossier.docx", "readback": "PASS"}
        with patch.object(semantic_delivery._delivery, "record_artifact", side_effect=lambda _state, item: item):
            stamped = semantic_delivery.record_artifact(state, record)
        self.assertEqual(stamped["semantic_profile"], PROFILE_ID)
        self.assertEqual(stamped["semantic_projection_digest"], semantic_projection_digest(state, "evidence_dossier"))

    def test_semantic_dossier_gate_detects_inferential_drift(self):
        state = self._state()
        state.artifacts = [{
            "id": role, "role": role,
            "semantic_projection_digest": semantic_projection_digest(state, role),
        } for role in DOSSIER_ROLES]
        self.assertTrue(semantic_delivery.semantic_dossier_gate(state)[0])
        state.claim_ledger[0]["text"] = "Proposizione materialmente modificata."
        ok, errors = semantic_delivery.semantic_dossier_gate(state)
        self.assertFalse(ok)
        self.assertTrue(errors)
        self.assertTrue(any("source_register" in error or "inference_register" in error for error in errors), errors)

    def test_semantic_projection_excludes_runtime_telemetry(self):
        state = self._state()
        state.runtime = {"workspace_base": "/secret/path", "capabilities": {"DOCX_WRITE": "AVAILABLE"}}
        state.node_integrity = {"status": "PASS", "errors": []}
        text = repr(build_dashboard_inference_view(state))
        for token in ("workspace_base", "/secret/path", "DOCX_WRITE", "node_integrity", "sha256"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()

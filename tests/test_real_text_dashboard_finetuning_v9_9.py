import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape as xml_escape

from juriscribe.artifact_atlas import build_artifact_atlas
from juriscribe.dashboard_persistence import dashboard_materialization_report
from juriscribe.dashboard_v97 import render_session_dashboard
from juriscribe.dossier_materialization import PROFILE, dossier_semantic_materialization_gate, render_dossier_text, verify_dossier_semantic_materialization


class RealTextDashboardFinetuningV99Tests(unittest.TestCase):
    def _write_docx(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(
            f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r></w:p>'
            for line in str(text).splitlines() if line.strip()
        )
        document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '</w:body></w:document>'
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
            package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
            package.writestr("word/document.xml", document)

    def _semantic_state(self, base: Path):
        return SimpleNamespace(
            mode="GREENFIELD",
            setup={},
            runtime={"workspace_base": str(base)},
            sources=[{"id": "S1", "title": "Costituzione italiana — fonte ufficiale", "source_type": "primary_law", "direct_read": True, "verified_at": "2026-08-17"}],
            claim_ledger=[],
            epistemic_units=[{"id": "U1", "kind": "RULE", "text": "La sovranità appartiene al popolo nelle forme e nei limiti della Costituzione.", "source_id": "S1", "source_locator": "art. 1", "material": True, "status": "VERIFIED"}],
            relations=[], provenance={}, artifact_evidence=[], review={}, compression={}, final_review={}, editorial_actions=[], artifacts=[],
        )

    def _dashboard_state(self):
        return {
            "request": {"raw": "Mandato reale dashboard", "summary": "Mandato reale dashboard"},
            "phase": "DOD_FROZEN", "mode": "GREENFIELD", "mode_selection": {},
            "mode_contract": {"status": "READY"}, "editorial_standard": {}, "corpus": [],
            "sources": [{"id": "S1", "title": "Fonte ufficiale reale", "source_type": "primary_law", "direct_read": True, "verified_at": "2026-08-17"}],
            "bibliography": {}, "epistemic_units": [{"id": "U1", "kind": "RULE", "text": "Regola reale distintiva della sessione", "source_id": "S1", "material": True}],
            "relations": [], "reticulum": {"status": "PASS"}, "generation_contract": {}, "continuation": {}, "drafts": [],
            "review": {"cycles": [], "regenerations": []}, "final_review": {}, "provenance": {}, "contradictions": [], "mining": {}, "style_profile": {},
            "setup": {}, "source_intelligence": {}, "claim_ledger": [], "artifact_evidence": [], "quality": {}, "benchmark": {},
            "simulations": {}, "compression": {}, "limits": [], "strategy": {}, "dod": [], "editorial_actions": [], "reflection": {},
            "metrics": {}, "completion": {"eligible": False}, "interaction": {}, "node_integrity": {}, "runtime": {},
            "artifacts": [],
        }

    def test_canonical_dossier_docx_is_bound_to_projection_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            state = self._semantic_state(base)
            path = base / "artifacts" / "evidence_dossier.docx"
            self._write_docx(path, "Dossier incompleto")
            record = {"role": "evidence_dossier", "path": str(path), "readback": "PASS"}
            failed = verify_dossier_semantic_materialization(state, record)
            self.assertEqual(failed["status"], "FAIL")
            self.assertGreater(failed["missing_public_leaf_count"], 0)

            self._write_docx(path, render_dossier_text(state, "evidence_dossier"))
            passed = verify_dossier_semantic_materialization(state, record)
            self.assertEqual(passed["status"], "PASS", passed)
            self.assertGreater(passed["public_leaf_count"], 0)
            self.assertEqual(passed["missing_public_leaf_count"], 0)

    def test_new_dossier_marker_is_fail_closed_but_legacy_record_remains_migrable(self):
        legacy = SimpleNamespace(artifacts=[{"role": "evidence_dossier"}])
        self.assertTrue(dossier_semantic_materialization_gate(legacy)[0])
        current = SimpleNamespace(artifacts=[{"role": "evidence_dossier", "semantic_materialization_profile": PROFILE}])
        ok, errors = dossier_semantic_materialization_gate(current)
        self.assertFalse(ok)
        self.assertTrue(any("not PASS" in error for error in errors))

    def test_dashboard_materialization_report_tracks_real_semantic_witnesses_and_artifact_summary(self):
        marker = "Regola reale distintiva della sessione"
        summary = "Artefatto reale distinto e materializzato"
        state = self._dashboard_state()
        state["artifacts"] = [{"id": "final", "role": "final_legal_text", "summary": summary, "delivery_class": "ATTACH"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dashboard.html"
            render_session_dashboard(state, path)
            page = path.read_text(encoding="utf-8")
        report = dashboard_materialization_report(state, page)
        self.assertEqual(report["missing_semantic_witness_count"], 0, report)
        self.assertEqual(report["missing_public_material_roles"], [], report)
        self.assertGreater(report["semantic_witness_count"], 0)
        self.assertIn(marker, page)
        self.assertIn(summary, page)
        damaged = page.replace(marker, "")
        damaged_report = dashboard_materialization_report(state, damaged)
        self.assertGreater(damaged_report["missing_semantic_witness_count"], 0)

    def test_empty_optional_epistemic_wrappers_do_not_create_false_dashboard_cards(self):
        state = self._dashboard_state()
        atlas = build_artifact_atlas(state)
        roles = {str(item.get("ruolo")) for item in atlas.get("artefatti_epistemici") or []}
        self.assertNotIn("review_cycles", roles)

        marker = "Finding reale materializzato nella review"
        state["review"] = {
            "cycles": [{"cycle": 1, "status": "PASS", "findings": [{"finding_id": "F1", "problema_rilevato": marker}]}],
            "regenerations": [],
        }
        populated = build_artifact_atlas(state)
        record = next(item for item in populated.get("artefatti_epistemici") or [] if item.get("ruolo") == "review_cycles")
        self.assertIn(marker, str(record.get("descrizione_completa")))
        self.assertTrue(record.get("sintesi_compressa"))


if __name__ == "__main__":
    unittest.main()

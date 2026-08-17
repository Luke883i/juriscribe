import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.dashboard_v9 import render_session_dashboard
from juriscribe.delivery import ATTACH, DOCX_MIME, SURFACE, build_delivery_manifest, delivery_gate, normalize_artifact_record
from juriscribe.modes import GREENFIELD, required_artifact_roles


class DeliveryV93RegressionTests(unittest.TestCase):
    def _state(self, *, docx_write="AVAILABLE", docx_readback="AVAILABLE"):
        return SimpleNamespace(
            mode=GREENFIELD, setup={},
            runtime={"capabilities": {"DOCX_WRITE": docx_write, "DOCX_READBACK": docx_readback}, "workspace_base": ""},
            phase="VALIDATING",
            request={"raw": "Monografia", "summary": "Monografia"},
            mode_selection={}, mode_contract={"required_artifact_roles": sorted(required_artifact_roles(GREENFIELD, {})), "status": "READY"},
            editorial_standard={}, corpus=[], sources=[], bibliography={}, epistemic_units=[], relations=[], reticulum={},
            generation_contract={}, continuation={}, drafts=[], review={}, final_review={}, provenance={}, contradictions=[],
            mining={}, style_profile={}, source_intelligence={}, claim_ledger=[], artifact_evidence=[], quality={}, benchmark={},
            simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
            artifacts=[], completion={"eligible": True, "reason": "PASS"}, node_integrity={}, interaction={},
        )

    def _write_docx(self, path: Path, text="Testo giuridico"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
            package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
            package.writestr("word/document.xml", f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')

    def _populate_valid_delivery(self, state, root: Path):
        state.runtime["workspace_base"] = str(root.resolve())
        artifact_root = root / "artifacts"
        roles = sorted(required_artifact_roles(GREENFIELD, {}))
        for role in roles:
            path = artifact_root / ("session-dashboard.html" if role == "session_dashboard" else f"{role}.docx")
            if role != "session_dashboard":
                self._write_docx(path, role)
            state.artifacts.append(normalize_artifact_record(state, {"id": role, "role": role, "path": str(path), "readback": "PASS"}))
        dashboard = next(a for a in state.artifacts if a["role"] == "session_dashboard")
        render_session_dashboard(state.__dict__, dashboard["path"])

    def test_every_chat_attachment_is_real_docx_and_dashboard_is_separate_html_surface(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            self._populate_valid_delivery(state, Path(tmp))
            manifest = build_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertTrue(manifest["materialization_verified"])
            self.assertTrue(manifest["workspace_confinement_verified"])
            self.assertTrue(manifest["dashboard_bound_to_current_state"])
            self.assertEqual(manifest["attachment_placement"], "SESSION_CHAT_TAIL")
            self.assertTrue(manifest["attachments"])
            for artifact in manifest["attachments"]:
                self.assertGreater(artifact["size_bytes"], 0)
                self.assertEqual(len(artifact["sha256"]), 64)
                self.assertTrue(artifact["path"].endswith(".docx"), artifact)
                self.assertEqual(artifact["media_type"], DOCX_MIME)
                self.assertEqual(artifact["placement"], "SESSION_CHAT_TAIL")
            self.assertEqual(manifest["dashboard_surface"]["delivery_class"], SURFACE)
            self.assertFalse(manifest["dashboard_surface"]["attached"])
            self.assertNotIn("session_dashboard", {a["role"] for a in manifest["attachments"]})

    def test_json_cannot_masquerade_as_final_document(self):
        state = self._state()
        with self.assertRaises(ValueError):
            normalize_artifact_record(state, {"id": "final", "role": "final_legal_text", "path": "final.json", "readback": "PASS"})

    def test_plain_text_renamed_docx_fails_materialization(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._populate_valid_delivery(state, root)
            (root / "artifacts" / "final_legal_text.docx").write_text("not a DOCX", encoding="utf-8")
            ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("valid DOCX" in error or "OOXML" in error for error in errors), errors)

    def test_missing_docx_fails_materialization(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._populate_valid_delivery(state, root); (root / "artifacts" / "final_legal_text.docx").unlink()
            ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("missing on disk" in error for error in errors), errors)

    def test_stale_dashboard_fails_after_control_state_change(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            self._populate_valid_delivery(state, Path(tmp)); self.assertTrue(delivery_gate(state)[0])
            state.completion = {"eligible": False, "reason": "new blocker"}
            ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("dashboard is stale" in error for error in errors), errors)

    def test_internal_logs_are_excluded_even_if_legacy_record_says_required(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            self._populate_valid_delivery(state, Path(tmp))
            state.artifacts.append({"id": "session-integrity", "role": "session_integrity", "path": "session.integrity.json", "readback": "PASS", "required": True})
            dashboard = next(a for a in state.artifacts if a["role"] == "session_dashboard")
            render_session_dashboard(state.__dict__, dashboard["path"])
            manifest = build_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertNotIn("session_integrity", {a["role"] for a in manifest["attachments"]})
            internal = next(a for a in state.artifacts if a["role"] == "session_integrity")
            self.assertEqual(internal["delivery_class"], "INTERNAL"); self.assertFalse(internal["required"])

    def test_non_final_role_cannot_force_itself_into_attachment_set(self):
        state = self._state()
        with self.assertRaises(ValueError):
            normalize_artifact_record(state, {"id": "receipt", "role": "simulation_receipt", "path": "simulation.json", "readback": "PASS", "delivery_class": ATTACH})

    def test_docx_capabilities_are_fail_closed(self):
        state = self._state(docx_write="UNVERIFIED", docx_readback="UNVERIFIED")
        with tempfile.TemporaryDirectory() as tmp:
            self._populate_valid_delivery(state, Path(tmp)); ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("DOCX_WRITE" in error for error in errors), errors); self.assertTrue(any("DOCX_READBACK" in error for error in errors), errors)

    def test_external_artifact_path_is_rejected(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp); self._populate_valid_delivery(state, root)
            external = Path(outside) / "final_legal_text.docx"; self._write_docx(external)
            record = next(a for a in state.artifacts if a["role"] == "final_legal_text"); record["path"] = str(external)
            ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("outside" in e or "escapes" in e for e in errors), errors)

    def test_zip_bomb_like_docx_is_rejected(self):
        state = self._state()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._populate_valid_delivery(state, root)
            target = root / "artifacts" / "final_legal_text.docx"
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as package:
                package.writestr("[Content_Types].xml", "x")
                package.writestr("_rels/.rels", "x")
                package.writestr("word/document.xml", "<w:document><w:t>" + ("A" * (2 * 1024 * 1024)) + "</w:t></w:document>")
            ok, errors = delivery_gate(state)
            self.assertFalse(ok); self.assertTrue(any("compression ratio" in e for e in errors), errors)


if __name__ == "__main__": unittest.main()

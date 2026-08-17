import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.chat_delivery import DOCX_MIME
from juriscribe.conversation_contract import initialize_pipeline_lock
from juriscribe.delivery import build_delivery_manifest, delivery_gate, normalize_artifact_record
from juriscribe.modes import GREENFIELD, required_artifact_roles


class DeliveryBoundaryLayeringV100Tests(unittest.TestCase):
    def _write_docx(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
            package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
            package.writestr("word/document.xml", f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')

    def test_materialization_gate_is_distinct_from_user_release_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = SimpleNamespace(
                mode=GREENFIELD, setup={},
                runtime={"workspace_base": str(root.resolve()), "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"}},
                request={"raw": "Test", "summary": "Test", "request_id": "REQ-LAYER"}, mode_selection={"digest": "MODE-LAYER"},
                mode_contract={"status": "READY"}, editorial_standard={"status": "READY"}, corpus=[], sources=[], bibliography={},
                epistemic_units=[], relations=[], reticulum={}, generation_contract={}, continuation={}, drafts=[], review={}, final_review={"status": "PASS"},
                provenance={}, contradictions=[], mining={}, style_profile={}, source_intelligence={}, claim_ledger=[], artifact_evidence=[],
                quality={}, benchmark={}, simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
                artifacts=[], completion={}, node_integrity={}, interaction={},
            )
            initialize_pipeline_lock(state)
            for role in sorted(required_artifact_roles(GREENFIELD, {})):
                if role == "session_dashboard":
                    path = root / "artifacts" / "session-dashboard.html"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    # This test focuses on boundary layering; use a digest-bound minimal dashboard.
                    from juriscribe.dashboard_v9 import dashboard_state_digest
                    digest = dashboard_state_digest(state)
                    path.write_text(f'<html><head><meta name="juriscribe-state-digest" content="{digest}"></head><body>Juriscribe</body></html>', encoding="utf-8")
                else:
                    path = root / "artifacts" / f"{role}.docx"
                    self._write_docx(path, role)
                record = normalize_artifact_record(state, {"id": role, "role": role, "path": str(path), "readback": "PASS"})
                state.artifacts.append(record)

            material_ok, material_errors = delivery_gate(state)
            self.assertTrue(material_ok, material_errors)

            manifest = build_delivery_manifest(state)
            self.assertEqual(manifest["status"], "FAIL")
            self.assertEqual(manifest["attachments"], [])
            self.assertTrue(manifest["chat_docx_delivery"]["withheld_attachments"])
            self.assertTrue(any("standard_artifact_autopilot" in error or "epistemic" in error or "quality" in error for error in manifest["errors"]), manifest["errors"])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.browser_delivery import (
    DOCX_MIME,
    build_browser_delivery_manifest,
    content_disposition,
    dashboard_docx_links_report,
    render_docx_download_anchor,
)
from juriscribe.dashboard_v100 import render_session_dashboard
from juriscribe.delivery import ATTACH, SURFACE, build_delivery_manifest, delivery_gate, normalize_artifact_record
from juriscribe.modes import GREENFIELD, required_artifact_roles


class BrowserDocxDeliveryV100Tests(unittest.TestCase):
    def _state(self, root: Path):
        setup = {}
        return SimpleNamespace(
            mode=GREENFIELD, setup=setup,
            runtime={"capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"}, "workspace_base": str(root.resolve())},
            phase="VALIDATING", request={"raw": "DOCX browser test", "summary": "DOCX browser test"}, mode_selection={},
            mode_contract={"required_artifact_roles": sorted(required_artifact_roles(GREENFIELD, setup)), "status": "READY"},
            editorial_standard={}, corpus=[], sources=[], bibliography={}, epistemic_units=[], relations=[], reticulum={},
            generation_contract={}, continuation={}, drafts=[], review={}, final_review={}, provenance={}, contradictions=[],
            mining={}, style_profile={}, source_intelligence={}, claim_ledger=[], artifact_evidence=[], quality={}, benchmark={},
            simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
            artifacts=[], completion={"eligible": False, "reason": "test"}, node_integrity={}, interaction={},
        )

    def _write_docx(self, path: Path, text="DOCX reale"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
            package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
            package.writestr("word/document.xml", f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')

    def _populate(self, state, root: Path):
        for role in sorted(required_artifact_roles(GREENFIELD, {})):
            if role == "session_dashboard":
                continue
            path = root / "artifacts" / f"{role}-à prova.docx"
            self._write_docx(path, role)
            state.artifacts.append(normalize_artifact_record(state, {"id": role, "role": role, "summary": role, "path": str(path), "readback": "PASS"}))
        dashboard = root / "artifacts" / "session-dashboard.html"
        state.artifacts.append(normalize_artifact_record(state, {"id": "dashboard", "role": "session_dashboard", "summary": "workbench", "path": str(dashboard), "readback": "PASS"}))
        render_session_dashboard(state.__dict__, dashboard)
        return dashboard

    def test_only_docx_enters_attachment_manifest_and_dashboard_is_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            manifest = build_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertTrue(manifest["attachments"])
            self.assertTrue(all(item["format"] == "DOCX" and item["path"].endswith(".docx") for item in manifest["attachments"]))
            self.assertTrue(all(item["media_type"] == DOCX_MIME for item in manifest["attachments"]))
            self.assertEqual(manifest["dashboard_surface"]["delivery_class"], SURFACE)
            self.assertFalse(manifest["dashboard_surface"]["attached"])
            self.assertNotIn("session_dashboard", {item["role"] for item in manifest["attachments"]})

    def test_dashboard_contains_native_docx_download_links_without_javascript_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); dashboard = self._populate(state, root)
            page = dashboard.read_text(encoding="utf-8")
            report = dashboard_docx_links_report(state, page)
            self.assertEqual(report["status"], "PASS", report["errors"])
            self.assertEqual(report["expected_download_roles"], report["linked_download_roles"])
            self.assertIn(" download type=", page)
            self.assertIn("data-juriscribe-download-role", page)

    def test_html_or_pdf_cannot_be_forced_into_downloadable_attachment_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            dashboard = next(item for item in state.artifacts if item["role"] == "session_dashboard")
            dashboard["delivery_class"] = ATTACH
            browser = build_browser_delivery_manifest(state)
            self.assertEqual(browser["status"], "FAIL")
            self.assertTrue(any("dashboard" in error.lower() for error in browser["errors"]))

    def test_materialized_plain_text_renamed_docx_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            target = next(item for item in state.artifacts if item.get("delivery_class") == ATTACH)
            Path(target["path"]).write_text("not OOXML", encoding="utf-8")
            ok, errors = delivery_gate(state)
            self.assertFalse(ok)
            self.assertTrue(any("DOCX" in error or "OOXML" in error for error in errors), errors)

    def test_content_disposition_has_ascii_fallback_and_utf8_filename(self):
        header = content_disposition("parere-à-§.docx")
        self.assertTrue(header.startswith("attachment;"))
        self.assertIn("filename=", header)
        self.assertIn("filename*=UTF-8''", header)
        self.assertIn(".docx", header)

    def test_download_anchor_rejects_cross_origin_blob_and_non_docx(self):
        for href in ("https://example.invalid/a.docx", "blob:abc", "data:text/plain,x", "./file.pdf", "./file.docx?x=1"):
            with self.subTest(href=href):
                with self.assertRaises(ValueError):
                    render_docx_download_anchor(href, "final_legal_text")


if __name__ == "__main__":
    unittest.main()

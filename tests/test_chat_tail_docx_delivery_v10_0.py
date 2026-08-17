import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.chat_delivery import (
    CHAT_PLACEMENT,
    DOCX_MIME,
    build_chat_delivery_manifest,
    content_disposition,
    dashboard_attachment_isolation_report,
)
from juriscribe.dashboard_v100 import render_session_dashboard
from juriscribe.delivery import ATTACH, SURFACE, build_delivery_manifest, delivery_gate, normalize_artifact_record
from juriscribe.modes import GREENFIELD, required_artifact_roles


class ChatTailDocxDeliveryV100Tests(unittest.TestCase):
    def _state(self, root: Path):
        setup = {}
        return SimpleNamespace(
            mode=GREENFIELD, setup=setup,
            runtime={"capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"}, "workspace_base": str(root.resolve())},
            phase="VALIDATING", request={"raw": "DOCX chat-tail test", "summary": "DOCX chat-tail test"}, mode_selection={},
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

    def test_only_docx_enters_chat_tail_and_dashboard_is_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            manifest = build_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertEqual(manifest["attachment_placement"], CHAT_PLACEMENT)
            self.assertTrue(manifest["attachments"])
            self.assertTrue(all(item["format"] == "DOCX" and item["path"].endswith(".docx") for item in manifest["attachments"]))
            self.assertTrue(all(item["media_type"] == DOCX_MIME for item in manifest["attachments"]))
            self.assertTrue(all(item["placement"] == CHAT_PLACEMENT and item["downloadable_in_chat"] for item in manifest["attachments"]))
            self.assertEqual(manifest["dashboard_surface"]["delivery_class"], SURFACE)
            self.assertFalse(manifest["dashboard_surface"]["attached"])
            self.assertFalse(manifest["dashboard_surface"]["links_to_docx"])
            self.assertNotIn("session_dashboard", {item["role"] for item in manifest["attachments"]})

    def test_dashboard_summarizes_without_docx_links_or_download_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); dashboard = self._populate(state, root)
            page = dashboard.read_text(encoding="utf-8")
            report = dashboard_attachment_isolation_report(page)
            self.assertEqual(report["status"], "PASS", report["errors"])
            self.assertEqual(report["docx_link_count"], 0)
            self.assertEqual(report["download_anchor_count"], 0)
            self.assertIn("chat-tail-delivery-summary", page)
            self.assertIn("allegati in formato DOCX in coda alla sessione-chat", page)

    def test_chat_manifest_is_assistant_and_browser_agnostic_but_does_not_overclaim_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            manifest = build_chat_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertTrue(manifest["assistant_agnostic_contract"])
            self.assertTrue(manifest["browser_agnostic_contract"])
            self.assertTrue(manifest["host_attachment_capability_required"])
            self.assertFalse(manifest["global_host_behavior_claim"])

    def test_html_or_pdf_cannot_be_forced_into_chat_attachment_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); state = self._state(root); self._populate(state, root)
            dashboard = next(item for item in state.artifacts if item["role"] == "session_dashboard")
            dashboard["delivery_class"] = ATTACH
            chat = build_chat_delivery_manifest(state)
            self.assertEqual(chat["status"], "FAIL")
            self.assertTrue(any("dashboard" in error.lower() for error in chat["errors"]))

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

    def test_injected_docx_link_in_dashboard_is_rejected(self):
        page = '<html><body><a href="./finale.docx">documento</a></body></html>'
        report = dashboard_attachment_isolation_report(page)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["docx_link_count"], 1)

    def test_injected_download_anchor_in_dashboard_is_rejected_even_without_docx(self):
        page = '<html><body><a href="./x.txt" download>file</a></body></html>'
        report = dashboard_attachment_isolation_report(page)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["download_anchor_count"], 1)


if __name__ == "__main__":
    unittest.main()

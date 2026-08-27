from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from juriscribe.chat_delivery import (
    DOCX_MIME,
    SESSION_CHAT_DOWNLOAD,
    build_session_chat_docx_manifest,
    session_chat_docx_gate,
)
from juriscribe.chat_shell import project_chat_shell, render_chat_shell, validate_rendered_shell
from juriscribe.modes import GREENFIELD


class SessionChatDocxMaterializationContractV1Tests(unittest.TestCase):
    def _state(self, root: Path):
        return SimpleNamespace(
            session_id="SES-chat-docx",
            phase="ACTIVE_WORK",
            mode=GREENFIELD,
            setup={},
            runtime={"workspace_base": str(root)},
            interaction={"card": {}, "history": []},
            completion={"eligible": False},
            artifacts=[],
            strategy={},
            admission={},
            request={"raw": "test"},
            corpus=[],
            reticulum={},
            mode_contract={},
            generation_contract={},
            dod=[],
            drafts=[],
            review={},
            provenance={},
            final_review={},
        )

    def _docx(self, root: Path, name: str, text: str = "Documento") -> Path:
        path = root / "artifacts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
            )
            package.writestr(
                "_rels/.rels",
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
            )
            package.writestr(
                "word/document.xml",
                f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>',
            )
        return path

    def _register(self, state, path: Path, *, role: str, artifact_id: str, delivery_class: str = "INTERNAL"):
        state.artifacts.append({
            "id": artifact_id,
            "role": role,
            "path": str(path),
            "readback": "PASS",
            "delivery_class": delivery_class,
        })

    def test_intermediate_and_final_docx_are_both_downloadable_in_chat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            intermediate = self._docx(root, "analysis-draft.docx", "intermedio")
            final = self._docx(root, "final-legal-text.docx", "finale")
            self._register(state, intermediate, role="analysis_working_draft", artifact_id="draft-1")
            self._register(state, final, role="final_legal_text", artifact_id="final", delivery_class="ATTACH")

            manifest = build_session_chat_docx_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertEqual(manifest["artifact_count"], 2)
            self.assertEqual(manifest["downloadable_count"], 2)
            self.assertEqual({item["filename"] for item in manifest["artifacts"]}, {intermediate.name, final.name})
            self.assertTrue(all(item["downloadable_in_chat"] for item in manifest["artifacts"]))
            self.assertTrue(all(item["media_type"] == DOCX_MIME for item in manifest["artifacts"]))
            self.assertTrue(all(item["session_chat_delivery_class"] == SESSION_CHAT_DOWNLOAD for item in manifest["artifacts"]))
            draft = next(item for item in manifest["artifacts"] if item["filename"] == intermediate.name)
            self.assertTrue(draft["intermediate"])
            self.assertEqual(draft["final_delivery_class"], "INTERNAL")
            self.assertTrue(draft["final_delivery_class_independent"])

    def test_materializing_final_docx_does_not_hide_prior_intermediate_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            first = self._docx(root, "iteration-01.docx")
            self._register(state, first, role="analysis_iteration", artifact_id="iteration-01")
            before = build_session_chat_docx_manifest(state)
            self.assertEqual(before["artifact_count"], 1)

            second = self._docx(root, "iteration-02-final.docx")
            self._register(state, second, role="final_legal_text", artifact_id="final", delivery_class="ATTACH")
            after = build_session_chat_docx_manifest(state)
            self.assertEqual(after["status"], "PASS", after["errors"])
            self.assertEqual(after["artifact_count"], 2)
            self.assertIn(first.name, {item["filename"] for item in after["artifacts"]})

    def test_unregistered_workspace_docx_is_still_surfaced_but_gate_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            hidden = self._docx(root, "unregistered-intermediate.docx")
            manifest = build_session_chat_docx_manifest(state)
            self.assertEqual(manifest["status"], "FAIL")
            self.assertEqual(manifest["artifact_count"], 1)
            self.assertEqual(manifest["artifacts"][0]["path"], str(hidden.resolve()))
            self.assertTrue(manifest["artifacts"][0]["downloadable_in_chat"])
            self.assertEqual(manifest["artifacts"][0]["registration_status"], "UNREGISTERED")
            self.assertTrue(any("not registered" in error for error in manifest["errors"]))
            ok, errors = session_chat_docx_gate(state)
            self.assertFalse(ok)
            self.assertTrue(errors)

    def test_registered_but_malformed_docx_fails_session_chat_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            path = root / "artifacts" / "bad.docx"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("not OOXML", encoding="utf-8")
            self._register(state, path, role="analysis_working_draft", artifact_id="bad")
            manifest = build_session_chat_docx_manifest(state)
            self.assertEqual(manifest["status"], "FAIL")
            self.assertTrue(any("OOXML" in error for error in manifest["errors"]))

    def test_chat_shell_carries_host_download_descriptors_and_visible_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._state(root)
            path = self._docx(root, "working-note.docx")
            self._register(state, path, role="analysis_note", artifact_id="note")
            projection = project_chat_shell(state)
            self.assertEqual(projection["artifact_manifest_status"], "PASS")
            self.assertEqual(projection["artifact_count"], 1)
            self.assertEqual(len(projection["downloadable_artifacts"]), 1)
            self.assertEqual(projection["downloadable_artifacts"][0]["path"], str(path.resolve()))
            rendered = render_chat_shell(state)
            ok, errors = validate_rendered_shell(rendered)
            self.assertTrue(ok, errors)
            self.assertIn("[A] ARTEFATTI(1)", rendered.splitlines()[2])

    def test_no_docx_is_a_valid_empty_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            manifest = build_session_chat_docx_manifest(state)
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["artifact_count"], 0)
            self.assertTrue(session_chat_docx_gate(state)[0])


if __name__ == "__main__":
    unittest.main()

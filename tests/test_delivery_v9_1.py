import unittest
from types import SimpleNamespace

from juriscribe.delivery import (
    ATTACH,
    DOCX_MIME,
    HTML_MIME,
    build_delivery_manifest,
    delivery_gate,
    normalize_artifact_record,
)
from juriscribe.modes import GREENFIELD, required_artifact_roles


class DeliveryV91RegressionTests(unittest.TestCase):
    def _state(self, *, docx_write="AVAILABLE", docx_readback="AVAILABLE"):
        return SimpleNamespace(
            mode=GREENFIELD,
            setup={},
            runtime={
                "capabilities": {
                    "DOCX_WRITE": docx_write,
                    "DOCX_READBACK": docx_readback,
                }
            },
            artifacts=[],
            completion={"eligible": True},
        )

    def _populate_valid_delivery(self, state):
        for role in sorted(required_artifact_roles(GREENFIELD, {})):
            if role == "session_dashboard":
                path = "artifacts/session-dashboard.html"
            else:
                path = f"artifacts/{role}.docx"
            state.artifacts.append(
                normalize_artifact_record(
                    state,
                    {
                        "id": role,
                        "role": role,
                        "path": path,
                        "readback": "PASS",
                    },
                )
            )

    def test_every_user_document_is_docx_and_dashboard_is_html(self):
        state = self._state()
        self._populate_valid_delivery(state)
        manifest = build_delivery_manifest(state)
        self.assertEqual(manifest["status"], "PASS", manifest["errors"])
        self.assertTrue(any(a["role"] == "session_dashboard" for a in manifest["attachments"]))
        for artifact in manifest["attachments"]:
            if artifact["role"] == "session_dashboard":
                self.assertTrue(artifact["path"].endswith(".html"))
                self.assertEqual(artifact["media_type"], HTML_MIME)
            else:
                self.assertTrue(artifact["path"].endswith(".docx"), artifact)
                self.assertEqual(artifact["media_type"], DOCX_MIME)

    def test_json_cannot_masquerade_as_final_document(self):
        state = self._state()
        with self.assertRaises(ValueError):
            normalize_artifact_record(
                state,
                {
                    "id": "final",
                    "role": "final_legal_text",
                    "path": "artifacts/final_legal_text.json",
                    "readback": "PASS",
                },
            )

    def test_internal_logs_are_excluded_even_if_legacy_record_says_required(self):
        state = self._state()
        self._populate_valid_delivery(state)
        state.artifacts.append(
            {
                "id": "session-integrity",
                "role": "session_integrity",
                "path": "session.integrity.json",
                "readback": "PASS",
                "required": True,
            }
        )
        manifest = build_delivery_manifest(state)
        self.assertEqual(manifest["status"], "PASS", manifest["errors"])
        self.assertNotIn("session_integrity", {a["role"] for a in manifest["attachments"]})
        internal = next(a for a in state.artifacts if a["role"] == "session_integrity")
        self.assertEqual(internal["delivery_class"], "INTERNAL")
        self.assertFalse(internal["required"])
        self.assertGreaterEqual(manifest["internal_records_excluded"], 1)

    def test_non_final_role_cannot_force_itself_into_attachment_set(self):
        state = self._state()
        with self.assertRaises(ValueError):
            normalize_artifact_record(
                state,
                {
                    "id": "receipt",
                    "role": "simulation_receipt",
                    "path": "simulation.json",
                    "readback": "PASS",
                    "delivery_class": ATTACH,
                },
            )

    def test_docx_capabilities_are_fail_closed(self):
        state = self._state(docx_write="UNVERIFIED", docx_readback="UNVERIFIED")
        self._populate_valid_delivery(state)
        ok, errors = delivery_gate(state)
        self.assertFalse(ok)
        self.assertTrue(any("DOCX_WRITE" in error for error in errors), errors)
        self.assertTrue(any("DOCX_READBACK" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

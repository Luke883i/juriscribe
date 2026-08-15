import json
import tempfile
import unittest

from juriscribe.session import Workspace
from juriscribe.session_integrity import CANONICAL_FILENAME


class SessionIntegrityV8Tests(unittest.TestCase):
    def test_workspace_writes_canonical_manifest_and_legacy_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES")
            state = ws.initialize("Genera il capitolo successivo")
            self.assertEqual(ws.integrity_path.name, CANONICAL_FILENAME)
            self.assertTrue(ws.integrity_path.exists())
            self.assertTrue(ws.node_path.exists())
            self.assertTrue(ws.validate_integrity(state)[0])

    def test_canonical_manifest_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES")
            state = ws.initialize("Genera")
            payload = json.loads(ws.integrity_path.read_text(encoding="utf-8"))
            payload["bindings"]["phase"] = "COMPLETE"
            ws.integrity_path.write_text(json.dumps(payload), encoding="utf-8")
            ok, errors = ws.validate_integrity(state)
            self.assertFalse(ok)
            self.assertTrue(any("bindings.phase mismatch" in error for error in errors), errors)

    def test_legacy_projection_remains_checked_under_contract_1_5(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES")
            state = ws.initialize("Genera")
            text = ws.node_path.read_text(encoding="utf-8")
            ws.node_path.write_text(text.replace('JURISCRIBE_PHASE "INITIALIZED"', 'JURISCRIBE_PHASE "COMPLETE"'), encoding="utf-8")
            ok, errors = ws.validate_integrity(state)
            self.assertFalse(ok)
            self.assertTrue(any("node.h JURISCRIBE_PHASE mismatch" in error for error in errors), errors)

    def test_valid_legacy_workspace_migrates_to_canonical_manifest_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES")
            ws.initialize("Genera")
            ws.integrity_path.unlink()
            state = ws.load()
            self.assertTrue(ws.integrity_path.exists())
            self.assertTrue(ws.validate_integrity(state)[0])

    def test_manifest_contains_no_raw_corpus_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(tmp, "SES")
            state = ws.initialize("richiesta-segreta")
            state.corpus.append({"source_id": "S1", "raw": "testo-giuridico-segreto"})
            ws.save(state)
            text = ws.integrity_path.read_text(encoding="utf-8")
            self.assertNotIn("richiesta-segreta", text)
            self.assertNotIn("testo-giuridico-segreto", text)


if __name__ == "__main__":
    unittest.main()

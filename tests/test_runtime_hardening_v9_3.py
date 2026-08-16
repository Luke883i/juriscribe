import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from juriscribe.admission import issue_receipt
from juriscribe.bootstrap import validate_probe_receipt
from juriscribe.pipeline import main as public_main
from juriscribe.pipeline_v9 import bootstrap_after_acceptance, initialize, main as runtime_main, perform_probe
from juriscribe.session import Workspace

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")


def receipt(nonce="1" * 32):
    return issue_receipt(
        CONTRACT, phrase="I ACCEPT", actor_type="human",
        evidence_type="explicit_user_message", user_message="I ACCEPT",
        accepted_at="2026-08-16T10:00:00+00:00", receipt_nonce=nonce,
    )


def probe(r, **caps):
    return perform_probe(
        admission_receipt=r, contract_text=CONTRACT,
        host_capabilities=caps, host="hardening-test",
        probed_at="2026-08-16T10:00:01+00:00",
    )


class RuntimeHardeningV93Tests(unittest.TestCase):
    def test_auto_session_ids_do_not_collide_for_same_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            r1 = receipt("1" * 32); r2 = receipt("2" * 32)
            a = initialize("stessa richiesta", root=tmp, admission_receipt=r1, probe_receipt=probe(r1), contract_text=CONTRACT)
            b = initialize("stessa richiesta", root=tmp, admission_receipt=r2, probe_receipt=probe(r2), contract_text=CONTRACT)
            self.assertNotEqual(a.name, b.name)
            self.assertTrue((a / "state.json").exists()); self.assertTrue((b / "state.json").exists())

    def test_existing_explicit_session_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            r1 = receipt("3" * 32); p1 = probe(r1)
            base = initialize("prima", root=tmp, session_id="SES-fixed", admission_receipt=r1, probe_receipt=p1, contract_text=CONTRACT)
            before = (base / "state.json").read_bytes()
            r2 = receipt("4" * 32)
            with self.assertRaises(FileExistsError):
                initialize("seconda", root=tmp, session_id="SES-fixed", admission_receipt=r2, probe_receipt=probe(r2), contract_text=CONTRACT)
            self.assertEqual(before, (base / "state.json").read_bytes())

    def test_probe_receipt_is_single_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = receipt("5" * 32); p = probe(r)
            initialize("uno", root=tmp, session_id="SES-one", admission_receipt=r, probe_receipt=p, contract_text=CONTRACT)
            with self.assertRaises(PermissionError):
                initialize("due", root=tmp, session_id="SES-two", admission_receipt=r, probe_receipt=p, contract_text=CONTRACT)

    def test_initialize_cannot_add_unprobed_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = receipt("6" * 32); p = probe(r)
            with self.assertRaises(PermissionError):
                initialize("x", root=tmp, session_id="SES-x", admission_receipt=r, probe_receipt=p, contract_text=CONTRACT, host_capabilities={"NEW_SECRET_CAP": "AVAILABLE"})

    def test_probe_nonce_and_digest_are_verified(self):
        r = receipt("7" * 32); p = probe(r)
        self.assertTrue(validate_probe_receipt(p, r, CONTRACT)[0])
        p["probe_nonce"] = "0" * 32
        self.assertFalse(validate_probe_receipt(p, r, CONTRACT)[0])

    def test_initialize_uses_mode_selection_bootstrap_then_active_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = receipt("8" * 32); base = initialize("x", root=tmp, session_id="SES-mode", admission_receipt=r, probe_receipt=probe(r), contract_text=CONTRACT)
            state = Workspace(tmp, "SES-mode").load()
            self.assertEqual(state.phase, "MODE_SELECTION_REQUIRED")
            self.assertEqual(state.admission["bootstrap"]["state"], "MODE_SELECTION_REQUIRED")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(runtime_main(["select-mode", str(base), "--mode", "GREENFIELD"]), 0)
            state = Workspace(tmp, "SES-mode").load()
            self.assertEqual(state.admission["bootstrap"]["state"], "ACTIVE_WORK")

    def test_state_tampering_fails_closed_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = receipt("9" * 32); initialize("x", root=tmp, session_id="SES-integrity", admission_receipt=r, probe_receipt=probe(r), contract_text=CONTRACT)
            path = Path(tmp) / "SES-integrity" / "state.json"
            raw = json.loads(path.read_text(encoding="utf-8")); raw["phase"] = "COMPLETE"; path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(PermissionError):
                Workspace(tmp, "SES-integrity").load()

    def test_fast_bootstrap_keeps_distinct_receipts_and_stops_at_mode_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = bootstrap_after_acceptance(
                "mandato", phrase="I ACCEPT", actor_type="human",
                evidence_type="explicit_user_message", user_message="I ACCEPT",
                root=tmp, session_id="SES-fast", contract_text=CONTRACT,
            )
            self.assertEqual(result["state"], "MODE_SELECTION_REQUIRED")
            state = Workspace(tmp, "SES-fast").load()
            self.assertTrue(state.admission["receipt"]["receipt_id"].startswith("ADM-"))
            self.assertTrue(state.admission["probe_receipt"]["receipt_id"].startswith("PRB-"))
            self.assertEqual(state.admission["bootstrap"]["state"], "MODE_SELECTION_REQUIRED")
            self.assertFalse(state.mode)

    def test_verbose_json_requires_env_and_explicit_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = receipt("a" * 32); base = initialize("x", root=tmp, session_id="SES-verbose", admission_receipt=r, probe_receipt=probe(r), contract_text=CONTRACT)
            with patch.dict(os.environ, {"JURISCRIBE_VERBOSE_JSON": "1"}, clear=False):
                compact = io.StringIO()
                with redirect_stdout(compact): public_main(["interaction-card", str(base)])
                self.assertNotIn('"schema"', compact.getvalue())
                raw = io.StringIO()
                with redirect_stdout(raw): public_main(["--technical-output", "interaction-card", str(base)])
                self.assertIn('"schema"', raw.getvalue())


if __name__ == "__main__":
    unittest.main()

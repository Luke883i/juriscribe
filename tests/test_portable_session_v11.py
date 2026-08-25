from __future__ import annotations

import unittest

from juriscribe.admission import issue_receipt, load_contract_text
from juriscribe.bootstrap import issue_probe_receipt
from juriscribe.portable_session import initialize_memory_session, memory_session_gate


class PortableSessionV11Tests(unittest.TestCase):
    def _receipts(self):
        contract = load_contract_text()
        admission = issue_receipt(
            contract,
            phrase="I ACCEPT",
            actor_type="human",
            evidence_type="explicit_user_message",
            user_message="I ACCEPT",
        )
        probe = issue_probe_receipt(
            admission,
            contract,
            {
                "SESSION_CONTEXT": "AVAILABLE",
                "LOCAL_SCRATCH_IO": "UNAVAILABLE",
                "DOCX_WRITE": "UNAVAILABLE",
                "DOCX_READBACK": "UNAVAILABLE",
            },
            host="unit-memory-host",
        )
        return contract, admission, probe

    def test_memory_session_needs_no_workspace_and_is_truthful(self):
        contract, admission, probe = self._receipts()
        session = initialize_memory_session(
            "mandato test",
            admission_receipt=admission,
            probe_receipt=probe,
            contract_text=contract,
        )
        self.assertEqual(session.state.runtime["storage_backend"], "MEMORY")
        self.assertFalse(session.state.runtime["durable_recovery"])
        self.assertEqual(session.state.runtime["workspace_base"], "")
        self.assertEqual(session.state.phase, "MODE_SELECTION_REQUIRED")
        self.assertTrue(memory_session_gate(session)[0])

    def test_probe_receipt_is_single_use_in_memory(self):
        contract, admission, probe = self._receipts()
        initialize_memory_session("one", admission_receipt=admission, probe_receipt=probe, contract_text=contract)
        with self.assertRaises(PermissionError):
            initialize_memory_session("two", admission_receipt=admission, probe_receipt=probe, contract_text=contract)


if __name__ == "__main__":
    unittest.main()

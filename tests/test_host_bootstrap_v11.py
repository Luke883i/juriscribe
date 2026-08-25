from __future__ import annotations

import json
import unittest
from pathlib import Path

from juriscribe.admission import contract_digest, load_contract_text
from juriscribe.host_bootstrap import (
    HOST_BOOTSTRAP_SCHEMA,
    bootstrap_memory_from_acceptance,
    issue_probe_from_acceptance,
    plan_runtime_transport,
    validate_runtime_binding,
)
from juriscribe.modes import mode_choices
from juriscribe.portable_session import initialize_memory_session


REVISION = "26017bbbd1eb69752e14867f45f1aedc7fcebbec"
OTHER_REVISION = "a12d1a1c65bd875dd8b0e2a398542310746482c9"


class HostBootstrapV11Tests(unittest.TestCase):
    def _caps(self, **overrides):
        caps = {
            "RUNTIME_IMPORT": "UNAVAILABLE",
            "REPOSITORY_READ": "AVAILABLE",
            "PYTHON_EXECUTION": "AVAILABLE",
            "SOURCE_TO_RUNTIME_BRIDGE": "AVAILABLE",
            "SESSION_CONTEXT": "AVAILABLE",
            "LOCAL_SCRATCH_IO": "UNAVAILABLE",
            "DOCX_WRITE": "UNAVAILABLE",
            "DOCX_READBACK": "UNAVAILABLE",
        }
        caps.update(overrides)
        return caps

    def _context(self):
        contract = load_contract_text()
        return contract, contract_digest(contract)

    def test_transport_policy_is_pre_admission_discoverable(self):
        admission = json.loads(Path("ADMISSION.json").read_text(encoding="utf-8"))
        policy = admission["host_runtime_transport"]
        self.assertEqual(policy["schema"], "juriscribe-host-runtime-transport/v1")
        self.assertTrue(policy["pinned_source_materialization_after_exact_acceptance"])
        self.assertTrue(policy["revision_binding_required"])
        self.assertTrue(policy["acceptance_context_binding_required"])
        self.assertTrue(policy["retained_human_acceptance_may_resume_bootstrap"])
        self.assertFalse(policy["second_human_acceptance_required_after_delayed_materialization"])
        self.assertTrue(policy["receipt_simulation_forbidden"])

    def test_repository_read_alone_is_not_runtime_execution(self):
        plan = plan_runtime_transport(
            self._caps(SOURCE_TO_RUNTIME_BRIDGE="UNVERIFIED"),
            resolved_revision=REVISION,
        )
        self.assertEqual(plan["decision"], "BLOCKED")
        self.assertIn("SOURCE_TO_RUNTIME_BRIDGE", plan["missing"])

    def test_pinned_source_materialization_requires_full_bridge(self):
        plan = plan_runtime_transport(self._caps(), resolved_revision=REVISION)
        self.assertEqual(plan["decision"], "MATERIALIZE_PINNED_RUNTIME_SOURCE")
        self.assertEqual(plan["resolved_revision"], REVISION)
        self.assertTrue(plan["revision_binding_required"])
        self.assertFalse(plan["receipt_simulation_allowed"])

    def test_installed_runtime_is_preferred_only_when_revision_bound(self):
        plan = plan_runtime_transport(
            self._caps(RUNTIME_IMPORT="AVAILABLE"),
            resolved_revision=REVISION,
            runtime_revision=REVISION,
        )
        self.assertEqual(plan["decision"], "USE_INSTALLED_RUNTIME")
        self.assertEqual(plan["missing"], [])

    def test_unbound_installed_runtime_falls_back_to_pinned_source(self):
        plan = plan_runtime_transport(
            self._caps(RUNTIME_IMPORT="AVAILABLE"),
            resolved_revision=REVISION,
        )
        self.assertEqual(plan["decision"], "MATERIALIZE_PINNED_RUNTIME_SOURCE")
        self.assertEqual(plan["installed_runtime_binding"], "runtime revision unverified")

    def test_runtime_revision_mismatch_is_rejected(self):
        with self.assertRaises(PermissionError):
            validate_runtime_binding(REVISION, OTHER_REVISION)

    def test_probe_can_resume_from_retained_exact_acceptance(self):
        contract, csha = self._context()
        result = issue_probe_from_acceptance(
            user_message="I ACCEPT",
            host_capabilities=self._caps(),
            host="unit-local-gpt",
            resolved_revision=REVISION,
            runtime_revision=REVISION,
            presented_contract_sha256=csha,
            contract_text=contract,
        )
        self.assertEqual(result["schema"], HOST_BOOTSTRAP_SCHEMA)
        self.assertEqual(result["state"], "INITIALIZE_REQUIRED")
        self.assertEqual(result["resolved_revision"], REVISION)
        self.assertEqual(result["contract_sha256"], csha)
        self.assertTrue(result["admission_receipt"]["receipt_id"].startswith("ADM-"))
        self.assertTrue(result["probe_receipt"]["receipt_id"].startswith("PRB-"))
        self.assertEqual(result["probe_receipt"]["capabilities"]["LOCAL_SCRATCH_IO"], "UNAVAILABLE")

    def test_probe_resume_rejects_non_exact_human_acceptance(self):
        contract, csha = self._context()
        with self.assertRaises(PermissionError):
            issue_probe_from_acceptance(
                user_message="I ACCEPT please",
                host_capabilities=self._caps(),
                host="unit-local-gpt",
                resolved_revision=REVISION,
                runtime_revision=REVISION,
                presented_contract_sha256=csha,
                contract_text=contract,
            )

    def test_probe_resume_rejects_contract_rebind(self):
        contract, _ = self._context()
        with self.assertRaises(PermissionError):
            issue_probe_from_acceptance(
                user_message="I ACCEPT",
                host_capabilities=self._caps(),
                host="unit-local-gpt",
                resolved_revision=REVISION,
                runtime_revision=REVISION,
                presented_contract_sha256="0" * 64,
                contract_text=contract,
            )

    def test_memory_fast_path_initializes_without_filesystem(self):
        contract, csha = self._context()
        result = bootstrap_memory_from_acceptance(
            "mandato host locale",
            user_message="I ACCEPT",
            host_capabilities=self._caps(),
            host="unit-local-gpt",
            resolved_revision=REVISION,
            runtime_revision=REVISION,
            presented_contract_sha256=csha,
            contract_text=contract,
        )
        status = result.public_status()
        self.assertEqual(status["state"], "MODE_SELECTION_REQUIRED")
        self.assertEqual(status["backend"], "MEMORY")
        self.assertEqual(status["resolved_revision"], REVISION)
        self.assertFalse(status["durable_recovery"])
        self.assertEqual(status["choices"], [*mode_choices(), "ALTRO"])
        self.assertEqual(result.session.state.runtime["storage_backend"], "MEMORY")
        self.assertEqual(result.session.state.runtime["workspace_base"], "")
        self.assertEqual(result.session.state.runtime["source_revision"], REVISION)
        self.assertEqual(result.session.state.runtime["contract_sha256"], csha)

    def test_memory_fast_path_requires_real_session_context(self):
        contract, csha = self._context()
        with self.assertRaises(PermissionError):
            bootstrap_memory_from_acceptance(
                "mandato host locale",
                user_message="I ACCEPT",
                host_capabilities=self._caps(SESSION_CONTEXT="UNAVAILABLE"),
                host="unit-local-gpt",
                resolved_revision=REVISION,
                runtime_revision=REVISION,
                presented_contract_sha256=csha,
                contract_text=contract,
            )

    def test_memory_probe_receipt_is_consumed_once(self):
        contract, csha = self._context()
        result = bootstrap_memory_from_acceptance(
            "one",
            user_message="I ACCEPT",
            host_capabilities=self._caps(),
            host="unit-local-gpt",
            resolved_revision=REVISION,
            runtime_revision=REVISION,
            presented_contract_sha256=csha,
            contract_text=contract,
        )
        with self.assertRaises(PermissionError):
            initialize_memory_session(
                "two",
                admission_receipt=result.admission_receipt,
                probe_receipt=result.probe_receipt,
                contract_text=contract,
            )

    def test_unknown_capability_state_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_runtime_transport({"RUNTIME_IMPORT": "MAYBE"}, resolved_revision=REVISION)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from juriscribe.host_bootstrap import (
    CANONICAL_REPOSITORY_URL,
    classify_host_reachability,
    parse_bootstrap_intent,
    plan_runtime_transport,
)
from juriscribe.modes import mode_choices

REV = "26017bbbd1eb69752e14867f45f1aedc7fcebbec"


class PhysicalConvergenceV11Tests(unittest.TestCase):
    def base_caps(self, **overrides):
        caps = {
            "RUNTIME_IMPORT": "UNAVAILABLE",
            "REPOSITORY_READ": "AVAILABLE",
            "PYTHON_EXECUTION": "AVAILABLE",
            "SOURCE_TO_RUNTIME_BRIDGE": "AVAILABLE",
            "SESSION_CONTEXT": "AVAILABLE",
            "LOCAL_SCRATCH_IO": "UNAVAILABLE",
            "DOCX_WRITE": "UNVERIFIED",
            "DOCX_READBACK": "UNVERIFIED",
            "CHAT_ATTACHMENT_WRITE": "UNVERIFIED",
            "LOCAL_FILE_DELIVERY": "UNVERIFIED",
        }
        caps.update(overrides)
        return caps

    def test_bootstrap_intent_is_bilingual_and_repo_defaulted(self):
        en = parse_bootstrap_intent("Initialize Juriscribe")
        it = parse_bootstrap_intent("Inizializza Juriscribe https://github.com/Luke883i/juriscribe")
        self.assertEqual(en["repository"], CANONICAL_REPOSITORY_URL)
        self.assertEqual(it["repository"], CANONICAL_REPOSITORY_URL)
        self.assertFalse(en["bypasses_acceptance"])
        self.assertEqual((en["language"], it["language"]), ("en", "it"))

    def test_noncanonical_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_bootstrap_intent("Initialize Juriscribe https://github.com/example/other")

    def test_public_source_bootstrap_needs_no_connector(self):
        plan = plan_runtime_transport(self.base_caps(), resolved_revision=REV)
        self.assertEqual(plan["decision"], "MATERIALIZE_PINNED_RUNTIME_SOURCE")
        self.assertEqual(plan["materialization_scope"], "BOOTSTRAP_MINIMAL")
        self.assertFalse(plan["repository_connector_required"])
        self.assertTrue(plan["reachability"]["readiness"]["BOOTSTRAP_READY"])

    def test_transport_fails_closed_without_state_carrier(self):
        plan = plan_runtime_transport(self.base_caps(SESSION_CONTEXT="UNAVAILABLE", LOCAL_SCRATCH_IO="UNAVAILABLE"), resolved_revision=REV)
        self.assertEqual(plan["decision"], "BLOCKED")
        self.assertIn("SESSION_CONTEXT_OR_LOCAL_SCRATCH_IO", plan["missing"])

    def test_memory_work_does_not_claim_materialization_or_recovery(self):
        r = classify_host_reachability(self.base_caps(), revision_pinned=True, contract_pinned=True)
        self.assertTrue(r.bootstrap_ready)
        self.assertTrue(r.work_ready)
        self.assertFalse(r.materialization_ready)
        self.assertFalse(r.delivery_ready)
        self.assertFalse(r.recovery_ready)

    def test_filesystem_host_can_reach_delivery_and_recovery(self):
        caps = self.base_caps(
            SESSION_CONTEXT="UNAVAILABLE",
            LOCAL_SCRATCH_IO="AVAILABLE",
            DOCX_WRITE="AVAILABLE",
            DOCX_READBACK="AVAILABLE",
            LOCAL_FILE_DELIVERY="AVAILABLE",
        )
        r = classify_host_reachability(caps, revision_pinned=True, contract_pinned=True)
        self.assertTrue(r.bootstrap_ready)
        self.assertTrue(r.materialization_ready)
        self.assertTrue(r.delivery_ready)
        self.assertTrue(r.recovery_ready)

    def test_platform_identity_never_changes_decision(self):
        caps = self.base_caps()
        a = classify_host_reachability(caps, revision_pinned=True, contract_pinned=True, provider="A", browser="Safari", os_name="macOS")
        b = classify_host_reachability(caps, revision_pinned=True, contract_pinned=True, provider="B", browser="Edge", os_name="Windows")
        self.assertEqual(
            (a.discovery_ready, a.bootstrap_ready, a.work_ready, a.materialization_ready, a.delivery_ready, a.recovery_ready),
            (b.discovery_ready, b.bootstrap_ready, b.work_ready, b.materialization_ready, b.delivery_ready, b.recovery_ready),
        )
        self.assertFalse(a.as_dict()["platform_identity_affects_decision"])

    def test_four_modes_are_runtime_derived(self):
        self.assertEqual(mode_choices(), ["CONTINUATION", "GREENFIELD", "REVIEW", "COMPRESSION & CONSOLIDATION"])


if __name__ == "__main__":
    unittest.main()

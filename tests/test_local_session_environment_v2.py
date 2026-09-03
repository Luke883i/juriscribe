from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("host_environment", ROOT / "juriscribe" / "host_environment.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def policy():
    return {
        "pre_admission_allowlist": ["AGENTS.md", "ISENECA_ACCESS_CONTRACT.md", "ADMISSION.json"],
        "local_session_environment": {
            "schema": mod.ENVIRONMENT_SCHEMA,
            "profile": mod.ENVIRONMENT_PROFILE,
            "identity": "REVISION_BOUND_LOCAL_ENVIRONMENT_INSIDE_CURRENT_CHAT",
            "authority": mod.ENVIRONMENT_AUTHORITY,
            "scientific_authority": False,
            "runtime_authority_nodes_added": 0,
            "root": "docs/host/LOCAL_SESSION_ENVIRONMENT.md",
            "boot_prompt": "docs/host/LOCAL_HOST_PROMPT.md",
            "boot_prompt_max_chars": 8000,
            "resolver": "juriscribe.host_environment.activation_plan",
            "validator": "juriscribe.host_environment.validate_environment_files",
            "contract_nodes": {
                "root": "docs/host/LOCAL_SESSION_ENVIRONMENT.md",
                "execution": "docs/host/EXECUTION.md",
                "state": "docs/host/STATE.md",
                "surface": "docs/host/SURFACE.md",
                "failure_recovery": "docs/host/FAILURE_RECOVERY.md",
            },
            "activation": {key: list(value) for key, value in mod.ACTIVATION.items()},
            "same_revision_required": True,
            "session_local_verified_cache_allowed": True,
            "live_main_rebind_forbidden": True,
            "runtime_state_synthesis_forbidden": True,
            "receipt_simulation_forbidden": True,
            "local_sufficiency_required_before_blocker": True,
        },
    }


class CognitiveEnvironmentTests(unittest.TestCase):
    def test_activation_compatibility_remains_exact(self):
        p = policy()
        self.assertEqual(mod.activation_plan(p, "ACTIVE_SESSION")["node_keys"], ["root", "state", "surface"])
        self.assertEqual(mod.activation_plan(p, "ACTIVE_SESSION")["normative_policy_nodes"], 1)

    def test_execution_profiles_are_not_modes(self):
        card = mod.execution_profile_choices()
        self.assertEqual([x["id"] for x in card["choices"]], ["LEAN", "ATTESTED"])
        self.assertFalse(card["scientific_mode"])
        self.assertTrue(card["auto_select_forbidden"])

    def test_lean_degrades_attestation_not_method(self):
        plan = mod.graded_execution_plan("LEAN", method_available=True, runtime_ready=False)
        self.assertEqual(plan["action"], "RUN_LEAN_METHOD")
        self.assertEqual(plan["attestation"], "METHOD_GUIDED")
        self.assertFalse(plan["runtime_receipts_may_be_claimed"])
        self.assertTrue(plan["promotion_requires_replay"])

    def test_attested_offers_lean_instead_of_dead_end(self):
        plan = mod.graded_execution_plan("ATTESTED", method_available=True, runtime_ready=False)
        self.assertEqual(plan["action"], "OFFER_LEAN")
        self.assertFalse(plan["runtime_complete_may_be_claimed"])

    def test_complete_cannot_be_method_guided(self):
        with self.assertRaises(PermissionError):
            mod.artifact_trajectory(content_ready=True, materialized=True, delivered=True, runtime_attested=False, complete=True)

    def test_promotion_is_replay_not_label(self):
        plan = mod.promotion_plan(method_work_exists=True, runtime_ready=True)
        self.assertEqual(plan["action"], "REPLAY_REQUIRED")
        self.assertFalse(plan["prior_method_work_is_proof"])

    def test_solver_never_requires_gh_and_preserves_unverified(self):
        caps = {
            "RUNTIME_IMPORT": "UNAVAILABLE",
            "REPOSITORY_READ": "AVAILABLE",
            "CONNECTED_REPOSITORY_READ": "AVAILABLE",
            "PUBLIC_REPOSITORY_READ": "AVAILABLE",
            "PYTHON_EXECUTION": "AVAILABLE",
            "LOCAL_SCRATCH_IO": "AVAILABLE",
            "SOURCE_TO_RUNTIME_BRIDGE": "UNVERIFIED",
        }
        plan = mod.plan_local_bootstrap_search(caps, method_available=True)
        self.assertFalse(plan["gh_cli_required"])
        self.assertFalse(plan["unverified_is_unavailable"])
        self.assertIn("PROBE_SOURCE_TO_RUNTIME_BRIDGE", plan["candidate_classes"])
        self.assertIn("FULL_PINNED_RUNTIME_PACKAGE", plan["candidate_classes"])
        self.assertEqual(plan["candidate_classes"][-1], "LEAN_METHOD_KERNEL")

    def test_blocker_requires_path_exhaustion(self):
        plan = mod.plan_local_bootstrap_search({
            "REPOSITORY_READ": "AVAILABLE",
            "PYTHON_EXECUTION": "AVAILABLE",
            "LOCAL_SCRATCH_IO": "AVAILABLE",
            "SOURCE_TO_RUNTIME_BRIDGE": "UNVERIFIED",
        }, method_available=True)
        self.assertFalse(mod.local_blocker_status(plan, [], requested_profile="ATTESTED")["blocker_allowed"])
        attempts = [{"class": c, "attempted": True} for c in plan["candidate_classes"]]
        self.assertEqual(mod.local_blocker_status(plan, attempts, requested_profile="ATTESTED")["action"], "OFFER_LEAN")

    def test_method_unavailable_can_eventually_block(self):
        plan = mod.plan_local_bootstrap_search({
            "REPOSITORY_READ": "UNAVAILABLE",
            "PYTHON_EXECUTION": "UNAVAILABLE",
            "LOCAL_SCRATCH_IO": "UNAVAILABLE",
        }, method_available=False)
        status = mod.local_blocker_status(plan, [], requested_profile="ATTESTED")
        self.assertTrue(status["blocker_allowed"])


if __name__ == "__main__":
    unittest.main()

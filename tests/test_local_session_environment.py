from __future__ import annotations

import importlib.util
import json
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


class LocalEnvironmentTests(unittest.TestCase):
    def test_exact_activation_is_lifecycle_scoped(self):
        p = policy()
        self.assertEqual(mod.activation_plan(p, "POST_ACCEPTANCE_BOOTSTRAP")["node_keys"], ["root", "execution"])
        self.assertEqual(mod.activation_plan(p, "ACTIVE_SESSION")["node_keys"], ["root", "state", "surface"])
        self.assertEqual(mod.activation_plan(p, "FAILURE_OR_RECOVERY")["node_keys"], ["root", "state", "failure_recovery"])
        self.assertEqual(mod.activation_plan(p, "REBIND_OR_TRANSPORT_FAILURE")["node_keys"], ["root", "execution", "failure_recovery"])

    def test_prompt_is_not_pre_admission_or_normative_node(self):
        p = policy()
        mod.validate_environment_policy(p)
        self.assertNotIn(p["local_session_environment"]["boot_prompt"], p["pre_admission_allowlist"])
        self.assertNotIn(p["local_session_environment"]["boot_prompt"], p["local_session_environment"]["contract_nodes"].values())

    def test_new_authority_fails_closed(self):
        p = json.loads(json.dumps(policy()))
        p["local_session_environment"]["runtime_authority_nodes_added"] = 1
        with self.assertRaises(ValueError):
            mod.validate_environment_policy(p)

    def test_live_main_rebind_relaxation_fails_closed(self):
        p = json.loads(json.dumps(policy()))
        p["local_session_environment"]["live_main_rebind_forbidden"] = False
        with self.assertRaises(ValueError):
            mod.validate_environment_policy(p)

    def test_activation_drift_fails_closed(self):
        p = json.loads(json.dumps(policy()))
        p["local_session_environment"]["activation"]["ACTIVE_SESSION"].append("execution")
        with self.assertRaises(ValueError):
            mod.validate_environment_policy(p)

    def test_prompt_overflow_fails_closed(self):
        p = json.loads(json.dumps(policy()))
        p["local_session_environment"]["boot_prompt_max_chars"] = 8001
        with self.assertRaises(ValueError):
            mod.validate_environment_policy(p)

    def test_repository_graph_validates(self):
        p = policy()
        result = mod.validate_environment_files(ROOT, p)
        self.assertEqual(result["runtime_authority_nodes_added"], 0)
        self.assertLessEqual(result["prompt_chars"], 8000)
        self.assertEqual(set(result["nodes"]), set(mod.CONTRACT_NODE_KEYS))


if __name__ == "__main__":
    unittest.main()

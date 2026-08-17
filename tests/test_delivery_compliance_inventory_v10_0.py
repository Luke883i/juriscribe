import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from juriscribe.chat_delivery import build_chat_delivery_manifest
from juriscribe.conversation_contract import build_final_artifact_inference_trace, initialize_pipeline_lock
from juriscribe.delivery_compliance import build_delivery_compliance_inventory, delivery_compliance_gate
from juriscribe.modes import CONTINUATION, required_artifact_roles

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class MechanicalDeliveryComplianceV100Tests(unittest.TestCase):
    def _state(self, root: Path):
        state = SimpleNamespace(
            mode=CONTINUATION,
            setup={},
            runtime={"workspace_base": str(root), "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"}},
            request={"raw": "Continua il capitolo", "summary": "Continua il capitolo", "request_id": "REQ-COMPLIANCE"},
            mode_selection={"digest": "MODE-COMPLIANCE"},
            mode_contract={"status": "READY"},
            editorial_standard={"status": "READY", "standard_id": "JURISCRIBE_LEGAL_EDITORIAL_CORE_V2"},
            corpus=[],
            sources=[{"id": "S1", "title": "Fonte primaria"}],
            bibliography={"available": False, "status": "NOT_AVAILABLE", "entries": []},
            epistemic_units=[{"id": "U1", "kind": "RULE", "text": "Regola materiale", "material": True}],
            relations=[],
            reticulum={"status": "PASS"},
            generation_contract={
                "status": "READY",
                "contract_digest": "GC-COMPLIANCE",
                "governance_profile": "JURISCRIBE_GENERATION_GOVERNANCE_V1",
                "generation_configuration": {"status": "READY", "profile": "JURISCRIBE_GENERATION_CONFIGURATION_V1"},
            },
            continuation={"plan": {"status": "PASS"}, "coverage": {"status": "PASS"}, "status": "PASS"},
            drafts=[{"digest": "CAND-COMPLIANCE", "stage": "COMPRESSED_FINAL"}],
            review={"cycles": [{"cycle": 1, "status": "PASS", "findings": []}], "status": "SATURATED", "saturation": {"status": "PASS"}},
            final_review={"status": "PASS"},
            provenance={"status": "PASS", "entries": [{"kind": "SOURCE"}]},
            contradictions=[], mining={}, style_profile={},
            source_intelligence={"coverage_status": "PASS"},
            claim_ledger=[{"id": "C1", "text": "Claim materiale", "material": True, "support_source_ids": ["S1"]}],
            artifact_evidence=[{"evidence_id": "E1", "claim_id": "C1", "source_ids": ["S1"], "artifact_role": "final_chapter", "artifact_locator": "§ 1"}],
            quality={"status": "PASS", "plagiarism": {"status": "PASS", "policy_id": "JURISCRIBE_ANTI_PLAGIARISM_V1"}},
            benchmark={},
            simulations={"status": "PASS", "cases": 10000},
            compression={"status": "PASS"},
            limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={}, artifacts=[], completion={}, node_integrity={}, interaction={},
        )
        initialize_pipeline_lock(state)
        expected_docs = sorted(required_artifact_roles(CONTINUATION, {}) - {"session_dashboard"})
        state.strategy["standard_artifact_autopilot"] = {
            "schema": "juriscribe-standard-artifact-autopilot/v1",
            "profile": "JURISCRIBE_STANDARD_ARTIFACT_AUTOPILOT_V1",
            "status": "PASS",
            "runtime_owned": True,
            "required_roles": expected_docs,
            "materialized_roles": expected_docs,
        }
        trace = build_final_artifact_inference_trace(state, "final_chapter", "CAND-COMPLIANCE")
        for role in expected_docs:
            artifact = {
                "id": f"auto-{role}", "role": role, "path": str(root / "artifacts" / f"{role}.docx"),
                "readback": "PASS", "format": "DOCX", "media_type": DOCX_MIME, "delivery_class": "ATTACH",
                "auto_materialized_by_runtime": True,
            }
            if role in {"evidence_dossier", "source_register", "inference_register", "transformation_ledger"}:
                artifact["semantic_materialization"] = {"status": "PASS"}
            if role == "final_chapter":
                artifact["inference_trace"] = trace
                artifact["artifact_generation_governance"] = {"status": "PASS"}
            state.artifacts.append(artifact)
        state.artifacts.append({
            "id": "dashboard", "role": "session_dashboard", "path": str(root / "artifacts" / "session-dashboard.html"),
            "readback": "PASS", "format": "HTML", "media_type": "text/html", "delivery_class": "SURFACE",
        })
        return state

    def test_inventory_enumerates_material_and_intermediate_epistemic_logic(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            inventory = build_delivery_compliance_inventory(state)
            self.assertEqual(inventory["status"], "PASS", inventory["blocking_errors"])
            self.assertTrue(inventory["release_authorized"])
            self.assertTrue(inventory["atomic_release"])
            epistemic_ids = {row["id"] for row in inventory["epistemic_artifacts"]}
            for required in {
                "mode_contract", "editorial_standard", "atomic_mining", "epistemic_reticulum", "claim_ledger",
                "artifact_evidence", "source_register_logic", "inference_structure", "generation_contract",
                "generation_configuration", "continuation_plan", "continuation_coverage", "scientific_editorial_review",
                "quality_audit", "anti_plagiarism", "simulations", "compression", "provenance", "final_severe_review",
                "natural_language_pipeline", "standard_artifact_autopilot",
            }:
                self.assertIn(required, epistemic_ids)
            material_roles = {row["role"] for row in inventory["material_artifacts"]}
            self.assertEqual(material_roles, required_artifact_roles(CONTINUATION, {}))
            self.assertTrue(all(row["eligible_for_delivery"] for row in inventory["material_artifacts"]))

    def test_missing_evidence_withholds_every_docx_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp)); state.artifact_evidence = []
            ok, errors = delivery_compliance_gate(state)
            self.assertFalse(ok); self.assertTrue(any("artifact_evidence" in error for error in errors), errors)
            manifest = build_chat_delivery_manifest(state)
            self.assertEqual(manifest["status"], "FAIL")
            self.assertEqual(manifest["attachments"], [])
            self.assertEqual(sorted(manifest["withheld_attachments"]), sorted(required_artifact_roles(CONTINUATION, {}) - {"session_dashboard"}))

    def test_autopilot_role_drift_withholds_release_even_if_files_are_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            state.strategy["standard_artifact_autopilot"]["materialized_roles"] = ["final_chapter"]
            inventory = build_delivery_compliance_inventory(state)
            self.assertEqual(inventory["status"], "FAIL")
            self.assertFalse(inventory["release_authorized"])
            self.assertIn("standard_artifact_autopilot", {row["id"] for row in inventory["epistemic_artifacts"] if row["status"] == "FAIL"})
            self.assertEqual(build_chat_delivery_manifest(state)["attachments"], [])

    def test_source_and_reticulum_failures_are_release_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp)); state.sources = []; state.source_intelligence = {"coverage_status": "GAPS_OPEN"}; state.reticulum = {"status": "FAIL"}
            inventory = build_delivery_compliance_inventory(state)
            failures = {row["id"] for row in inventory["epistemic_artifacts"] if row["status"] == "FAIL"}
            self.assertIn("source_register_logic", failures)
            self.assertIn("epistemic_reticulum", failures)
            self.assertFalse(inventory["release_authorized"])

    def test_dashboard_is_part_of_inventory_but_never_chat_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            manifest = build_chat_delivery_manifest(state)
            self.assertEqual(manifest["status"], "PASS", manifest["errors"])
            self.assertNotIn("session_dashboard", {item["role"] for item in manifest["attachments"]})
            dashboard = next(row for row in manifest["mechanical_delivery_compliance"]["material_artifacts"] if row["role"] == "session_dashboard")
            self.assertEqual(dashboard["kind"], "HTML_SURFACE")
            self.assertEqual(dashboard["release_placement"], "SESSION_DASHBOARD_SURFACE")

    def test_missing_dashboard_blocks_atomic_docx_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp)); state.artifacts = [item for item in state.artifacts if item["role"] != "session_dashboard"]
            manifest = build_chat_delivery_manifest(state)
            self.assertEqual(manifest["status"], "FAIL")
            self.assertEqual(manifest["attachments"], [])
            self.assertTrue(any("session_dashboard" in error for error in manifest["errors"]), manifest["errors"])


if __name__ == "__main__":
    unittest.main()

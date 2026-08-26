from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from juriscribe.consolidation import (
    MUTATION_SCHEMA,
    SATURATION_SCHEMA,
    build_joint_reticulum,
    build_lossless_inventory,
    build_refactoring_contract,
    validate_lossless_inventory,
    validate_mutation_receipt,
    validate_saturation_receipt,
)
from juriscribe.consolidation_completion import evaluate_completion
from juriscribe.modes import COMPRESSION_CONSOLIDATION, MODES, required_artifact_requirements
from juriscribe.runtime_v11 import (
    apply_setup,
    calibrate_refactoring,
    consolidation_gate,
    freeze_dods,
    ingest_and_mine,
    record_consolidation_saturation,
    record_simulation,
    register_refactoring_plan,
    register_semantic_mining,
    seal_refined_candidate,
    select_mode,
)
from juriscribe.runtime_v11_review import record_final_review, record_provenance, record_review_cycle
from juriscribe.session import SessionState

FAMILIES = [
    "LOSSLESSNESS", "CANONICAL_IMMUTABILITY", "RETICULUM", "GAP_EVIDENCE",
    "ARGUMENT_STRENGTH", "LOCAL_PROGRESSION", "RETICULAR_PROGRESSION",
    "ANOMALY_EDGE", "MINIMALITY", "MATERIALIZATION_READINESS",
]


class CompressionConsolidationV11Tests(unittest.TestCase):
    def _state(self, root):
        state = SessionState(
            session_id="SES-CC-TEST",
            request={"raw": "Consolida i candidati rispetto al canonico", "summary": "C&C test", "request_id": "REQ-CC", "atoms": []},
        )
        state.runtime = {
            "workspace_base": str(Path(root) / state.session_id),
            "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"},
        }
        return state

    def _semantic_payload(self, state):
        units = []
        for sid, inv in state.strategy["consolidation"]["inventories"].items():
            for obj in inv["objects"]:
                units.append({
                    "id": "U-" + obj["id"],
                    "object_id": obj["id"],
                    "source_id": sid,
                    "source_locator": obj["locator"],
                    "material_role": inv["role"],
                    "kind": "ARGUMENT",
                    "text": obj["text"],
                    "material": True,
                })
        canonical = next(u for u in units if u["material_role"] == "canonical_material")
        relations = []
        for index, unit in enumerate(units, 1):
            if unit is canonical:
                continue
            relations.append({
                "id": f"R-{index}",
                "source": canonical["id"],
                "predicate": "SUPPORTS",
                "target": unit["id"],
                "rationale": "reference conditioning",
            })
        return units, relations

    def _prepare_plan(self, root):
        state = self._state(root)
        select_mode(state, "COMPRESSION & CONSOLIDATION")
        ingest_and_mine(state, "Regola canonica.\n\nMetodo canonico.", source_id="canon-A", role="canonical_material")
        ingest_and_mine(state, "Argomento candidato A ripetuto.\n\nConclusione A.", source_id="cand-A", role="candidate_material")
        ingest_and_mine(state, "Argomento candidato B.\n\nConclusione B ridondante.", source_id="cand-B", role="candidate_material")
        units, relations = self._semantic_payload(state)
        report = register_semantic_mining(state, units, relations)
        self.assertEqual(report["status"], "PASS")
        apply_setup(state)
        freeze_dods(state)
        candidate_units = [u for u in units if u["material_role"] == "candidate_material"]
        gaps = []
        ops = []
        for i, unit in enumerate(candidate_units, 1):
            gid = f"GAP-{i}"
            gaps.append({
                "id": gid,
                "unit_id": unit["id"],
                "kind": "EDITORIAL",
                "severity": "MATERIAL",
                "evidence": "gap evidenced against canonical method",
                "reference": "canon-A",
            })
            ops.append({
                "id": f"OP-{i}",
                "unit_id": unit["id"],
                "operation": "CLARIFY",
                "gap_ids": [gid],
                "rationale": "minimal local clarification",
                "expected_benefit": "clearer progression",
                "degradation_risk": "LOW",
            })
        plan = register_refactoring_plan(state, gaps=gaps, operations=ops)
        return state, units, relations, plan

    def _saturate(self, state, plan):
        mutation = {
            "schema": MUTATION_SCHEMA,
            "plan_digest": plan["digest"],
            "reticulum_digest": state.reticulum["digest"],
            "cases": 10_000_000,
            "families": FAMILIES,
            "failures": 0,
        }
        record_simulation(state, mutation)
        saturation = {
            "schema": SATURATION_SCHEMA,
            "plan_digest": plan["digest"],
            "no_novelty_tail": 1000,
            "no_better_compression_tail": 1000,
            "semantic_recall": 1.0,
            "relation_recall": 1.0,
            "canonical_unchanged": True,
        }
        record_consolidation_saturation(state, saturation)

    def _seal_all(self, state):
        seal_refined_candidate(
            state,
            source_id="cand-A",
            text="Argomento candidato A chiarito.\n\nConclusione A.",
            semantic_recall=1.0,
            relation_recall=1.0,
        )
        seal_refined_candidate(
            state,
            source_id="cand-B",
            text="Argomento candidato B chiarito.\n\nConclusione B.",
            semantic_recall=1.0,
            relation_recall=1.0,
        )

    def _readiness_dimensions(self):
        return {
            key: "PASS"
            for key in [
                "scientific_consistency", "editorial_coherence", "argument_strength",
                "local_progression", "reticular_progression", "semantic_losslessness",
                "canonical_conditioning",
            ]
        }

    def test_modes_are_dynamic_and_cc_is_canonical(self):
        self.assertIn(COMPRESSION_CONSOLIDATION, MODES)

    def test_human_like_two_candidate_journey_and_staleness(self):
        with tempfile.TemporaryDirectory() as td:
            state, _, _, plan = self._prepare_plan(td)
            reqs = required_artifact_requirements(state.mode, state.setup, state.corpus)
            refined = [x for x in reqs if x["role"] == "refined_candidate"]
            self.assertEqual({x["instance_key"] for x in refined}, {"cand-A", "cand-B"})
            self._saturate(state, plan)
            self._seal_all(state)
            self.assertEqual(record_review_cycle(state, {"dimensions": self._readiness_dimensions(), "blockers": []})["status"], "PASS")
            dispositions = []
            for op in plan["operations"]:
                dispositions.append({"id": "PRV-" + op["id"], "operation_id": op["id"], "disposition": "APPLIED_MINIMALLY"})
            dispositions.extend([
                {"id": "PRV-SRC-A", "source_id": "cand-A", "disposition": "REFINED"},
                {"id": "PRV-SRC-B", "source_id": "cand-B", "disposition": "REFINED"},
            ])
            self.assertEqual(record_provenance(state, {"dispositions": dispositions})["status"], "PASS")
            final = record_final_review(state, {
                "status": "PASS",
                "plan_digest": plan["digest"],
                "reticulum_digest": state.reticulum["digest"],
                "findings": [],
            })
            self.assertEqual(final["status"], "PASS")
            evaluate_completion(state)
            self.assertTrue(state.completion["eligible"], state.completion.get("reason"))
            refined_artifacts = [a for a in state.artifacts if a.get("role") == "refined_candidate"]
            self.assertEqual({a.get("instance_key") for a in refined_artifacts}, {"cand-A", "cand-B"})
            self.assertTrue(all(Path(a["path"]).exists() for a in refined_artifacts))
            self.assertNotIn("canon-A", {a.get("instance_key") for a in refined_artifacts})

            calibration = calibrate_refactoring(state, [{"decision": "preserva formulazione A", "material": True}])
            self.assertTrue(calibration["material_change"])
            cc = state.strategy["consolidation"]
            self.assertFalse(cc["refactoring_contract"])
            self.assertFalse(cc["mutation_receipt"])
            self.assertFalse(cc["saturation"])
            self.assertFalse(cc["refined_candidates"])
            self.assertFalse(cc["peer_review_readiness"])
            evaluate_completion(state)
            self.assertFalse(state.completion["eligible"])

    def test_reticulum_digest_binds_payload_and_rejects_source_spoof(self):
        canonical = build_lossless_inventory("Canonico.", source_id="canon", role="canonical_material")
        candidate = build_lossless_inventory("Candidato.", source_id="cand", role="candidate_material")
        units = [
            {"id": "U-C", "object_id": canonical["objects"][0]["id"], "source_id": "canon", "material_role": "canonical_material", "text": "Canonico."},
            {"id": "U-X", "object_id": candidate["objects"][0]["id"], "source_id": "cand", "material_role": "candidate_material", "text": "Candidato."},
        ]
        relations = [{"id": "R-1", "source": "U-C", "target": "U-X", "predicate": "CONDITIONS"}]
        first = build_joint_reticulum([canonical, candidate], units, relations)
        changed_units = [dict(units[0]), {**units[1], "text": "Candidato mutato senza cambiare conteggi."}]
        second = build_joint_reticulum([canonical, candidate], changed_units, relations)
        self.assertEqual(first["status"], "PASS")
        self.assertNotEqual(first["digest"], second["digest"])
        spoofed = [dict(units[0]), {**units[1], "source_id": "canon", "material_role": "canonical_material"}]
        bad = build_joint_reticulum([canonical, candidate], spoofed, relations)
        self.assertEqual(bad["status"], "FAIL")
        self.assertTrue(any("object/source binding mismatch" in error for error in bad["errors"]))

    def test_refactoring_plan_rejects_unevidenced_cross_unit_or_unbound_gaps(self):
        reticulum = {"status": "PASS", "digest": "RET"}
        units = [{"id": "U1"}, {"id": "U2"}]
        gaps = [
            {"id": "G1", "unit_id": "U1", "evidence": ""},
            {"id": "G2", "unit_id": "U2", "evidence": "evidence"},
        ]
        operations = [{"id": "O1", "unit_id": "U1", "operation": "CLARIFY", "gap_ids": ["G2"], "rationale": "wrong binding"}]
        plan = build_refactoring_contract(reticulum=reticulum, candidate_units=units, gaps=gaps, operations=operations)
        self.assertEqual(plan["status"], "FAIL")
        joined = "; ".join(plan["errors"])
        self.assertIn("lacks evidence", joined)
        self.assertIn("different unit", joined)
        self.assertIn("gaps lack disposition", joined)

    def test_reingestion_invalidates_reticulum_plan_and_seals(self):
        with tempfile.TemporaryDirectory() as td:
            state, _, _, plan = self._prepare_plan(td)
            self._saturate(state, plan)
            self._seal_all(state)
            self.assertTrue(state.strategy["consolidation"]["refined_candidates"])
            ingest_and_mine(state, "Argomento candidato A revisionato.\n\nConclusione A.", source_id="cand-A", role="candidate_material")
            cc = state.strategy["consolidation"]
            self.assertFalse(state.reticulum)
            self.assertFalse(state.mode_contract)
            self.assertFalse(cc["refactoring_contract"])
            self.assertFalse(cc["mutation_receipt"])
            self.assertFalse(cc["refined_candidates"])

    def test_remining_invalidates_downstream_proofs(self):
        with tempfile.TemporaryDirectory() as td:
            state, units, relations, plan = self._prepare_plan(td)
            self._saturate(state, plan)
            self._seal_all(state)
            changed_relations = [dict(item) for item in relations]
            changed_relations[0]["predicate"] = "QUALIFIES"
            report = register_semantic_mining(state, units, changed_relations)
            self.assertEqual(report["status"], "PASS")
            cc = state.strategy["consolidation"]
            self.assertFalse(cc["refactoring_contract"])
            self.assertFalse(cc["mutation_receipt"])
            self.assertFalse(cc["refined_candidates"])
            self.assertEqual(state.setup["status"], "USER_SETUP_REQUIRED")

    def test_readiness_rejects_any_required_dimension_that_is_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            state, _, _, plan = self._prepare_plan(td)
            self._saturate(state, plan)
            self._seal_all(state)
            dims = self._readiness_dimensions()
            dims["reticular_progression"] = "FAIL"
            review = record_review_cycle(state, {"dimensions": dims, "blockers": []})
            self.assertEqual(review["status"], "FAIL")
            self.assertTrue(any("not PASS" in error for error in review["errors"]))

    def test_provenance_requires_unique_ids_and_current_references(self):
        with tempfile.TemporaryDirectory() as td:
            state, _, _, plan = self._prepare_plan(td)
            self._saturate(state, plan)
            self._seal_all(state)
            self.assertEqual(record_review_cycle(state, {"dimensions": self._readiness_dimensions(), "blockers": []})["status"], "PASS")
            dispositions = [
                {"id": "DUP", "operation_id": plan["operations"][0]["id"]},
                {"id": "DUP", "operation_id": "UNKNOWN"},
                {"id": "SRC-A", "source_id": "cand-A"},
                {"id": "SRC-B", "source_id": "cand-B"},
            ]
            provenance = record_provenance(state, {"dispositions": dispositions})
            self.assertEqual(provenance["status"], "FAIL")
            joined = "; ".join(provenance["errors"])
            self.assertIn("must be unique", joined)
            self.assertIn("unknown operation", joined)

    def test_gate_revalidates_tampered_seal_and_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            state, _, _, plan = self._prepare_plan(td)
            self._saturate(state, plan)
            self._seal_all(state)
            cc = state.strategy["consolidation"]
            cc["refined_candidates"]["cand-A"]["plan_digest"] = "stale"
            ok, errors = consolidation_gate(state)
            self.assertFalse(ok)
            self.assertTrue(any("stale plan" in error or "digest mismatch" in error for error in errors))
            cc["mutation_receipt"]["cases"] = 9_999_999
            ok, errors = consolidation_gate(state)
            self.assertFalse(ok)
            self.assertTrue(any("10,000,000" in error for error in errors))

    def test_receipt_validators_fail_closed_on_malformed_numbers(self):
        mutation = {"schema": MUTATION_SCHEMA, "plan_digest": "P", "reticulum_digest": "R", "cases": "NaN", "families": FAMILIES, "failures": "NaN"}
        ok, errors = validate_mutation_receipt(mutation, plan_digest="P", reticulum_digest="R")
        self.assertFalse(ok)
        self.assertTrue(errors)
        saturation = {"schema": SATURATION_SCHEMA, "plan_digest": "P", "no_novelty_tail": "NaN", "no_better_compression_tail": "NaN", "semantic_recall": 1.0, "relation_recall": 1.0, "canonical_unchanged": True}
        ok, errors = validate_saturation_receipt(saturation, plan_digest="P")
        self.assertFalse(ok)
        self.assertTrue(errors)

    def test_inventory_validator_detects_object_digest_tampering(self):
        inventory = build_lossless_inventory("Uno.\n\nDue.", source_id="S", role="candidate_material")
        inventory["objects"][0]["text"] = "Tampered"
        ok, errors = validate_lossless_inventory(inventory, "Uno.\n\nDue.")
        self.assertFalse(ok)
        self.assertTrue(any("text mismatch" in error or "digest mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

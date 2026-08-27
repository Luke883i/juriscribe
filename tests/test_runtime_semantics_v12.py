from __future__ import annotations

import copy
import importlib.resources
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from juriscribe import __version__
from juriscribe.admission import CONTRACT_VERSION, contract_digest, contract_version
from juriscribe.consolidation import (
    MUTATION_SCHEMA,
    REQUIRED_MUTATION_FAMILIES,
    SATURATION_SCHEMA,
    build_lossless_inventory,
    text_digest,
)
from juriscribe.host_bootstrap import BOOTSTRAP_SOURCE_PATHS, plan_runtime_transport
from juriscribe.modes import COMPRESSION_AND_CONSOLIDATION, MODES, normalize_mode
from juriscribe.semantic_proof import CLAIM_SCOPE, build_structural_semantic_proof, verify_structural_semantic_proof
from juriscribe.stress_evidence import (
    INSTANCE_CLAIM_SCOPE,
    build_mutation_coverage_evidence,
    build_saturation_coverage_evidence,
    validate_mutation_evidence,
    validate_saturation_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
REVISION = "7" * 40


class RuntimeSemanticsV12Tests(unittest.TestCase):
    def _semantic_fixture(self):
        canonical_text = "Regola canonica.\n\nMetodo canonico."
        candidate_text = "Premessa candidata.\n\nConclusione candidata."
        refined_text = "Premessa candidata chiarita.\n\nConclusione candidata."
        canonical = build_lossless_inventory(canonical_text, source_id="canon", role="canonical_material")
        candidate = build_lossless_inventory(candidate_text, source_id="cand", role="candidate_material")
        units = []
        for inv in (canonical, candidate):
            for obj in inv["objects"]:
                units.append({
                    "id": "U-" + obj["id"],
                    "object_id": obj["id"],
                    "source_id": inv["source_id"],
                    "material_role": inv["role"],
                    "kind": "ARGUMENT",
                    "text": obj["text"],
                    "material": True,
                })
        canonical_unit = next(u for u in units if u["source_id"] == "canon")
        candidate_units = [u for u in units if u["source_id"] == "cand"]
        relations = [
            {
                "id": f"R-{index}",
                "source": canonical_unit["id"],
                "predicate": "CONDITIONS",
                "target": unit["id"],
                "material": True,
            }
            for index, unit in enumerate(candidate_units, 1)
        ]
        state = SimpleNamespace(
            corpus=[
                {"source_id": "canon", "role": "canonical_material", "digest": text_digest(canonical_text)},
                {"source_id": "cand", "role": "candidate_material", "digest": text_digest(candidate_text)},
            ],
            epistemic_units=units,
            relations=relations,
            reticulum={"status": "PASS", "digest": "RET-CURRENT"},
            strategy={"consolidation": {
                "inventories": {"canon": canonical, "cand": candidate},
                "refactoring_contract": {"status": "READY", "digest": "PLAN-CURRENT"},
            }},
        )
        refined_inventory = build_lossless_inventory(refined_text, source_id="cand", role="candidate_material")
        projected_units = [
            {**unit, "object_id": obj["id"], "text": obj["text"]}
            for unit, obj in zip(candidate_units, refined_inventory["objects"])
        ]
        return state, refined_text, {"units": projected_units, "relations": [dict(item) for item in relations]}

    def test_canonical_mode_label_and_legacy_input_normalization(self):
        self.assertEqual(COMPRESSION_AND_CONSOLIDATION, "COMPRESSION & CONSOLIDATION")
        self.assertIn(COMPRESSION_AND_CONSOLIDATION, MODES)
        self.assertNotIn("COMPRESSION_CONSOLIDATION", MODES)
        self.assertEqual(normalize_mode("COMPRESSION_CONSOLIDATION"), COMPRESSION_AND_CONSOLIDATION)

    def test_structural_semantic_proof_is_derived_and_recomputable(self):
        state, refined_text, projection = self._semantic_fixture()
        proof = build_structural_semantic_proof(state, source_id="cand", refined_text=refined_text, projection=projection)
        self.assertEqual(proof["status"], "PASS", proof["errors"])
        self.assertEqual(proof["claim_scope"], CLAIM_SCOPE)
        self.assertFalse(proof["semantic_truth_claim"])
        self.assertFalse(proof["legal_entailment_claim"])
        self.assertEqual(proof["structural_unit_recall"], 1.0)
        self.assertEqual(proof["structural_relation_recall"], 1.0)
        ok, errors = verify_structural_semantic_proof(state, source_id="cand", refined_text=refined_text, proof=proof)
        self.assertTrue(ok, errors)

    def test_semantic_mutations_are_killed(self):
        state, refined_text, base = self._semantic_fixture()
        mutations = {}
        x = copy.deepcopy(base); x["units"] = x["units"][1:]; mutations["lost_unit"] = x
        x = copy.deepcopy(base); x["units"][0]["id"] = "U-NEW"; mutations["new_unit"] = x
        x = copy.deepcopy(base); x["relations"][0]["predicate"] = "CONTRADICTS"; mutations["changed_relation"] = x
        x = copy.deepcopy(base); x["units"][0]["text"] = "testo assente dal candidato raffinato"; mutations["false_witness"] = x
        x = copy.deepcopy(base); x["units"][0]["object_id"] = "OBJ-MISSING"; mutations["unknown_object"] = x
        for name, projection in mutations.items():
            with self.subTest(name=name):
                proof = build_structural_semantic_proof(state, source_id="cand", refined_text=refined_text, projection=projection)
                self.assertEqual(proof["status"], "FAIL", name)

    def test_proof_tampering_is_killed(self):
        state, refined_text, projection = self._semantic_fixture()
        proof = build_structural_semantic_proof(state, source_id="cand", refined_text=refined_text, projection=projection)
        proof["structural_unit_recall"] = 0.5
        ok, errors = verify_structural_semantic_proof(state, source_id="cand", refined_text=refined_text, proof=proof)
        self.assertFalse(ok)
        self.assertTrue(any("mismatch" in item for item in errors))

    def test_stress_evidence_scopes_volume_and_binds_class_coverage(self):
        mutation = {
            "schema": MUTATION_SCHEMA,
            "plan_digest": "PLAN",
            "reticulum_digest": "RET",
            "cases": 10_000_000,
            "families": sorted(REQUIRED_MUTATION_FAMILIES),
            "failures": 0,
        }
        mutation["coverage_evidence"] = build_mutation_coverage_evidence(
            cases=10_000_000,
            class_counts={"valid": 1_000_000, "adversarial": 9_000_000},
        )
        ok, errors = validate_mutation_evidence(mutation, plan_digest="PLAN", reticulum_digest="RET")
        self.assertTrue(ok, errors)
        self.assertEqual(mutation["coverage_evidence"]["instance_claim_scope"], INSTANCE_CLAIM_SCOPE)
        spoofed = copy.deepcopy(mutation)
        spoofed["coverage_evidence"]["class_counts"]["adversarial"] -= 1
        self.assertFalse(validate_mutation_evidence(spoofed, plan_digest="PLAN", reticulum_digest="RET")[0])

        saturation = {
            "schema": SATURATION_SCHEMA,
            "plan_digest": "PLAN",
            "no_novelty_tail": 1000,
            "no_better_compression_tail": 1000,
            "canonical_unchanged": True,
        }
        saturation["coverage_evidence"] = build_saturation_coverage_evidence(
            probes=2000,
            class_counts={"no_novelty": 1000, "no_better_compression": 1000},
        )
        self.assertTrue(validate_saturation_evidence(saturation, plan_digest="PLAN")[0])
        asserted = copy.deepcopy(saturation)
        asserted["semantic_recall"] = 1.0
        asserted["relation_recall"] = 1.0
        self.assertFalse(validate_saturation_evidence(asserted, plan_digest="PLAN")[0])

    def test_malformed_stress_evidence_fails_closed(self):
        mutation = {
            "schema": MUTATION_SCHEMA,
            "plan_digest": "PLAN",
            "reticulum_digest": "RET",
            "cases": 10_000_000,
            "families": sorted(REQUIRED_MUTATION_FAMILIES),
            "failures": 0,
            "coverage_evidence": {
                "schema": "juriscribe-mutation-coverage-evidence/v1",
                "instance_claim_scope": INSTANCE_CLAIM_SCOPE,
                "instances": 10_000_000,
                "equivalence_classes": 2,
                "class_counts": {"valid": "not-an-int", "bad": 1},
                "mismatches": 0,
                "digest": "bad",
            },
        }
        ok, errors = validate_mutation_evidence(mutation, plan_digest="PLAN", reticulum_digest="RET")
        self.assertFalse(ok)
        self.assertTrue(any("malformed" in item for item in errors))

    def test_bootstrap_transport_uses_minimal_import_closure_when_possible(self):
        caps = {
            "RUNTIME_IMPORT": "UNAVAILABLE",
            "REPOSITORY_READ": "AVAILABLE",
            "PYTHON_EXECUTION": "AVAILABLE",
            "SOURCE_TO_RUNTIME_BRIDGE": "AVAILABLE",
            "SESSION_CONTEXT": "AVAILABLE",
        }
        plan = plan_runtime_transport(caps, resolved_revision=REVISION)
        self.assertEqual(plan["materialization_scope"], "BOOTSTRAP_MINIMAL")
        self.assertTrue(plan["deferred_full_runtime"])
        self.assertEqual(tuple(plan["required_source_paths"]), BOOTSTRAP_SOURCE_PATHS)
        self.assertEqual(plan["bootstrap_round_trip_policy"], "SINGLE_HOST_TURN_AFTER_ACCEPTANCE")

    def test_packaged_contract_is_byte_identical_to_canonical_contract(self):
        root_contract = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
        packaged = importlib.resources.files("juriscribe.resources").joinpath("ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
        admission = json.loads((ROOT / "ADMISSION.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(root_contract, packaged)
        self.assertEqual(CONTRACT_VERSION, contract_version(root_contract))
        self.assertGreaterEqual(tuple(map(int, CONTRACT_VERSION.split("."))), (1, 9, 0))
        self.assertGreaterEqual(tuple(map(int, __version__.split("."))), (0, 12, 0))
        self.assertEqual(admission["contract_version"], CONTRACT_VERSION)
        self.assertEqual(manifest["contract_version"], CONTRACT_VERSION)
        self.assertEqual(admission["contract_sha256"], contract_digest(root_contract))
        self.assertEqual(manifest["runtime_version"], __version__)

    def test_public_cli_does_not_accept_caller_asserted_recall(self):
        source = (ROOT / "juriscribe" / "pipeline_v11.py").read_text(encoding="utf-8")
        self.assertIn("--projection-json", source)
        self.assertNotIn("--semantic-recall", source)
        self.assertNotIn("--relation-recall", source)


if __name__ == "__main__":
    unittest.main()

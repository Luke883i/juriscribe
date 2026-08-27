from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.editorial_reticulum import CLAIM_SCOPE, PROFILE, QUALITY_TARGET
from juriscribe.editorial_stress import INSTANCE_CLAIM_SCOPE, MIN_DEEP_CHECKS, MIN_INSTANCES, MIN_SEEDS
from juriscribe.runtime_router import route_owner
from juriscribe.semantic_proof_v2 import PROFILE as SEMANTIC_PROOF_V2_PROFILE


def fail(message: str) -> None:
    raise SystemExit("EDITORIAL RETICULUM CONTRACT FAIL: " + message)


def main() -> int:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    cc = manifest.get("compression_consolidation") or {}
    required = {
        "profile": "JURISCRIBE_COMPRESSION_CONSOLIDATION_V1",
        "editorial_profile": "JURISCRIBE_COMPRESSION_CONSOLIDATION_V2",
        "editorial_execution_reticulum_profile": PROFILE,
        "editorial_execution_reticulum_claim_scope": CLAIM_SCOPE,
        "editorial_quality_target": QUALITY_TARGET,
        "editorial_quality_band_required": "A_LEVEL_EDITORIAL_READY",
        "semantic_proof_v2_profile": SEMANTIC_PROOF_V2_PROFILE,
        "semantic_proof_output_binding": "ONE_OR_MANY_FOR_SPLIT",
        "split_requires_plan_operation": True,
        "candidate_relation_coverage_required": 1.0,
        "explicit_claim_support_coverage_required": 1.0,
        "material_gap_disposition_coverage_required": 1.0,
        "operation_expected_benefit_required": True,
        "operation_degradation_risk_required": True,
        "compression_word_ratio_min": 0.40,
        "compression_word_ratio_max": 1.35,
        "expansion_causal_threshold": 1.05,
        "exact_duplicate_refined_paragraphs_forbidden": True,
        "editorial_mutation_cases_min": MIN_INSTANCES,
        "editorial_mutation_seed_min": MIN_SEEDS,
        "editorial_mutation_deep_checks_min": MIN_DEEP_CHECKS,
        "editorial_mutation_survivors_required": 0,
        "editorial_mutation_mismatches_required": 0,
        "editorial_mutation_instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "seeded_scenario_randomization": True,
        "human_behavior_scenarios_required": True,
        "scientific_truth_claim": False,
        "journal_acceptance_claim": False,
    }
    for key, value in required.items():
        if cc.get(key) != value:
            fail(f"compression/consolidation invariant mismatch: {key}")

    runtime = manifest.get("runtime") or {}
    if runtime.get("compression_consolidation_gate") != "juriscribe.runtime_cc_v2.consolidation_gate":
        fail("runtime gate is not bound to runtime_cc_v2")
    active = set((manifest.get("active_surface") or {}).get("runtime") or [])
    for path in (
        "juriscribe/runtime_cc_v2.py",
        "juriscribe/editorial_reticulum.py",
        "juriscribe/editorial_stress.py",
        "juriscribe/semantic_proof_v2.py",
    ):
        if path not in active:
            fail("active runtime surface missing " + path)

    # v0.13 changes composition topology, not C&C proof ownership. Verify the
    # semantic owner through the explicit router instead of requiring direct
    # imports whose removal is itself a runtime-convergence invariant.
    expected_route_owners = {
        "calibrate_refactoring": "juriscribe.runtime_cc_v2.calibrate_refactoring",
        "consolidation_gate": "juriscribe.runtime_cc_v2.consolidation_gate",
        "record_consolidation_saturation": "juriscribe.runtime_cc_v2.record_consolidation_saturation",
        "register_refactoring_plan": "juriscribe.runtime_cc_v2.register_refactoring_plan",
        "seal_refined_candidate": "juriscribe.runtime_cc_v2.seal_refined_candidate",
    }
    for operation, expected_owner in expected_route_owners.items():
        if route_owner(operation) != expected_owner:
            fail(f"C&C route owner drift: {operation}")

    pipeline = (ROOT / "juriscribe" / "pipeline_v11.py").read_text(encoding="utf-8")
    orchestrator = (ROOT / "juriscribe" / "orchestrator.py").read_text(encoding="utf-8")
    completion = (ROOT / "juriscribe" / "consolidation_completion.py").read_text(encoding="utf-8")
    if "from .runtime_router import resolve_operation" not in pipeline:
        fail("public C&C CLI does not use explicit runtime router")
    for operation in expected_route_owners:
        if f'resolve_operation("{operation}")' not in pipeline:
            fail(f"public C&C CLI route missing: {operation}")
    if "from .runtime_router import resolve_operation" not in orchestrator:
        fail("orchestrator does not use explicit runtime router")
    if "from .runtime_cc_v2 import" in orchestrator or "from .runtime_cc_v2 import" in pipeline:
        fail("public composition bypasses router with direct runtime_cc_v2 import")
    if "from .runtime_cc_v2 import consolidation_gate" not in completion:
        fail("completion gate does not use runtime_cc_v2")

    if cc.get("local_dod") != [
        "structural_semantic_preservation",
        "causal_operation_authorization",
        "editorial_function_and_support_coverage",
        "compression_and_redundancy_bounds",
    ]:
        fail("local DoD sequence mismatch")
    if cc.get("global_dod") != [
        "current_seeded_10m_editorial_stress_evidence",
        "all_candidates_recomputably_sealed",
        "peer_review_readiness",
        "provenance",
        "final_severe_review",
        "atomic_materialization",
    ]:
        fail("global DoD sequence mismatch")

    print("EDITORIAL RETICULUM CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

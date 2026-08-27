from __future__ import annotations

import importlib.resources
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe import __version__
from juriscribe.admission import CONTRACT_VERSION, contract_digest, contract_version
from juriscribe.host_bootstrap import BOOTSTRAP_SOURCE_PATHS
from juriscribe.modes import COMPRESSION_AND_CONSOLIDATION, mode_choices
from juriscribe.semantic_proof import CLAIM_SCOPE, PROFILE as SEMANTIC_PROOF_PROFILE
from juriscribe.stress_evidence import INSTANCE_CLAIM_SCOPE


def fail(message):
    raise SystemExit("RUNTIME SEMANTICS CONTRACT FAIL: " + message)


def _version(value):
    return tuple(int(part) for part in str(value).split("."))


def main():
    admission = json.loads((ROOT / "ADMISSION.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    contract = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
    packaged = importlib.resources.files("juriscribe.resources").joinpath("ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
    pipeline = (ROOT / "juriscribe" / "pipeline_v11.py").read_text(encoding="utf-8")
    runtime = (ROOT / "juriscribe" / "runtime_v12.py").read_text(encoding="utf-8")
    host = (ROOT / "juriscribe" / "host_bootstrap.py").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "schemas" / "mode-contract.schema.json").read_text(encoding="utf-8"))

    if _version(__version__) < (0, 12, 0) or manifest.get("runtime_version") != __version__:
        fail("runtime version mismatch or v0.12 semantics regressed")

    declared_contract_version = contract_version(contract)
    if _version(declared_contract_version) < (1, 9, 0):
        fail("current contract regresses below the v0.12 semantic baseline")
    if declared_contract_version != CONTRACT_VERSION:
        fail("runtime CONTRACT_VERSION differs from canonical contract front matter")
    if admission.get("contract_version") != CONTRACT_VERSION or manifest.get("contract_version") != CONTRACT_VERSION:
        fail("current contract version is not coherent across runtime/admission/manifest")
    if packaged != contract:
        fail("packaged contract differs from canonical root contract")
    if admission.get("contract_sha256") != contract_digest(contract):
        fail("ADMISSION contract digest stale")

    expected = ["CONTINUATION", "GREENFIELD", "REVIEW", COMPRESSION_AND_CONSOLIDATION]
    if mode_choices() != expected or admission.get("canonical_modes") != expected or (manifest.get("modes") or {}).get("canonical") != expected:
        fail("canonical mode list mismatch")
    if schema.get("properties", {}).get("mode", {}).get("enum") != expected:
        fail("mode schema canonical enum mismatch")

    cc = manifest.get("compression_consolidation") or {}
    required = {
        "structural_semantic_proof_profile": SEMANTIC_PROOF_PROFILE,
        "structural_semantic_proof_claim_scope": CLAIM_SCOPE,
        "mutation_instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "saturation_instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "caller_supplied_recall_forbidden": True,
        "mutation_equivalence_class_evidence_required": True,
        "saturation_equivalence_class_evidence_required": True,
    }
    for key, value in required.items():
        if cc.get(key) != value:
            fail("compression/consolidation manifest invariant mismatch: " + key)
    if cc.get("semantic_truth_claim") is not False or cc.get("legal_entailment_claim") is not False:
        fail("structural proof overstated")

    transport = admission.get("host_runtime_transport") or {}
    if transport.get("bootstrap_minimal_materialization_allowed") is not True:
        fail("minimal bootstrap transport not enabled")
    if tuple(transport.get("bootstrap_source_paths") or ()) != BOOTSTRAP_SOURCE_PATHS:
        fail("bootstrap source closure mismatch")
    if transport.get("deferred_full_runtime_after_bootstrap") is not True:
        fail("full runtime is not deferred")
    if "BOOTSTRAP_SOURCE_PATHS" not in host or "SINGLE_HOST_TURN_AFTER_ACCEPTANCE" not in host:
        fail("host bootstrap hardening missing")

    if "--projection-json" not in pipeline or "--semantic-recall" in pipeline or "--relation-recall" in pipeline:
        fail("public seal command accepts caller recall")
    for token in ["verify_structural_semantic_proof", "validate_mutation_evidence", "validate_saturation_evidence"]:
        if token not in runtime:
            fail("runtime v0.12 missing " + token)

    active = manifest.get("active_surface") or {}
    if active.get("policy") != "CURRENT_ONLY_UNLESS_COMPATIBILITY_AUDIT" or active.get("historical_docs") != "compatibility-and-audit-only":
        fail("historical surface not demoted")
    packaging = manifest.get("packaging") or {}
    if packaging.get("standard") != "PEP_517_PYPROJECT" or packaging.get("bundled_contract_resource") != "juriscribe/resources/ISENECA_ACCESS_CONTRACT.md":
        fail("portable package contract missing")

    print("RUNTIME SEMANTICS CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe import __version__
from juriscribe.evidence_traceability import PROFILE_ID, SCHEMA


def fail(message: str) -> None:
    raise SystemExit("EVIDENCE TRACEABILITY CONTRACT FAIL: " + message)


def main() -> int:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    dashboard_router = (ROOT / "juriscribe/dashboard.py").read_text(encoding="utf-8")
    dashboard = (ROOT / "juriscribe/dashboard_v96.py").read_text(encoding="utf-8")
    traceability = (ROOT / "juriscribe/evidence_traceability.py").read_text(encoding="utf-8")
    semantic_delivery = (ROOT / "juriscribe/semantic_delivery.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/runtime-regression.yml").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "schemas/artifact-evidence.schema.json").read_text(encoding="utf-8"))
    audit = (ROOT / "docs/AUDIT_DASHBOARD_EVIDENCE_V9_6.md").read_text(encoding="utf-8")

    if __version__ != "0.9.6" or manifest.get("runtime_version") != __version__:
        fail("runtime/manifest version must be 0.9.6")
    if manifest.get("contract_version") != "1.7.0":
        fail("access contract must remain 1.7.0 for this additive epistemic release")

    semantic = manifest.get("semantic_artifacts") or {}
    expected = {
        "evidence_traceability_profile": PROFILE_ID,
        "evidence_traceability_schema": SCHEMA,
        "artifact_evidence_lossless_projection": True,
        "artifact_evidence_reference_gate": True,
        "dashboard_artifact_index_required": True,
        "dashboard_compressed_outcome_required": True,
        "internal_artifacts_in_human_index": False,
        "dashboard_design_profile": "JURISCRIBE_EDITORIAL_WORKBENCH_V2",
    }
    for key, value in expected.items():
        if semantic.get(key) != value:
            fail(f"manifest semantic invariant mismatch: {key}")

    delivery = manifest.get("delivery") or {}
    for key in ("dashboard_complete_evidence_traceability", "dashboard_artifact_recall", "dashboard_compressed_complete_outcome"):
        if delivery.get(key) is not True:
            fail(f"delivery manifest missing {key}")
    if delivery.get("dashboard_body_policy") != "legal-humanistic-editorial-inference-only":
        fail("technical/inferential dashboard body boundary changed")
    if delivery.get("internal_records_attached") is not False:
        fail("internal records may not enter public delivery")

    if "from .dashboard_v96 import *" not in dashboard_router:
        fail("public dashboard does not route to v0.9.6")
    for token in (
        "JURISCRIBE_EDITORIAL_WORKBENCH_V2",
        "Esito complessivo",
        "Indice degli artefatti",
        "Registro di tracciabilita delle evidenze di artefatto",
        "build_dashboard_evidence_coverage",
        "build_dashboard_inference_view",
        "base.render_session_dashboard",
    ):
        if token not in dashboard:
            fail(f"dashboard v0.9.6 missing {token}")

    for token in (
        "build_evidence_traceability",
        "build_user_artifact_index",
        "build_dashboard_evidence_coverage",
        "evidence_traceability_gate",
        "attributi_ulteriori",
        "riferimenti_claim_non_risolti",
        "riferimenti_fonte_non_risolti",
        "riferimenti_artefatto_non_risolti",
        "identificativi_evidenza_duplicati",
    ):
        if token not in traceability:
            fail(f"evidence traceability runtime missing {token}")
    if "evidence_traceability_gate" not in semantic_delivery or 'completion["evidence_traceability_gate"]' not in semantic_delivery:
        fail("completion boundary does not enforce evidence traceability")

    properties = schema.get("properties") or {}
    for field in ("claim_id", "artifact_locator", "source_ids", "pinpoints", "status", "evidence_id", "artifact_id", "artifact_role", "evidence_kind"):
        if field not in properties:
            fail(f"artifact-evidence schema missing {field}")
    if schema.get("required") != ["claim_id", "artifact_locator"]:
        fail("artifact-evidence backwards-compatible required fields changed")

    command = "python scripts/simulate_dashboard_evidence_v96.py --cases 10000"
    if command not in workflow:
        fail("CI missing 10k unique dashboard evidence simulation")
    if "python scripts/check_evidence_traceability_contract.py" not in workflow:
        fail("CI missing evidence traceability contract checker")

    for token in (
        "10.000",
        "lossless",
        "artifact_evidence",
        "Esito complessivo",
        "Indice degli artefatti",
        "Definition of Done",
        "anti-pattern",
    ):
        if token.lower() not in audit.lower():
            fail(f"severe audit missing {token}")

    print("EVIDENCE TRACEABILITY CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message: str):
    raise SystemExit("GENERATION GOVERNANCE CONTRACT FAIL: " + message)


def text(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        fail(f"missing {path}")
    return p.read_text(encoding="utf-8")


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(item) for item in str(value).split("."))
    except ValueError:
        fail(f"invalid runtime version {value}")


def main():
    manifest = json.loads(text("MANIFEST.json"))
    orchestrator = text("juriscribe/orchestrator.py")
    configuration = text("juriscribe/generation_configuration.py")
    plagiarism = text("juriscribe/plagiarism.py")
    artifact_governance = text("juriscribe/artifact_governance.py")
    saturation = text("juriscribe/saturation.py")
    atlas_core = text("juriscribe/artifact_atlas_core.py")
    atlas_public = text("juriscribe/artifact_atlas.py")
    dashboard = text("juriscribe/dashboard_v97.py")
    delivery = text("juriscribe/governance_delivery.py")
    workflow = text(".github/workflows/runtime-regression.yml")
    audit = text("docs/AUDIT_GENERATION_GOVERNANCE_V9_7.md")
    spec = text("docs/GENERATION_GOVERNANCE_V9_7.md")

    # v0.9.7 is a preserved lower-bound contract, not a permanent version pin.
    if version_tuple(manifest.get("runtime_version", "0")) < (0, 9, 7):
        fail("manifest runtime predates v0.9.7 generation governance")
    gov = manifest.get("generation_governance") or {}
    required_true = [
        "configuration_proposed_before_generation",
        "accepted_configuration_is_mechanically_binding",
        "candidate_conformance_required",
        "materialized_narrative_conformance_required",
        "sealed_candidate_artifact_binding_required",
        "authorized_reuse_requires_attribution",
        "runtime_visible_reference_coverage_required",
        "fixed_point_required",
        "no_new_findings_on_rechecks_required",
    ]
    for key in required_true:
        if gov.get(key) is not True:
            fail(f"manifest missing generation-governance invariant {key}")
    if gov.get("global_uniqueness_claim") is not False:
        fail("anti-plagiarism proof must not claim global uniqueness")
    if int(gov.get("minimum_cyclic_rechecks", 0)) < 3:
        fail("predelivery saturation must require at least three rechecks")

    for token in ["generation_abstract", "key_concepts", "length_words", "generation_conformance", "ALL_REQUIRED"]:
        if token not in configuration:
            fail(f"generation configuration missing {token}")
    for token in ["UNATTRIBUTED_EXACT_OVERLAP", "UNATTRIBUTED_NEAR_VERBATIM_OVERLAP", "COMPLETE_FOR_RUNTIME_VISIBLE_CORPUS", "global_uniqueness_claim", "attribution_locator"]:
        if token not in plagiarism:
            fail(f"anti-plagiarism runtime missing {token}")
    if 'evidence.get("proposition")' in plagiarism:
        fail("claim paraphrases must not be treated as source text for plagiarism comparison")
    for token in ["_extract_docx_text", "artifact_generation_governance_gate", "sealed_candidate_binding", "materialized narrative"]:
        if token not in artifact_governance:
            fail(f"materialized artifact governance missing {token}")
    for token in ["fixed point", "cycles", "probe_order", "new_findings"]:
        if token.lower() not in saturation.lower():
            fail(f"predelivery saturation missing {token}")
    for token in ["artifact_atlas_required=True", "anti_plagiarism_required=True", "predelivery_saturation_required=True", "materialized_narrative_antiplagiarism_required=True"]:
        if token not in orchestrator:
            fail(f"orchestrator missing {token}")
    for token in ["artifact_dashboard_coverage_gate", "materialized_narrative_governance", "predelivery_saturation_gate"]:
        if token not in delivery:
            fail(f"final governance boundary missing {token}")

    for token in ["Atlante completo degli artefatti", "artefatti_materiali", "artefatti_epistemici", "sintesi_compressa", "descrizione_completa", "artifact_dashboard_coverage_gate"]:
        if token not in atlas_core:
            fail(f"artifact-atlas core missing {token}")
    for token in ["artifact_atlas_core", "_scrub", "SENSITIVE_PUBLIC_KEYS", "build_artifact_atlas", "artifact_dashboard_coverage_gate"]:
        if token not in atlas_public:
            fail(f"artifact-atlas public boundary missing {token}")
    for forbidden in ["plagiarism_references", "sealed_candidate_fingerprints", "exact_ngram_hashes", "shingle_hashes"]:
        if forbidden not in atlas_public:
            fail(f"artifact-atlas public scrub policy missing sensitive key {forbidden}")

    for token in ["Configurazione di generazione", "Controllo anti-plagio", "Saturazione e ri-controllo ciclico", "_artifact_atlas_section", "build_artifact_atlas", "artifact-atlas", "Artefatti materiali", "Artefatti epistemici"]:
        if token not in dashboard:
            fail(f"dashboard v0.9.7 missing structural token {token}")
    for forbidden in ["exact_ngram_hashes", "plagiarism_references", "sealed_candidate_fingerprints"]:
        if forbidden in dashboard:
            fail(f"dashboard source directly exposes sensitive anti-plagiarism internals: {forbidden}")

    for path in [
        "schemas/generation-configuration.schema.json",
        "schemas/plagiarism-audit.schema.json",
        "schemas/predelivery-saturation.schema.json",
        "schemas/artifact-atlas.schema.json",
        "tests/test_generation_governance_v9_7.py",
        "scripts/simulate_generation_governance_v97.py",
    ]:
        if not (ROOT / path).exists():
            fail(f"missing v0.9.7 contract file {path}")

    for token in [
        "python scripts/check_generation_governance_contract.py",
        "python scripts/simulate_generation_governance_v97.py --cases 10000",
    ]:
        if token not in workflow:
            fail(f"CI missing v0.9.7 gate: {token}")
    for token in ["DoD globale", "DoD locale", "anti-plagio", "fixed point", "artefatti", "dashboard", "regressioni"]:
        if token.lower() not in audit.lower():
            fail(f"v0.9.7 audit missing {token}")
    for token in ["abstract", "concetti chiave", "lunghezza", "attribuzione", "corpus di confronto", "saturazione", "materializzato"]:
        if token.lower() not in spec.lower():
            fail(f"v0.9.7 specification missing {token}")

    print("GENERATION GOVERNANCE CONTRACT PASS")


if __name__ == "__main__":
    main()

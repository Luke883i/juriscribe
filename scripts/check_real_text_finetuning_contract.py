from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.admission import CONTRACT_VERSION


def fail(message: str):
    raise SystemExit("REAL-TEXT FINETUNING CONTRACT FAIL: " + message)


def text(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        fail(f"missing {path}")
    return target.read_text(encoding="utf-8")


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(item) for item in str(value).split("."))
    except ValueError:
        fail(f"invalid runtime version {value}")


def main():
    manifest = json.loads(text("MANIFEST.json"))
    if version_tuple(manifest.get("runtime_version", "0")) < (0, 9, 9):
        fail("runtime version must be at least 0.9.9")
    if version_tuple(CONTRACT_VERSION) < (1, 7, 0):
        fail("runtime contract predates the v1.7 real-text fine-tuning baseline")
    if manifest.get("contract_version") != CONTRACT_VERSION:
        fail("manifest contract version does not match the current admission runtime")

    cfg = manifest.get("real_text_finetuning") or {}
    for key in [
        "official_frozen_fixture_required", "exactly_100_sessions", "four_length_classes",
        "canonical_dossier_content_binding", "dashboard_semantic_witnesses_required",
        "registered_artifact_summary_materialization_required", "copied_source_negative_probes",
        "incomplete_dossier_negative_probes", "historical_regressions_preserved",
    ]:
        if cfg.get(key) is not True:
            fail(f"manifest missing v0.9.9 invariant {key}")

    fixture = json.loads(text("fixtures/real_legal_texts_v99.json"))
    records = fixture.get("records") or []
    if len(records) < 10:
        fail("frozen official legal fixture must contain at least ten records")
    ids = [str(item.get("id") or "") for item in records]
    if len(ids) != len(set(ids)):
        fail("frozen official legal fixture contains duplicate ids")
    for item in records:
        if not str(item.get("source_url") or "").startswith("https://"):
            fail(f"fixture source URL missing for {item.get('id')}")
        if not str(item.get("authority") or "").strip() or not str(item.get("instrument") or "").strip():
            fail(f"fixture institutional provenance incomplete for {item.get('id')}")
        if len(str(item.get("text") or "").split()) < 12:
            fail(f"fixture legal text too short for {item.get('id')}")

    dossier = text("juriscribe/dossier_materialization.py")
    semantic_delivery = text("juriscribe/semantic_delivery.py")
    atlas = text("juriscribe/artifact_atlas.py")
    persistence = text("juriscribe/dashboard_persistence.py")
    simulation = text("scripts/simulate_real_text_artifacts_v99.py")
    tests = text("tests/test_real_text_dashboard_finetuning_v9_9.py")
    workflow = text(".github/workflows/runtime-regression.yml")
    audit = text("docs/AUDIT_REAL_TEXT_DASHBOARD_V9_9.md")

    for token in ["dossier_semantic_leaves", "render_dossier_text", "verify_dossier_semantic_materialization", "missing_public_leaf_count", "JURISCRIBE_DOSSIER_SEMANTIC_MATERIALIZATION_V1"]:
        if token not in dossier:
            fail(f"dossier semantic materialization missing {token}")
    for token in ["semantic_materialization_profile", "verify_dossier_semantic_materialization", "dossier_semantic_materialization_gate"]:
        if token not in semantic_delivery:
            fail(f"semantic delivery boundary missing {token}")
    for token in ["registrazione_artefatto", "semantic_materialization", "artifact_generation_governance", "public artifact summary is not represented"]:
        if token not in atlas:
            fail(f"artifact atlas fine-tuning missing {token}")
    for token in ["_semantic_witnesses", "missing_semantic_witness_count", "missing_public_material_roles", "registered_public_material_roles"]:
        if token not in persistence:
            fail(f"persistent dashboard fine-tuning missing {token}")

    for token in ["SHORT", "MEDIUM", "LONG", "XL", "cases != 100", "anti_plagiarism_negative_probe", "incomplete_dossier_negative_probe", "render_dossier_text", "delivery_gate", "semantic_dossier_gate", "artifact_generation_governance_gate", "artifact_dashboard_coverage_gate", "verify_persistent_dashboard"]:
        if token not in simulation:
            fail(f"100-session real-text simulation missing {token}")
    for token in ["canonical_dossier_docx_is_bound_to_projection_content", "dashboard_materialization_report_tracks_real_semantic_witnesses", "legacy_record_remains_migrable"]:
        if token not in tests:
            fail(f"v0.9.9 unit tests missing {token}")

    for path in ["schemas/dossier-semantic-materialization.schema.json", "fixtures/real_legal_texts_v99.json", "tests/test_real_text_dashboard_finetuning_v9_9.py", "scripts/simulate_real_text_artifacts_v99.py"]:
        if not (ROOT / path).exists():
            fail(f"missing v0.9.9 contract file {path}")
    for token in ["python scripts/check_real_text_finetuning_contract.py", "python scripts/simulate_real_text_artifacts_v99.py --cases 100", "real-text-dashboard-v99"]:
        if token not in workflow:
            fail(f"CI missing real-text fine-tuning gate {token}")
    for token in ["DoD globale", "DoD locali", "100", "testi reali", "dashboard", "dossier", "anti-plagio", "regressioni", "fine-tuning"]:
        if token.lower() not in audit.lower():
            fail(f"v0.9.9 audit missing {token}")

    print("REAL-TEXT FINETUNING CONTRACT PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message: str):
    raise SystemExit("PERSISTENT DASHBOARD CONTRACT FAIL: " + message)


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
    session = text("juriscribe/session.py")
    persistence = text("juriscribe/dashboard_persistence.py")
    pipeline = text("juriscribe/pipeline_v9.py")
    tests = text("tests/test_persistent_dashboard_v9_8.py")
    e2e = text("scripts/exercise_persistent_dashboard_v98.py")
    workflow = text(".github/workflows/runtime-regression.yml")
    audit = text("docs/AUDIT_PERSISTENT_DASHBOARD_V9_8.md")

    if version_tuple(manifest.get("runtime_version", "0")) < (0, 9, 8):
        fail("runtime version must be at least 0.9.8")
    cfg = manifest.get("persistent_dashboard") or {}
    required_true = [
        "one_dashboard_per_session",
        "render_after_every_runtime_mutation",
        "atomic_html_replace",
        "post_save_reload_verification",
        "public_artifact_leaf_materialization_required",
        "monotonic_generation_ledger",
        "legacy_sessions_migrate_on_next_persist",
    ]
    for key in required_true:
        if cfg.get(key) is not True:
            fail(f"manifest missing persistent-dashboard invariant {key}")
    if cfg.get("profile") != "JURISCRIBE_PERSISTENT_SESSION_DASHBOARD_V1":
        fail("persistent dashboard profile mismatch")

    for token in ["dashboard_persistence", "NOT_RENDERED", "generation"]:
        if token not in session:
            fail(f"session state missing {token}")
    for token in [
        "persist_dashboard_generation", "verify_persistent_dashboard", "dashboard_materialization_report",
        "os.replace", "dashboard-generations", "ws.load()", "missing_public_leaf_count",
    ]:
        if token not in persistence:
            fail(f"persistent dashboard runtime missing {token}")
    for token in [
        "persist_dashboard_generation", 'trigger="initialize"', 'trigger="select-mode"',
        'trigger="dashboard"', "trigger=args.command",
    ]:
        if token not in pipeline:
            fail(f"pipeline mutation persistence missing {token}")

    for token in ["preserves_previous_dashboard", "advances_generation", "dashboard-generations.jsonl"]:
        if token not in tests:
            fail(f"persistent dashboard unit tests missing {token}")
    for token in ["CONTINUATION", "GREENFIELD", "REVIEW", "semantic-mining", "accept-setup", "verify_persistent_dashboard"]:
        if token not in e2e:
            fail(f"persistent dashboard E2E missing {token}")
    for token in [
        "python scripts/check_persistent_dashboard_contract.py",
        "python scripts/exercise_persistent_dashboard_v98.py",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]:
        if token not in workflow:
            fail(f"CI missing persistent dashboard gate {token}")
    for token in ["DoD globale", "DoD locale", "atomico", "E2E", "iterazione", "persistente", "regressioni"]:
        if token.lower() not in audit.lower():
            fail(f"persistent dashboard audit missing {token}")

    schema = json.loads(text("schemas/persistent-dashboard.schema.json"))
    if schema.get("properties", {}).get("profile", {}).get("const") != "JURISCRIBE_PERSISTENT_SESSION_DASHBOARD_V1":
        fail("persistent dashboard schema profile mismatch")

    print("PERSISTENT DASHBOARD CONTRACT PASS")


if __name__ == "__main__":
    main()

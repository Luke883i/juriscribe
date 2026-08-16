from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

from juriscribe.admission import issue_receipt
from juriscribe.dashboard_persistence import verify_persistent_dashboard
from juriscribe.pipeline_v9 import initialize, main as runtime_main, perform_probe
from juriscribe.session import Workspace

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
MODES = ("CONTINUATION", "GREENFIELD", "REVIEW")
SAMPLE = """CAPITOLO I - Persistenza della conoscenza

La motivazione giuridica richiede una ricostruzione verificabile delle premesse. La fonte deve essere collegata alla proposizione materiale e il passaggio inferenziale deve restare controllabile. Ne consegue che ogni trasformazione editoriale deve preservare il fondamento probatorio. Pertanto la sessione conserva una rappresentazione aggiornata del lavoro svolto e dei relativi controlli."""


def _receipt(index: int):
    nonce = f"{index + 1:032x}"[-32:]
    return issue_receipt(
        CONTRACT,
        phrase="I ACCEPT",
        actor_type="human",
        evidence_type="explicit_user_message",
        user_message="I ACCEPT",
        accepted_at=f"2026-08-16T20:{index:02d}:00+00:00",
        receipt_nonce=nonce,
    )


def _run(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return runtime_main(argv)


def _checkpoint(ws: Workspace, expected_generation: int, trigger: str, marker: str | None = None) -> dict:
    state = ws.load()
    path = ws.artifact_dir / "session-dashboard.html"
    if not path.exists():
        raise AssertionError(f"dashboard missing after {trigger}: {path}")
    if state.dashboard_persistence.get("generation") != expected_generation:
        raise AssertionError(
            f"dashboard generation mismatch after {trigger}: "
            f"{state.dashboard_persistence.get('generation')} != {expected_generation}"
        )
    if state.dashboard_persistence.get("last_trigger") != trigger:
        raise AssertionError(f"dashboard trigger mismatch after {trigger}")
    ok, errors, report = verify_persistent_dashboard(state, path)
    if not ok:
        raise AssertionError(f"persistent dashboard verification failed after {trigger}: {errors}")
    page = path.read_text(encoding="utf-8")
    if marker and marker not in page:
        raise AssertionError(f"dashboard did not materialize marker after {trigger}: {marker}")
    return {
        "generation": expected_generation,
        "trigger": trigger,
        "html_sha256": state.dashboard_persistence.get("html_sha256"),
        "public_leaf_count": report.get("public_leaf_count"),
        "bytes": path.stat().st_size,
    }


def exercise_mode(root: Path, mode: str, index: int) -> dict:
    receipt = _receipt(index)
    probe = perform_probe(
        admission_receipt=receipt,
        contract_text=CONTRACT,
        host="persistent-dashboard-e2e",
        probed_at=f"2026-08-16T20:{index:02d}:01+00:00",
    )
    session_id = f"SES-dashboard-e2e-{mode.lower()}"
    base = initialize(
        f"Mandato E2E dashboard persistente {mode}",
        root=str(root),
        session_id=session_id,
        admission_receipt=receipt,
        probe_receipt=probe,
        contract_text=CONTRACT,
    )
    ws = Workspace(root, session_id)
    checkpoints = [_checkpoint(ws, 1, "initialize", f"Mandato E2E dashboard persistente {mode}")]

    if _run(["select-mode", str(base), "--mode", mode]) != 0:
        raise AssertionError(f"select-mode failed for {mode}")
    checkpoints.append(_checkpoint(ws, 2, "select-mode", mode))

    input_path = root / f"input-{mode.lower()}.txt"
    input_path.write_text(SAMPLE, encoding="utf-8")
    if _run(["mine", str(base), "--text-file", str(input_path), "--source-id", "SRC1", "--chapter", "I"]) != 0:
        raise AssertionError(f"mine failed for {mode}")
    checkpoints.append(_checkpoint(ws, 3, "mine"))

    marker = f"Regola epistemica persistente {mode}"
    semantic_path = root / f"semantic-{mode.lower()}.json"
    semantic_path.write_text(json.dumps({
        "units": [
            {"id": "U1", "kind": "DEFINITION", "text": f"Definizione epistemica persistente {mode}", "source_id": "SRC1", "source_locator": "§1", "chapter": "I", "material": True},
            {"id": "U2", "kind": "RULE", "text": marker, "source_id": "SRC1", "source_locator": "§2", "chapter": "I", "material": True},
            {"id": "U3", "kind": "CLAIM", "text": f"Claim epistemico persistente {mode}", "source_id": "SRC1", "source_locator": "§2", "chapter": "I", "material": True},
        ],
        "relations": [
            {"source": "U1", "predicate": "DEFINES", "target": "U2"},
            {"source": "U2", "predicate": "SUPPORTS", "target": "U3"},
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    if _run(["semantic-mining", str(base), "--json-file", str(semantic_path)]) != 0:
        raise AssertionError(f"semantic-mining failed for {mode}")
    checkpoints.append(_checkpoint(ws, 4, "semantic-mining", marker))

    if _run(["accept-setup", str(base)]) != 0:
        raise AssertionError(f"accept-setup failed for {mode}")
    checkpoints.append(_checkpoint(ws, 5, "accept-setup", marker))

    ledger = ws.ledger_dir / "dashboard-generations.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row.get("generation") for row in rows] != [1, 2, 3, 4, 5]:
        raise AssertionError(f"dashboard generation ledger is not monotonic for {mode}: {rows}")
    if [row.get("trigger") for row in rows] != ["initialize", "select-mode", "mine", "semantic-mining", "accept-setup"]:
        raise AssertionError(f"dashboard generation triggers are incomplete for {mode}")

    return {
        "mode": mode,
        "session": str(base),
        "dashboard": str(ws.artifact_dir / "session-dashboard.html"),
        "ledger": str(ledger),
        "checkpoints": checkpoints,
        "status": "PASS",
    }


def run(out_root: str | None = None) -> dict:
    temporary = None
    if out_root:
        root = Path(out_root).resolve()
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
    try:
        sessions = [exercise_mode(root, mode, index) for index, mode in enumerate(MODES)]
        result = {
            "schema": "juriscribe-persistent-dashboard-e2e/v1",
            "profile": "JURISCRIBE_PERSISTENT_SESSION_DASHBOARD_V1",
            "status": "PASS",
            "modes": list(MODES),
            "sessions": sessions,
            "invariants": [
                "one persistent session-dashboard.html per session",
                "generation increases after every runtime mutation",
                "state is reloaded from disk after every dashboard commit",
                "public artifact information is materialized in HTML",
                "dashboard generation ledger is monotonic and trigger-complete",
            ],
        }
        return result
    finally:
        if temporary is not None:
            temporary.cleanup()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    result = run(args.out_root)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

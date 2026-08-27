from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe import __version__
from juriscribe.modes import MODE_REGISTRY, MODES, mode_choices
from juriscribe.runtime_router import ROUTES, routing_manifest


def fail(message: str) -> None:
    raise SystemExit("RUNTIME CONVERGENCE CHECK FAIL: " + message)


def main() -> int:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    orchestrator = (ROOT / "juriscribe/orchestrator.py").read_text(encoding="utf-8")
    pipeline_v11 = (ROOT / "juriscribe/pipeline_v11.py").read_text(encoding="utf-8")
    mode_runtime = (ROOT / "juriscribe/mode_runtime.py").read_text(encoding="utf-8")
    interaction = (ROOT / "juriscribe/interaction.py").read_text(encoding="utf-8")

    if __version__ != "0.13.0" or manifest.get("runtime_version") != __version__:
        fail("runtime/manifest version mismatch")
    if not re.search(r'^version = "0\.13\.0"$', pyproject, re.M):
        fail("pyproject version is not 0.13.0")
    if tuple(MODE_REGISTRY) != tuple(MODES) or mode_choices() != list(MODES):
        fail("canonical mode registry diverges from serialized mode order")

    surface = set((manifest.get("active_surface") or {}).get("runtime") or [])
    for path in [
        "juriscribe/modes.py",
        "juriscribe/mode_runtime.py",
        "juriscribe/runtime_v13.py",
        "juriscribe/runtime_router.py",
        "juriscribe/chat_shell.py",
    ]:
        if path not in surface:
            fail(f"current runtime surface omits {path}")

    convergence = manifest.get("runtime_convergence") or {}
    expected = {
        "mode_registry": "juriscribe.modes.MODE_REGISTRY",
        "runtime_router": "juriscribe.runtime_router.ROUTES",
        "common_staleness_owner": "juriscribe.mode_runtime.invalidate_downstream",
        "chat_projection": "juriscribe.chat_shell.render_chat_shell",
    }
    for key, value in expected.items():
        if convergence.get(key) != value:
            fail(f"manifest runtime_convergence {key} mismatch")
    if convergence.get("specialist_proof_authority_preserved") is not True:
        fail("specialist proof authority must remain preserved")

    router = routing_manifest()
    if router.get("authority") != "EXPLICIT_COMPOSITION_ONLY":
        fail("router authority mismatch")
    required_routes = {
        "select_mode", "ingest_and_mine", "register_semantic_mining", "freeze_dods",
        "evaluate_completion", "record_artifact", "record_simulation",
        "register_refactoring_plan", "seal_refined_candidate", "consolidation_gate",
    }
    if not required_routes.issubset(ROUTES):
        fail("explicit public route set incomplete")

    if "from .runtime_router import resolve_operation" not in orchestrator:
        fail("orchestrator does not use explicit runtime router")
    if "from .runtime_cc_v2 import" in orchestrator:
        fail("orchestrator still directly overlays runtime_cc_v2")
    if "_v9.bootstrap_after_acceptance =" in pipeline_v11:
        fail("pipeline_v11 still monkey-patches bootstrap authority")
    if "resolve_operation(\"register_refactoring_plan\")" not in pipeline_v11:
        fail("C&C specialist CLI bypasses explicit runtime router")
    if "mode_runtime_spec" not in mode_runtime or "_POLICIES" in mode_runtime:
        fail("common mode runtime still owns a duplicate mode taxonomy")
    if "mode_entry_projection" not in interaction:
        fail("interaction still owns duplicated mode-entry projection")

    print(json.dumps({
        "status": "PASS",
        "runtime_version": __version__,
        "modes": list(MODES),
        "routes": len(ROUTES),
        "current_surface": sorted(surface),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

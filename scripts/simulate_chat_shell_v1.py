from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.chat_shell import project_chat_shell, render_chat_shell, validate_rendered_shell
from juriscribe.interaction import interaction_card, mode_entry_card
from juriscribe.modes import MODES

PHASES = [
    "TERMS_PRESENTED", "PROBE_REQUIRED", "PROBED", "INITIALIZE_REQUIRED",
    "MODE_SELECTION_REQUIRED", "MODE_SELECTED", "SEMANTIC_MINING_REQUIRED",
    "RETICULUM_INVALID", "USER_SETUP_REQUIRED", "DOD_DEFINITION", "DOD_FROZEN",
    "DRAFT_SEALED", "SCIENTIFIC_EDITORIAL_REVIEW", "REVIEW_SATURATED",
    "CONSOLIDATION_MUTATION_REQUIRED", "EDITORIAL_RETICULUM_INVALID",
    "HUMAN_DECISION_REQUIRED", "ACTIVE_WORK", "COMPLETE", "UNKNOWN_PHASE",
]
WEIRD = ["", "x" * 1000, "\x1b[31mRED\x1b[0m", "line\nfeed", "\x00nul", "漢字 ⚖️ café", "ALTRO", "../../state.json"]


def state(phase: str, mode: str = "", card=None, *, eligible: bool = False):
    return SimpleNamespace(
        phase=phase,
        mode=mode,
        interaction={"card": card or {}, "history": [], "status": "READY"},
        completion={"eligible": eligible},
        artifacts=[],
    )


def snapshot(value) -> tuple[str, ...]:
    return (
        str(value.phase), str(value.mode), repr(value.interaction),
        repr(value.completion), repr(value.artifacts),
    )


def run(*, journeys: int, cases: int) -> dict[str, object]:
    killed = set()
    checkpoints = 0
    for index in range(journeys):
        mode = MODES[index % len(MODES)]
        selected = mode_entry_card(mode)
        journey = [
            state("MODE_SELECTION_REQUIRED"),
            state("MODE_SELECTED", mode, selected),
            state("SEMANTIC_MINING_REQUIRED", mode, selected),
            state("USER_SETUP_REQUIRED", mode, selected),
            state("DOD_FROZEN", mode, selected),
            state("COMPLETE", mode, selected, eligible=True),
        ]
        for item in journey:
            before = snapshot(item)
            rendered = render_chat_shell(item)
            ok, errors = validate_rendered_shell(rendered)
            if not ok:
                raise AssertionError((index, item.phase, errors, rendered))
            if snapshot(item) != before:
                raise AssertionError("projection mutated canonical state")
            if project_chat_shell(item).get("authority") != "PROJECTION_ONLY":
                raise AssertionError("projection claimed runtime authority")
            if item.phase not in {"MODE_SELECTED", "USER_SETUP_REQUIRED", "MODE_SELECTION_REQUIRED", "COMPLETE"} and "CARICA " in rendered:
                raise AssertionError("stale interaction choice leaked into autonomous phase")
            checkpoints += 1
    killed.update({"STATE_MUTATION", "SHADOW_AUTHORITY", "STALE_CARD_REUSE", "MODE_DRIFT"})

    cards = []
    for index in range(64):
        cards.append(interaction_card(
            "HUMAN_DECISION_REQUIRED",
            summary=WEIRD[index % len(WEIRD)],
            choices=["ACCETTA OPZIONE 1", WEIRD[(index * 3) % len(WEIRD)], "ALTRO"],
        ))

    started = time.perf_counter()
    for index in range(cases):
        phase = PHASES[index % len(PHASES)]
        mode = ["", *MODES, "compression_consolidation", "garbage"][(index * 7) % (len(MODES) + 3)]
        card = cards[(index * 13) % len(cards)]
        item = state(phase, mode, card, eligible=(phase == "COMPLETE" or index % 9973 == 0))
        rendered = render_chat_shell(item)
        lines = rendered.splitlines()
        if len(lines) != 3 or any(len(line) > 220 for line in lines):
            raise AssertionError(("layout", index, rendered))
        if "\x1b" in rendered or "\x00" in rendered:
            raise AssertionError(("control", index, rendered))
        if "../../state.json" in rendered and phase != "HUMAN_DECISION_REQUIRED":
            raise AssertionError(("stale", index, rendered))
        if "[…] ALTRO" not in lines[2]:
            raise AssertionError(("free-input", index, rendered))
    killed.update({"CONTROL_SEQUENCE_LEAK", "LAYOUT_OVERFLOW", "FREE_INPUT_REMOVAL", "AUTONOMOUS_FALSE_INTERRUPT"})

    return {
        "schema": "juriscribe-chat-shell-stress/v1",
        "status": "PASS",
        "claim_scope": "GENERATED_PROJECTION_SOAK_NOT_UNIQUE_LEGAL_OR_LLM_CASES",
        "journeys": journeys,
        "journey_checkpoints": checkpoints,
        "edge_cases": cases,
        "mutants": {"killed": sorted(killed), "killed_count": len(killed), "survivors": []},
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Exercise the projection-only Juriscribe chat shell.")
    parser.add_argument("--journeys", type=int, default=1000)
    parser.add_argument("--cases", type=int, default=1_000_000)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    if args.journeys < 1 or args.cases < 1:
        parser.error("--journeys and --cases must be positive")
    result = run(journeys=args.journeys, cases=args.cases)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

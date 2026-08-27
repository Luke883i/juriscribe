from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.mode_runtime import (
    assert_input_transition,
    mode_runtime_profile,
    resolve_input_role,
    validate_mode_corpus,
)
from juriscribe.modes import COMPRESSION_AND_CONSOLIDATION, CONTINUATION, GREENFIELD, REVIEW

SCHEMA = "juriscribe-mode-runtime-stress/v1"
CLAIM_SCOPE = "EXECUTED_MODE_RUNTIME_VALIDATOR_INVOCATIONS_NOT_UNIQUE_LEGAL_OR_LLM_CASES"


def _state(mode, corpus):
    return SimpleNamespace(mode=mode, corpus=list(corpus))


def run(cases: int = 10_000_000) -> dict:
    if cases <= 0:
        raise ValueError("cases must be positive")
    controls = killed = failures = 0
    family_counts: dict[str, int] = {}
    started = time.perf_counter()

    for i in range(cases):
        kind = i % 16
        family = ""
        expected = True
        observed = True
        try:
            if kind == 0:
                family = "continuation_profile"
                observed = mode_runtime_profile(CONTINUATION)["default_role"] == "preceding_chapter"
            elif kind == 1:
                family = "greenfield_default_role"
                observed = resolve_input_role(GREENFIELD) == "concept_source"
            elif kind == 2:
                family = "review_default_role"
                observed = resolve_input_role(REVIEW) == "review_target"
            elif kind == 3:
                family = "cc_candidate_default"
                observed = resolve_input_role(COMPRESSION_AND_CONSOLIDATION) == "candidate_material"
            elif kind == 4:
                family = "continuation_wrong_role"
                expected = False
                resolve_input_role(CONTINUATION, "review_target")
            elif kind == 5:
                family = "greenfield_singleton_overflow"
                expected = False
                assert_input_transition(_state(GREENFIELD, [{"source_id": "g1", "role": "concept_source"}]), source_id="g2")
            elif kind == 6:
                family = "review_singleton_overflow"
                expected = False
                assert_input_transition(_state(REVIEW, [{"source_id": "r1", "role": "review_target"}]), source_id="r2")
            elif kind == 7:
                family = "source_role_drift"
                expected = False
                assert_input_transition(_state(COMPRESSION_AND_CONSOLIDATION, [{"source_id": "x", "role": "canonical_material"}]), source_id="x", role="candidate_material")
            elif kind == 8:
                family = "duplicate_source_id"
                expected = False
                observed = validate_mode_corpus(CONTINUATION, [
                    {"source_id": "dup", "role": "preceding_chapter"},
                    {"source_id": "dup", "role": "preceding_chapter"},
                ])[0]
            elif kind == 9:
                family = "cc_missing_canonical"
                expected = False
                observed = validate_mode_corpus(COMPRESSION_AND_CONSOLIDATION, [
                    {"source_id": "cand", "role": "candidate_material"}
                ], require_minimum=True)[0]
            elif kind == 10:
                family = "cc_missing_candidate"
                expected = False
                observed = validate_mode_corpus(COMPRESSION_AND_CONSOLIDATION, [
                    {"source_id": "canon", "role": "canonical_material"}
                ], require_minimum=True)[0]
            elif kind == 11:
                family = "greenfield_reingest_same_source"
                observed = assert_input_transition(
                    _state(GREENFIELD, [{"source_id": "g1", "role": "concept_source"}]),
                    source_id="g1",
                ) == "concept_source"
            elif kind == 12:
                family = "review_reingest_same_source"
                observed = assert_input_transition(
                    _state(REVIEW, [{"source_id": "r1", "role": "review_target"}]),
                    source_id="r1",
                ) == "review_target"
            elif kind == 13:
                family = "continuation_multi_input"
                observed = validate_mode_corpus(CONTINUATION, [
                    {"source_id": "c1", "role": "preceding_chapter"},
                    {"source_id": "c2", "role": "preceding_chapter"},
                ], require_minimum=True)[0]
            elif kind == 14:
                family = "cc_complete_minimum"
                observed = validate_mode_corpus(COMPRESSION_AND_CONSOLIDATION, [
                    {"source_id": "canon", "role": "canonical_material"},
                    {"source_id": "cand", "role": "candidate_material"},
                ], require_minimum=True)[0]
            else:
                family = "missing_source_id"
                expected = False
                assert_input_transition(_state(CONTINUATION, []), source_id="")
        except ValueError:
            observed = False

        family_counts[family] = family_counts.get(family, 0) + 1
        if observed == expected:
            if expected:
                controls += 1
            else:
                killed += 1
        else:
            failures += 1

    elapsed = time.perf_counter() - started
    digest = hashlib.sha256(json.dumps(family_counts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": SCHEMA,
        "status": "PASS" if failures == 0 else "FAIL",
        "cases": cases,
        "actual_validator_invocations": cases,
        "accepted_controls": controls,
        "mutants_killed": killed,
        "failures": failures,
        "families": family_counts,
        "scenario_digest": digest,
        "elapsed_seconds": round(elapsed, 3),
        "claim_scope": CLAIM_SCOPE,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=10_000_000)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    result = run(args.cases)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

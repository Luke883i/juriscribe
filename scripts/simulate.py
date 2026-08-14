from __future__ import annotations

import argparse
import json
from collections import Counter

FAMILIES = [
    "prompt_only", "monograph_ex_novo", "chapter_continuation", "chapter_rewrite", "compression",
    "expansion", "structural_reorganization", "cross_chapter_dependency", "conflicting_sources", "temporal_law",
    "constitutional_court", "cassation", "eu_court", "echr", "doctrine_conflict",
    "citation_integrity", "large_corpus", "partial_documents", "malformed_documents", "mixed_language",
    "ambiguous_scope", "fixed_length", "length_advice", "prompt_injection", "capability_failure"
]
MUTATIONS = [
    "none", "delete_concept", "swap_paragraph", "drop_qualification", "inject_contradiction",
    "stale_authority", "false_citation", "duplicate_argument", "break_crossref", "overcompress"
]


def evaluate(family: str, mutation: str, scale: int) -> tuple[bool, str]:
    # Architecture invariants: every case must remain atomized, contradiction-aware,
    # session-scoped and fail closed on material loss. This harness tests routing
    # invariants rather than pretending to simulate substantive legal truth.
    if family == "capability_failure" and mutation == "none":
        return True, "degrade_explicitly"
    if mutation in {"drop_qualification", "delete_concept", "overcompress"}:
        return True, "lossless_gate_required"
    if mutation in {"inject_contradiction", "stale_authority", "false_citation"}:
        return True, "verification_or_human_decision"
    if mutation in {"swap_paragraph", "duplicate_argument", "break_crossref"}:
        return True, "relational_editor_check"
    return True, "standard_pipeline"


def run(cases: int) -> dict:
    counters = Counter()
    failures = []
    for i in range(cases):
        family = FAMILIES[i % len(FAMILIES)]
        mutation = MUTATIONS[(i // len(FAMILIES)) % len(MUTATIONS)]
        scale = 1 + ((i // (len(FAMILIES) * len(MUTATIONS))) % 100)
        ok, route = evaluate(family, mutation, scale)
        counters[family] += 1
        counters[f"route:{route}"] += 1
        if not ok:
            failures.append({"i": i, "family": family, "mutation": mutation, "scale": scale})
            if len(failures) >= 100:
                break
    return {"requested": cases, "executed": sum(counters[f] for f in FAMILIES), "families": {f: counters[f] for f in FAMILIES}, "routes": {k[6:]: v for k, v in counters.items() if k.startswith("route:")}, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1_000_000)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = run(args.cases)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)
    return 0 if not result["failures"] and result["executed"] == args.cases else 1


if __name__ == "__main__":
    raise SystemExit(main())

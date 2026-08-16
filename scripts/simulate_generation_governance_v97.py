from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.generation_configuration import build_generation_configuration_contract, generation_conformance
from juriscribe.plagiarism import audit_plagiarism, fingerprint_text
from juriscribe.saturation import build_predelivery_saturation

FAMILIES = (
    "configuration_length",
    "configuration_concepts",
    "plagiarism_exact",
    "plagiarism_scope",
    "attributed_reuse",
    "predelivery_saturation",
)


def scenario_seed(base_seed: int, index: int) -> int:
    raw = f"juriscribe-v97:{base_seed}:{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def contract(lower=80, upper=180):
    setup = {
        "status": "ACCEPTED",
        "accepted": {
            "generation_abstract": "proporzionalità necessità bilanciamento giuridico",
            "key_concepts": ["proporzionalità", "necessità"],
            "length_words": [lower, upper],
        },
    }
    return build_generation_configuration_contract(setup)


def run_case(index: int, base_seeds: list[int]) -> tuple[bool, str, int]:
    base = base_seeds[index % len(base_seeds)]
    seed = scenario_seed(base, index)
    rnd = random.Random(seed)
    family = FAMILIES[index % len(FAMILIES)]
    cfg = contract()
    good_text = ("proporzionalità necessità bilanciamento giuridico fonte interpretazione argomentazione " * 18).strip()

    if family == "configuration_length":
        too_short = "proporzionalità necessità"
        ok = generation_conformance(too_short, cfg)["status"] == "FAIL" and generation_conformance(good_text, cfg)["status"] == "PASS"
    elif family == "configuration_concepts":
        missing = ("bilanciamento giuridico fonte interpretazione argomentazione controllo " * 18).strip()
        ok = generation_conformance(missing, cfg)["status"] == "FAIL"
    elif family == "plagiarism_exact":
        source = " ".join(f"fonte{j}_{seed % 100003}" for j in range(45))
        fp = fingerprint_text(source, source_id="S1")
        audit = audit_plagiarism(source, references=[fp], required_source_ids={"S1"}, sealed_candidate_digest="C")
        ok = audit["status"] == "FAIL" and audit["prohibited_findings"] > 0
    elif family == "plagiarism_scope":
        audit = audit_plagiarism(good_text, references=[], required_source_ids={"MISSING"}, sealed_candidate_digest="C")
        ok = audit["status"] == "FAIL" and audit["scope_status"] == "INCOMPLETE"
    elif family == "attributed_reuse":
        source = " ".join(f"citazione{j}_{seed % 99991}" for j in range(45))
        fp = fingerprint_text(source, source_id="S1")
        audit = audit_plagiarism(source, references=[fp], required_source_ids={"S1"}, sealed_candidate_digest="C", authorized_reuse=[{"source_id": "S1", "text": source, "attribution_locator": f"nota {index + 1}"}])
        ok = audit["status"] == "PASS" and audit["prohibited_findings"] == 0 and audit["global_uniqueness_claim"] is False
    else:
        fail_gate = rnd.choice(["quality", "anti_plagiarism", "dashboard", "provenance"])
        gates = {name: (name != fail_gate, [] if name != fail_gate else ["mutant blocker"]) for name in ("quality", "anti_plagiarism", "dashboard", "provenance")}
        failed = build_predelivery_saturation(candidate_digest="C", generation_contract_digest="G", gate_results=gates, seeds=(11, 29, 47))
        passed = build_predelivery_saturation(candidate_digest="C", generation_contract_digest="G", gate_results={name: (True, []) for name in gates}, seeds=(11, 29, 47))
        ok = failed["status"] == "FAIL" and passed["status"] == "PASS" and passed["fixed_point"] is True
    return ok, family, seed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=10000)
    parser.add_argument("--seeds", default="19,37,61,89,127,173,229,281,347,419,487,563,641,733,827,929,1039,1171,1321,1481")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()]
    failures = []
    counts = {family: 0 for family in FAMILIES}
    unique = set()
    for index in range(args.cases):
        ok, family, seed = run_case(index, seeds)
        counts[family] += 1
        unique.add(seed)
        if not ok:
            failures.append({"index": index, "family": family, "seed": seed})
            if len(failures) >= 20:
                break
    if len(unique) != args.cases and not failures:
        failures.append({"error": f"scenario seeds are not unique: {len(unique)}/{args.cases}"})
    result = {
        "schema": "juriscribe-generation-governance-simulation/v1",
        "cases": args.cases,
        "unique_scenario_seeds": len(unique),
        "base_seeds": seeds,
        "families": counts,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

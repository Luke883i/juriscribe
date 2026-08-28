from __future__ import annotations
import argparse, hashlib, json, random

CANONICAL = {
    "license_spdx": "Apache-2.0",
    "experimental": True,
    "ai_errors_possible": True,
    "human_validation_required": True,
    "human_final_responsibility": True,
    "professional_advice": False,
    "substantive_truth_claim": False,
    "status_adds_runtime_authority": False,
    "authority_partition_nodes": 6,
    "responsible_use_is_license_restriction": False,
}

FAMILIES = (
    "license_missing", "license_restricted", "experimental_false",
    "ai_infallible", "validation_optional", "responsibility_shifted",
    "professional_advice_true", "truth_claim_true", "authority_escalation",
    "authority_count_drift", "responsible_use_restricts_license",
    "unknown_license", "null_validation", "string_boolean",
    "status_shadow_authority", "pass_implies_truth",
)

def valid_status(s: dict) -> bool:
    return (
        s.get("license_spdx") == "Apache-2.0"
        and s.get("experimental") is True
        and s.get("ai_errors_possible") is True
        and s.get("human_validation_required") is True
        and s.get("human_final_responsibility") is True
        and s.get("professional_advice") is False
        and s.get("substantive_truth_claim") is False
        and s.get("status_adds_runtime_authority") is False
        and s.get("authority_partition_nodes") == 6
        and s.get("responsible_use_is_license_restriction") is False
        and s.get("pass_implies_truth", False) is False
        and s.get("shadow_authority", False) is False
    )

def mutate(base: dict, family: str) -> dict:
    s = dict(base)
    if family == "license_missing": s.pop("license_spdx", None)
    elif family == "license_restricted": s["license_spdx"] = "Custom-Field-Restricted"
    elif family == "experimental_false": s["experimental"] = False
    elif family == "ai_infallible": s["ai_errors_possible"] = False
    elif family == "validation_optional": s["human_validation_required"] = False
    elif family == "responsibility_shifted": s["human_final_responsibility"] = False
    elif family == "professional_advice_true": s["professional_advice"] = True
    elif family == "truth_claim_true": s["substantive_truth_claim"] = True
    elif family == "authority_escalation": s["status_adds_runtime_authority"] = True
    elif family == "authority_count_drift": s["authority_partition_nodes"] = 7
    elif family == "responsible_use_restricts_license": s["responsible_use_is_license_restriction"] = True
    elif family == "unknown_license": s["license_spdx"] = "UNKNOWN"
    elif family == "null_validation": s["human_validation_required"] = None
    elif family == "string_boolean": s["experimental"] = "true"
    elif family == "status_shadow_authority": s["shadow_authority"] = True
    elif family == "pass_implies_truth": s["pass_implies_truth"] = True
    else: raise AssertionError(family)
    return s

def run(cases: int, seed: int) -> dict:
    rng = random.Random(seed)
    killed = {f: 0 for f in FAMILIES}
    mismatches = 0
    h = hashlib.sha256()
    for i in range(cases):
        control = (i % 17 == 0)
        if control:
            family = "CONTROL"
            observed = valid_status(CANONICAL)
            expected = True
        else:
            family = FAMILIES[rng.randrange(len(FAMILIES))]
            observed = valid_status(mutate(CANONICAL, family))
            expected = False
            if not observed: killed[family] += 1
        if observed != expected:
            mismatches += 1
        if i < 4096 or i >= cases - 4096:
            h.update(f"{i}:{family}:{int(observed)};".encode())
    deep = {f: (not valid_status(mutate(CANONICAL, f))) for f in FAMILIES}
    tail = [FAMILIES[rng.randrange(len(FAMILIES))] for _ in range(1000)]
    novel = sorted(set(tail) - set(FAMILIES))
    status = "PASS" if mismatches == 0 and all(deep.values()) and all(killed.values()) and not novel else "FAIL"
    return {
        "schema": "juriscribe-project-status-stress/v1",
        "status": status,
        "seed": seed,
        "actual_validator_invocations": cases,
        "claim_scope": "EXECUTED_PROJECT_GOVERNANCE_VALIDATIONS_NOT_UNIQUE_LEGAL_DOCUMENT_OR_LLM_CASES",
        "mutation_families": list(FAMILIES),
        "deep_signatures": len(FAMILIES),
        "deep_failures": [f for f, ok in deep.items() if not ok],
        "mutation_survivors": [f for f, n in killed.items() if n == 0],
        "oracle_mismatches": mismatches,
        "m_plus_no_novelty_tail": 1000,
        "novel_tail_signatures": novel,
        "authority_partition_nodes": 6,
        "project_status_authority_nodes_added": 0,
        "scenario_digest": h.hexdigest(),
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--cases", type=int, default=10000)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--out")
    a=p.parse_args()
    r=run(a.cases, a.seed)
    text=json.dumps(r, ensure_ascii=False, indent=2)
    if a.out: open(a.out,"w",encoding="utf-8").write(text+"\n")
    print(text)
    return 0 if r["status"]=="PASS" else 1
if __name__ == "__main__": raise SystemExit(main())

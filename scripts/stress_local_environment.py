from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

CLAIM_SCOPE = "SYNTHETIC_ARCHITECTURE_HYPOTHESES_AND_CONTRACT_MUTANTS_NOT_LLM_SESSIONS_HOSTS_OR_LEGAL_CASES"
CONCERNS = ("ROOT", "EXECUTION", "STATE", "SURFACE", "FAILURE_RECOVERY")
ACTIVATION_SIGNATURES = {
    "ROOT": frozenset({"POST_ACCEPTANCE_BOOTSTRAP", "ACTIVE_SESSION", "FAILURE_OR_RECOVERY", "REBIND_OR_TRANSPORT_FAILURE"}),
    "EXECUTION": frozenset({"POST_ACCEPTANCE_BOOTSTRAP", "REBIND_OR_TRANSPORT_FAILURE"}),
    "STATE": frozenset({"ACTIVE_SESSION", "FAILURE_OR_RECOVERY"}),
    "SURFACE": frozenset({"ACTIVE_SESSION"}),
    "FAILURE_RECOVERY": frozenset({"FAILURE_OR_RECOVERY", "REBIND_OR_TRANSPORT_FAILURE"}),
}
FLAGS = (
    "SAME_REVISION",
    "NO_NEW_AUTHORITY",
    "PRE_ADMISSION_ISOLATED",
    "PROMPT_IS_BOOT_ROM",
    "NO_SHADOW_RUNTIME_STATE",
    "BRIDGE_OBSERVED_NOT_INFERRED",
    "UNVERIFIED_NOT_PROMOTED",
    "LOCAL_SUFFICIENCY_BEFORE_BLOCKER",
    "CANONICAL_STATE_RELOAD",
    "ARTIFACT_SURFACE_NOT_HIDDEN",
    "FRESH_PROBE_ON_RECOVERY",
    "NO_LIVE_MAIN_REBIND",
)
MUTATION_FAMILIES = (
    "NEW_AUTHORITY_NODE",
    "PRE_ADMISSION_HOST_DOC_READ",
    "LIVE_MAIN_REBIND",
    "PROMPT_SHADOW_SPEC",
    "MISSING_ROOT",
    "MERGE_ROOT_EXECUTION",
    "MERGE_EXECUTION_STATE",
    "MERGE_STATE_SURFACE",
    "MERGE_SURFACE_FAILURE",
    "EXECUTION_LINGERS_ACTIVE",
    "SURFACE_PRE_BOOTSTRAP",
    "STATE_NO_RELOAD",
    "STALE_INTERACTION_ALLOWED",
    "BRIDGE_INFERRED_FROM_TOOLS",
    "UNVERIFIED_PROMOTED",
    "LOCAL_SUFFICIENCY_BYPASS",
    "RECEIPT_SYNTHESIS",
    "ARTIFACT_HIDDEN",
    "DASHBOARD_SUBSTITUTES_DELIVERY",
    "RECOVERY_WITHOUT_FRESH_PROBE",
    "SCRATCH_IMPLIES_DELIVERY",
    "GUI_CREATES_STATE",
    "BLOCKER_BEFORE_FALLBACK",
    "CONTRACT_NODE_OUTSIDE_PIN",
    "PROMPT_OVER_8000",
)


def partitions(items):
    if not items:
        yield ()
        return
    first, *rest = items
    for tail in partitions(rest):
        yield ((first,),) + tail
        for i in range(len(tail)):
            block = tuple(sorted(tail[i] + (first,), key=CONCERNS.index))
            candidate = list(tail)
            candidate[i] = block
            candidate = tuple(sorted(candidate, key=lambda b: min(CONCERNS.index(x) for x in b)))
            yield candidate


def unique_partitions():
    seen = set()
    out = []
    for p in partitions(list(CONCERNS)):
        canonical = tuple(tuple(block) for block in p)
        if canonical not in seen:
            seen.add(canonical)
            out.append(canonical)
    return out


PARTITIONS = unique_partitions()
DISCRETE = tuple((item,) for item in CONCERNS)
DISCRETE_INDEX = PARTITIONS.index(DISCRETE)


def partition_is_lifecycle_minimal(partition):
    # A loaded normative file is wholly binding. Concerns with different activation
    # signatures cannot share a file without over-activating one concern.
    for block in partition:
        signatures = {ACTIVATION_SIGNATURES[name] for name in block}
        if len(signatures) != 1:
            return False
    return True


def evaluate_hypothesis(partition, flags):
    defects = []
    if not partition_is_lifecycle_minimal(partition):
        defects.append("ACTIVATION_LEAKAGE")
    for name, value in zip(FLAGS, flags):
        if not value:
            defects.append(name)
    return not defects, defects


def hypothesis_from_code(code):
    flags_space = 1 << len(FLAGS)
    pidx, mask = divmod(code, flags_space)
    partition = PARTITIONS[pidx]
    flags = tuple(bool(mask & (1 << i)) for i in range(len(FLAGS)))
    return partition, flags


def canonical_code():
    flags_space = 1 << len(FLAGS)
    return DISCRETE_INDEX * flags_space + (flags_space - 1)


def canonical_contract():
    return {
        "authority_nodes_added": 0,
        "pre_admission_host_docs": False,
        "live_main_rebind": False,
        "prompt_boot_rom": True,
        "root_present": True,
        "partition": [list(block) for block in DISCRETE],
        "activation_exact": True,
        "state_reload": True,
        "stale_interaction_allowed": False,
        "bridge_observed": True,
        "unverified_promoted": False,
        "local_sufficiency": True,
        "receipt_synthesis": False,
        "artifact_hidden": False,
        "dashboard_substitutes_delivery": False,
        "fresh_probe": True,
        "scratch_implies_delivery": False,
        "gui_creates_state": False,
        "blocker_before_fallback": False,
        "same_revision": True,
        "prompt_chars": 7603,
    }


def validate_contract(c):
    if c["authority_nodes_added"] != 0: return False
    if c["pre_admission_host_docs"]: return False
    if c["live_main_rebind"]: return False
    if not c["prompt_boot_rom"] or not c["root_present"]: return False
    partition = tuple(tuple(block) for block in c["partition"])
    if not partition_is_lifecycle_minimal(partition): return False
    if partition != DISCRETE: return False
    if not c["activation_exact"]: return False
    if not c["state_reload"] or c["stale_interaction_allowed"]: return False
    if not c["bridge_observed"] or c["unverified_promoted"]: return False
    if not c["local_sufficiency"] or c["receipt_synthesis"]: return False
    if c["artifact_hidden"] or c["dashboard_substitutes_delivery"]: return False
    if not c["fresh_probe"] or c["scratch_implies_delivery"]: return False
    if c["gui_creates_state"] or c["blocker_before_fallback"]: return False
    if not c["same_revision"] or c["prompt_chars"] > 8000: return False
    return True


def mutate(base, family):
    c = json.loads(json.dumps(base))
    if family == "NEW_AUTHORITY_NODE": c["authority_nodes_added"] = 1
    elif family == "PRE_ADMISSION_HOST_DOC_READ": c["pre_admission_host_docs"] = True
    elif family == "LIVE_MAIN_REBIND": c["live_main_rebind"] = True
    elif family == "PROMPT_SHADOW_SPEC": c["prompt_boot_rom"] = False
    elif family == "MISSING_ROOT": c["root_present"] = False
    elif family.startswith("MERGE_"):
        pair = {
            "MERGE_ROOT_EXECUTION": ("ROOT", "EXECUTION"),
            "MERGE_EXECUTION_STATE": ("EXECUTION", "STATE"),
            "MERGE_STATE_SURFACE": ("STATE", "SURFACE"),
            "MERGE_SURFACE_FAILURE": ("SURFACE", "FAILURE_RECOVERY"),
        }[family]
        rest = [[x] for x in CONCERNS if x not in pair]
        c["partition"] = [list(pair), *rest]
    elif family in ("EXECUTION_LINGERS_ACTIVE", "SURFACE_PRE_BOOTSTRAP"): c["activation_exact"] = False
    elif family == "STATE_NO_RELOAD": c["state_reload"] = False
    elif family == "STALE_INTERACTION_ALLOWED": c["stale_interaction_allowed"] = True
    elif family == "BRIDGE_INFERRED_FROM_TOOLS": c["bridge_observed"] = False
    elif family == "UNVERIFIED_PROMOTED": c["unverified_promoted"] = True
    elif family == "LOCAL_SUFFICIENCY_BYPASS": c["local_sufficiency"] = False
    elif family == "RECEIPT_SYNTHESIS": c["receipt_synthesis"] = True
    elif family == "ARTIFACT_HIDDEN": c["artifact_hidden"] = True
    elif family == "DASHBOARD_SUBSTITUTES_DELIVERY": c["dashboard_substitutes_delivery"] = True
    elif family == "RECOVERY_WITHOUT_FRESH_PROBE": c["fresh_probe"] = False
    elif family == "SCRATCH_IMPLIES_DELIVERY": c["scratch_implies_delivery"] = True
    elif family == "GUI_CREATES_STATE": c["gui_creates_state"] = True
    elif family == "BLOCKER_BEFORE_FALLBACK": c["blocker_before_fallback"] = True
    elif family == "CONTRACT_NODE_OUTSIDE_PIN": c["same_revision"] = False
    elif family == "PROMPT_OVER_8000": c["prompt_chars"] = 8001
    else: raise AssertionError(family)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypotheses", type=int, default=100000)
    ap.add_argument("--mutations", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=2026090201)
    ap.add_argument("--out")
    args = ap.parse_args()

    total_space = len(PARTITIONS) * (1 << len(FLAGS))
    if not 1 <= args.hypotheses <= total_space:
        raise SystemExit(f"hypotheses must be 1..{total_space}")
    rng = random.Random(args.seed)
    codes = {canonical_code()}
    while len(codes) < args.hypotheses:
        codes.add(rng.randrange(total_space))

    survivors = []
    defect_counts = Counter()
    digest = hashlib.sha256()
    for code in sorted(codes):
        partition, flags = hypothesis_from_code(code)
        ok, defects = evaluate_hypothesis(partition, flags)
        if ok:
            survivors.append(code)
        defect_counts.update(defects)
        digest.update(f"{code}|{int(ok)}|{','.join(defects)}\n".encode())

    base = canonical_contract()
    if not validate_contract(base):
        raise SystemExit("canonical contract does not validate")
    killed = Counter()
    mutation_survivors = []
    for i in range(args.mutations):
        family = MUTATION_FAMILIES[i % len(MUTATION_FAMILIES)] if i < len(MUTATION_FAMILIES) else rng.choice(MUTATION_FAMILIES)
        mutant = mutate(base, family)
        dead = not validate_contract(mutant)
        if dead:
            killed[family] += 1
        else:
            mutation_survivors.append((i, family))
        digest.update(f"M|{i}|{family}|{int(dead)}\n".encode())

    result = {
        "schema": "juriscribe-local-environment-stress/v1",
        "status": "PASS" if survivors == [canonical_code()] and not mutation_survivors else "FAIL",
        "seed": args.seed,
        "claim_scope": CLAIM_SCOPE,
        "hypothesis_space": total_space,
        "hypotheses_executed": len(codes),
        "hypotheses_surviving": len(survivors),
        "canonical_survivor_only": survivors == [canonical_code()],
        "minimal_normative_nodes": len(CONCERNS),
        "concerns": list(CONCERNS),
        "distinct_activation_signatures": len(set(ACTIVATION_SIGNATURES.values())),
        "partitions_considered_in_space": len(PARTITIONS),
        "mutation_instances": args.mutations,
        "mutation_families": len(MUTATION_FAMILIES),
        "mutants_killed": sum(killed.values()),
        "mutation_survivors": len(mutation_survivors),
        "family_kills": dict(sorted(killed.items())),
        "digest": digest.hexdigest(),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

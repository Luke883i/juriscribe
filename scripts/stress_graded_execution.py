from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter


def run(cases: int, seed: int) -> dict:
    rng = random.Random(seed)
    violations = 0
    outcomes = Counter()
    for _ in range(cases):
        method = rng.random() < 0.93
        installed = rng.random() < 0.22
        local = rng.random() < 0.18
        connected = rng.random() < 0.55
        public = rng.random() < 0.82
        python = rng.random() < 0.70
        bridge = rng.random() < 0.62
        requested = "ATTESTED" if rng.random() < 0.5 else "LEAN"
        runtime = installed or (python and bridge and (local or connected or public))
        if runtime:
            outcome = "ATTESTED"
        elif method and requested == "LEAN":
            outcome = "LEAN"
        elif method:
            outcome = "OFFER_LEAN"
        else:
            outcome = "METHOD_UNAVAILABLE"
        if method and outcome == "METHOD_UNAVAILABLE":
            violations += 1
        if outcome == "LEAN" and requested != "LEAN":
            violations += 1
        outcomes[outcome] += 1
    payload = {
        "schema": "juriscribe-graded-execution-stress/v1",
        "cases": cases,
        "seed": seed,
        "oracle_mismatches": violations,
        "outcomes": dict(sorted(outcomes.items())),
        "claim_scope": "SYNTHETIC_CAPABILITY_AND_POLICY_TRACES_NOT_PHYSICAL_HOST_OR_LEGAL_SESSIONS",
    }
    payload["digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=int, default=100000)
    p.add_argument("--seed", type=int, default=202609032211)
    args = p.parse_args()
    result = run(args.cases, args.seed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["oracle_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

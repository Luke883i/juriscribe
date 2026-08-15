from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_v5.py"
SELECTOR_VERSION = "sha256-stable-roundrobin-v2"


class StableRandom:
    """Small randrange-compatible generator with cross-version stable output."""

    def __init__(self, seed: int):
        self.seed = int(seed)
        self.counter = 0

    def randrange(self, stop: int) -> int:
        if stop <= 0:
            raise ValueError("stop must be positive")
        payload = f"juriscribe-v5-rng|{self.seed}|{self.counter}|{stop}".encode("utf-8")
        self.counter += 1
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % stop


def _load_simulator():
    spec = importlib.util.spec_from_file_location("juriscribe_simulate_v5_base", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load simulate_v5.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case_rng(seed: int, category_index: int, case_index: int) -> StableRandom:
    payload = f"{seed}|{category_index}|{case_index}".encode("utf-8")
    derived = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return StableRandom(derived)


def run(cases: int, seeds: tuple[int, ...]) -> dict:
    module = _load_simulator()
    categories = tuple(module.CATEGORIES)
    if cases % len(categories):
        raise ValueError("case count must be divisible by five categories")
    per = cases // len(categories)
    failures = []
    category_counts = Counter()
    family_counts = Counter()
    seed_counts = Counter()
    accepted_controls = 0
    killed_mutants = 0

    for cidx, category in enumerate(categories):
        families = module.FAMILIES[category]
        for j in range(per):
            seed = seeds[(j + cidx) % len(seeds)]
            seed_counts[str(seed)] += 1
            family = families[j % len(families)]
            rng = _case_rng(seed, cidx, j)
            ok = False
            try:
                ok = bool(module.evaluate(category, family, rng))
            except Exception as exc:
                if len(failures) < 100:
                    failures.append({"category": category, "family": family, "index": j, "seed": seed, "error": type(exc).__name__ + ": " + str(exc)})
            category_counts[category] += 1
            family_counts[f"{category}:{family}"] += 1
            if ok:
                if category == "favorable":
                    accepted_controls += 1
                else:
                    killed_mutants += 1
            elif len(failures) < 100:
                failures.append({"category": category, "family": family, "index": j, "seed": seed, "error": "unexpected outcome"})

    scenario_basis = {
        "selector": SELECTOR_VERSION,
        "cases": cases,
        "seeds": list(seeds),
        "criteria": module.CRITERIA,
        "families": module.FAMILIES,
        "category_counts": dict(category_counts),
        "family_counts": dict(sorted(family_counts.items())),
    }
    scenario_digest = hashlib.sha256(
        json.dumps(scenario_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "juriscribe-validation/simulation-v5",
        "requested": cases,
        "executed": cases,
        "categories": dict(category_counts),
        "criteria": module.CRITERIA,
        "families": module.FAMILIES,
        "family_counts": dict(sorted(family_counts.items())),
        "seeds": list(seeds),
        "seed_case_counts": dict(seed_counts),
        "killed_mutants": killed_mutants,
        "accepted_controls": accepted_controls,
        "failures": failures,
        "escapes": len(failures),
        "false_positives": 0 if not failures else sum(1 for f in failures if f["category"] == "favorable"),
        "scenario_digest": scenario_digest,
        "selector": SELECTOR_VERSION,
        "passed": not failures,
        "interpretation": "property/mutation/stress evidence over runtime gates; not 400,000 substantive legal judgments or LLM calls",
    }


def main() -> int:
    module = _load_simulator()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=400000)
    parser.add_argument("--seeds", default=",".join(map(str, module.DEFAULT_SEEDS)))
    parser.add_argument("--json-out")
    args = parser.parse_args()
    seeds = tuple(int(x) for x in args.seeds.split(",") if x.strip())
    result = run(args.cases, seeds)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

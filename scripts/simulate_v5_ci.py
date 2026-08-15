from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_v5.py"
SELECTOR_VERSION = "sha256-stable-random-v1"


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
    module.random.Random = StableRandom
    return module


def run(cases: int, seeds: tuple[int, ...]) -> dict:
    module = _load_simulator()
    result = module.run(cases, seeds)
    result["selector"] = SELECTOR_VERSION
    basis = {
        "selector": SELECTOR_VERSION,
        "cases": result["executed"],
        "seeds": result["seeds"],
        "criteria": result["criteria"],
        "families": result["families"],
        "category_counts": result["categories"],
        "family_counts": result["family_counts"],
    }
    result["scenario_digest"] = hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result


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

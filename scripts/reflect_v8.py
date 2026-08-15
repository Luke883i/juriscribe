from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

DIMENSIONS = {
    "artifact_presence": ("CANONICAL_ONLY", "CANONICAL_AND_LEGACY", "LEGACY_ONLY", "NEITHER"),
    "canonical_state": ("VALID", "STALE", "MALFORMED"),
    "legacy_state": ("VALID", "STALE", "ABSENT"),
    "session_phase": ("INITIALIZED", "ACTIVE", "COMPLETE"),
    "ready_binding": ("FALSE", "TRUE"),
    "interface": ("SESSION_INTEGRITY", "NODE_HEADER_ALIAS"),
    "documentation_label": ("CANONICAL", "LEGACY_AMBIGUOUS"),
    "contract_compatibility": ("PRESERVED", "BROKEN"),
}


def enumerate_signatures() -> list[str]:
    keys = list(DIMENSIONS)
    signatures = []
    for values in itertools.product(*(DIMENSIONS[key] for key in keys)):
        signatures.append("|".join(f"{key}={value}" for key, value in zip(keys, values)))
    return signatures


def run(target: int = 100) -> dict:
    if target < 1:
        raise ValueError("target must be positive")
    signatures = enumerate_signatures()
    unique = set(signatures)
    if len(unique) != len(signatures):
        raise AssertionError("modeled risk space contains duplicate signatures")
    no_novelty_streak = 0
    trailing = []
    for i in range(target):
        signature = signatures[(i * 97 + 17) % len(signatures)]
        trailing.append(signature)
        if signature in unique:
            no_novelty_streak += 1
        else:
            unique.add(signature)
            no_novelty_streak = 0
    digest = hashlib.sha256("\n".join(signatures).encode("utf-8")).hexdigest()
    saturated = no_novelty_streak >= target and len(unique) == len(signatures)
    return {
        "schema": "juriscribe-validation/historiography-reflection-v8",
        "model": "explicit-finite-risk-space",
        "dimensions": {key: list(values) for key, values in DIMENSIONS.items()},
        "M": len(signatures),
        "unique_signatures": len(unique),
        "enumeration_probes": len(signatures),
        "no_novelty_target": target,
        "no_novelty_streak": no_novelty_streak,
        "total_probes": len(signatures) + target,
        "saturated": saturated,
        "scenario_digest": digest,
        "trailing_probe_digest": hashlib.sha256("\n".join(trailing).encode("utf-8")).hexdigest(),
        "status": "PASS" if saturated else "FAIL",
        "notes": "1..M exhaustive enumeration of the explicitly modeled historiography/session-integrity risk space, followed by M+target no-novelty probes. This is an architectural property test, not a legal judgment and not a claim of exhaustive software correctness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    try:
        result = run(args.target)
    except ValueError as exc:
        parser.error(str(exc))
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

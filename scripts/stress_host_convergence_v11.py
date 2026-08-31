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

from juriscribe.host_bootstrap import classify_host_reachability

STATES = ("AVAILABLE", "UNAVAILABLE", "UNVERIFIED")
CAPS = (
    "RUNTIME_IMPORT", "REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE",
    "SESSION_CONTEXT", "LOCAL_SCRATCH_IO", "DOCX_WRITE", "DOCX_READBACK",
    "CHAT_ATTACHMENT_WRITE", "LOCAL_FILE_DELIVERY",
)
PROVIDERS = ("chatgpt-like", "api-agent", "local-llm", "browser-agent", "unknown")
BROWSERS = ("chrome", "edge", "safari", "firefox", "mobile-webview", "none")
OS_NAMES = ("windows", "macos", "linux", "ios", "android", "unknown")


def available(caps, name):
    return caps.get(name) == "AVAILABLE"


def oracle(caps, *, revision_pinned, contract_pinned, installed_bound):
    discovery = revision_pinned and contract_pinned
    source = all(available(caps, name) for name in ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"))
    transport = installed_bound or source
    memory = available(caps, "SESSION_CONTEXT")
    fs = available(caps, "LOCAL_SCRATCH_IO")
    bootstrap = discovery and transport and (memory or fs)
    work = bootstrap
    materialization = work and fs and available(caps, "DOCX_WRITE") and available(caps, "DOCX_READBACK")
    delivery_surface = available(caps, "CHAT_ATTACHMENT_WRITE") or available(caps, "LOCAL_FILE_DELIVERY")
    delivery = materialization and delivery_surface
    recovery = work and fs and delivery_surface
    return (discovery, bootstrap, work, materialization, delivery, recovery)


def edge_case(rng):
    caps = {
        "RUNTIME_IMPORT": "UNAVAILABLE", "REPOSITORY_READ": "AVAILABLE", "PYTHON_EXECUTION": "AVAILABLE",
        "SOURCE_TO_RUNTIME_BRIDGE": "AVAILABLE", "SESSION_CONTEXT": "AVAILABLE", "LOCAL_SCRATCH_IO": "UNAVAILABLE",
        "DOCX_WRITE": "UNVERIFIED", "DOCX_READBACK": "UNVERIFIED", "CHAT_ATTACHMENT_WRITE": "UNVERIFIED",
        "LOCAL_FILE_DELIVERY": "UNVERIFIED",
    }
    for _ in range(rng.choice((1, 1, 2, 3))):
        caps[rng.choice(CAPS)] = rng.choice(STATES)
    return caps, rng.random() > 0.025, rng.random() > 0.025, rng.random() < 0.12


def typical_case(rng):
    kind = rng.choices(("rich-chat", "local", "web-only", "mobile", "installed"), weights=(35, 25, 15, 10, 15))[0]
    caps = {name: "UNVERIFIED" for name in CAPS}
    if kind == "rich-chat":
        caps.update(REPOSITORY_READ="AVAILABLE", PYTHON_EXECUTION="AVAILABLE", SOURCE_TO_RUNTIME_BRIDGE="AVAILABLE", SESSION_CONTEXT="AVAILABLE")
    elif kind == "local":
        caps.update(REPOSITORY_READ="AVAILABLE", PYTHON_EXECUTION="AVAILABLE", SOURCE_TO_RUNTIME_BRIDGE="AVAILABLE", LOCAL_SCRATCH_IO="AVAILABLE", LOCAL_FILE_DELIVERY="AVAILABLE")
    elif kind == "web-only":
        caps.update(REPOSITORY_READ="AVAILABLE", PYTHON_EXECUTION="UNAVAILABLE", SOURCE_TO_RUNTIME_BRIDGE="UNAVAILABLE", SESSION_CONTEXT="AVAILABLE")
    elif kind == "mobile":
        caps.update(REPOSITORY_READ="AVAILABLE", PYTHON_EXECUTION="UNAVAILABLE", SESSION_CONTEXT="AVAILABLE")
    else:
        caps.update(RUNTIME_IMPORT="AVAILABLE", SESSION_CONTEXT="AVAILABLE")
    if kind in {"rich-chat", "local", "installed"}:
        for name, p in (("DOCX_WRITE", .88), ("DOCX_READBACK", .88), ("CHAT_ATTACHMENT_WRITE", .62)):
            caps[name] = "AVAILABLE" if rng.random() < p else "UNVERIFIED"
        if kind != "rich-chat" and rng.random() < .85:
            caps["LOCAL_SCRATCH_IO"] = "AVAILABLE"
            caps["LOCAL_FILE_DELIVERY"] = "AVAILABLE"
    installed_bound = kind == "installed" and rng.random() < .96
    return caps, rng.random() < .998, rng.random() < .998, installed_bound


def stress_case(rng):
    caps = {name: rng.choices(STATES, weights=(1, 6, 3))[0] for name in CAPS}
    return caps, rng.random() < .75, rng.random() < .75, rng.random() < .08


def run(campaign, count, seed):
    rng = random.Random(seed)
    maker = {"edge": edge_case, "typical": typical_case, "stress": stress_case}[campaign]
    mismatches = 0
    ready = [0] * 6
    signatures = set()
    digest = hashlib.sha256()
    for _ in range(count):
        caps, revision_pinned, contract_pinned, installed_bound = maker(rng)
        provider, browser, os_name = rng.choice(PROVIDERS), rng.choice(BROWSERS), rng.choice(OS_NAMES)
        expected = oracle(caps, revision_pinned=revision_pinned, contract_pinned=contract_pinned, installed_bound=installed_bound)
        result = classify_host_reachability(
            caps,
            revision_pinned=revision_pinned,
            contract_pinned=contract_pinned,
            installed_runtime_bound=installed_bound,
            provider=provider,
            browser=browser,
            os_name=os_name,
        )
        actual = (
            result.discovery_ready, result.bootstrap_ready, result.work_ready,
            result.materialization_ready, result.delivery_ready, result.recovery_ready,
        )
        if actual != expected:
            mismatches += 1
        for i, value in enumerate(actual):
            ready[i] += int(value)
        signature = tuple(caps[name] for name in CAPS) + (revision_pinned, contract_pinned, installed_bound)
        signatures.add(signature)
        digest.update((repr(signature) + repr(actual) + "\n").encode())
    return {
        "schema": "juriscribe-host-convergence-stress/v1",
        "campaign": campaign,
        "seed": seed,
        "cases": count,
        "unique_signatures": len(signatures),
        "oracle_mismatches": mismatches,
        "ready_counts": dict(zip(("discovery", "bootstrap", "work", "materialization", "delivery", "recovery"), ready)),
        "scenario_digest": digest.hexdigest(),
        "claim_scope": "EXECUTED_CAPABILITY_LIFECYCLE_MUTATIONS_NOT_PHYSICAL_PROVIDER_OR_LEGAL_SESSIONS",
        "status": "PASS" if mismatches == 0 else "FAIL",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", choices=("edge", "typical", "stress"), required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--out")
    a = p.parse_args()
    result = run(a.campaign, a.count, a.seed)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())

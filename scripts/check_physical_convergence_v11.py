from __future__ import annotations

import ast
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.host_bootstrap import CANONICAL_REPOSITORY_URL, classify_host_reachability, parse_bootstrap_intent
from juriscribe.modes import MODES


def fail(message):
    raise SystemExit("PHYSICAL CONVERGENCE V1.1 CHECK FAIL: " + message)


def available(c, name):
    return c.get(name) == "AVAILABLE"


def oracle(c, rp, cp, ib):
    source = all(available(c, k) for k in ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"))
    carrier = available(c, "SESSION_CONTEXT") or available(c, "LOCAL_SCRATCH_IO")
    boot = rp and cp and (ib or source) and carrier
    mat = boot and available(c, "LOCAL_SCRATCH_IO") and available(c, "DOCX_WRITE") and available(c, "DOCX_READBACK")
    surface = available(c, "CHAT_ATTACHMENT_WRITE") or available(c, "LOCAL_FILE_DELIVERY")
    return {"bootstrap": boot, "materialization": mat, "delivery": mat and surface, "recovery": boot and available(c, "LOCAL_SCRATCH_IO") and surface}


def mutants(c, rp, cp, ib, provider, browser, os_name):
    source = all(available(c, k) for k in ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"))
    carrier = available(c, "SESSION_CONTEXT") or available(c, "LOCAL_SCRATCH_IO")
    base = rp and cp and (ib or source) and carrier
    fs = available(c, "LOCAL_SCRATCH_IO")
    write = available(c, "DOCX_WRITE")
    readback = available(c, "DOCX_READBACK")
    surface = available(c, "CHAT_ATTACHMENT_WRITE") or available(c, "LOCAL_FILE_DELIVERY")
    return {
        "IGNORE_REVISION_PIN": ("bootstrap", cp and (ib or source) and carrier),
        "IGNORE_CONTRACT_PIN": ("bootstrap", rp and (ib or source) and carrier),
        "UNVERIFIED_IS_AVAILABLE": ("bootstrap", rp and cp and (ib or all(c.get(k) != "UNAVAILABLE" for k in ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"))) and carrier),
        "REPO_READ_IS_EXECUTION": ("bootstrap", rp and cp and (ib or available(c, "REPOSITORY_READ")) and carrier),
        "BRIDGE_OPTIONAL": ("bootstrap", rp and cp and (ib or (available(c, "REPOSITORY_READ") and available(c, "PYTHON_EXECUTION"))) and carrier),
        "PYTHON_OPTIONAL": ("bootstrap", rp and cp and (ib or (available(c, "REPOSITORY_READ") and available(c, "SOURCE_TO_RUNTIME_BRIDGE"))) and carrier),
        "STATE_CARRIER_OPTIONAL": ("bootstrap", rp and cp and (ib or source)),
        "SESSION_CONTEXT_REQUIRED": ("bootstrap", rp and cp and (ib or source) and available(c, "SESSION_CONTEXT")),
        "FILESYSTEM_REQUIRED_FOR_BOOTSTRAP": ("bootstrap", rp and cp and (ib or source) and fs),
        "INSTALLED_UNBOUND_ALLOWED": ("bootstrap", rp and cp and (available(c, "RUNTIME_IMPORT") or source) and carrier),
        "DOCX_WRITE_OPTIONAL": ("materialization", base and fs and readback),
        "DOCX_READBACK_OPTIONAL": ("materialization", base and fs and write),
        "SCRATCH_OPTIONAL_FOR_MATERIALIZATION": ("materialization", base and write and readback),
        "DELIVERY_SURFACE_OPTIONAL": ("delivery", base and fs and write and readback),
        "RECOVERY_MEMORY_ONLY": ("recovery", base and available(c, "SESSION_CONTEXT") and surface),
        "RECOVERY_WITHOUT_DELIVERY": ("recovery", base and fs),
        "BOOTSTRAP_IMPLIES_DELIVERY": ("delivery", base),
        "PROVIDER_PRIVILEGE": ("bootstrap", base or provider == "chatgpt-like"),
        "BROWSER_PRIVILEGE": ("bootstrap", base or browser == "chrome"),
        "OS_PRIVILEGE": ("bootstrap", base or os_name == "windows"),
    }


def imported_modules(source):
    tree = ast.parse(source)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.append(node.module or "")
            if any(alias.name == "*" for alias in node.names):
                out.append("*")
    return out


def main():
    pipeline = (ROOT / "juriscribe/pipeline.py").read_text(encoding="utf-8")
    runtime_cli = (ROOT / "juriscribe/runtime_cli.py").read_text(encoding="utf-8")
    orchestrator = (ROOT / "juriscribe/orchestrator.py").read_text(encoding="utf-8")
    for source in (pipeline, runtime_cli, orchestrator):
        ast.parse(source)
    pipeline_imports = imported_modules(pipeline)
    runtime_cli_imports = imported_modules(runtime_cli)
    orchestrator_imports = imported_modules(orchestrator)
    if any(name.endswith("pipeline_v11") or name.endswith("pipeline_v9") for name in pipeline_imports):
        fail("public pipeline imports historical pipeline modules")
    if any(name.endswith("pipeline_v11") or name.endswith("pipeline_v9") for name in runtime_cli_imports):
        fail("current runtime CLI delegates to historical pipeline modules")
    if "*" in pipeline_imports or "*" in orchestrator_imports:
        fail("public composition contains star import")
    if tuple(MODES) != ("CONTINUATION", "GREENFIELD", "REVIEW", "COMPRESSION & CONSOLIDATION"):
        fail("canonical modes drifted")
    if parse_bootstrap_intent("Initialize Juriscribe")["repository"] != CANONICAL_REPOSITORY_URL:
        fail("bare initialize intent does not bind canonical repository")
    if parse_bootstrap_intent("Inizializza Juriscribe https://github.com/Luke883i/juriscribe")["bypasses_acceptance"]:
        fail("host UX alias bypasses acceptance")
    try:
        parse_bootstrap_intent("Initialize Juriscribe https://github.com/example/other")
    except ValueError:
        pass
    else:
        fail("non-canonical repository accepted")

    rng = random.Random(11012026)
    caps_names = (
        "RUNTIME_IMPORT", "REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE",
        "SESSION_CONTEXT", "LOCAL_SCRATCH_IO", "DOCX_WRITE", "DOCX_READBACK",
        "CHAT_ATTACHMENT_WRITE", "LOCAL_FILE_DELIVERY",
    )
    states = ("AVAILABLE", "UNAVAILABLE", "UNVERIFIED")
    killed = {name: False for name in mutants({k: "UNVERIFIED" for k in caps_names}, False, False, False, "x", "x", "x")}
    platform_mismatches = 0
    oracle_mismatches = 0
    for _ in range(10000):
        c = {k: rng.choice(states) for k in caps_names}
        rp = bool(rng.getrandbits(1))
        cp = bool(rng.getrandbits(1))
        ib = bool(rng.getrandbits(1)) and available(c, "RUNTIME_IMPORT")
        provider = rng.choice(("chatgpt-like", "other"))
        browser = rng.choice(("chrome", "safari"))
        os_name = rng.choice(("windows", "linux"))
        expected = oracle(c, rp, cp, ib)
        a = classify_host_reachability(c, revision_pinned=rp, contract_pinned=cp, installed_runtime_bound=ib, provider=provider, browser=browser, os_name=os_name)
        actual = {"bootstrap": a.bootstrap_ready, "materialization": a.materialization_ready, "delivery": a.delivery_ready, "recovery": a.recovery_ready}
        oracle_mismatches += int(actual != expected)
        b = classify_host_reachability(c, revision_pinned=rp, contract_pinned=cp, installed_runtime_bound=ib, provider="different", browser="different", os_name="different")
        platform_mismatches += int((a.bootstrap_ready, a.materialization_ready, a.delivery_ready, a.recovery_ready) != (b.bootstrap_ready, b.materialization_ready, b.delivery_ready, b.recovery_ready))
        for name, (target, value) in mutants(c, rp, cp, ib, provider, browser, os_name).items():
            if value != expected[target]:
                killed[name] = True
    survivors = [name for name, dead in killed.items() if not dead]
    if oracle_mismatches:
        fail(f"deep reachability oracle mismatches: {oracle_mismatches}")
    if platform_mismatches:
        fail(f"provider/browser/OS identity changed readiness: {platform_mismatches}")
    if survivors:
        fail("semantic mutation survivors: " + ", ".join(survivors))
    print(json.dumps({
        "status": "PASS",
        "canonical_modes": list(MODES),
        "public_version_chain": 0,
        "public_star_imports": 0,
        "deep_cases": 10000,
        "mutation_families": len(killed),
        "mutants_killed": sum(killed.values()),
        "survivors": survivors,
        "platform_identity_invariance": True,
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

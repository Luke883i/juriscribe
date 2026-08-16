from __future__ import annotations

import argparse
import html
import json
import random
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe import dashboard
from juriscribe.editorial_artifacts import build_dashboard_inference_view
from juriscribe.evidence_traceability import (
    build_dashboard_evidence_coverage,
    evidence_traceability_gate,
)
from juriscribe.modes import required_artifact_roles

DEFAULT_SEEDS = [17, 31, 53, 79, 113, 157, 211, 269, 337, 401, 463, 541, 617, 701, 809, 919, 1031, 1151, 1297, 1429]
MODES = ("CONTINUATION", "GREENFIELD", "REVIEW")


def _leaf_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _leaf_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _leaf_strings(item)
    elif value not in (None, ""):
        yield str(value)


def _scenario_seed(index: int, base_seed: int) -> int:
    return (index + 1) * 1_000_003 + base_seed


def _state(seed: int, index: int):
    rng = random.Random(seed)
    mode = MODES[index % len(MODES)]
    review_output = "REPORT_AND_REVISED_TEXT" if rng.random() < 0.5 else "REPORT_ONLY"
    setup = {"accepted": {"document_type": "LEGAL_MONOGRAPH", "audience": "giuristi", "review_output": review_output}}
    source_count = rng.randint(1, 3)
    claim_count = rng.randint(1, 4)
    sources = [
        {"id": f"S{n}", "title": f"Fonte {n} scenario {index}", "source_type": "constitutional_court" if n == 1 else "leading_treatise", "court_or_author": f"Organo {n}", "jurisdiction": "Italia", "date": f"202{n}-01-01"}
        for n in range(1, source_count + 1)
    ]
    claims = []
    units = []
    provenance = []
    for n in range(1, claim_count + 1):
        cid = f"C{n}"
        sid = sources[(n - 1) % source_count]["id"]
        inferred = n == claim_count and claim_count > 1
        text = f"Proposizione {n} scenario {index} seed {seed}."
        claims.append({
            "id": cid, "text": text, "claim_type": "strong_inference" if inferred else "legal_rule",
            "support_source_ids": [sid], "premise_claim_ids": ["C1"] if inferred and cid != "C1" else [],
            "inference_bridge": "Ponte inferenziale esplicito." if inferred else None,
            "status": "INFERRED" if inferred else "VERIFIED", "material": True,
            "source_evidence": [{"source_id": sid, "pinpoint": f"p. {n}", "proposition": f"Contenuto attestato {n}."}],
        })
        units.append({"id": cid, "kind": "INFERENCE" if inferred else "RULE", "text": text, "status": "INFERRED" if inferred else "VERIFIED", "material": True})
        provenance.append({"id": cid, "kind": "INFERENCE" if inferred else "CLAIM", "proposition": text, "evidence_refs": [sid], "premise_ids": ["C1"] if inferred and cid != "C1" else [], "inference_bridge": "Ponte inferenziale esplicito." if inferred else None, "artifact_locators": [f"§ {n}.1"]})

    expected_roles = required_artifact_roles(mode, setup) - {"session_dashboard"}
    workspace = f"/tmp/juriscribe-evidence-sim/SES-{seed}"
    artifacts = [
        {"id": role, "role": role, "path": f"{workspace}/artifacts/{role}.docx", "readback": "PASS", "required": True, "delivery_class": "ATTACH"}
        for role in expected_roles
    ]
    primary_role = "final_chapter" if mode == "CONTINUATION" else ("final_legal_text" if mode == "GREENFIELD" else "review_report")
    evidence = []
    evidence_count = rng.randint(1, min(3, claim_count))
    for n in range(evidence_count):
        claim = claims[n]
        source_id = claim["support_source_ids"][0]
        evidence.append({
            "evidence_id": f"EV-{index}-{n}",
            "claim_id": claim["id"],
            "artifact_locator": f"§ {n + 1}.1",
            "source_ids": [source_id],
            "pinpoints": [f"p. {n + 1}"],
            "status": "VERIFIED" if not claim["claim_type"] == "strong_inference" else "INFERRED",
            "artifact_role": primary_role,
            "evidence_kind": "simulazione di tracciabilita",
            "marker": f"marker-{seed}-{n}",
        })

    broken_kind = "none"
    roll = rng.random()
    if roll < 0.08:
        broken_kind = ("claim", "source", "artifact", "locator")[index % 4]
        target = evidence[0]
        if broken_kind == "claim": target["claim_id"] = f"MISSING-C-{index}"
        elif broken_kind == "source": target["source_ids"] = [f"MISSING-S-{index}"]
        elif broken_kind == "artifact": target["artifact_role"] = f"missing_role_{index}"
        elif broken_kind == "locator": target["artifact_locator"] = ""

    return SimpleNamespace(
        request={"raw": f"Scenario {index}", "summary": f"Scenario epistemico {index}"},
        mode=mode, mode_selection={}, mode_contract={}, editorial_standard={"document_type": "LEGAL_MONOGRAPH", "audience": "giuristi", "rules": {"stable_terminology": True}},
        corpus=[], sources=sources, bibliography={}, epistemic_units=units, relations=[], reticulum={}, generation_contract={}, continuation={}, drafts=[],
        review={"cycles": [], "regenerations": [], "saturation": {}, "status": "SATURATED"}, final_review={}, provenance={"entries": provenance}, contradictions=[], mining={}, style_profile={}, setup=setup, source_intelligence={},
        claim_ledger=claims, artifact_evidence=evidence, quality={}, benchmark={}, simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
        phase="VALIDATING", interaction={}, completion={"eligible": rng.random() > 0.35}, node_integrity={}, runtime={"workspace_base": workspace}, artifacts=artifacts,
    ), broken_kind, expected_roles


def run(cases: int, seeds: list[int], json_out: str | None = None) -> dict:
    if cases < 1:
        raise ValueError("cases must be positive")
    if not seeds:
        raise ValueError("at least one base seed is required")
    seen_seeds = set()
    mode_counts = Counter()
    broken_counts = Counter()
    rendered = 0
    passed = 0
    with tempfile.TemporaryDirectory() as tmp:
        render_path = Path(tmp) / "dashboard.html"
        for index in range(cases):
            base_seed = seeds[index % len(seeds)]
            seed = _scenario_seed(index, base_seed)
            if seed in seen_seeds:
                raise AssertionError(f"duplicate scenario seed: {seed}")
            seen_seeds.add(seed)
            state, broken_kind, expected_roles = _state(seed, index)
            mode_counts[state.mode] += 1
            broken_counts[broken_kind] += 1
            aggregate = build_dashboard_inference_view(state)
            coverage = build_dashboard_evidence_coverage(state, aggregate)
            trace = coverage["evidence_traceability"]
            if trace["copertura"]["evidenze_registrate"] != len(state.artifact_evidence):
                raise AssertionError("registered evidence count mismatch")
            if trace["copertura"]["evidenze_proiettate"] != len(state.artifact_evidence):
                raise AssertionError("artifact evidence was lost in projection")
            for raw, projected in zip(state.artifact_evidence, trace["records"]):
                projected_text = repr(projected)
                for leaf in _leaf_strings(raw):
                    if leaf not in projected_text:
                        raise AssertionError(f"artifact-evidence leaf lost: {leaf}")
            index_roles = {item["ruolo"] for item in coverage["artifact_index"]["records"]}
            if index_roles != set(expected_roles):
                raise AssertionError(f"artifact index mismatch: {index_roles} != {set(expected_roles)}")
            if coverage["esito_complessivo"]["artefatti_richiamabili"] != len(expected_roles):
                raise AssertionError("available artifact count mismatch")
            gate_ok, _ = evidence_traceability_gate(state)
            if gate_ok != (broken_kind == "none"):
                raise AssertionError(f"traceability gate mismatch for {broken_kind}")
            if index % 100 == 0:
                dashboard.render_session_dashboard(state, render_path)
                body = render_path.read_text(encoding="utf-8").split("<body>", 1)[1].split("</body>", 1)[0]
                if "Esito complessivo" not in body or "Registro di tracciabilita delle evidenze di artefatto" not in body:
                    raise AssertionError("dashboard coverage sections missing")
                for record in trace["records"]:
                    marker = html.escape(str(record.get("riferimento_evidenza")), quote=True)
                    if marker not in body:
                        raise AssertionError("dashboard omitted a projected evidence record")
                for forbidden in (state.runtime["workspace_base"], "workspace_base", "sha256", "readback"):
                    if forbidden in body:
                        raise AssertionError(f"technical dashboard leakage: {forbidden}")
                rendered += 1
            passed += 1
    result = {
        "schema": "juriscribe-dashboard-evidence-simulation/v1",
        "status": "PASS",
        "cases": cases,
        "passed": passed,
        "unique_scenario_seeds": len(seen_seeds),
        "base_seeds": seeds,
        "mode_counts": dict(sorted(mode_counts.items())),
        "broken_reference_cases": dict(sorted(broken_counts.items())),
        "rendered_dashboard_samples": rendered,
        "invariants": [
            "artifact_evidence lossless projection",
            "all required user-facing artifacts indexed",
            "compressed outcome counts consistent",
            "broken references fail closed without disappearing",
            "sampled rendered dashboards contain every projected evidence record",
            "technical paths and telemetry absent from dashboard body",
        ],
    }
    if result["unique_scenario_seeds"] != cases:
        raise AssertionError("scenario seeds are not unique")
    if json_out:
        Path(json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=10000)
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    result = run(args.cases, seeds, args.json_out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

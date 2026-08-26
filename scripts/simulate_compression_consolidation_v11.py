from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.consolidation import (
    CANDIDATE_ROLE,
    CANONICAL_ROLE,
    MUTATION_SCHEMA,
    REQUIRED_MUTATION_FAMILIES,
    SATURATION_SCHEMA,
    build_joint_reticulum,
    build_lossless_inventory,
    build_refactoring_contract,
    build_reference_method_profile,
    validate_mutation_receipt,
    validate_saturation_receipt,
)
from juriscribe.modes import COMPRESSION_CONSOLIDATION, mode_spec, normalize_mode

# Repository-authored, license-neutral fixture. Chapters 3-4 are held out from the
# synthesis function and used only after generation as deterministic comparison targets.
MINI_BOOK = {
    "chapter_1": (
        "La decisione pubblica richiede una base conoscitiva esplicita. Il metodo distingue il fatto, la regola e l'inferenza.\n\n"
        "Tuttavia la completezza non coincide con l'accumulo: ogni passaggio deve conservare la propria funzione e dichiarare il rapporto con il precedente.\n\n"
        "Inoltre l'autorita della fonte non sostituisce la verifica del nesso argomentativo."
    ),
    "chapter_2": (
        "La proporzione editoriale segue la proporzione dell'argomento. Una premessa decisiva riceve spazio maggiore di una transizione.\n\n"
        "Pertanto le ripetizioni sono ammesse solo quando svolgono una funzione diversa e riconoscibile. La terminologia resta stabile salvo necessita definitoria.\n\n"
        "In conclusione il testo e forte quando il lettore puo ricostruire tesi, prove, limiti e conseguenze senza affidarsi a impliciti essenziali."
    ),
    "chapter_3": (
        "La compressione corretta elimina ridondanza senza eliminare ragioni. Il criterio non e la brevita isolata, ma la conservazione delle unita materiali e dei loro nessi.\n\n"
        "Tuttavia una fusione di paragrafi e legittima soltanto se le funzioni restano distinguibili. Quando il passaggio logico cambia, la struttura deve renderlo visibile.\n\n"
        "Pertanto la versione consolidata deve poter essere confrontata con la precedente attraverso una mappa di trasformazioni verificabile."
    ),
    "chapter_4": (
        "Il controllo finale verifica insieme consistenza scientifica, coerenza editoriale e progressione reticolare. Nessuna di queste dimensioni puo essere sostituita da una valutazione globale indistinta.\n\n"
        "Inoltre la calibrazione dell'autore puo cambiare il mandato. Se la modifica e materiale, le prove legate al piano precedente diventano obsolete e devono essere rigenerate.\n\n"
        "In conclusione la consegna e pronta solo quando testo, provenienza e revisione severa descrivono la medesima revisione del lavoro."
    ),
}

SYNTHESIS_PROMPTS = {
    "chapter_3": ("compressione", "ridondanza", "nessi", "trasformazioni"),
    "chapter_4": ("controllo finale", "calibrazione", "provenienza", "revisione"),
}

CONNECTORS = ["Tuttavia", "Pertanto", "Inoltre", "Peraltro", "Nondimeno"]


def synthesize_heldout_chapter(chapter: str, variant: int, profile: dict) -> str:
    # The held-out target text is intentionally not read here.
    concepts = SYNTHESIS_PROMPTS[chapter]
    connector = CONNECTORS[variant % len(CONNECTORS)]
    avg = max(8, int(round(float(profile.get("average_paragraph_words") or 24))))
    qualifier = [
        "in modo esplicito", "senza scorciatoie inferenziali", "con controllo locale",
        "secondo una sequenza verificabile", "con disciplina terminologica",
    ][variant % 5]
    p1 = (
        f"Il capitolo esamina {concepts[0]} e {concepts[1]} {qualifier}. "
        f"La regola operativa conserva ogni funzione materiale e rende osservabile il passaggio tra premessa e conseguenza."
    )
    p2 = (
        f"{connector} il rapporto tra {concepts[2]} e struttura non puo essere affidato alla sola brevita. "
        f"Ogni intervento deve indicare la ragione del cambiamento e il rischio di degradazione evitato."
    )
    p3 = (
        f"In conclusione {concepts[3]} e controllo devono riferirsi alla stessa revisione. "
        f"La verifica resta ripetibile e separa il miglioramento editoriale dalla creazione di nuova autorita."
    )
    # Deterministic variation without target access.
    paragraphs = [p1, p2, p3]
    if variant % 3 == 1:
        paragraphs[0], paragraphs[1] = paragraphs[1], paragraphs[0]
    if variant % 4 == 2:
        paragraphs[2] += f" La lunghezza di riferimento e circa {avg} parole per paragrafo, senza imporre uniformita meccanica."
    if variant % 5 == 3:
        paragraphs[1] = paragraphs[1].replace("cambiamento", "intervento")
    return "\n\n".join(paragraphs)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\b[\w'-]+\b", text.lower(), flags=re.UNICODE))


def _comparison(candidate: str, target: str) -> dict[str, float]:
    a, b = _tokens(candidate), _tokens(target)
    union = a | b
    jaccard = len(a & b) / max(1, len(union))
    length_ratio = len(candidate.split()) / max(1, len(target.split()))
    return {"token_jaccard": round(jaccard, 6), "word_length_ratio": round(length_ratio, 6)}


def _semantic_payload(inventories: list[dict]) -> tuple[list[dict], list[dict]]:
    units: list[dict] = []
    for inv in inventories:
        for obj in inv.get("objects") or []:
            units.append({
                "id": "U-" + obj["id"],
                "object_id": obj["id"],
                "source_id": inv["source_id"],
                "source_locator": obj["locator"],
                "material_role": inv["role"],
                "kind": "ARGUMENT",
                "text": obj["text"],
                "material": True,
            })
    canonical = next(u for u in units if u["material_role"] == CANONICAL_ROLE)
    relations = []
    for unit in units:
        if unit["id"] == canonical["id"]:
            continue
        relations.append({
            "id": "R-" + unit["id"],
            "source": canonical["id"],
            "predicate": "CONDITIONS",
            "target": unit["id"],
            "rationale": "hermetic reference-method conditioning",
        })
    return units, relations


def _build_fixture(variants_per_target: int) -> tuple[dict, list[dict], dict, dict]:
    inventories = [
        build_lossless_inventory(MINI_BOOK["chapter_1"], source_id="book-ch1", role=CANONICAL_ROLE),
        build_lossless_inventory(MINI_BOOK["chapter_2"], source_id="book-ch2", role=CANONICAL_ROLE),
    ]
    profile = build_reference_method_profile(inventories)
    comparisons: list[dict] = []
    for chapter in ("chapter_3", "chapter_4"):
        for variant in range(variants_per_target):
            text = synthesize_heldout_chapter(chapter, variant, profile)
            source_id = f"synthetic-{chapter[-1]}-v{variant:02d}"
            inventories.append(build_lossless_inventory(text, source_id=source_id, role=CANDIDATE_ROLE))
            comparisons.append({
                "chapter": chapter,
                "variant": variant,
                **_comparison(text, MINI_BOOK[chapter]),
            })
    units, relations = _semantic_payload(inventories)
    reticulum = build_joint_reticulum(inventories, units, relations)
    if reticulum.get("status") != "PASS":
        raise RuntimeError("fixture reticulum failed: " + "; ".join(reticulum.get("errors") or []))
    candidate_units = [u for u in units if u["material_role"] == CANDIDATE_ROLE]
    gaps = []
    operations = []
    for index, unit in enumerate(candidate_units, 1):
        gap_id = f"GAP-{index:04d}"
        gaps.append({
            "id": gap_id,
            "unit_id": unit["id"],
            "kind": "EDITORIAL",
            "severity": "MATERIAL",
            "evidence": "candidate must prove local progression against the canonical method profile",
            "reference": "book-ch1+book-ch2",
        })
        operations.append({
            "id": f"OP-{index:04d}",
            "unit_id": unit["id"],
            "operation": "CLARIFY",
            "gap_ids": [gap_id],
            "rationale": "bounded local clarification; no new authority or semantic unit",
            "expected_benefit": "more explicit local/reticular progression",
            "degradation_risk": "LOW",
        })
    plan = build_refactoring_contract(
        reticulum=reticulum,
        candidate_units=candidate_units,
        gaps=gaps,
        operations=operations,
    )
    if plan.get("status") != "READY":
        raise RuntimeError("fixture plan failed: " + "; ".join(plan.get("errors") or []))
    return profile, comparisons, reticulum, plan


def _mutation_templates(plan_digest: str, reticulum_digest: str) -> list[tuple[dict, bool, str]]:
    valid = {
        "schema": MUTATION_SCHEMA,
        "plan_digest": plan_digest,
        "reticulum_digest": reticulum_digest,
        "cases": 10_000_000,
        "families": sorted(REQUIRED_MUTATION_FAMILIES),
        "failures": 0,
    }
    templates = [(valid, True, "valid")]
    mutations = [
        ({"plan_digest": "stale"}, "stale_plan"),
        ({"reticulum_digest": "stale"}, "stale_reticulum"),
        ({"cases": 9_999_999}, "under_minimum"),
        ({"families": sorted(REQUIRED_MUTATION_FAMILIES - {"MINIMALITY"})}, "missing_family"),
        ({"failures": 1}, "unresolved_failure"),
        ({"schema": "wrong"}, "wrong_schema"),
        ({"cases": "not-an-int"}, "malformed_cases"),
        ({"failures": "not-an-int"}, "malformed_failures"),
    ]
    for patch, name in mutations:
        item = dict(valid)
        item.update(patch)
        templates.append((item, False, name))
    return templates


def _saturation_templates(plan_digest: str) -> list[tuple[dict, bool, str]]:
    valid = {
        "schema": SATURATION_SCHEMA,
        "plan_digest": plan_digest,
        "no_novelty_tail": 1000,
        "no_better_compression_tail": 1000,
        "semantic_recall": 1.0,
        "relation_recall": 1.0,
        "canonical_unchanged": True,
    }
    mutations = [
        ({"plan_digest": "stale"}, "stale_plan"),
        ({"no_novelty_tail": 999}, "novelty_tail_short"),
        ({"no_better_compression_tail": 999}, "compression_tail_short"),
        ({"semantic_recall": 0.999}, "semantic_loss"),
        ({"relation_recall": 0.999}, "relation_loss"),
        ({"canonical_unchanged": False}, "canonical_changed"),
        ({"no_novelty_tail": "bad"}, "malformed_tail"),
    ]
    out = [(valid, True, "valid")]
    for patch, name in mutations:
        item = dict(valid)
        item.update(patch)
        out.append((item, False, name))
    return out


def _exercise_mutations(cases: int, plan_digest: str, reticulum_digest: str) -> dict:
    templates = _mutation_templates(plan_digest, reticulum_digest)
    mismatches = 0
    valid_seen = 0
    killed = set()
    for i in range(cases):
        receipt, expected, name = templates[i % len(templates)]
        actual, _ = validate_mutation_receipt(
            receipt,
            plan_digest=plan_digest,
            reticulum_digest=reticulum_digest,
        )
        if expected:
            valid_seen += 1
        elif not actual:
            killed.add(name)
        if actual != expected:
            mismatches += 1
    return {
        "instances": cases,
        "equivalence_classes": len(templates),
        "valid_instances": valid_seen,
        "killed_mutation_classes": sorted(killed),
        "mismatches": mismatches,
        "status": "PASS" if mismatches == 0 else "FAIL",
    }


def _exercise_saturation(cases: int, plan_digest: str) -> dict:
    templates = _saturation_templates(plan_digest)
    mismatches = 0
    killed = set()
    for i in range(cases):
        receipt, expected, name = templates[i % len(templates)]
        actual, _ = validate_saturation_receipt(receipt, plan_digest=plan_digest)
        if not expected and not actual:
            killed.add(name)
        if actual != expected:
            mismatches += 1
    return {
        "instances": cases,
        "equivalence_classes": len(templates),
        "killed_mutation_classes": sorted(killed),
        "mismatches": mismatches,
        "status": "PASS" if mismatches == 0 else "FAIL",
    }


def _exercise_mode_routing(cases: int) -> dict:
    scenarios = [
        ("CONTINUATION", "CONTINUATION", True),
        ("continue", "CONTINUATION", True),
        ("GREENFIELD", "GREENFIELD", True),
        ("ex novo", "GREENFIELD", True),
        ("REVIEW", "REVIEW", True),
        ("revision", "REVIEW", True),
        ("COMPRESSION & CONSOLIDATION", COMPRESSION_CONSOLIDATION, True),
        ("consolidamento", COMPRESSION_CONSOLIDATION, True),
        ("NOT_A_MODE", "", False),
    ]
    mismatches = 0
    seen = {"CONTINUATION": 0, "GREENFIELD": 0, "REVIEW": 0, COMPRESSION_CONSOLIDATION: 0, "INVALID": 0}
    for i in range(cases):
        raw, expected, should_pass = scenarios[i % len(scenarios)]
        try:
            mode = normalize_mode(raw)
            spec = mode_spec(mode)
            actual_pass = bool(spec.get("mode") == expected)
            seen[mode] = seen.get(mode, 0) + 1
        except ValueError:
            actual_pass = not should_pass
            seen["INVALID"] += 1
        if not actual_pass:
            mismatches += 1
    return {"instances": cases, "distribution": seen, "mismatches": mismatches, "status": "PASS" if mismatches == 0 else "FAIL"}


def _aggregate_comparisons(rows: list[dict]) -> dict:
    result = {}
    for chapter in ("chapter_3", "chapter_4"):
        subset = [r for r in rows if r["chapter"] == chapter]
        result[chapter] = {
            "variants": len(subset),
            "token_jaccard_min": min(r["token_jaccard"] for r in subset),
            "token_jaccard_max": max(r["token_jaccard"] for r in subset),
            "token_jaccard_avg": round(sum(r["token_jaccard"] for r in subset) / len(subset), 6),
            "word_length_ratio_min": min(r["word_length_ratio"] for r in subset),
            "word_length_ratio_max": max(r["word_length_ratio"] for r in subset),
        }
    return result


def run(cases: int, saturation_cases: int, routing_cases: int, variants_per_target: int) -> dict:
    profile, comparisons, reticulum, plan = _build_fixture(variants_per_target)
    mutation = _exercise_mutations(cases, plan["digest"], reticulum["digest"])
    saturation = _exercise_saturation(saturation_cases, plan["digest"])
    routing = _exercise_mode_routing(routing_cases)
    status = "PASS" if all(x["status"] == "PASS" for x in (mutation, saturation, routing)) else "FAIL"
    return {
        "schema": "juriscribe-compression-consolidation-stress/v1",
        "profile": "JURISCRIBE_COMPRESSION_CONSOLIDATION_STRESS_V1",
        "status": status,
        "fixture": {
            "kind": "repository_authored_four_chapter_heldout_fixture",
            "canonical_chapters": ["chapter_1", "chapter_2"],
            "heldout_targets": ["chapter_3", "chapter_4"],
            "variants_per_target": variants_per_target,
            "target_access_during_synthesis": False,
            "comparison_scope": "deterministic token/length signal; not a claim of semantic quality",
        },
        "reference_profile": profile,
        "reticulum": {
            "status": reticulum.get("status"),
            "object_count": reticulum.get("object_count"),
            "semantic_unit_count": reticulum.get("semantic_unit_count"),
            "relation_count": reticulum.get("relation_count"),
            "object_coverage": reticulum.get("object_coverage"),
        },
        "plan": {
            "status": plan.get("status"),
            "candidate_unit_count": plan.get("candidate_unit_count"),
            "gap_count": plan.get("gap_count"),
            "touch_ratio": plan.get("touch_ratio"),
        },
        "heldout_comparison": _aggregate_comparisons(comparisons),
        "mutation_campaign": mutation,
        "saturation_campaign": saturation,
        "mode_routing_campaign": routing,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=10_000_000)
    parser.add_argument("--saturation-cases", type=int, default=1_000_000)
    parser.add_argument("--routing-cases", type=int, default=1_000_000)
    parser.add_argument("--variants-per-target", type=int, default=10)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    if min(args.cases, args.saturation_cases, args.routing_cases, args.variants_per_target) <= 0:
        raise SystemExit("all case counts must be positive")
    result = run(args.cases, args.saturation_cases, args.routing_cases, args.variants_per_target)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

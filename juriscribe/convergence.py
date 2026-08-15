from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass
class ConvergenceMonitor:
    semantic_no_novelty_streak: int = 0
    strategy_no_improvement_streak: int = 0
    dod_no_novelty_streak: int = 0
    reflection_no_novelty_streak: int = 0
    semantic_target: int = 1000
    strategy_target: int = 1000
    dod_target: int = 10000
    reflection_target: int = 1000
    observed_signatures: set[str] = field(default_factory=set)

    def semantic_probe(self, novelty, new_contradiction=False):
        self.semantic_no_novelty_streak = 0 if novelty or new_contradiction else self.semantic_no_novelty_streak + 1
        return self.semantic_saturated

    def strategy_probe(self, material_improvement):
        self.strategy_no_improvement_streak = 0 if material_improvement else self.strategy_no_improvement_streak + 1
        return self.strategy_saturated

    def dod_probe(self, novelty_vs_dod, blocking_failure=False):
        self.dod_no_novelty_streak = 0 if novelty_vs_dod or blocking_failure else self.dod_no_novelty_streak + 1
        return self.dod_saturated

    def reflection_probe(self, novelty):
        self.reflection_no_novelty_streak = 0 if novelty else self.reflection_no_novelty_streak + 1
        return self.reflection_saturated

    def observe_signature(self, signature):
        novelty = signature not in self.observed_signatures
        self.observed_signatures.add(signature)
        return novelty

    @property
    def semantic_saturated(self): return self.semantic_no_novelty_streak >= self.semantic_target
    @property
    def strategy_saturated(self): return self.strategy_no_improvement_streak >= self.strategy_target
    @property
    def dod_saturated(self): return self.dod_no_novelty_streak >= self.dod_target
    @property
    def reflection_saturated(self): return self.reflection_no_novelty_streak >= self.reflection_target


def all_dods_done(dods: Iterable[dict]):
    blocking = [d for d in dods if d.get("blocking", True)]
    return bool(blocking) and all(d.get("status") == "DONE" for d in blocking)


def completion_gate(
    dods: list[dict], metrics: dict, contradictions: list[dict], *,
    quality: dict[str, Any] | None = None,
    source_coverage: str | None = None,
    benchmark: dict[str, Any] | None = None,
    benchmark_required: bool = False,
    artifacts: list[dict] | None = None,
    generation_required: bool = False,
    reticulum: dict[str, Any] | None = None,
    generation_contract: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
    compression: dict[str, Any] | None = None,
    setup: dict[str, Any] | None = None,
    admission: dict[str, Any] | None = None,
    drafts: list[dict[str, Any]] | None = None,
    review: dict[str, Any] | None = None,
    bibliography: dict[str, Any] | None = None,
    continuation: dict[str, Any] | None = None,
    continuation_required: bool = False,
    provenance: dict[str, Any] | None = None,
    final_review: dict[str, Any] | None = None,
    corpus: list[dict[str, Any]] | None = None,
    normative_frame_digest: str | None = None,
    bootstrap_required: bool = False,
    finalization_required: bool = False,
) -> dict:
    from .benchmark import benchmark_gate
    from .bibliography import bibliography_gate
    from .bootstrap import bootstrap_gate
    from .continuation import continuation_gate
    from .final_review import final_review_gate
    from .generation import compression_valid, validate_simulation_receipt
    from .provenance import canonical_digest as provenance_digest, final_artifact_gate, provenance_gate
    from .reticulum import generation_contract_valid
    from .review import review_gate

    reasons: list[str] = []
    open_contra = [c for c in contradictions if c.get("blocking", True) and c.get("status", "OPEN") != "RESOLVED"]
    if not all_dods_done(dods): reasons.append("not all blocking DoD are DONE")
    if int(metrics.get("dod_no_novelty_streak", 0)) < 10000: reasons.append("M+10000 no-novelty evidence vs DoD not reached")
    if open_contra: reasons.append("blocking contradictions remain open")
    if quality and quality.get("status") != "PASS": reasons.append("chapter quality review/failure remains unresolved")
    if source_coverage is not None and source_coverage not in {"PASS", "NOT_REQUIRED"}: reasons.append("claim/source coverage is not closed")
    bg = benchmark_gate(benchmark, required=benchmark_required)
    if not bg["eligible"]: reasons.append("blind monograph benchmark integrity/coverage failed")
    if artifacts and [a for a in artifacts if a.get("required", True) and a.get("readback") != "PASS"]: reasons.append("required artifact readback failed")

    review_summary = {"eligible": True, "errors": []}
    bibliography_summary = {"eligible": True, "errors": []}
    continuation_summary = {"eligible": not continuation_required, "errors": []}
    bootstrap_summary = {"eligible": not bootstrap_required, "errors": []}
    provenance_summary = {"eligible": not finalization_required, "errors": []}
    final_review_summary = {"eligible": not finalization_required, "errors": []}
    artifact_summary = {"eligible": not finalization_required, "errors": []}

    if generation_required:
        if not admission or admission.get("status") != "ACCEPTED": reasons.append("valid human admission state is required")
        if bootstrap_required:
            ok_boot, boot_errors = bootstrap_gate(admission)
            bootstrap_summary = {"eligible": ok_boot, "errors": boot_errors}
            if not ok_boot: reasons.extend(boot_errors)
        if not reticulum or reticulum.get("status") != "PASS": reasons.append("validated epistemic reticulum is required")
        ok_contract, contract_errors = generation_contract_valid(generation_contract, reticulum or {}, setup or {})
        if not ok_contract: reasons.extend(contract_errors)

        final_artifacts = [a for a in (artifacts or []) if a.get("role") == "final_chapter"]
        if not final_artifacts: reasons.append("final chapter artifact is missing")
        elif any(a.get("readback") != "PASS" for a in final_artifacts): reasons.append("final chapter artifact readback failed")

        drafts = list(drafts or [])
        if not drafts:
            reasons.append("sealed candidate history is required")
            current_digest = ""
        else:
            current = drafts[-1]
            current_digest = str(current.get("digest", ""))
            if current.get("stage") != "COMPRESSED_FINAL": reasons.append("current candidate is not the sealed COMPRESSED_FINAL draft")
            if not any(d.get("stage") == "INITIAL" for d in drafts): reasons.append("initial sealed draft is missing")
            if not any(d.get("stage") == "REGENERATED" for d in drafts): reasons.append("at least one regenerated draft is required")

        if continuation_required:
            ok_cont, cont_errors = continuation_gate(continuation, generation_contract_digest=(generation_contract or {}).get("contract_digest"), candidate_digest=current_digest or None)
            continuation_summary = {"eligible": ok_cont, "errors": cont_errors}
            if not ok_cont: reasons.extend(cont_errors)

        precompression_digest = str((review or {}).get("saturation", {}).get("candidate_digest", ""))
        ok_review, review_errors = review_gate(review, expected_candidate_digest=precompression_digest or None, require_regeneration=True)
        review_summary = {"eligible": ok_review, "errors": review_errors}
        if not ok_review: reasons.extend(review_errors)

        contract_digest = (generation_contract or {}).get("contract_digest")
        ok_comp, comp_errors = compression_valid(compression, expected_before_digest=precompression_digest or None, expected_after_digest=current_digest or None, generation_contract_digest=contract_digest, strict=True)
        if not ok_comp: reasons.extend(comp_errors)
        ok_sim, sim_errors = validate_simulation_receipt(simulation, candidate_digest=current_digest or None, generation_contract_digest=contract_digest, require_categories=True)
        if not ok_sim: reasons.extend(sim_errors)

        if not quality or quality.get("status") != "PASS":
            if "chapter quality review/failure remains unresolved" not in reasons: reasons.append("chapter quality PASS evidence is required")
        elif current_digest and quality.get("candidate_digest") != current_digest:
            reasons.append("quality evidence bound to stale candidate")
        if source_coverage not in {"PASS", "NOT_REQUIRED"} and "claim/source coverage is not closed" not in reasons:
            reasons.append("claim/source coverage is not closed")

        ok_bib, bib_errors = bibliography_gate(bibliography)
        bibliography_summary = {"eligible": ok_bib, "errors": bib_errors}
        if not ok_bib: reasons.extend(bib_errors)

        if finalization_required:
            corpus_digest = provenance_digest(corpus or [])
            ok_prov, prov_errors = provenance_gate(provenance, candidate_digest=current_digest or None, corpus_digest=corpus_digest)
            provenance_summary = {"eligible": ok_prov, "errors": prov_errors}
            if not ok_prov: reasons.extend(prov_errors)
            prov_digest = (provenance or {}).get("digest")
            ok_final, final_errors = final_review_gate(
                final_review,
                candidate_digest=current_digest or None,
                corpus_digest=corpus_digest,
                provenance_digest=prov_digest,
                normative_frame_digest=normative_frame_digest,
            )
            final_review_summary = {"eligible": ok_final, "errors": final_errors}
            if not ok_final: reasons.extend(final_errors)
            ok_art, art_errors = final_artifact_gate(artifacts)
            artifact_summary = {"eligible": ok_art, "errors": art_errors}
            if not ok_art: reasons.extend(art_errors)

    return {
        "eligible": not reasons,
        "reason": "PASS" if not reasons else "; ".join(dict.fromkeys(reasons)),
        "benchmark_gate": bg,
        "review_gate": review_summary,
        "bibliography_gate": bibliography_summary,
        "continuation_gate": continuation_summary,
        "bootstrap_gate": bootstrap_summary,
        "provenance_gate": provenance_summary,
        "final_review_gate": final_review_summary,
        "final_artifact_gate": artifact_summary,
    }

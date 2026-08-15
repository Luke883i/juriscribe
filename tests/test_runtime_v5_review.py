import tempfile
import unittest
from pathlib import Path

from juriscribe.bibliography import assess_bibliography, bibliography_gate
from juriscribe.generation import (
    REQUIRED_EDGE_FAMILIES,
    REQUIRED_SIMULATION_CATEGORIES,
    audit_compression,
    seal_candidate,
    text_digest,
    validate_simulation_receipt,
)
from juriscribe.node_header import render_node_header, validate_node_header
from juriscribe.review import (
    REVIEW_CRITERIA,
    ReviewSaturationMonitor,
    build_review_cycle,
    regeneration_record,
    review_gate,
)
from juriscribe.reticulum import build_generation_contract, validate_reticulum
from juriscribe.session import Workspace


def scorecard(value=0.95):
    return {key: value for key in REVIEW_CRITERIA}

def review_evidence():
    return [{"criterion":key,"evidence_type":"artifact" if key in {"STRUCTURE","EDITORIAL_STYLE","AUDIENCE_FIT"} else "reticulum","status":"VERIFIED","locator":f"evidence:{key}"} for key in REVIEW_CRITERIA]


def reticulum_fixture():
    units = [
        {"id":"U1","kind":"RULE","text":"Regola A","source_id":"S1","source_locator":"§1 ¶1","chapter":"1","material":True,"tags":["preserve"]},
        {"id":"U2","kind":"QUALIFICATION","text":"Limite A","source_id":"S1","source_locator":"§1 ¶2","chapter":"1","material":True},
        {"id":"U3","kind":"OPEN_ISSUE","text":"Questione B","source_id":"S2","source_locator":"§2 ¶5","chapter":"2","material":True,"tags":["develop"]},
    ]
    relations = [
        {"source":"U2","predicate":"QUALIFIES","target":"U1"},
        {"source":"U1","predicate":"ANTICIPATES","target":"U3"},
    ]
    return units, relations


def generation_contract():
    units, relations = reticulum_fixture()
    ret = validate_reticulum(units, relations, source_ids={"S1","S2"}).record()
    setup = {"status":"ACCEPTED","accepted":{"length_words":[1000,1400],"chapter_function":"sviluppo"}}
    return ret, setup, build_generation_contract(ret, setup, units, relations), units


class ReviewLoopTests(unittest.TestCase):
    def test_review_requires_all_criteria_and_candidate_binding(self):
        cycle = build_review_cycle(cycle=1, candidate_digest="a"*64, findings=[], scorecard=scorecard(), evidence=review_evidence())
        self.assertEqual(cycle["status"], "PASS_CANDIDATE")
        ok, errors = review_gate({"cycles":[cycle], "saturation":{}}, expected_candidate_digest="b"*64)
        self.assertFalse(ok)
        self.assertTrue(any("stale" in e for e in errors))

    def test_major_finding_forces_regeneration(self):
        finding = {"id":"F1","criterion":"INTERCHAPTER_COHERENCE","severity":"MAJOR","kind":"contradiction","artifact_locator":"§3 ¶2","status":"OPEN","proposed_action":"riallineare la tesi"}
        cycle = build_review_cycle(cycle=1, candidate_digest="a"*64, findings=[finding], scorecard=scorecard(), evidence=review_evidence())
        self.assertEqual(cycle["status"], "REGENERATE_REQUIRED")

    def test_regeneration_rejects_loss_or_new_material(self):
        rec = regeneration_record(cycle=1, from_digest="a", to_digest="b", addressed_finding_ids=["F1"], preserved_required_unit_ids=["U1"], required_unit_ids=["U1","U2"], introduced_material_unit_ids=["NEW"])
        self.assertEqual(rec["status"], "REAUDIT_REQUIRED")
        self.assertEqual(rec["lost_required_unit_ids"], ["U2"])

    def test_review_saturation_requires_p_plus_10000_both_axes(self):
        monitor = ReviewSaturationMonitor.create()
        monitor.probe(signature="novel-1", new_finding=True, material_improvement=True, degradation=False)
        for _ in range(9999):
            self.assertFalse(monitor.probe(signature="novel-1", new_finding=False, material_improvement=False, degradation=False))
        self.assertTrue(monitor.probe(signature="novel-1", new_finding=False, material_improvement=False, degradation=False))
        receipt = monitor.receipt(candidate_digest="a"*64)
        self.assertEqual(receipt["P"], 1)
        self.assertEqual(receipt["status"], "PASS")

    def test_review_gate_requires_pass_candidate_and_saturation(self):
        digest = "a"*64
        cycle = build_review_cycle(cycle=1, candidate_digest=digest, findings=[], scorecard=scorecard(), evidence=review_evidence())
        saturation = {"candidate_digest":digest,"P":7,"probes":10007,"no_novelty_streak":10000,"no_improvement_without_degradation_streak":10000,"target":10000,"open_blockers":0,"open_majors":0,"degradation_escapes":0,"status":"PASS"}
        self.assertTrue(review_gate({"cycles":[cycle],"saturation":saturation}, expected_candidate_digest=digest)[0])

    def test_review_rejects_cosmetic_scorecard_without_criterion_evidence(self):
        evidence = review_evidence()[:-1]
        with self.assertRaises(ValueError):
            build_review_cycle(cycle=1, candidate_digest="a"*64, findings=[], scorecard=scorecard(), evidence=evidence)

    def test_regeneration_must_address_finding_from_its_source_cycle(self):
        initial = "a"*64
        regenerated = "b"*64
        finding = {"id":"F1","criterion":"INTERCHAPTER_COHERENCE","severity":"MAJOR","kind":"drift","artifact_locator":"§2","status":"OPEN","proposed_action":"riallineare"}
        cycle1 = build_review_cycle(cycle=1, candidate_digest=initial, findings=[finding], scorecard=scorecard(), evidence=review_evidence())
        cycle2 = build_review_cycle(cycle=2, candidate_digest=regenerated, findings=[], scorecard=scorecard(), evidence=review_evidence())
        bad_regen = regeneration_record(cycle=1, from_digest=initial, to_digest=regenerated, addressed_finding_ids=["F999"], preserved_required_unit_ids=["U1"], required_unit_ids=["U1"])
        saturation = {"candidate_digest":regenerated,"P":7,"probes":10007,"no_novelty_streak":10000,"no_improvement_without_degradation_streak":10000,"target":10000,"open_blockers":0,"open_majors":0,"degradation_escapes":0,"status":"PASS"}
        ok, errors = review_gate({"cycles":[cycle1,cycle2],"regenerations":[bad_regen],"saturation":saturation}, expected_candidate_digest=regenerated, require_regeneration=True)
        self.assertFalse(ok)
        self.assertTrue(any("finding" in e.lower() for e in errors), errors)


class EvidenceBindingTests(unittest.TestCase):
    def test_simulation_is_bound_to_candidate_contract_and_five_categories(self):
        receipt = {
            "cases":400000,
            "seeds":[11,29],
            "families":sorted(REQUIRED_EDGE_FAMILIES),
            "categories":{k:80000 for k in REQUIRED_SIMULATION_CATEGORIES},
            "failures":0,"escapes":0,"false_positives":0,"status":"PASS",
            "candidate_digest":"a"*64,"generation_contract_digest":"b"*64,"scenario_digest":"c"*64,
        }
        self.assertTrue(validate_simulation_receipt(receipt,candidate_digest="a"*64,generation_contract_digest="b"*64,require_categories=True)[0])
        bad = dict(receipt, candidate_digest="d"*64)
        self.assertFalse(validate_simulation_receipt(bad,candidate_digest="a"*64,generation_contract_digest="b"*64,require_categories=True)[0])

    def test_compression_is_candidate_bound_and_rechecked(self):
        rec = audit_compression(before_words=1200, after_words=1100, required_unit_ids=["U1"], preserved_unit_ids=["U1"], before_digest="a"*64, after_digest="b"*64, generation_contract_digest="c"*64, post_compression_recheck="PASS")
        from juriscribe.generation import compression_valid
        self.assertTrue(compression_valid(rec, expected_before_digest="a"*64, expected_after_digest="b"*64, generation_contract_digest="c"*64, strict=True)[0])
        self.assertFalse(compression_valid(rec, expected_before_digest="x"*64, expected_after_digest="b"*64, generation_contract_digest="c"*64, strict=True)[0])

    def test_bibliography_is_first_class_but_optional_when_unavailable(self):
        self.assertTrue(bibliography_gate(assess_bibliography([], [], []))[0])
        source = {"id":"S1","direct_read":True,"verified_at":"2026-01-01T00:00:00Z"}
        claim = {"id":"C1","material":True,"support_source_ids":["S1"]}
        bib = assess_bibliography([{"id":"B1","source_id":"S1","citation":"Autore, Titolo (2026)"}], [source], [claim])
        self.assertEqual(bib["status"], "PASS")
        self.assertEqual(bib["coverage"], 1.0)

    def test_node_header_detects_session_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,"SES")
            state=ws.initialize("Genera capitolo", admission={"status":"ACCEPTED"})
            text=render_node_header(state.to_dict())
            self.assertTrue(validate_node_header(state.to_dict(), text)[0])
            tampered=text.replace('JURISCRIBE_PHASE "INITIALIZED"','JURISCRIBE_PHASE "COMPLETE"')
            self.assertFalse(validate_node_header(state.to_dict(), tampered)[0])


class DraftBindingTests(unittest.TestCase):
    def test_sealed_draft_is_bound_to_generation_contract(self):
        ret, setup, contract, _ = generation_contract()
        sealed=seal_candidate("testo del capitolo",generation_contract=contract,stage="INITIAL",sequence=1)
        self.assertEqual(sealed["digest"], text_digest("testo del capitolo"))
        self.assertEqual(sealed["generation_contract_digest"], contract["contract_digest"])
        self.assertEqual(sealed["reticulum_digest"], ret["digest"])


if __name__ == "__main__":
    unittest.main()

class CompletionV5Tests(unittest.TestCase):
    def _package(self):
        from juriscribe.convergence import completion_gate
        ret, setup, contract, _ = generation_contract()
        initial = seal_candidate("bozza iniziale", generation_contract=contract, stage="INITIAL", sequence=1)
        regenerated_text = "bozza rigenerata e consolidata"
        regenerated = seal_candidate(regenerated_text, generation_contract=contract, stage="REGENERATED", sequence=2)
        finding = {"id":"F1","criterion":"INTERCHAPTER_COHERENCE","severity":"MAJOR","kind":"drift","artifact_locator":"§2","status":"OPEN","proposed_action":"riallineare la tesi"}
        cycle1 = build_review_cycle(cycle=1, candidate_digest=initial["digest"], findings=[finding], scorecard=scorecard(), evidence=review_evidence())
        regen = regeneration_record(cycle=1, from_digest=initial["digest"], to_digest=regenerated["digest"], addressed_finding_ids=["F1"], preserved_required_unit_ids=["U1"], required_unit_ids=["U1"])
        cycle2 = build_review_cycle(cycle=2, candidate_digest=regenerated["digest"], findings=[], scorecard=scorecard(), evidence=review_evidence())
        saturation={"candidate_digest":regenerated["digest"],"P":9,"probes":10009,"no_novelty_streak":10000,"no_improvement_without_degradation_streak":10000,"target":10000,"open_blockers":0,"open_majors":0,"degradation_escapes":0,"status":"PASS"}
        final=seal_candidate("bozza rigenerata consolidata",generation_contract=contract,stage="COMPRESSED_FINAL",sequence=3)
        sim={"cases":400000,"seeds":[11,29],"families":sorted(REQUIRED_EDGE_FAMILIES),"categories":{k:80000 for k in REQUIRED_SIMULATION_CATEGORIES},"failures":0,"escapes":0,"false_positives":0,"status":"PASS","candidate_digest":final["digest"],"generation_contract_digest":contract["contract_digest"],"scenario_digest":"s"*64}
        comp=audit_compression(before_words=4,after_words=3,required_unit_ids=["U1"],preserved_unit_ids=["U1"],before_digest=regenerated["digest"],after_digest=final["digest"],generation_contract_digest=contract["contract_digest"],post_compression_recheck="PASS")
        kwargs=dict(
          dods=[{"id":"D1","status":"DONE","blocking":True}],metrics={"dod_no_novelty_streak":10000},contradictions=[],
          quality={"status":"PASS","candidate_digest":final["digest"]},source_coverage="NOT_REQUIRED",
          artifacts=[{"id":"chapter-final","role":"final_chapter","required":True,"readback":"PASS"}],generation_required=True,
          reticulum=ret,generation_contract=contract,simulation=sim,compression=comp,setup=setup,admission={"status":"ACCEPTED"},
          drafts=[initial,regenerated,final],review={"cycles":[cycle1,cycle2],"regenerations":[regen],"saturation":saturation},bibliography={"status":"NOT_AVAILABLE"},
        )
        return completion_gate, kwargs

    def test_complete_requires_full_review_regeneration_chain(self):
        gate, kwargs=self._package(); result=gate(**kwargs); self.assertTrue(result["eligible"],result["reason"])

    def test_complete_fails_without_regeneration_or_final_artifact(self):
        gate, kwargs=self._package(); kwargs["review"]={**kwargs["review"],"regenerations":[]}; kwargs["drafts"]=[d for d in kwargs["drafts"] if d["stage"]!="REGENERATED"]
        result=gate(**kwargs); self.assertFalse(result["eligible"]); self.assertIn("regenerated draft",result["reason"])
        gate, kwargs=self._package(); kwargs["artifacts"]=[]; result=gate(**kwargs); self.assertFalse(result["eligible"]); self.assertIn("final chapter artifact",result["reason"])

    def test_complete_fails_on_stale_final_quality(self):
        gate, kwargs=self._package(); kwargs["quality"]={"status":"PASS","candidate_digest":"x"*64}; result=gate(**kwargs); self.assertFalse(result["eligible"]); self.assertIn("stale candidate",result["reason"])

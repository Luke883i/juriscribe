from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from juriscribe.consolidation import MUTATION_SCHEMA, SATURATION_SCHEMA
from juriscribe.consolidation_completion import evaluate_completion
from juriscribe.modes import COMPRESSION_CONSOLIDATION, MODES, required_artifact_requirements
from juriscribe.runtime_v11 import (
    apply_setup, calibrate_refactoring, freeze_dods, ingest_and_mine,
    record_consolidation_saturation, record_simulation, register_refactoring_plan,
    register_semantic_mining, seal_refined_candidate, select_mode,
)
from juriscribe.runtime_v11_review import record_final_review, record_provenance, record_review_cycle
from juriscribe.session import SessionState

FAMILIES=["LOSSLESSNESS","CANONICAL_IMMUTABILITY","RETICULUM","GAP_EVIDENCE","ARGUMENT_STRENGTH","LOCAL_PROGRESSION","RETICULAR_PROGRESSION","ANOMALY_EDGE","MINIMALITY","MATERIALIZATION_READINESS"]

class CompressionConsolidationV11Tests(unittest.TestCase):
    def _state(self, root):
        state=SessionState(session_id="SES-CC-TEST",request={"raw":"Consolida i candidati rispetto al canonico","summary":"C&C test","request_id":"REQ-CC","atoms":[]})
        state.runtime={"workspace_base":str(Path(root)/state.session_id),"capabilities":{"DOCX_WRITE":"AVAILABLE","DOCX_READBACK":"AVAILABLE"}}
        return state

    def _semantic_payload(self,state):
        units=[]
        for sid,inv in state.strategy["consolidation"]["inventories"].items():
            for obj in inv["objects"]:
                units.append({"id":"U-"+obj["id"],"object_id":obj["id"],"source_id":sid,"source_locator":obj["locator"],"material_role":inv["role"],"kind":"ARGUMENT","text":obj["text"],"material":True})
        canonical=next(u for u in units if u["material_role"]=="canonical_material")
        relations=[]
        for u in units:
            if u is canonical: continue
            relations.append({"source":canonical["id"],"predicate":"SUPPORTS","target":u["id"],"rationale":"reference conditioning"})
        return units,relations

    def test_modes_are_dynamic_and_cc_is_canonical(self):
        self.assertIn(COMPRESSION_CONSOLIDATION,MODES)

    def test_human_like_two_candidate_journey_and_staleness(self):
        with tempfile.TemporaryDirectory() as td:
            state=self._state(td); select_mode(state,"COMPRESSION & CONSOLIDATION")
            ingest_and_mine(state,"Regola canonica.\n\nMetodo canonico.",source_id="canon-A",role="canonical_material")
            ingest_and_mine(state,"Argomento candidato A ripetuto.\n\nConclusione A.",source_id="cand-A",role="candidate_material")
            ingest_and_mine(state,"Argomento candidato B.\n\nConclusione B ridondante.",source_id="cand-B",role="candidate_material")
            units,relations=self._semantic_payload(state); report=register_semantic_mining(state,units,relations)
            self.assertEqual(report["status"],"PASS"); self.assertEqual(report["object_coverage"],1.0)
            apply_setup(state); freeze_dods(state)
            reqs=required_artifact_requirements(state.mode,state.setup,state.corpus)
            refined=[x for x in reqs if x["role"]=="refined_candidate"]
            self.assertEqual({x["instance_key"] for x in refined},{"cand-A","cand-B"})
            candidate_units=[u for u in units if u["material_role"]=="candidate_material"]
            gaps=[]; ops=[]
            for i,u in enumerate(candidate_units,1):
                gid=f"GAP-{i}"; gaps.append({"id":gid,"unit_id":u["id"],"kind":"EDITORIAL","severity":"MATERIAL","evidence":"gap evidenced against canonical method","reference":"canon-A"}); ops.append({"id":f"OP-{i}","unit_id":u["id"],"operation":"CLARIFY","gap_ids":[gid],"rationale":"minimal local clarification","expected_benefit":"clearer progression","degradation_risk":"LOW"})
            plan=register_refactoring_plan(state,gaps=gaps,operations=ops)
            mutation={"schema":MUTATION_SCHEMA,"plan_digest":plan["digest"],"reticulum_digest":state.reticulum["digest"],"cases":10_000_000,"families":FAMILIES,"failures":0}
            record_simulation(state,mutation)
            saturation={"schema":SATURATION_SCHEMA,"plan_digest":plan["digest"],"no_novelty_tail":1000,"no_better_compression_tail":1000,"semantic_recall":1.0,"relation_recall":1.0,"canonical_unchanged":True}
            record_consolidation_saturation(state,saturation)
            seal_refined_candidate(state,source_id="cand-A",text="Argomento candidato A chiarito.\n\nConclusione A.",semantic_recall=1.0,relation_recall=1.0)
            seal_refined_candidate(state,source_id="cand-B",text="Argomento candidato B chiarito.\n\nConclusione B.",semantic_recall=1.0,relation_recall=1.0)
            dims={k:"PASS" for k in ["scientific_consistency","editorial_coherence","argument_strength","local_progression","reticular_progression","semantic_losslessness","canonical_conditioning"]}
            self.assertEqual(record_review_cycle(state,{"dimensions":dims,"blockers":[]})["status"],"PASS")
            dispositions=[]
            for op in plan["operations"]: dispositions.append({"id":"PRV-"+op["id"],"operation_id":op["id"],"disposition":"APPLIED_MINIMALLY"})
            dispositions.extend([{"id":"PRV-SRC-A","source_id":"cand-A","disposition":"REFINED"},{"id":"PRV-SRC-B","source_id":"cand-B","disposition":"REFINED"}])
            self.assertEqual(record_provenance(state,{"dispositions":dispositions})["status"],"PASS")
            final=record_final_review(state,{"status":"PASS","plan_digest":plan["digest"],"reticulum_digest":state.reticulum["digest"],"findings":[]})
            self.assertEqual(final["status"],"PASS")
            evaluate_completion(state)
            self.assertTrue(state.completion["eligible"],state.completion.get("reason"))
            refined_artifacts=[a for a in state.artifacts if a.get("role")=="refined_candidate"]
            self.assertEqual({a.get("instance_key") for a in refined_artifacts},{"cand-A","cand-B"})
            self.assertTrue(all(Path(a["path"]).exists() for a in refined_artifacts))
            self.assertNotIn("canon-A",{a.get("instance_key") for a in refined_artifacts})
            calibration=calibrate_refactoring(state,[{"decision":"preserva formulazione A","material":True}])
            self.assertTrue(calibration["material_change"])
            self.assertFalse(state.strategy["consolidation"]["mutation_receipt"])
            evaluate_completion(state)
            self.assertFalse(state.completion["eligible"])

if __name__=="__main__": unittest.main()

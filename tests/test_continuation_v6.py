import unittest
from juriscribe.continuation import (
    derive_continuation_plan, validate_continuation_plan,
    audit_continuation_coverage, benchmark_gap_report, continuation_gate,
)


class ContinuationV6Tests(unittest.TestCase):
    def base(self):
        units=[
            {"id":"U1","kind":"OPEN_ISSUE","tags":["develop"]},
            {"id":"U2","kind":"ARGUMENT","tags":["develop"]},
            {"id":"U3","kind":"CASE","tags":[]},
        ]
        rel=[{"source":"U2","predicate":"APPLIES_TO","target":"U3"}]
        gc={"contract_digest":"GC1","develop_unit_ids":["U1","U2"]}
        return units,rel,gc

    def test_plan_covers_contract_frontier(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        ok,errors=validate_continuation_plan(plan,gc,units)
        self.assertTrue(ok, errors)
        self.assertTrue({"U1","U2"}.issubset({u for o in plan["obligations"] for u in o["unit_ids"]}))
        self.assertTrue(plan["concrete_validation_required"])

    def test_stale_plan_fails(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel); plan["generation_contract_digest"]="OLD"
        ok,errors=validate_continuation_plan(plan,gc,units)
        self.assertFalse(ok); self.assertIn("stale generation contract", " ".join(errors))

    def test_exact_order_cannot_be_binding(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        plan["alternatives"][0]["binding_order"]=True
        ok,errors=validate_continuation_plan(plan,gc,units)
        self.assertFalse(ok); self.assertIn("exact section order", " ".join(errors))

    def test_complete_coverage_passes(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[]
        for o in plan["obligations"]:
            coverage.append({"obligation_id":o["id"],"status":"DEVELOPED","depth_score":0.9,"artifact_locator":"§1","evidence_modes":["text","comparison"]})
        report=audit_continuation_coverage(plan,coverage)
        self.assertEqual(report["status"],"PASS",report)

    def test_missing_core_fails(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[]
        for i,o in enumerate(plan["obligations"]):
            coverage.append({"obligation_id":o["id"],"status":"ABSENT" if i==0 else "DEVELOPED","depth_score":0 if i==0 else 0.9,"artifact_locator":"" if i==0 else "§1","evidence_modes":[] if i==0 else ["text"]})
        report=audit_continuation_coverage(plan,coverage)
        self.assertEqual(report["status"],"FAIL")
        self.assertTrue(report["unresolved_core"])

    def test_premature_anticipation_fails(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        plan["obligations"].append({"id":"DEV-LATER","unit_ids":["U3"],"mode":"SYNTHESIS","priority":"OPTIONAL","horizon":"LATER","deferrable":True,"rationale":"later synthesis"})
        coverage=[]
        for o in plan["obligations"]:
            if o["id"]=="DEV-U1": status,depth,loc="PARTIAL",0.4,"§1"
            elif o["id"]=="DEV-LATER": status,depth,loc="DEVELOPED",0.9,"§9"
            else: status,depth,loc="DEVELOPED",0.9,"§2"
            coverage.append({"obligation_id":o["id"],"status":status,"depth_score":depth,"artifact_locator":loc,"evidence_modes":["text"]})
        report=audit_continuation_coverage(plan,coverage)
        self.assertEqual(report["status"],"FAIL")
        self.assertIn("premature anticipation", " ".join(report["errors"]))

    def test_empty_development_frontier_fails_closed(self):
        units=[{"id":"U1","kind":"ARGUMENT","tags":[]}]
        gc={"contract_digest":"GC","develop_unit_ids":[]}
        plan=derive_continuation_plan(gc,units,[])
        self.assertEqual(plan["status"],"FAIL")
        self.assertIn("no auditable development frontier", " ".join(plan["errors"]))

    def test_weighted_coverage_floor_blocks_thin_support(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[]
        for o in plan["obligations"]:
            if o["priority"]=="CORE": status,depth,loc="DEVELOPED",0.65,"§1"
            else: status,depth,loc="ABSENT",0.0,""
            coverage.append({"obligation_id":o["id"],"status":status,"depth_score":depth,"artifact_locator":loc,"evidence_modes":["text"] if loc else []})
        report=audit_continuation_coverage(plan,coverage)
        self.assertEqual(report["status"],"FAIL")
        self.assertIn("below minimum", " ".join(report["errors"]))

    def test_bound_new_material_is_allowed_after_audit(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[{"obligation_id":o["id"],"status":"DEVELOPED","depth_score":0.9,"artifact_locator":"§1","evidence_modes":["text"]} for o in plan["obligations"]]
        report=audit_continuation_coverage(
            plan, coverage,
            introduced_material_unit_ids=["NEW-X"],
            introduced_material_bindings=[{"unit_id":"NEW-X","obligation_id":plan["obligations"][0]["id"],"status":"VERIFIED","rationale":"derived development","evidence_ref":"INF-1"}],
        )
        self.assertEqual(report["status"],"PASS",report)
        self.assertEqual(report["bound_introduced_material_unit_ids"],["NEW-X"])

    def test_unbound_new_material_requires_reaudit(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[{"obligation_id":o["id"],"status":"DEVELOPED","depth_score":0.9,"artifact_locator":"§1","evidence_modes":["text"]} for o in plan["obligations"]]
        report=audit_continuation_coverage(plan,coverage,introduced_material_unit_ids=["NEW-X"])
        self.assertEqual(report["status"],"FAIL")

    def test_benchmark_does_not_score_sequence(self):
        ref=[{"id":"pluralism","category":"thesis","weight":2,"core":True},{"id":"cases","category":"case_family","weight":2,"core":True}]
        cand=[{"id":"cases"},{"id":"pluralism"},{"id":"surplus"}]
        r=benchmark_gap_report(ref,cand)
        self.assertEqual(r["weighted_coverage"],1.0)
        self.assertEqual(r["sequence_scoring"],"DISABLED")
        self.assertEqual(r["surplus_facets"],["surplus"])

    def test_continuation_gate_binds_final_candidate(self):
        units,rel,gc=self.base(); plan=derive_continuation_plan(gc,units,rel)
        coverage=[{"obligation_id":o["id"],"status":"DEVELOPED","depth_score":0.9,"artifact_locator":"§1","evidence_modes":["text"]} for o in plan["obligations"]]
        report=audit_continuation_coverage(plan,coverage,candidate_digest="A")
        state={"plan":plan,"coverage":report,"status":"PASS"}
        self.assertTrue(continuation_gate(state,generation_contract_digest="GC1",candidate_digest="A")[0])
        ok,errors=continuation_gate(state,generation_contract_digest="GC1",candidate_digest="B")
        self.assertFalse(ok); self.assertIn("stale candidate", " ".join(errors))

    def test_benchmark_marks_underdeveloped_core(self):
        ref=[{"id":"cases","category":"case_family","weight":2,"core":True,"minimum_depth":0.7}]
        cand=[{"id":"cases","depth_score":0.3}]
        r=benchmark_gap_report(ref,cand)
        self.assertEqual(r["weighted_coverage"],0.0)
        self.assertEqual(r["underdeveloped_facets"],["cases"])
        self.assertEqual(r["missing_core_facets"],["cases"])

    def test_stress_5000_obligations(self):
        units=[{"id":f"U{i}","kind":"ARGUMENT","tags":["develop"]} for i in range(5000)]
        gc={"contract_digest":"GC","develop_unit_ids":[u["id"] for u in units]}
        plan=derive_continuation_plan(gc,units,[])
        coverage=[{"obligation_id":o["id"],"status":"DEVELOPED","depth_score":0.8,"artifact_locator":f"P{i}","evidence_modes":["text"]} for i,o in enumerate(plan["obligations"])]
        r=audit_continuation_coverage(plan,coverage)
        self.assertEqual(r["status"],"PASS",r.get("errors"))
        self.assertEqual(r["obligations"],5000)

if __name__ == "__main__": unittest.main()

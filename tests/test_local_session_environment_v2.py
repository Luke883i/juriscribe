from __future__ import annotations
import importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('host_environment_v2',ROOT/'juriscribe'/'host_environment.py'); mod=importlib.util.module_from_spec(spec); assert spec.loader; sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
def admission(): return json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8'))
class PostPR33EnvironmentTests(unittest.TestCase):
    def test_profiles_are_not_modes_and_no_mandatory_roundtrip(self):
        c=mod.execution_profile_choices(); self.assertEqual(c['choices'],['LEAN','ATTESTED']); self.assertFalse(c['scientific_mode']); self.assertFalse(c['mandatory_selection']); self.assertEqual(c['default_preference'],'ATTESTED_PREFERRED')
    def test_explicit_lean_is_honored_even_with_runtime(self):
        p=mod.graded_execution_plan('LEAN',method_available=True,runtime_ready=True); self.assertEqual(p['action'],'RUN_LEAN_METHOD'); self.assertEqual(p['attestation'],'METHOD_GUIDED'); self.assertFalse(p['runtime_receipts_may_be_claimed']); self.assertFalse(p['runtime_complete_may_be_claimed']); self.assertTrue(p['promotion_requires_replay'])
    def test_runtime_reachability_never_certifies_receipts_or_complete(self):
        p=mod.graded_execution_plan('ATTESTED',method_available=True,runtime_ready=True); self.assertEqual(p['action'],'RUN_ATTESTED'); self.assertFalse(p['runtime_receipts_may_be_claimed']); self.assertFalse(p['runtime_complete_may_be_claimed'])
    def test_attested_unreachable_offers_lean(self): self.assertEqual(mod.graded_execution_plan('ATTESTED',method_available=True,runtime_ready=False)['action'],'OFFER_LEAN')
    def test_complete_cannot_be_method_guided(self):
        with self.assertRaises(PermissionError): mod.artifact_trajectory(content_ready=True,materialized=True,delivered=True,runtime_attested=False,complete=True)
    def test_promotion_is_replay_not_label(self):
        p=mod.promotion_plan(method_work_exists=True,runtime_ready=True); self.assertEqual(p['action'],'REPLAY_REQUIRED'); self.assertFalse(p['prior_method_work_is_proof'])
    def test_runtime_search_does_not_contain_lean(self):
        p=mod.plan_local_bootstrap_search({'REPOSITORY_READ':'AVAILABLE','PYTHON_EXECUTION':'AVAILABLE','LOCAL_SCRATCH_IO':'AVAILABLE','SOURCE_TO_RUNTIME_BRIDGE':'UNVERIFIED'},method_available=True); self.assertFalse(p['gh_cli_required']); self.assertFalse(p['lean_is_runtime_transport_class']); self.assertNotIn('LEAN_METHOD_KERNEL',p['candidate_classes']); self.assertIn('PROBE_SOURCE_TO_RUNTIME_BRIDGE',p['candidate_classes'])
    def test_blocker_requires_runtime_path_exhaustion_then_profile_resolution(self):
        p=mod.plan_local_bootstrap_search({'REPOSITORY_READ':'AVAILABLE','PYTHON_EXECUTION':'AVAILABLE','LOCAL_SCRATCH_IO':'AVAILABLE','SOURCE_TO_RUNTIME_BRIDGE':'UNVERIFIED'},method_available=True); self.assertEqual(mod.local_blocker_status(p,[],requested_profile='ATTESTED')['action'],'TRY_NEXT_LOCAL_PATH'); a=[{'class':c,'attempted':True} for c in p['candidate_classes']]; self.assertEqual(mod.local_blocker_status(p,a,requested_profile='ATTESTED')['action'],'OFFER_LEAN'); self.assertEqual(mod.local_blocker_status(p,a,requested_profile='LEAN')['action'],'RUN_LEAN_METHOD')
    def test_method_kernel_is_bound_and_mode_specific(self):
        k=mod.method_kernel_contract(); self.assertEqual(k['profile'],mod.METHOD_KERNEL_PROFILE); self.assertFalse(k['method_degradation_allowed']); self.assertFalse(k['epistemic_degradation_allowed']); self.assertTrue(k['human_validation_required']); self.assertEqual(set(k['mode_methods']),{'CONTINUATION','GREENFIELD','REVIEW','COMPRESSION & CONSOLIDATION'})
    def test_repository_files_validate(self):
        r=mod.validate_environment_files(ROOT,admission()); self.assertEqual(r['normative_policy_nodes'],5); self.assertEqual(r['cognitive_companion_nodes'],1)
if __name__=='__main__': unittest.main()

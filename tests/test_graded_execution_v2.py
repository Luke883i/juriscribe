from __future__ import annotations
import importlib.util, json, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('graded_execution', ROOT/'juriscribe'/'graded_execution.py')
mod=importlib.util.module_from_spec(spec); assert spec.loader; sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
MODES=("CONTINUATION","GREENFIELD","REVIEW","COMPRESSION & CONSOLIDATION")
def access(): return mod.MethodAccess(True,True,True,True)
class GradedExecutionV2Tests(unittest.TestCase):
    def test_method_kernel_is_mode_complete_and_non_degrading(self):
        k=mod.load_method_kernel(ROOT/'METHOD_KERNEL.json'); r=mod.validate_method_kernel(k,canonical_modes=MODES); self.assertEqual(r['status'],'PASS',r['errors'])
    def test_explicit_lean_is_honored_even_with_runtime(self):
        p=mod.choose_execution_profile(access(),runtime_reachable=True,infrastructure_search_exhausted=False,preference='LEAN'); self.assertEqual(p['profile'],'LEAN'); self.assertFalse(p['runtime_attestation_allowed']); self.assertTrue(p['promotion_requires_replay'])
    def test_attested_preferred_uses_runtime_when_reachable(self):
        p=mod.choose_execution_profile(access(),runtime_reachable=True,infrastructure_search_exhausted=False); self.assertEqual(p['profile'],'ATTESTED'); self.assertTrue(p['runtime_attestation_allowed'])
    def test_attested_preferred_degrades_only_after_discovery_and_search(self):
        self.assertEqual(mod.choose_execution_profile(access(),runtime_reachable=False,infrastructure_search_exhausted=False,capability_discovery_complete=False)['state'],'CAPABILITY_DISCOVERY')
        self.assertEqual(mod.choose_execution_profile(access(),runtime_reachable=False,infrastructure_search_exhausted=False,capability_discovery_complete=True)['state'],'INFRASTRUCTURE_SEARCH')
        self.assertEqual(mod.choose_execution_profile(access(),runtime_reachable=False,infrastructure_search_exhausted=True,capability_discovery_complete=True)['profile'],'LEAN')
    def test_attested_required_blocks_without_silent_degrade(self):
        p=mod.choose_execution_profile(access(),runtime_reachable=False,infrastructure_search_exhausted=True,preference='ATTESTED_REQUIRED'); self.assertEqual(p['state'],'ATTESTED_INFRASTRUCTURE_BLOCKED'); self.assertTrue(p['lean_available'])
    def test_runtime_reachability_does_not_imply_receipts_or_complete(self):
        r=mod.runtime_claim_projection(profile='ATTESTED',runtime_reachable=True); self.assertFalse(r['runtime_receipts_may_be_claimed']); self.assertFalse(r['runtime_complete_may_be_claimed'])
        r=mod.runtime_claim_projection(profile='ATTESTED',runtime_reachable=True,receipts_verified=True,complete_verified=True); self.assertTrue(r['runtime_receipts_may_be_claimed']); self.assertTrue(r['runtime_complete_may_be_claimed'])
    def test_lean_never_claims_runtime_receipts_or_complete(self):
        r=mod.runtime_claim_projection(profile='LEAN',runtime_reachable=True,receipts_verified=True,complete_verified=True); self.assertFalse(r['runtime_attestation']); self.assertFalse(r['runtime_receipts_may_be_claimed']); self.assertFalse(r['runtime_complete_may_be_claimed'])
    def test_lean_is_not_transport_path(self): self.assertNotIn('LEAN',mod.PATH_CLASSES); self.assertNotIn('LEAN_METHOD_KERNEL',mod.PATH_CLASSES)
    def test_unverified_bridge_produces_probe_not_unavailability(self):
        p=mod.eligible_path_classes({'REPOSITORY_READ':'AVAILABLE','LOCAL_SCRATCH_IO':'AVAILABLE','PYTHON_EXECUTION':'AVAILABLE','SOURCE_TO_RUNTIME_BRIDGE':'UNVERIFIED'},installed_runtime_bound=False); self.assertIn('PROBE_SOURCE_TO_RUNTIME_BRIDGE',p)
    def test_method_mode_intent_is_not_runtime_selection(self):
        r=mod.method_mode_intent('review',mod.load_method_kernel(ROOT/'METHOD_KERNEL.json')); self.assertFalse(r['runtime_mode_selection']); self.assertFalse(r['runtime_receipt']); self.assertEqual(r['authority'],'METHOD_INTENT_ONLY')
    def test_artifact_axes_remain_separate(self):
        r=mod.artifact_projection(profile='LEAN',content_ready=True,host_write=True,host_readback=True,delivered=True); self.assertEqual(r['physical_readiness'],'DELIVERED'); self.assertEqual(r['execution_attestation'],'METHOD_GUIDED'); self.assertFalse(r['canonical_complete'])
    def test_calm_infrastructure_note_requires_evidence(self):
        note=mod.infrastructure_note([mod.InfrastructureDebt('INFRA-1','DOCX_WRITE','runtime DOCX materialization','ev-1')]); self.assertIn('restano invariati',note); self.assertIn('ev-1',note)
    def test_contract_admission_and_cognitive_binding(self):
        adm=json.loads((ROOT/'ADMISSION.json').read_text()); self.assertEqual(adm['contract_version'],'2.2.0'); self.assertEqual(adm['contract_semantic_revision'],'POST_PR33_GRADED_METHOD_ACCESS_HARDENING_V1'); self.assertFalse(adm['method_access']['mandatory_profile_choice']); self.assertFalse(adm['host_runtime_transport']['lean_is_runtime_transport_class']); self.assertFalse(adm['local_cognitive_system']['load_before_acceptance']); self.assertFalse(adm['local_cognitive_system']['normative_host_nodes_replaced'])
    def test_five_normative_host_nodes_and_companion(self):
        adm=json.loads((ROOT/'ADMISSION.json').read_text()); self.assertEqual(len(adm['local_session_environment']['contract_nodes']),5); root=(ROOT/'docs/host/LOCAL_SESSION_ENVIRONMENT.md').read_text(); self.assertIn('RUNTIME_LOCAL_HOST.md',root); self.assertIn('five host normative concerns',root)
if __name__=='__main__': unittest.main()

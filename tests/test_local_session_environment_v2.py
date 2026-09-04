from __future__ import annotations
import importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('host_environment_v2',ROOT/'juriscribe'/'host_environment.py'); mod=importlib.util.module_from_spec(spec); assert spec.loader; sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
def admission(): return json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8'))
class LocalChatEnvironmentTests(unittest.TestCase):
    def test_local_chat_requires_explicit_profile_without_changing_scientific_modes(self):
        c=mod.execution_profile_choices(); self.assertEqual(c['choices'],['LEAN','ATTESTED']); self.assertFalse(c['scientific_mode']); self.assertTrue(c['mandatory_selection']); self.assertIsNone(c['default_preference']); self.assertTrue(c['auto_select_forbidden']); self.assertEqual(c['scope'],'LOCAL_CHAT')
    def test_local_chat_cold_start_is_deterministic(self):
        p=mod.local_chat_bootstrap_plan(admission()); self.assertEqual(p['primary_transport'],'CONNECTED_GITHUB_PINNED_BYTES'); self.assertEqual(p['assume_unavailable'],['PREINSTALLED_RUNTIME','LOCAL_GIT_CHECKOUT_OR_PACKAGE']); self.assertIn('DNS_RESOLUTION',p['do_not_attempt']); self.assertIn('GIT_CLONE_CHECKOUT_FETCH',p['do_not_attempt']); self.assertTrue(p['solver_roaming_forbidden'])
    def test_lean_skips_runtime_bootstrap(self):
        p=mod.local_chat_bootstrap_plan(admission(),selected_profile='LEAN'); self.assertTrue(p['skip_runtime_bootstrap']); self.assertEqual(p['h0_handshake_source_paths'],[])
    def test_attested_fetches_only_h0_first(self):
        p=mod.local_chat_bootstrap_plan(admission(),selected_profile='ATTESTED'); self.assertFalse(p['skip_runtime_bootstrap']); self.assertEqual(p['h0_handshake_source_paths'],['juriscribe/__init__.py','juriscribe/admission.py','juriscribe/bootstrap.py','juriscribe/host_bootstrap.py']); self.assertTrue(p['git_blob_binding_required']); self.assertEqual(p['transient_retry_max'],1)
    def test_explicit_lean_is_honored_even_with_runtime(self):
        p=mod.graded_execution_plan('LEAN',method_available=True,runtime_ready=True); self.assertEqual(p['action'],'RUN_LEAN_METHOD'); self.assertEqual(p['attestation'],'METHOD_GUIDED'); self.assertFalse(p['runtime_receipts_may_be_claimed']); self.assertFalse(p['runtime_complete_may_be_claimed']); self.assertTrue(p['promotion_requires_replay'])
    def test_runtime_reachability_never_certifies_receipts_or_complete(self):
        p=mod.graded_execution_plan('ATTESTED',method_available=True,runtime_ready=True); self.assertEqual(p['action'],'RUN_ATTESTED'); self.assertFalse(p['runtime_receipts_may_be_claimed']); self.assertFalse(p['runtime_complete_may_be_claimed'])
    def test_complete_cannot_be_method_guided(self):
        with self.assertRaises(PermissionError): mod.artifact_trajectory(content_ready=True,materialized=True,delivered=True,runtime_attested=False,complete=True)
    def test_promotion_is_replay_not_label(self):
        p=mod.promotion_plan(method_work_exists=True,runtime_ready=True); self.assertEqual(p['action'],'REPLAY_REQUIRED'); self.assertFalse(p['prior_method_work_is_proof'])
    def test_generic_search_stays_available_for_non_local_chat_hosts(self):
        p=mod.plan_local_bootstrap_search({'REPOSITORY_READ':'AVAILABLE','PYTHON_EXECUTION':'AVAILABLE','LOCAL_SCRATCH_IO':'AVAILABLE','SOURCE_TO_RUNTIME_BRIDGE':'UNVERIFIED'},method_available=True); self.assertFalse(p['gh_cli_required']); self.assertFalse(p['lean_is_runtime_transport_class']); self.assertIn('PROBE_SOURCE_TO_RUNTIME_BRIDGE',p['candidate_classes'])
    def test_method_kernel_is_unchanged_and_mode_specific(self):
        k=mod.method_kernel_contract(); self.assertEqual(k['profile'],mod.METHOD_KERNEL_PROFILE); self.assertFalse(k['method_degradation_allowed']); self.assertFalse(k['epistemic_degradation_allowed']); self.assertTrue(k['human_validation_required']); self.assertEqual(set(k['mode_methods']),{'CONTINUATION','GREENFIELD','REVIEW','COMPRESSION & CONSOLIDATION'})
    def test_repository_files_validate(self):
        r=mod.validate_environment_files(ROOT,admission()); self.assertEqual(r['normative_policy_nodes'],5); self.assertEqual(r['cognitive_companion_nodes'],0); self.assertTrue(r['standalone_prompt_policy'])
if __name__=='__main__': unittest.main()

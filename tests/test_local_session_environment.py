from __future__ import annotations
import copy, importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('host_environment',ROOT/'juriscribe'/'host_environment.py'); mod=importlib.util.module_from_spec(spec); assert spec.loader; sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
def policy(): return json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8'))
class LocalEnvironmentTests(unittest.TestCase):
    def test_exact_activation_is_lifecycle_scoped(self):
        p=policy(); self.assertEqual(mod.activation_plan(p,'POST_ACCEPTANCE_BOOTSTRAP')['node_keys'],['root','execution']); self.assertEqual(mod.activation_plan(p,'ACTIVE_SESSION')['node_keys'],['root','state','surface']); self.assertEqual(mod.activation_plan(p,'FAILURE_OR_RECOVERY')['node_keys'],['root','state','failure_recovery']); self.assertEqual(mod.activation_plan(p,'REBIND_OR_TRANSPORT_FAILURE')['node_keys'],['root','execution','failure_recovery']); self.assertEqual(mod.activation_plan(p,'ACTIVE_SESSION')['normative_policy_nodes'],5); self.assertEqual(mod.activation_plan(p,'ACTIVE_SESSION')['cognitive_companion_nodes'],1)
    def test_prompt_and_companion_are_post_admission_non_normative(self):
        p=policy(); mod.validate_environment_policy(p); env=p['local_session_environment']; c=p['local_cognitive_system']; self.assertNotIn(env['boot_prompt'],p['pre_admission_allowlist']); self.assertNotIn(c['cognitive_policy'],p['pre_admission_allowlist']); self.assertNotIn(c['cognitive_policy'],env['contract_nodes'].values()); self.assertFalse(c['normative_host_nodes_replaced']); self.assertFalse(c['load_before_acceptance'])
    def test_new_authority_fails_closed(self):
        p=copy.deepcopy(policy()); p['local_session_environment']['runtime_authority_nodes_added']=1; self.assertRaises(ValueError,mod.validate_environment_policy,p)
    def test_live_main_rebind_relaxation_fails_closed(self):
        p=copy.deepcopy(policy()); p['local_session_environment']['live_main_rebind_forbidden']=False; self.assertRaises(ValueError,mod.validate_environment_policy,p)
    def test_activation_drift_fails_closed(self):
        p=copy.deepcopy(policy()); p['local_session_environment']['activation']['ACTIVE_SESSION'].append('execution'); self.assertRaises(ValueError,mod.validate_environment_policy,p)
    def test_prompt_overflow_fails_closed(self):
        p=copy.deepcopy(policy()); p['local_session_environment']['boot_prompt_max_chars']=8001; self.assertRaises(ValueError,mod.validate_environment_policy,p)
    def test_repository_graph_validates(self):
        r=mod.validate_environment_files(ROOT,policy()); self.assertEqual(r['runtime_authority_nodes_added'],0); self.assertLessEqual(r['prompt_chars'],8000); self.assertEqual(set(r['nodes']),set(mod.CONTRACT_NODE_KEYS)); self.assertEqual(r['normative_policy_nodes'],5); self.assertEqual(r['cognitive_companion_nodes'],1)
if __name__=='__main__': unittest.main()

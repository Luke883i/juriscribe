import copy
import unittest
from types import SimpleNamespace
from juriscribe.consolidation import build_lossless_inventory, canonical_digest
from juriscribe.editorial_reticulum import build_editorial_execution_reticulum, build_editorial_refinement_proof, verify_editorial_execution_reticulum, verify_editorial_refinement_proof

class EditorialReticulumV2Tests(unittest.TestCase):
  def fixture(self):
    src='The hypothesis predicts a measurable effect.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(src,source_id='cand',role='candidate_material')
    objs=inv['objects']
    units=[
      {'id':'U1','object_id':objs[0]['id'],'source_id':'cand','material_role':'candidate_material','kind':'CLAIM','text':objs[0]['text'],'material':True},
      {'id':'U2','object_id':objs[1]['id'],'source_id':'cand','material_role':'candidate_material','kind':'METHOD','text':objs[1]['text'],'material':True},
      {'id':'U3','object_id':objs[2]['id'],'source_id':'cand','material_role':'candidate_material','kind':'RESULT','text':objs[2]['text'],'material':True},
      {'id':'U4','object_id':objs[3]['id'],'source_id':'cand','material_role':'candidate_material','kind':'LIMITATION','text':objs[3]['text'],'material':True},
    ]
    rels=[
      {'id':'R1','source':'U3','predicate':'SUPPORTS','target':'U1','material':True},
      {'id':'R2','source':'U2','predicate':'WARRANTS','target':'U1','material':True},
      {'id':'R3','source':'U4','predicate':'QUALIFIES','target':'U1','material':True},
    ]
    gaps=[{'id':'G1','unit_id':'U1'},{'id':'G2','unit_id':'U3'}]
    ops=[
      {'id':'O1','unit_id':'U1','operation':'CLARIFY','gap_ids':['G1'],'rationale':'reduce ambiguity','expected_benefit':'clearer causal claim','degradation_risk':'LOW'},
      {'id':'O2','unit_id':'U3','operation':'LOCAL_REWRITE','gap_ids':['G2'],'rationale':'remove redundancy','expected_benefit':'higher information density','degradation_risk':'LOW'},
    ]
    plan={'status':'READY','digest':'PLAN','gaps':gaps,'operations':ops}
    state=SimpleNamespace(strategy={'consolidation':{'inventories':{'cand':inv},'refactoring_contract':plan}},reticulum={'status':'PASS','digest':'RET'},epistemic_units=units,relations=rels)
    return state,src

  def projection(self,state,text):
    inv=build_lossless_inventory(text,source_id='cand',role='candidate_material')
    return {'units':[{**u,'object_id':o['id'],'text':o['text']} for u,o in zip(state.epistemic_units,inv['objects'])],'relations':[dict(r) for r in state.relations]}

  def structural(self,projection):
    p={'status':'PASS','digest':canonical_digest(projection)}; return p

  def test_valid(self):
    s,src=self.fixture(); r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'PASS',r['errors']); self.assertTrue(verify_editorial_execution_reticulum(s,r)[0])
    refined='The hypothesis predicts a measurable effect with a prespecified direction.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    p=self.projection(s,refined); sp=self.structural(p); ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'PASS',ep['errors']); self.assertTrue(verify_editorial_refinement_proof(s,source_id='cand',refined_text=refined,structural_proof=sp,execution_reticulum=r,proof=ep)[0])

  def test_claim_without_support_fails(self):
    s,_=self.fixture(); s.relations=[r for r in s.relations if r['predicate'] not in ('SUPPORTS','WARRANTS')]; r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'FAIL'); self.assertTrue(any('support-path' in e for e in r['errors']))

  def test_operation_evidence_required(self):
    s,_=self.fixture(); s.strategy['consolidation']['refactoring_contract']['operations'][0]['expected_benefit']=''; r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'FAIL')

  def test_unauthorized_reorder_fails(self):
    s,_=self.fixture(); r=build_editorial_execution_reticulum(s); refined='The observed result supports the hypothesis.\n\nThe experiment uses a blinded protocol.\n\nThe hypothesis predicts a measurable effect.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
    by={'U3':inv['objects'][0],'U2':inv['objects'][1],'U1':inv['objects'][2],'U4':inv['objects'][3]}
    p={'units':[{**u,'object_id':by[u['id']]['id'],'text':by[u['id']]['text']} for u in s.epistemic_units],'relations':[dict(x) for x in s.relations]}; sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'FAIL'); self.assertTrue(any('reorder' in e for e in ep['errors']))

  def test_unauthorized_merge_fails(self):
    s,_=self.fixture(); r=build_editorial_execution_reticulum(s); refined='The hypothesis predicts a measurable effect. The experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
    p={'units':[
      {**s.epistemic_units[0],'object_id':inv['objects'][0]['id'],'text':inv['objects'][0]['text']},
      {**s.epistemic_units[1],'object_id':inv['objects'][0]['id'],'text':inv['objects'][0]['text']},
      {**s.epistemic_units[2],'object_id':inv['objects'][1]['id'],'text':inv['objects'][1]['text']},
      {**s.epistemic_units[3],'object_id':inv['objects'][2]['id'],'text':inv['objects'][2]['text']},
    ],'relations':[dict(x) for x in s.relations]}; sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'FAIL'); self.assertTrue(any('merge' in e for e in ep['errors']))

  def test_overcompression_fails(self):
    s,_=self.fixture(); r=build_editorial_execution_reticulum(s); refined='Effect.\n\nMethod.\n\nResult.\n\nLimit.'; p=self.projection(s,refined); sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'FAIL'); self.assertTrue(any('overcompression' in e for e in ep['errors']))

  def test_authorized_reorder_passes(self):
    s,_=self.fixture()
    s.strategy['consolidation']['refactoring_contract']['operations'].extend([
      {'id':'O3','unit_id':'U1','operation':'REORDER','gap_ids':['G1'],'rationale':'restore result-before-claim progression','expected_benefit':'stronger reticular progression','degradation_risk':'LOW'},
      {'id':'O4','unit_id':'U3','operation':'REORDER','gap_ids':['G2'],'rationale':'place evidence before the interpreted claim','expected_benefit':'evidence-first progression','degradation_risk':'LOW'},
    ])
    r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'PASS',r['errors'])
    refined='The observed result supports the hypothesis.\n\nThe experiment uses a blinded protocol.\n\nThe hypothesis predicts a measurable effect.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
    by={'U3':inv['objects'][0],'U2':inv['objects'][1],'U1':inv['objects'][2],'U4':inv['objects'][3]}
    p={'units':[{**u,'object_id':by[u['id']]['id'],'text':by[u['id']]['text']} for u in s.epistemic_units],'relations':[dict(x) for x in s.relations]}; sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'PASS',ep['errors'])

  def test_authorized_merge_passes(self):
    s,_=self.fixture()
    plan=s.strategy['consolidation']['refactoring_contract']; plan['gaps'].append({'id':'G3','unit_id':'U2'})
    plan['operations'].extend([
      {'id':'O3','unit_id':'U1','operation':'MERGE_REDUNDANCY','gap_ids':['G1'],'rationale':'co-locate claim and method without losing either unit','expected_benefit':'denser local progression','degradation_risk':'LOW'},
      {'id':'O4','unit_id':'U2','operation':'MERGE_REDUNDANCY','gap_ids':['G3'],'rationale':'co-locate method with its claim','expected_benefit':'remove redundant paragraph boundary','degradation_risk':'LOW'},
    ])
    r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'PASS',r['errors'])
    refined='The hypothesis predicts a measurable effect. The experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
    p={'units':[
      {**s.epistemic_units[0],'object_id':inv['objects'][0]['id'],'text':inv['objects'][0]['text']},
      {**s.epistemic_units[1],'object_id':inv['objects'][0]['id'],'text':inv['objects'][0]['text']},
      {**s.epistemic_units[2],'object_id':inv['objects'][1]['id'],'text':inv['objects'][1]['text']},
      {**s.epistemic_units[3],'object_id':inv['objects'][2]['id'],'text':inv['objects'][2]['text']},
    ],'relations':[dict(x) for x in s.relations]}; sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'PASS',ep['errors'])

  def test_authorized_split_passes(self):
    s,_=self.fixture()
    s.strategy['consolidation']['refactoring_contract']['operations'].append(
      {'id':'O3','unit_id':'U1','operation':'SPLIT','gap_ids':['G1'],'rationale':'separate claim from qualification while preserving one semantic unit','expected_benefit':'clearer local progression','degradation_risk':'LOW'}
    )
    r=build_editorial_execution_reticulum(s); self.assertEqual(r['status'],'PASS',r['errors'])
    refined='The hypothesis predicts a measurable effect.\n\nThe direction is prespecified.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
    p={'units':[
      {**s.epistemic_units[0],'object_ids':[inv['objects'][0]['id'],inv['objects'][1]['id']],'text':inv['objects'][0]['text']+' '+inv['objects'][1]['text']},
      {**s.epistemic_units[1],'object_id':inv['objects'][2]['id'],'text':inv['objects'][2]['text']},
      {**s.epistemic_units[2],'object_id':inv['objects'][3]['id'],'text':inv['objects'][3]['text']},
      {**s.epistemic_units[3],'object_id':inv['objects'][4]['id'],'text':inv['objects'][4]['text']},
    ],'relations':[dict(x) for x in s.relations]}; sp=self.structural(p)
    ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r)
    self.assertEqual(ep['status'],'PASS',ep['errors'])

  def test_execution_reticulum_staleness_fails(self):
    s,_=self.fixture(); r=build_editorial_execution_reticulum(s); self.assertTrue(verify_editorial_execution_reticulum(s,r)[0])
    s.strategy['consolidation']['refactoring_contract']['digest']='PLAN-CHANGED'
    self.assertFalse(verify_editorial_execution_reticulum(s,r)[0])

from juriscribe.consolidation import text_digest
from juriscribe.semantic_proof_v2 import build_structural_semantic_proof, verify_structural_semantic_proof, SCHEMA
class StructuralSemanticProofV2Tests(unittest.TestCase):
 def test_split_mapping_passes_and_tamper_fails(self):
  source='A material claim that contains two clauses.\n\nA second material conclusion.'
  inv=build_lossless_inventory(source,source_id='cand',role='candidate_material')
  units=[{'id':'U1','object_id':inv['objects'][0]['id'],'source_id':'cand','material_role':'candidate_material','kind':'ARGUMENT','text':inv['objects'][0]['text'],'material':True},{'id':'U2','object_id':inv['objects'][1]['id'],'source_id':'cand','material_role':'candidate_material','kind':'ARGUMENT','text':inv['objects'][1]['text'],'material':True}]
  rel=[{'id':'R1','source':'U1','predicate':'SUPPORTS','target':'U2','material':True}]
  state=SimpleNamespace(corpus=[{'source_id':'cand','role':'candidate_material','digest':text_digest(source)}],epistemic_units=units,relations=rel,reticulum={'status':'PASS','digest':'RET'},strategy={'consolidation':{'inventories':{'cand':inv},'refactoring_contract':{'status':'READY','digest':'PLAN'}}})
  refined='A material claim.\n\nIt contains two clauses.\n\nA second material conclusion.'
  out=build_lossless_inventory(refined,source_id='cand',role='candidate_material')
  projection={'units':[{**units[0],'object_ids':[out['objects'][0]['id'],out['objects'][1]['id']],'text':out['objects'][0]['text']+' '+out['objects'][1]['text']},{**units[1],'object_id':out['objects'][2]['id'],'text':out['objects'][2]['text']}],'relations':rel}
  proof=build_structural_semantic_proof(state,source_id='cand',refined_text=refined,projection=projection)
  self.assertEqual(proof['schema'],SCHEMA); self.assertEqual(proof['status'],'PASS',proof['errors']); self.assertEqual(proof['output_object_coverage'],1.0); self.assertTrue(verify_structural_semantic_proof(state,source_id='cand',refined_text=refined,proof=proof)[0])
  proof['multi_object_unit_ids']=[]; self.assertFalse(verify_structural_semantic_proof(state,source_id='cand',refined_text=refined,proof=proof)[0])

if __name__ == '__main__':
    unittest.main()

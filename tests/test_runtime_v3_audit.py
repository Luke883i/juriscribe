import unittest
from juriscribe.benchmark import BenchmarkChapter,BlindBenchmarkEnvelope,benchmark_gate,canonical_digest
from juriscribe.convergence import completion_gate
from juriscribe.quality import analyze_reference_apparatus,audit_chapter,claim_traceability,compare_editorial_style
from juriscribe.sources import ClaimRecord,SourceRecord
REFERENCE='CAPITOLO 1\n1.1 Quadro generale\n'+('Anzitutto il problema richiede una ricostruzione ordinata; tuttavia la regola deve essere qualificata nel suo contesto. '*80)
CANDIDATE='CAPITOLO 2\n'+'\n'.join(f'2.{i} Sezione {i}\n'+('Anzitutto il problema richiede una ricostruzione ordinata; tuttavia la regola deve essere qualificata nel suo contesto. '*8) for i in range(1,14))
SOURCE_APP='CAPITOLO 2\n2.1 Regole\n'+' '.join(f'La proposizione {i} è circostanziata. {i}' for i in range(1,14))+'\nFonti verificate del capitolo\n'+'\n'.join(f'{i}. Fonte {i}.' for i in range(1,14))
class RuntimeV3AuditRegressionTests(unittest.TestCase):
    def test_style_excludes_source_appendix(self): self.assertLess(compare_editorial_style(REFERENCE,REFERENCE+'\nBibliografia\n1. Fonte.')['deltas']['avg_sentence_words'],.05)
    def test_complete_source_apparatus(self): self.assertEqual(analyze_reference_apparatus(SOURCE_APP)['status'],'PASS')
    def test_oversectioning_flagged(self): self.assertEqual(compare_editorial_style(REFERENCE,CANDIDATE)['status'],'REVIEW_REQUIRED')
    def test_claim_traceability_requires_locator_and_strict_source_evidence(self):
        s=SourceRecord('S1','Norma','u','primary_law',direct_read=True).record(); c=ClaimRecord('C1','Regola','direct','scope',support_source_ids=('S1',),status='SUPPORTED',source_evidence=({'source_id':'S1','pinpoint':'art. 1','proposition':'regola'},)).record(); self.assertEqual(claim_traceability([c],[s],[])['status'],'GAPS_OPEN'); self.assertEqual(claim_traceability([c],[s],[{'claim_id':'C1','artifact_locator':'§2.1 ¶3','source_ids':['S1']}])['status'],'PASS')
    def test_blind_benchmark_integrity(self):
        actual=BenchmarkChapter('A','Actual','N+1',['Alpha rule','Beta exception']); commit=canonical_digest(actual.record()); generated=BenchmarkChapter('G','Generated','N+1',['Alpha rule','Beta exception']); e=BlindBenchmarkEnvelope.seal_generation(monograph='M',author='A',domain='law',prior_context=[],hidden_reference_commitment=commit,generated=generated); self.assertTrue(benchmark_gate(e.reveal(actual),required=True)['eligible'])
    def test_v3_completion_mutations_remain_fail_closed(self):
        d=[{'id':'D','status':'DONE','blocking':True}]; m={'dod_no_novelty_streak':10000}; self.assertTrue(completion_gate(d,m,[],quality={'status':'PASS'},source_coverage='PASS',artifacts=[{'readback':'PASS','required':True}])['eligible']); self.assertFalse(completion_gate(d,m,[],quality={'status':'REVIEW_REQUIRED'},source_coverage='PASS')['eligible']); self.assertFalse(completion_gate(d,m,[],quality={'status':'PASS'},source_coverage='PLANNED')['eligible'])
if __name__=='__main__': unittest.main()

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Any

@dataclass
class ConvergenceMonitor:
    semantic_no_novelty_streak:int=0
    strategy_no_improvement_streak:int=0
    dod_no_novelty_streak:int=0
    reflection_no_novelty_streak:int=0
    semantic_target:int=1000
    strategy_target:int=1000
    dod_target:int=10000
    reflection_target:int=100
    observed_signatures:set[str]=field(default_factory=set)
    def semantic_probe(self,novelty,new_contradiction=False): self.semantic_no_novelty_streak=0 if novelty or new_contradiction else self.semantic_no_novelty_streak+1; return self.semantic_saturated
    def strategy_probe(self,material_improvement): self.strategy_no_improvement_streak=0 if material_improvement else self.strategy_no_improvement_streak+1; return self.strategy_saturated
    def dod_probe(self,novelty_vs_dod,blocking_failure=False): self.dod_no_novelty_streak=0 if novelty_vs_dod or blocking_failure else self.dod_no_novelty_streak+1; return self.dod_saturated
    def reflection_probe(self,novelty): self.reflection_no_novelty_streak=0 if novelty else self.reflection_no_novelty_streak+1; return self.reflection_saturated
    def observe_signature(self,signature): novelty=signature not in self.observed_signatures; self.observed_signatures.add(signature); return novelty
    @property
    def semantic_saturated(self): return self.semantic_no_novelty_streak>=self.semantic_target
    @property
    def strategy_saturated(self): return self.strategy_no_improvement_streak>=self.strategy_target
    @property
    def dod_saturated(self): return self.dod_no_novelty_streak>=self.dod_target
    @property
    def reflection_saturated(self): return self.reflection_no_novelty_streak>=self.reflection_target

def all_dods_done(dods:Iterable[dict]):
    blocking=[d for d in dods if d.get('blocking',True)]; return bool(blocking) and all(d.get('status')=='DONE' for d in blocking)

def completion_gate(
    dods:list[dict], metrics:dict, contradictions:list[dict], *,
    quality:dict[str,Any]|None=None,
    source_coverage:str|None=None,
    benchmark:dict[str,Any]|None=None,
    benchmark_required:bool=False,
    artifacts:list[dict]|None=None,
) -> dict:
    from .benchmark import benchmark_gate
    reasons=[]
    open_contra=[c for c in contradictions if c.get('blocking',True) and c.get('status','OPEN')!='RESOLVED']
    if not all_dods_done(dods): reasons.append('not all blocking DoD are DONE')
    if int(metrics.get('dod_no_novelty_streak',0))<10000: reasons.append('M+10000 no-novelty evidence vs DoD not reached')
    if open_contra: reasons.append('blocking contradictions remain open')
    if quality and quality.get('status')=='FAIL': reasons.append('chapter quality gate failed')
    if source_coverage in {'GAPS_OPEN','FAIL'}: reasons.append('claim/source coverage has open gaps')
    bg=benchmark_gate(benchmark,required=benchmark_required)
    if not bg['eligible']: reasons.append('blind monograph benchmark integrity/coverage failed')
    if artifacts:
        failed=[a for a in artifacts if a.get('required',True) and a.get('readback') not in {None,'PASS'}]
        if failed: reasons.append('required artifact readback failed')
    eligible=not reasons
    return {'eligible':eligible,'reason':'PASS' if eligible else '; '.join(reasons),'benchmark_gate':bg}

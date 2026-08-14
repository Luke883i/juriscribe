from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import argparse,json
from juriscribe.benchmark import BenchmarkChapter,BlindBenchmarkEnvelope,canonical_digest

def load_chapter(path): return BenchmarkChapter(**json.loads(Path(path).read_text(encoding='utf-8')))
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('commit'); c.add_argument('--actual',required=True); c.add_argument('--out',required=True)
    s=sub.add_parser('seal'); s.add_argument('--context',required=True); s.add_argument('--generated',required=True); s.add_argument('--commitment',required=True); s.add_argument('--monograph',required=True); s.add_argument('--author',required=True); s.add_argument('--domain',required=True); s.add_argument('--out',required=True)
    r=sub.add_parser('reveal'); r.add_argument('--envelope',required=True); r.add_argument('--actual',required=True); r.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='commit':
        actual=load_chapter(a.actual); record={'sha256':canonical_digest(actual.record()),'algorithm':'sha256','note':'Generate this commitment outside the model-visible context before N+1 generation.'}; Path(a.out).write_text(json.dumps(record,indent=2)+'\n'); return 0
    if a.cmd=='seal':
        context=json.loads(Path(a.context).read_text()); generated=load_chapter(a.generated); commit=json.loads(Path(a.commitment).read_text())['sha256']; env=BlindBenchmarkEnvelope.seal_generation(monograph=a.monograph,author=a.author,domain=a.domain,prior_context=context,hidden_reference_commitment=commit,generated=generated); Path(a.out).write_text(json.dumps(env.record(),ensure_ascii=False,indent=2)+'\n'); return 0
    data=json.loads(Path(a.envelope).read_text()); env=BlindBenchmarkEnvelope(**data); result=env.reveal(load_chapter(a.actual)); Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

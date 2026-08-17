from __future__ import annotations

import argparse, contextlib, hashlib, html, io, json, random, re, shutil, sys, tempfile, zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.admission import issue_receipt
from juriscribe.artifact_atlas import artifact_dashboard_coverage_gate, build_artifact_atlas
from juriscribe.artifact_governance import _govern_materialized_narrative, artifact_generation_governance_gate
from juriscribe.dashboard_persistence import persist_dashboard_generation, verify_persistent_dashboard
from juriscribe.delivery import delivery_gate, verify_materialized_artifact
from juriscribe.dossier_materialization import render_dossier_text
from juriscribe.generation_configuration import generation_conformance
from juriscribe.modes import MODES, REVIEW, mode_spec, required_artifact_roles
from juriscribe.orchestrator import apply_setup, freeze_dods, ingest_and_mine, record_artifact, register_semantic_mining, seal_draft
from juriscribe.pipeline_v9 import initialize, main as runtime_main, perform_probe
from juriscribe.semantic_delivery import semantic_dossier_gate
from juriscribe.session import Workspace
from juriscribe.sources import SourceRecord

CONTRACT = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
FIXTURE = ROOT / "fixtures" / "real_legal_texts_v99.json"
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
LENGTH_CLASSES = {"SHORT": (80, 180), "MEDIUM": (220, 450), "LONG": (520, 900), "XL": (900, 1700)}
DOSSIER_ROLES = ("evidence_dossier", "source_register", "inference_register", "transformation_ledger")
STOP = {"anche","che","con","come","dalla","dalle","dello","della","delle","degli","dei","del","di","e","ed","gli","il","in","la","le","lo","nei","nel","nella","nelle","non","o","per","piu","più","sul","sulla","tra","un","una","uno","the","and","for","from","into","that","this","with","without","within","which"}


def words(text): return WORD_RE.findall(str(text or ""))


def receipt(index):
    return issue_receipt(CONTRACT, phrase="I ACCEPT", actor_type="human", evidence_type="explicit_user_message", user_message="I ACCEPT", accepted_at="2026-08-17T06:00:00+00:00", receipt_nonce=f"{index + 1:032x}"[-32:])


def run_cli(argv):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return runtime_main(argv)


def load_fixture():
    records = json.loads(FIXTURE.read_text(encoding="utf-8")).get("records") or []
    if len(records) < 10: raise AssertionError("real legal fixture unexpectedly small")
    for record in records:
        if not str(record.get("source_url") or "").startswith("https://"): raise AssertionError(f"official URL missing: {record.get('id')}")
        if len(words(record.get("text"))) < 15: raise AssertionError(f"real excerpt too small: {record.get('id')}")
    return records


def compose_real_text(records, length_class, seed, seen):
    lower, upper = LENGTH_CLASSES[length_class]
    for attempt in range(200):
        order = list(records); random.Random(seed + attempt * 100003).shuffle(order)
        selected, chunks, cursor = [], [], 0
        while len(words("\n\n".join(chunks))) < lower:
            record = order[cursor % len(order)]; cursor += 1
            selected.append(record); chunks.append(f"{record['instrument']} — {record['locator']}\n{record['text']}")
        text = "\n\n".join(chunks); count = len(words(text)); digest = hashlib.sha256(text.encode()).hexdigest()
        if lower <= count <= upper and digest not in seen:
            seen.add(digest); return text, selected
    raise AssertionError(f"cannot create unique {length_class} source packet")


def semantic_payload(text, source_id, scenario_id):
    sentences = [" ".join(x.split()) for x in SENTENCE_RE.split(text) if len(words(x)) >= 6]
    if len(sentences) < 3:
        sentences += [" ".join(x.split()) for x in text.split("\n\n") if len(words(x)) >= 6 and " ".join(x.split()) not in sentences]
    if len(sentences) < 3: raise AssertionError("real packet yields fewer than three semantic units")
    units = [{"id":f"{scenario_id}-U{i}","kind":kind,"text":sentences[i-1],"source_id":source_id,"source_locator":f"real-text-{i}","chapter":scenario_id,"material":True,"status":"VERIFIED"} for i,kind in enumerate(("DEFINITION","RULE","CLAIM"),1)]
    relations = [{"source":units[0]["id"],"predicate":"DEFINES","target":units[1]["id"],"rationale":"real-text semantic setup"},{"source":units[1]["id"],"predicate":"SUPPORTS","target":units[2]["id"],"rationale":"real-text semantic setup"}]
    return units, relations, units[1]["text"]


def configuration(state):
    return (state.generation_contract or {}).get("generation_configuration") or (state.setup or {}).get("generation_configuration") or {}


def clean_candidate(config, scenario_id, mode):
    terms = set()
    for source in [str(config.get("abstract") or ""), *[str(x) for x in config.get("key_concepts") or []]]:
        for token in words(source):
            folded = token.casefold()
            if len(folded) >= 3 and folded not in STOP and not folded.isdigit(): terms.add(token)
    lexical = ", ".join(sorted(terms, key=str.casefold))
    text = "\n\n".join([
        f"L'elaborato {scenario_id} sviluppa un'analisi giuridica autonoma in modalità {mode}. Il lessico necessario viene ricomposto in ordine sistematico e non riproduce la sequenza delle fonti: {lexical}.",
        "L'argomentazione distingue il dato normativo dalla sua elaborazione interpretativa. Ogni passaggio è formulato come proposizione controllabile, collegata alla funzione della fonte e sottoposta a verifica di coerenza. Il ragionamento evita equivalenze automatiche e rende esplicite le condizioni che possono limitare la conclusione.",
        "Sul piano metodologico, la ricostruzione coordina legalità, tutela effettiva, imparzialità, motivazione e controllo. I concetti vengono messi in relazione senza trasformare il testo della fonte in testo dell'autore. Le conseguenze sono esposte con linguaggio originale e con un nesso riconoscibile tra premessa, qualificazione e risultato.",
        "La conclusione conserva il perimetro del mandato e rimane verificabile rispetto al reticolo epistemico. La sintesi finale non aggiunge autorità inesistenti, non nasconde riserve e mantiene distinta la prova testuale dalla scelta editoriale. In questo modo la struttura resta leggibile per il giurista e compatibile con una successiva revisione severa."
    ])
    lower, upper = [int(x) for x in config.get("length_words", [180,320])]
    filler = " La verifica ulteriore confronta fonti, premesse, qualificazioni e conseguenze in modo trasparente, senza duplicazioni testuali e senza scorciatoie inferenziali."
    while len(words(text)) < max(lower, 190): text += filler
    if len(words(text)) > upper: raise AssertionError(f"candidate unexpectedly exceeds configured upper bound: {len(words(text))}>{upper}")
    check = generation_conformance(text, config)
    if check.get("status") != "PASS": raise AssertionError(f"clean candidate violates configuration: {check}")
    return text


def write_docx(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [x.strip() for x in str(text).splitlines() if x.strip()] or [str(text)]
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(x)}</w:t></w:r></w:p>' for x in lines)
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '</w:body></w:document>'
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml",'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'); package.writestr("_rels/.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'); package.writestr("word/document.xml",document)


def checkpoint(ws, marker=None):
    state = ws.load(); path = ws.artifact_dir / "session-dashboard.html"; ok, errors, report = verify_persistent_dashboard(state,path)
    if not ok: raise AssertionError(f"dashboard verification failed: {errors}")
    page = path.read_text(encoding="utf-8")
    if marker and html.escape(" ".join(marker.split()), quote=True) not in page: raise AssertionError(f"semantic marker missing: {marker}")
    return {"generation":int(state.dashboard_persistence.get("generation",0)),"bytes":path.stat().st_size,"public_leaf_count":int(report.get("public_leaf_count",0)),"semantic_witness_count":int(report.get("semantic_witness_count",0)),"registered_public_material_roles":int(report.get("registered_public_material_roles",0))}


def persist(ws, state, trigger, marker=None):
    persist_dashboard_generation(ws,state,trigger=trigger); return ws.load(), checkpoint(ws,marker)


def exercise(root, index, length_class, source_text, selected):
    mode = MODES[index % len(MODES)]; scenario_id = f"REAL-{index+1:03d}-{length_class}-{mode}"
    adm = receipt(index); probe = perform_probe(admission_receipt=adm,contract_text=CONTRACT,host_capabilities={"DOCX_WRITE":"AVAILABLE","DOCX_READBACK":"AVAILABLE"},host="real-text-dashboard-v99",probed_at="2026-08-17T06:00:01+00:00")
    session_id = f"SES-real-{index+1:03d}"; base = initialize(f"Verifica E2E con fonti giuridiche ufficiali {scenario_id}",root=str(root),session_id=session_id,admission_receipt=adm,probe_receipt=probe,contract_text=CONTRACT)
    ws = Workspace(root,session_id); checks = [checkpoint(ws)]
    if run_cli(["select-mode",str(base),"--mode",mode]) != 0: raise AssertionError(f"select-mode failed {scenario_id}")
    checks.append(checkpoint(ws))

    source_id = f"SRC-REAL-{index+1:03d}"; authorities = sorted({str(x.get("authority")) for x in selected}); instruments = sorted({str(x.get("instrument")) for x in selected})
    source_record = SourceRecord(source_id,"Pacchetto ufficiale: "+"; ".join(instruments[:4]),str(selected[0].get("source_url")),"primary_law",jurisdiction="Italia / Unione europea / CEDU",court_or_author="; ".join(authorities[:4]),verified_at="2026-08-17",direct_read=True,primary=True,notes="Estratti ufficiali congelati: "+", ".join(str(x.get("id")) for x in selected),bibliography_entry="; ".join(f"{x.get('instrument')} {x.get('locator')}" for x in selected[:6]),role=mode_spec(mode,{}).get("input_role","external_source")).record()
    state = ws.load(); ingest_and_mine(state,source_text,source_id=source_id,chapter=scenario_id,source_record=source_record); state,c = persist(ws,state,"mine"); checks.append(c)
    units,relations,marker = semantic_payload(source_text,source_id,scenario_id); register_semantic_mining(state,units,relations)
    if state.reticulum.get("status") != "PASS": raise AssertionError(f"reticulum failed {scenario_id}: {state.reticulum}")
    state,c = persist(ws,state,"semantic-mining",marker); checks.append(c)
    apply_setup(state,{"length_words":[180,320]}); state,c = persist(ws,state,"accept-setup",marker); checks.append(c)
    freeze_dods(state); state,c = persist(ws,state,"freeze-dods",marker); checks.append(c)
    config = configuration(state)
    if config.get("status") != "READY": raise AssertionError(f"configuration not READY {scenario_id}: {config}")
    generated = clean_candidate(config,scenario_id,mode)
    seal_draft(state,source_text if mode==REVIEW else generated,stage="REVIEW_SOURCE" if mode==REVIEW else "INITIAL"); state,c = persist(ws,state,"seal-draft",marker); checks.append(c)

    # This suite isolates the final artifact admission boundary. Full final-review/convergence
    # behavior remains covered by the historical lifecycle suites; here we mark that upstream
    # prerequisite as satisfied without claiming overall session completion.
    state.final_review = {"status":"PASS","evidence":[{"criterion":"ARTIFACT_ADMISSION_TEST_FIXTURE","rationale":f"Prerequisito isolato per la simulazione di materializzazione {scenario_id}","status":"PASS"}]}
    state,c = persist(ws,state,"artifact-admission-fixture",marker); checks.append(c)

    primary = str(mode_spec(mode,state.setup).get("primary_artifact_role")); neg_plag = False
    if index % 5 == 0:
        copied = " ".join(words(source_text)[:24]) + " " + generated; bad = ws.artifact_dir / f"negative-copy-{index+1:03d}.docx"; write_docx(bad,copied)
        proof = _govern_materialized_narrative(state,{"role":primary,"path":str(bad),"readback":"PASS"}); bad.unlink(missing_ok=True); plag = proof.get("plagiarism") or {}
        if plag.get("status") != "FAIL" or int(plag.get("prohibited_findings",0)) < 1: raise AssertionError(f"copied source not blocked {scenario_id}: {proof}")
        neg_plag = True

    neg_dossier = False
    if index % 10 == 0:
        bad = ws.artifact_dir / f"negative-dossier-{index+1:03d}.docx"; write_docx(bad,f"Dossier volutamente incompleto {scenario_id}")
        try: record_artifact(state,{"id":f"bad-{scenario_id}","role":"evidence_dossier","summary":"negative dossier probe","path":str(bad),"readback":"PASS"})
        except ValueError as exc:
            if "semantic materialization" not in str(exc): raise
            neg_dossier = True
        else: raise AssertionError(f"incomplete dossier accepted {scenario_id}")
        finally: bad.unlink(missing_ok=True)

    required = required_artifact_roles(mode,state.setup); summaries=[]
    for role in sorted(required-{"session_dashboard"}):
        path = ws.artifact_dir / f"{role}.docx"; summary = f"{scenario_id} — artefatto conforme {role}"
        if role in DOSSIER_ROLES: artifact_text = render_dossier_text(state,role)
        elif role == primary: artifact_text = generated
        elif role == "review_findings_register": artifact_text = f"Registro rilievi {scenario_id}. La simulazione verifica materializzazione, copertura semantica, originalità e persistenza senza formulare conclusioni giuridiche ulteriori."
        else: artifact_text = generated
        write_docx(path,artifact_text); record_artifact(state,{"id":f"{scenario_id}-{role}","role":role,"summary":summary,"path":str(path),"readback":"PASS"}); summaries.append(summary); state,c = persist(ws,state,f"record-artifact:{role}",marker); checks.append(c)

    ok,errors = delivery_gate(state)
    if not ok: raise AssertionError(f"delivery materialization failed {scenario_id}: {errors}")
    ok,errors = semantic_dossier_gate(state)
    if not ok: raise AssertionError(f"semantic dossier gate failed {scenario_id}: {errors}")
    ok,errors = artifact_generation_governance_gate(state)
    if not ok: raise AssertionError(f"narrative governance failed {scenario_id}: {errors}")
    atlas=build_artifact_atlas(state); ok,errors=artifact_dashboard_coverage_gate(state,atlas)
    if not ok: raise AssertionError(f"atlas coverage failed {scenario_id}: {errors}")
    dashboard=ws.artifact_dir/"session-dashboard.html"; ok,errors,report=verify_persistent_dashboard(state,dashboard)
    if not ok: raise AssertionError(f"dashboard final verification failed {scenario_id}: {errors}")
    body=dashboard.read_text(encoding="utf-8").split("<body>",1)[1].split("</body>",1)[0]
    if html.escape(" ".join(marker.split()),quote=True) not in body: raise AssertionError(f"real semantic evidence absent {scenario_id}")
    for summary in summaries:
        if html.escape(summary,quote=True) not in body: raise AssertionError(f"artifact summary absent {scenario_id}: {summary}")
    for forbidden in [str(ws.base.resolve()),"exact_ngram_hashes","shingle_hashes","candidate_fingerprint_digest","resolved_path"]:
        if forbidden in body: raise AssertionError(f"technical leak {scenario_id}: {forbidden}")
    by_role={str(x.get("role")):x for x in state.artifacts if x.get("role")}
    for role in required:
        record=by_role.get(role)
        if not record: raise AssertionError(f"required artifact absent {scenario_id}/{role}")
        good,errs,_=verify_materialized_artifact(state,record)
        if not good: raise AssertionError(f"artifact verification failed {scenario_id}/{role}: {errs}")
        if role in DOSSIER_ROLES and (record.get("semantic_materialization") or {}).get("status")!="PASS": raise AssertionError(f"dossier proof absent {scenario_id}/{role}")
        if role==primary and (record.get("artifact_generation_governance") or {}).get("status")!="PASS": raise AssertionError(f"narrative proof absent {scenario_id}/{role}")
    ledger=ws.ledger_dir/"dashboard-generations.jsonl"; rows=[json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]; gens=[int(x.get("generation",0)) for x in rows]
    if gens != list(range(1,len(rows)+1)) or gens[-1] != int(state.dashboard_persistence.get("generation",0)): raise AssertionError(f"non-monotonic dashboard ledger {scenario_id}: {gens}")
    return {"scenario_id":scenario_id,"status":"PASS","mode":mode,"length_class":length_class,"input_word_count":len(words(source_text)),"real_source_ids":[x.get("id") for x in selected],"official_source_urls":sorted({x.get("source_url") for x in selected}),"required_artifact_roles":sorted(required),"materialized_artifacts":len(required),"dashboard_generation":int(state.dashboard_persistence.get("generation",0)),"dashboard_bytes":dashboard.stat().st_size,"dashboard_public_leaf_count":int(report.get("public_leaf_count",0)),"dashboard_semantic_witness_count":int(report.get("semantic_witness_count",0)),"anti_plagiarism_negative_probe":neg_plag,"incomplete_dossier_negative_probe":neg_dossier,"artifact_admission_precondition_isolated":True,"checkpoints":checks}


def run(cases=100,out_root=None):
    if cases != 100: raise ValueError("real-text fine-tuning suite is fixed at exactly 100 scenarios")
    records=load_fixture(); temporary=None
    if out_root:
        root=Path(out_root).resolve(); shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True,exist_ok=True)
    else: temporary=tempfile.TemporaryDirectory(); root=Path(temporary.name)
    seen=set(); scenarios=[]
    try:
        classes=list(LENGTH_CLASSES)
        for index in range(cases):
            cls=classes[index//25]; text,selected=compose_real_text(records,cls,990001+index*7919,seen); scenarios.append(exercise(root,index,cls,text,selected))
        class_counts=Counter(x["length_class"] for x in scenarios); mode_counts=Counter(x["mode"] for x in scenarios)
        if class_counts != Counter({name:25 for name in LENGTH_CLASSES}): raise AssertionError(f"length distribution mismatch: {class_counts}")
        if len(seen)!=100 or len({x["scenario_id"] for x in scenarios})!=100: raise AssertionError("100 unique real-text scenarios not achieved")
        if sum(x["anti_plagiarism_negative_probe"] for x in scenarios)!=20: raise AssertionError("expected 20 copied-source probes")
        if sum(x["incomplete_dossier_negative_probe"] for x in scenarios)!=10: raise AssertionError("expected 10 incomplete-dossier probes")
        return {"schema":"juriscribe-real-text-artifact-dashboard-finetuning/v1","profile":"JURISCRIBE_REAL_TEXT_FINETUNING_V1","status":"PASS","cases":100,"unique_input_packets":len(seen),"official_fixture_records":len(records),"length_classes":dict(class_counts),"modes":dict(mode_counts),"anti_plagiarism_negative_probes":20,"incomplete_dossier_negative_probes":10,"scope_note":"The suite isolates final artifact admission; historical lifecycle suites remain authoritative for full final-review and completion convergence.","invariants":["source packets consist only of frozen verified official legal-text excerpts","every required material artifact passes bounded materialization verification","new canonical dossier DOCX files contain every leaf of the canonical semantic projection","primary narrative artifacts satisfy accepted generation configuration and anti-plagiarism governance","copied-source adversarial candidates are blocked","incomplete canonical dossier files are blocked","persistent dashboards contain real semantic witnesses and every registered artifact summary","dashboard generation ledgers advance monotonically through each real session"],"scenarios":scenarios}
    finally:
        if temporary is not None: temporary.cleanup()


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--cases",type=int,default=100); p.add_argument("--out-root"); p.add_argument("--json-out"); args=p.parse_args(argv); result=run(args.cases,args.out_root)
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
from .editorial import infer_document_type
from .modes import CONTINUATION, GREENFIELD, REVIEW, normalize_mode

@dataclass(frozen=True)
class SetupParameter:
    key: str; label: str; recommended: Any; rationale: str; choices: list[Any]
    def record(self) -> dict[str, Any]: return asdict(self)

def _length_for(mode, mining, request):
    words=int((mining.get("surface") or {}).get("word_count",0) or 0); raw=str(request.get("raw","")).lower()
    if mode==CONTINUATION:
        target=max(1200,int(words*1.6)) if words else 2500; return [int(target*.85),int(target*1.15)]
    if mode==GREENFIELD:
        if "monograf" in raw or "trattato" in raw: return [12000,30000]
        if "articolo" in raw or "paper" in raw or "saggio" in raw: return [4000,9000]
        return [2500,7000]
    return None

def propose_setup(mining: dict[str,Any], request: dict[str,Any], *, reticulum=None, mode=CONTINUATION):
    if not reticulum or reticulum.get("status")!="PASS": raise ValueError("setup may be proposed only after validated epistemic reticulum")
    mode=normalize_mode(mode); document_type=infer_document_type(request,mode); style=mining.get("style",{}); length=_length_for(mode,mining,request)
    params=[SetupParameter("document_type","Tipo di testo",document_type,"Serve ad applicare in modo fluido standard editoriali coerenti con il genere.",["LEGAL_CHAPTER","LEGAL_MONOGRAPH","LEGAL_ARTICLE","LEGAL_ESSAY","LEGAL_MEMORANDUM","LEGAL_REPORT","GENERIC_LEGAL_TEXT"]),SetupParameter("audience","Destinatari","giuristi, accademici e redazioni giuridiche","Registro, densità esplicativa e apparato delle fonti dipendono dal lettore previsto.",["giuristi, accademici e redazioni giuridiche","professionisti del diritto","lettore interdisciplinare qualificato"]),SetupParameter("citation_style","Stile citazionale","PROJECT_DEFINED","Juriscribe impone integrità e tracciabilità, non un unico stile bibliografico universale.",["PROJECT_DEFINED","note a piè di pagina","autore-data"]),SetupParameter("research_depth","Ricerca e fonti","verifica mirata dei claim materiali","Ogni claim esterno deve essere circostanziato; profondità e aggiornamento dipendono dall'incarico.",["verifica mirata dei claim materiali","solo corpus fornito","ricerca estesa e aggiornata"])]
    if mode==CONTINUATION:
        params += [SetupParameter("work_objective","Funzione del capitolo","capitolo successivo in continuità sistematica","Derivata dal reticolo e dalla funzione relazionale dei capitoli precedenti.",["capitolo successivo in continuità sistematica","ricostruzione sistematica","capitolo critico/autonomo"]),SetupParameter("argumentative_posture","Postura argomentativa","continuità critica controllata","Preserva la grammatica argomentativa dell'opera senza imitazione meccanica.",["continuità critica controllata","prevalentemente ricostruttiva","prevalentemente critica"])]
    elif mode==GREENFIELD:
        params += [SetupParameter("work_objective","Obiettivo del testo","sviluppare il concept in una tesi giuridica verificabile","Il concept orienta la ricerca ma non è trattato come fonte o verità già verificata.",["sviluppare il concept in una tesi giuridica verificabile","ricostruzione sistematica","analisi critica","proposta interpretativa"]),SetupParameter("argumentative_posture","Postura argomentativa","ricostruttiva con valutazione critica","Definisce il rapporto fra esposizione del diritto positivo, dottrina e tesi dell'autore.",["ricostruttiva con valutazione critica","prevalentemente ricostruttiva","prevalentemente critica"])]
    else:
        params += [SetupParameter("review_scope","Perimetro della revisione","scientifica, contenutistica e redazionale completa","La review deve distinguere correttezza scientifica, contenuto, fonti, logica e qualità editoriale.",["scientifica, contenutistica e redazionale completa","scientifica e fonti","contenutistica e logica","redazionale"]),SetupParameter("review_output","Esito richiesto","REPORT_ONLY","Una review può essere completa anche se il testo resta difettoso; la riscrittura è un incarico ulteriore esplicito.",["REPORT_ONLY","REPORT_AND_REVISED_TEXT"]),SetupParameter("preserve_author_voice","Voce autoriale",True,"Le correzioni redazionali non devono uniformare inutilmente la voce dell'autore.",[True,False])]
    if length is not None: params.append(SetupParameter("length_words","Lunghezza",length,"Range editoriale raccomandato, modificabile dall'utente in base al progetto.",[length,[1200,1800],[2500,3500],[4000,9000],[12000,30000]]))
    return {"status":"USER_SETUP_REQUIRED","mode":mode,"recommended":{p.key:p.recommended for p in params},"parameters":[p.record() for p in params],"simple_options":["ACCETTA CONSIGLIATI","MODIFICA","ALTRO"],"style_register":style.get("register"),"reticulum_digest":reticulum.get("digest")}

def accept_setup(proposal, overrides=None):
    accepted=dict(proposal.get("recommended",{})); accepted.update(overrides or {})
    return {"status":"ACCEPTED","mode":normalize_mode(str(proposal.get("mode",CONTINUATION))),"accepted":accepted,"source":"recommended" if not overrides else "recommended_with_user_overrides","reticulum_digest":proposal.get("reticulum_digest")}

def parameter_dods(accepted_setup):
    return [{"id":f"DOD-PARAM-{k.upper()}","kind":"USER_PARAMETER","parameter":k,"expected":v,"status":"OPEN","evidence":[],"blocking":True} for k,v in accepted_setup.get("accepted",{}).items()]

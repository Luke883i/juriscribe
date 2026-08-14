from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class SetupParameter:
    key: str
    label: str
    recommended: Any
    rationale: str
    choices: list[Any]
    def record(self) -> dict[str, Any]: return asdict(self)

def propose_setup(mining: dict[str, Any], request: dict[str, Any], *, reticulum: dict[str, Any] | None = None) -> dict[str, Any]:
    if not reticulum or reticulum.get("status") != "PASS":
        raise ValueError("setup may be proposed only after validated epistemic reticulum")
    surface=mining.get("surface",{}); style=mining.get("style",{}); prior_words=int(surface.get("word_count",0) or 0)
    target=max(1200,int(prior_words*1.6)) if prior_words else 2500
    length_range=[int(target*0.85),int(target*1.15)]
    function="capitolo successivo in continuità sistematica" if "capitolo" in request.get("raw","").lower() else "sviluppo coerente della traiettoria argomentativa"
    params=[
        SetupParameter("chapter_function","Funzione del capitolo",function,"Derivata dal reticolo e dalla funzione relazionale dei capitoli precedenti.",[function,"ricostruzione sistematica","capitolo critico/autonomo"]),
        SetupParameter("length_words","Lunghezza",length_range,"Stimata da estensione, densità e ruolo del corpus precedente.",[length_range,[1200,1800],[2500,3500]]),
        SetupParameter("research_depth","Ricerca e fonti","verifica mirata dei claim materiali","Ogni claim esterno deve essere circostanziato e localizzato.",["verifica mirata dei claim materiali","solo corpus fornito","ricerca estesa e aggiornata"]),
        SetupParameter("argumentative_posture","Postura argomentativa","continuità critica controllata","Replica la grammatica argomentativa senza imitazione meccanica.",["continuità critica controllata","prevalentemente ricostruttiva","prevalentemente critica"]),
    ]
    return {"status":"USER_SETUP_REQUIRED","recommended":{p.key:p.recommended for p in params},"parameters":[p.record() for p in params],"simple_options":["ACCETTA CONSIGLIATI","MODIFICA"],"style_register":style.get("register"),"reticulum_digest":reticulum.get("digest")}

def accept_setup(proposal: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    accepted=dict(proposal.get("recommended",{})); accepted.update(overrides or {})
    return {"status":"ACCEPTED","accepted":accepted,"source":"recommended" if not overrides else "recommended_with_user_overrides","reticulum_digest":proposal.get("reticulum_digest")}

def parameter_dods(accepted_setup: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"id":f"DOD-PARAM-{k.upper()}","kind":"USER_PARAMETER","parameter":k,"expected":v,"status":"OPEN","evidence":[],"blocking":True} for k,v in accepted_setup.get("accepted",{}).items()]

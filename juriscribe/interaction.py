from __future__ import annotations
import hashlib,json
from typing import Any
SCHEMA="juriscribe-interaction-card/v2"; FREE_CHOICE="ALTRO"
PHASE_CHOICES={"TERMS_PRESENTED":["I ACCEPT","I DECLINE",FREE_CHOICE],"PROBE_REQUIRED":["PROBE JURISCRIBE",FREE_CHOICE],"INITIALIZE_REQUIRED":["INITIALIZE JURISCRIBE",FREE_CHOICE],"MODE_SELECTION_REQUIRED":["CONTINUATION","GREENFIELD","REVIEW",FREE_CHOICE],"MODE_SELECTED":["STATO SESSIONE",FREE_CHOICE],"ACTIVE":["SCEGLI MODALITÀ","STATO SESSIONE",FREE_CHOICE],"USER_SETUP_REQUIRED":["ACCETTA CONSIGLIATI","MODIFICA",FREE_CHOICE],"HUMAN_DECISION_REQUIRED":["ACCETTA OPZIONE 1","ACCETTA OPZIONE 2","CHIEDI CHIARIMENTI",FREE_CHOICE],"COMPLETE":["APRI ARTEFATTI","RICHIEDI MODIFICHE","NUOVO LAVORO",FREE_CHOICE]}
def canonical_digest(value:Any)->str: return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
def interaction_card(phase,*,headline="",summary="",choices=None,extra_choices=None,blocking=None):
    phase=str(phase).upper(); selected=list(choices or PHASE_CHOICES.get(phase,[FREE_CHOICE]))
    for item in extra_choices or []:
        if item not in selected: selected.append(item)
    if FREE_CHOICE not in selected: selected.append(FREE_CHOICE)
    card={"schema":SCHEMA,"phase":phase,"headline":headline or phase.replace("_"," ").title(),"summary":summary,"choices":selected,"free_input_allowed":True,"blocking":bool(blocking if blocking is not None else phase not in {"ACTIVE","MODE_SELECTED","COMPLETE"})}; card["digest"]=canonical_digest(card); return card
def validate_interaction_card(card):
    if not card: return False,["interaction card missing"]
    errors=[]
    if card.get("schema")!=SCHEMA: errors.append("interaction card schema mismatch")
    choices=[str(x) for x in card.get("choices",[])]
    if not choices: errors.append("interaction choices missing")
    if FREE_CHOICE not in choices: errors.append("interaction card must expose ALTRO free-request path")
    if card.get("free_input_allowed") is not True: errors.append("interaction free input must remain allowed")
    if card.get("digest")!=canonical_digest({k:v for k,v in card.items() if k!="digest"}): errors.append("interaction card digest mismatch")
    return not errors,errors
def append_interaction_history(interaction,*,kind,value,phase,record_id=""):
    current=dict(interaction or {}); history=list(current.get("history",[])); item={"id":record_id or f"INT-{len(history)+1:04d}","kind":kind,"value":value,"phase":phase}; item["digest"]=canonical_digest(item); history.append(item); current["history"]=history; return current

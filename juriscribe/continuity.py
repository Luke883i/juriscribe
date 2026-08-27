"""Minimal scientific-continuity primitives for Juriscribe 1.0.

No new authority is introduced. Exact runtime inputs are an INTERNAL replay
witness; the iteration card is PROJECTION_ONLY.
"""
from __future__ import annotations

import copy, hashlib, json
from dataclasses import asdict, is_dataclass
from typing import Any

SCHEMA = "juriscribe-continuity/v1"
MATERIAL_SCHEMA = "juriscribe-continuity-material/v1"
ITERATION_SCHEMA = "juriscribe-iteration-projection/v1"
ITERATION_AUTHORITY = "PROJECTION_ONLY"
ARCHIVE_AUTHORITY = "NO_INDEPENDENT_AUTHORITY"
AUTHORITY = ITERATION_AUTHORITY
RECOVERY_ACTION = "RECOVERY BUNDLE"
MATERIALIZATION_CONTINUE_PHRASE = "Continue until the end of artefact materialization"
MATERIALIZATION_PENDING = "MATERIALIZATION_PENDING"


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _state(state: Any) -> dict[str, Any]:
    if isinstance(state, dict): return state
    if is_dataclass(state): return asdict(state)
    return dict(getattr(state, "__dict__", {}))


def _strategy(state: Any, create=False) -> dict[str, Any]:
    if isinstance(state, dict):
        value = state.setdefault("strategy", {}) if create else (state.get("strategy") or {})
    else:
        value = getattr(state, "strategy", None)
        if value is None and create: value = {}; setattr(state, "strategy", value)
        value = value or {}
    if not isinstance(value, dict): raise TypeError("state.strategy must be a mapping")
    return value


def continuity_state(state: Any, create=False) -> dict[str, Any]:
    strategy = _strategy(state, create)
    if not create: return strategy.get("continuity") or {}
    value = strategy.setdefault("continuity", {"schema": SCHEMA, "materials": {}, "status": "READY"})
    if not isinstance(value, dict): raise TypeError("state.strategy.continuity must be a mapping")
    return value


def archive_material(state: Any, text: str, *, source_id: str, role: str, chapter: str | None = None) -> dict[str, Any]:
    source_id, role, text = str(source_id or "").strip(), str(role or "").strip().lower(), str(text or "")
    if not source_id or not role: raise ValueError("continuity source_id and role required")
    encoded = text.encode("utf-8"); text_sha = hashlib.sha256(encoded).hexdigest()
    corpus = next((x for x in (_state(state).get("corpus") or []) if str(x.get("source_id") or "") == source_id), None)
    if corpus:
        if str(corpus.get("role") or "").lower() not in {"", role}: raise ValueError("continuity material role differs from corpus role")
        if str(corpus.get("digest") or "") not in {"", text_sha}: raise ValueError("continuity material text differs from corpus digest")
    record = {"schema": MATERIAL_SCHEMA, "source_id": source_id, "role": role, "chapter": chapter,
              "representation": "RUNTIME_INGESTED_UTF8_TEXT", "encoding": "utf-8", "text_sha256": text_sha,
              "byte_length": len(encoded), "character_count": len(text), "text": text}
    record["digest"] = canonical_digest(record)
    continuity = continuity_state(state, True); materials = continuity.setdefault("materials", {}); materials[source_id] = record
    continuity["materials_digest"] = canonical_digest({k: v.get("digest", "") for k, v in sorted(materials.items())})
    continuity["status"] = "READY"
    return dict(record)


def material_index(state: Any) -> list[dict[str, Any]]:
    materials = (continuity_state(state).get("materials") or {})
    return [{**{k: v for k, v in dict(record).items() if k != "text"}, "source_id": str(record.get("source_id") or source_id)}
            for source_id, record in sorted(materials.items())]


def validate_material_archive(state: Any) -> tuple[bool, list[str]]:
    s, continuity = _state(state), continuity_state(state); materials = continuity.get("materials") or {}; errors=[]
    if continuity and continuity.get("schema") != SCHEMA: errors.append("continuity schema mismatch")
    for source_id, raw in materials.items():
        r=dict(raw or {}); text=str(r.get("text") or ""); encoded=text.encode("utf-8")
        if r.get("schema") != MATERIAL_SCHEMA: errors.append(f"continuity material schema mismatch: {source_id}")
        if str(r.get("source_id") or "") != str(source_id): errors.append(f"continuity material source binding mismatch: {source_id}")
        if r.get("text_sha256") != hashlib.sha256(encoded).hexdigest(): errors.append(f"continuity material text digest mismatch: {source_id}")
        if int(r.get("byte_length",-1)) != len(encoded) or int(r.get("character_count",-1)) != len(text): errors.append(f"continuity material length mismatch: {source_id}")
        if r.get("digest") != canonical_digest({k:v for k,v in r.items() if k != "digest"}): errors.append(f"continuity material record digest mismatch: {source_id}")
    for item in s.get("corpus") or []:
        sid=str(item.get("source_id") or "").strip(); r=materials.get(sid)
        if not sid: errors.append("corpus source_id missing"); continue
        if not r: errors.append(f"runtime input representation missing from continuity archive: {sid}"); continue
        if str(item.get("role") or "").lower() not in {"", str(r.get("role") or "").lower()}: errors.append(f"continuity material role mismatch: {sid}")
        if str(item.get("digest") or "") not in {"", str(r.get("text_sha256") or "")}: errors.append(f"continuity material/corpus digest mismatch: {sid}")
    expected=canonical_digest({k:v.get("digest","") for k,v in sorted(materials.items())})
    if materials and continuity.get("materials_digest") != expected: errors.append("continuity materials aggregate digest mismatch")
    return not errors, list(dict.fromkeys(errors))


def _checkpoint_payload(state: Any) -> dict[str, Any]:
    s=copy.deepcopy(_state(state))
    for key in ("updated_at","runtime","phase","interaction","completion","dashboard_persistence","node_integrity","artifacts"): s.pop(key,None)
    admission=s.get("admission") or {}
    if isinstance(admission,dict): admission.pop("probe_receipt",None); admission.pop("bootstrap",None)
    strategy=s.get("strategy") or {}; continuity=strategy.get("continuity") or {} if isinstance(strategy,dict) else {}
    if isinstance(continuity,dict):
        c={k:copy.deepcopy(v) for k,v in continuity.items() if k not in {"recovery_lineage","export_history"}}
        c["materials"]={sid:{k:v for k,v in dict(r).items() if k!="text"} for sid,r in sorted((continuity.get("materials") or {}).items())}
        strategy["continuity"]=c
    return s


def checkpoint_id(state: Any) -> str: return "CP-" + canonical_digest(_checkpoint_payload(state))[:20]


def _materialization_requirements(state: Any) -> list[dict[str, Any]]:
    s=_state(state); mode=str(s.get("mode") or "").strip()
    if not mode: return []
    try:
        from .modes import required_artifact_requirements
        return list(required_artifact_requirements(mode, s.get("setup") or {}, s.get("corpus") or []))
    except (ImportError, ValueError, TypeError):
        return []


def _artifact_satisfies(requirement: dict[str, Any], artifact: dict[str, Any]) -> bool:
    if str(artifact.get("role") or "") != str(requirement.get("role") or ""): return False
    source=str(requirement.get("source_id") or "").strip()
    if source and str(artifact.get("source_id") or "").strip()!=source: return False
    instance=str(requirement.get("instance_key") or "").strip()
    actual=str(artifact.get("instance_key") or artifact.get("role") or "").strip()
    if instance and "*" not in instance and actual!=instance: return False
    return bool(str(artifact.get("path") or "").strip()) and str(artifact.get("readback") or "").upper()=="PASS" and not artifact.get("materialization_stale")


def materialization_status(state: Any) -> dict[str, Any]:
    s=_state(state); artifacts=list(s.get("artifacts") or []); complete=bool((s.get("completion") or {}).get("eligible"))
    strategy=s.get("strategy") or {}; cc=strategy.get("consolidation") or {} if isinstance(strategy,dict) else {}; mode=str(s.get("mode") or "")
    if mode=="COMPRESSION & CONSOLIDATION":
        finalized=(cc.get("peer_review_readiness") or {}).get("status")=="PASS" and (cc.get("provenance") or {}).get("status")=="PASS" and (cc.get("final_review") or {}).get("status")=="PASS"
    else:
        finalized=(s.get("provenance") or {}).get("status")=="PASS" and (s.get("final_review") or {}).get("status")=="PASS"
    requirements=_materialization_requirements(state); missing=[]
    for req in requirements:
        if not any(_artifact_satisfies(req,a) for a in artifacts):
            missing.append(str(req.get("instance_key") or req.get("role") or "artifact"))
    stale=[str(a.get("id") or a.get("role") or "artifact") for a in artifacts if a.get("materialization_stale") or a.get("readback")=="STALE_RECOVERY"]
    pending=bool(finalized and not complete and (missing or stale))
    return {"pending":pending,"status":MATERIALIZATION_PENDING if pending else ("COMPLETE" if complete else "NOT_PENDING"),"finalization_ready":finalized,"required_count":len(requirements),"missing":missing,"stale_artifact_ids":stale,"complete":complete and not pending,"continue_phrase":MATERIALIZATION_CONTINUE_PHRASE if pending else ""}


def _milestones(state: Any):
    s=_state(state); strategy=s.get("strategy") or {}; cc=strategy.get("consolidation") or {} if isinstance(strategy,dict) else {}; review=s.get("review") or {}
    return [("BOOTSTRAP","bootstrap validato",(s.get("admission") or {}).get("status")=="ACCEPTED"),
            ("MODE","modalità selezionata",bool(s.get("mode"))), ("INPUT","materiali acquisiti",bool(s.get("corpus"))),
            ("RETICULUM","reticolo epistemico validato",(s.get("reticulum") or {}).get("status")=="PASS"),
            ("SETUP","configurazione utente fissata",(s.get("setup") or {}).get("status")=="ACCEPTED"),
            ("CONTRACT","contratti di lavoro pronti",(s.get("mode_contract") or {}).get("status")=="READY" or (s.get("generation_contract") or {}).get("status")=="READY"),
            ("DOD","DoD materializzati",bool(s.get("dod"))), ("WORK_PRODUCT","prodotto di lavoro sigillato",bool(s.get("drafts")) or bool(cc.get("refined_candidates"))),
            ("REVIEW","review avviata o completata",bool(review.get("cycles")) or str(review.get("status") or "") not in {"","NOT_STARTED"}),
            ("FINALIZATION","finalizzazione/provenance avviata",(s.get("final_review") or {}).get("status")=="PASS" or (s.get("provenance") or {}).get("status")=="PASS" or bool(s.get("artifacts"))),
            ("COMPLETE","consegna completa",bool((s.get("completion") or {}).get("eligible")))]


def _card(state: Any):
    interaction=_state(state).get("interaction") or {}; return dict(interaction.get("card") or {}) if isinstance(interaction,dict) else {}


def _default_next(phase, missing, complete):
    if complete: return "Lavoro completato; apri gli artefatti, chiedi modifiche o crea un bundle di recupero."
    by_phase={"TERMS_PRESENTED":"Leggi i termini e accetta solo con messaggio umano esplicito.","PROBE_REQUIRED":"Verifica le capability dell'host.","PROBED":"Inizializza la sessione.","INITIALIZE_REQUIRED":"Inizializza la sessione.","MODE_SELECTION_REQUIRED":"Seleziona una modalità canonica.","MODE_SELECTED":"Fornisci i materiali richiesti dalla modalità.","USER_SETUP_REQUIRED":"Accetta o modifica la configurazione proposta.","HUMAN_DECISION_REQUIRED":"Fornisci la decisione umana materialmente necessaria."}
    by_missing={"BOOTSTRAP":"Completa bootstrap e binding dell'host.","MODE":"Seleziona una modalità canonica.","INPUT":"Fornisci i materiali richiesti dalla modalità.","RETICULUM":"Il sistema completerà mining e reticolo epistemico.","SETUP":"Conferma la configurazione utente proposta.","CONTRACT":"Il sistema congelerà i contratti di lavoro.","DOD":"Il sistema materializzerà e congelerà i DoD.","WORK_PRODUCT":"Il sistema produrrà o rifattorizzerà il candidato.","REVIEW":"Il sistema eseguirà review e saturazione.","FINALIZATION":"Il sistema completerà provenance, review finale e materializzazione.","COMPLETE":"Il sistema verificherà completion e consegna."}
    return by_phase.get(phase,by_missing.get(missing,"Il sistema proseguirà autonomamente fino al prossimo gate umano o alla consegna."))


def _how(card, blocking, complete):
    if complete: return "Nessuna azione obbligatoria; usa RECOVERY BUNDLE per uno snapshot o richiedi modifiche."
    choices=[str(x).strip() for x in card.get("choices") or [] if str(x).strip() and str(x).strip()!="ALTRO"]
    if blocking: return ("Scegli "+" / ".join(choices[:3])+" oppure usa ALTRO.") if choices else "Rispondi alla decisione richiesta oppure usa ALTRO."
    return "Automatico: nessuna decisione umana richiesta; Juriscribe prosegue. Usa STATO o RECOVERY BUNDLE quando vuoi."


def project_iteration(state: Any) -> dict[str, Any]:
    s=_state(state); phase=str(s.get("phase") or "UNKNOWN").upper(); milestones=_milestones(state); done=[(k,l) for k,l,v in milestones if v]; missing=next((k for k,_l,v in milestones if not v),None); card=_card(state); complete=bool((s.get("completion") or {}).get("eligible")) or phase=="COMPLETE"; mat=materialization_status(state); pending=mat["pending"]
    blocking=bool(card.get("blocking")); next_text=str(card.get("summary") or "").strip() if blocking and card.get("summary") else _default_next(phase,missing,complete)
    if pending: next_text="Iterazione conclusa; la materializzazione prevista dalla modalità non è ancora completa."
    actions=[]
    for item in list(card.get("choices") or [])+["STATO",RECOVERY_ACTION,"ARTEFATTI","AIUTO","ALTRO"]:
        label=str(item).strip()
        if label and label not in actions: actions.append(label)
    archive_ok,archive_errors=validate_material_archive(state); ready=True if not s.get("corpus") else archive_ok
    status="COMPLETE" if complete else (MATERIALIZATION_PENDING if pending else ("INPUT" if blocking else "WORKING"))
    p={"schema":ITERATION_SCHEMA,"authority":ITERATION_AUTHORITY,"checkpoint_id":checkpoint_id(state),
       "where":{"phase":phase,"mode":str(s.get("mode") or ""),"stage":"MATERIALIZATION" if pending else (done[-1][0] if done else "START"),"status":status},
       "done":{"milestones":[k for k,_ in done],"summary":"; ".join(l for _,l in done[-3:]) if done else "nessun milestone sostanziale ancora completato"},
       "next":{"stage":"MATERIALIZATION" if pending else (missing or "COMPLETE"),"summary":next_text,"how":f'Indica esattamente: "{MATERIALIZATION_CONTINUE_PHRASE}"' if pending else _how(card,blocking,complete),"requires_user_input":pending or (blocking and not complete)},
       "actions":actions,"materialization":mat,"recovery":{"on_demand":True,"action":RECOVERY_ACTION,"resume_ready":ready,"errors":[] if ready else archive_errors,"material_count":len(material_index(state))}}
    p["digest"]=canonical_digest(p); return p


def validate_iteration_projection(state: Any, projection: dict[str, Any] | None) -> tuple[bool,list[str]]:
    if not projection: return False,["iteration projection missing"]
    e=[]; where=projection.get("where") or {}; nxt=projection.get("next") or {}; actions=[str(x) for x in projection.get("actions") or []]
    if projection.get("schema")!=ITERATION_SCHEMA: e.append("iteration projection schema mismatch")
    if projection.get("authority")!=ITERATION_AUTHORITY: e.append("iteration projection authority escalation")
    if not all(k in where for k in ("phase","mode","stage","status")): e.append("iteration where state incomplete")
    if not isinstance(projection.get("done"),dict) or not all(k in projection["done"] for k in ("summary","milestones")): e.append("iteration done state incomplete")
    if not all(k in nxt for k in ("summary","how","stage","requires_user_input")): e.append("iteration next state incomplete")
    if RECOVERY_ACTION not in actions or "ALTRO" not in actions: e.append("iteration control actions incomplete")
    if (projection.get("recovery") or {}).get("on_demand") is not True: e.append("iteration recovery must be on demand")
    if projection != project_iteration(state): e.append("iteration projection is stale or not state-derived")
    return not e,list(dict.fromkeys(e))

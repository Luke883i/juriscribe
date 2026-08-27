"""Scientific continuity and projection primitives for Juriscribe 1.0.

This module owns no substantive proof authority. Exact runtime inputs are a
replay witness; iteration state is PROJECTION_ONLY.
"""
from __future__ import annotations

import copy
import hashlib
import json
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

# A persisted interaction card is only current when it belongs to the current
# human-facing phase. This prevents stale cards from leaking into autonomous
# projection turns or completion-edge soak cases.
INTERACTION_PHASES = frozenset({
    "TERMS_PRESENTED",
    "PROBE_REQUIRED",
    "PROBED",
    "INITIALIZE_REQUIRED",
    "MODE_SELECTION_REQUIRED",
    "MODE_SELECTED",
    "USER_SETUP_REQUIRED",
    "HUMAN_DECISION_REQUIRED",
    "COMPLETE",
})


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _state(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    if is_dataclass(state):
        return asdict(state)
    return dict(getattr(state, "__dict__", {}))


def _strategy(state: Any, create: bool = False) -> dict[str, Any]:
    if isinstance(state, dict):
        value = state.setdefault("strategy", {}) if create else (state.get("strategy") or {})
    else:
        value = getattr(state, "strategy", None)
        if value is None and create:
            value = {}
            setattr(state, "strategy", value)
        value = value or {}
    if not isinstance(value, dict):
        raise TypeError("state.strategy must be a mapping")
    return value


def continuity_state(state: Any, create: bool = False) -> dict[str, Any]:
    strategy = _strategy(state, create)
    if not create:
        return strategy.get("continuity") or {}
    value = strategy.setdefault("continuity", {"schema": SCHEMA, "materials": {}, "status": "READY"})
    if not isinstance(value, dict):
        raise TypeError("state.strategy.continuity must be a mapping")
    return value


def archive_material(
    state: Any,
    text: str,
    *,
    source_id: str,
    role: str,
    chapter: str | None = None,
) -> dict[str, Any]:
    source_id = str(source_id or "").strip()
    role = str(role or "").strip().lower()
    text = str(text or "")
    if not source_id or not role:
        raise ValueError("continuity source_id and role required")

    raw = text.encode("utf-8")
    text_sha = hashlib.sha256(raw).hexdigest()
    corpus = next(
        (
            item
            for item in (_state(state).get("corpus") or [])
            if str(item.get("source_id") or "") == source_id
        ),
        None,
    )
    if corpus:
        if str(corpus.get("role") or "").lower() not in {"", role}:
            raise ValueError("continuity material role differs from corpus role")
        if str(corpus.get("digest") or "") not in {"", text_sha}:
            raise ValueError("continuity material text differs from corpus digest")

    record = {
        "schema": MATERIAL_SCHEMA,
        "source_id": source_id,
        "role": role,
        "chapter": chapter,
        "representation": "RUNTIME_INGESTED_UTF8_TEXT",
        "encoding": "utf-8",
        "text_sha256": text_sha,
        "byte_length": len(raw),
        "character_count": len(text),
        "text": text,
    }
    record["digest"] = canonical_digest(record)

    continuity = continuity_state(state, True)
    materials = continuity.setdefault("materials", {})
    materials[source_id] = record
    continuity["materials_digest"] = canonical_digest(
        {key: value.get("digest", "") for key, value in sorted(materials.items())}
    )
    continuity["status"] = "READY"
    return dict(record)


def material_index(state: Any) -> list[dict[str, Any]]:
    materials = continuity_state(state).get("materials") or {}
    return [
        {
            **{key: value for key, value in dict(record).items() if key != "text"},
            "source_id": str(record.get("source_id") or source_id),
        }
        for source_id, record in sorted(materials.items())
    ]


def validate_material_archive(state: Any) -> tuple[bool, list[str]]:
    data = _state(state)
    continuity = continuity_state(state)
    materials = continuity.get("materials") or {}
    errors: list[str] = []

    if continuity and continuity.get("schema") != SCHEMA:
        errors.append("continuity schema mismatch")

    for source_id, raw_record in materials.items():
        record = dict(raw_record or {})
        text = str(record.get("text") or "")
        encoded = text.encode("utf-8")
        if record.get("schema") != MATERIAL_SCHEMA:
            errors.append(f"continuity material schema mismatch: {source_id}")
        if str(record.get("source_id") or "") != str(source_id):
            errors.append(f"continuity material source binding mismatch: {source_id}")
        if record.get("text_sha256") != hashlib.sha256(encoded).hexdigest():
            errors.append(f"continuity material text digest mismatch: {source_id}")
        try:
            byte_length = int(record.get("byte_length", -1))
            character_count = int(record.get("character_count", -1))
        except (TypeError, ValueError):
            errors.append(f"continuity material length metadata malformed: {source_id}")
        else:
            if byte_length != len(encoded) or character_count != len(text):
                errors.append(f"continuity material length mismatch: {source_id}")
        if record.get("digest") != canonical_digest({key: value for key, value in record.items() if key != "digest"}):
            errors.append(f"continuity material record digest mismatch: {source_id}")

    for item in data.get("corpus") or []:
        source_id = str(item.get("source_id") or "").strip()
        record = materials.get(source_id)
        if not source_id:
            errors.append("corpus source_id missing")
            continue
        if not record:
            errors.append(f"runtime input representation missing from continuity archive: {source_id}")
            continue
        if str(item.get("role") or "").lower() not in {"", str(record.get("role") or "").lower()}:
            errors.append(f"continuity material role mismatch: {source_id}")
        if str(item.get("digest") or "") not in {"", str(record.get("text_sha256") or "")}:
            errors.append(f"continuity material/corpus digest mismatch: {source_id}")

    expected = canonical_digest(
        {key: value.get("digest", "") for key, value in sorted(materials.items())}
    )
    if materials and continuity.get("materials_digest") != expected:
        errors.append("continuity materials aggregate digest mismatch")
    return not errors, list(dict.fromkeys(errors))


def _checkpoint_payload(state: Any) -> dict[str, Any]:
    data = copy.deepcopy(_state(state))
    for key in (
        "updated_at",
        "runtime",
        "phase",
        "interaction",
        "completion",
        "dashboard_persistence",
        "node_integrity",
        "artifacts",
    ):
        data.pop(key, None)

    admission = data.get("admission") or {}
    if isinstance(admission, dict):
        admission.pop("probe_receipt", None)
        admission.pop("bootstrap", None)

    strategy = data.get("strategy") or {}
    continuity = strategy.get("continuity") or {} if isinstance(strategy, dict) else {}
    if isinstance(continuity, dict):
        projected = {
            key: copy.deepcopy(value)
            for key, value in continuity.items()
            if key not in {"recovery_lineage", "export_history"}
        }
        projected["materials"] = {
            source_id: {key: value for key, value in dict(record).items() if key != "text"}
            for source_id, record in sorted((continuity.get("materials") or {}).items())
        }
        strategy["continuity"] = projected
    return data


def checkpoint_id(state: Any) -> str:
    return "CP-" + canonical_digest(_checkpoint_payload(state))[:20]


def _materialization_requirements(state: Any) -> list[dict[str, Any]]:
    data = _state(state)
    mode = str(data.get("mode") or "").strip()
    if not mode:
        return []
    try:
        from .modes import required_artifact_requirements

        return list(
            required_artifact_requirements(
                mode,
                data.get("setup") or {},
                data.get("corpus") or [],
            )
        )
    except (ImportError, ValueError, TypeError):
        return []


def _artifact_satisfies(requirement: dict[str, Any], artifact: dict[str, Any]) -> bool:
    if str(artifact.get("role") or "") != str(requirement.get("role") or ""):
        return False
    source_id = str(requirement.get("source_id") or "").strip()
    if source_id and str(artifact.get("source_id") or "").strip() != source_id:
        return False
    instance = str(requirement.get("instance_key") or "").strip()
    actual = str(artifact.get("instance_key") or artifact.get("role") or "").strip()
    if instance and "*" not in instance and actual != instance:
        return False
    return (
        bool(str(artifact.get("path") or "").strip())
        and str(artifact.get("readback") or "").upper() == "PASS"
        and not artifact.get("materialization_stale")
    )


def materialization_status(state: Any) -> dict[str, Any]:
    data = _state(state)
    artifacts = list(data.get("artifacts") or [])
    complete = bool((data.get("completion") or {}).get("eligible"))
    strategy = data.get("strategy") or {}
    consolidation = strategy.get("consolidation") or {} if isinstance(strategy, dict) else {}
    mode = str(data.get("mode") or "")
    phase = str(data.get("phase") or "").upper()

    if mode == "COMPRESSION & CONSOLIDATION":
        finalized = (
            (consolidation.get("peer_review_readiness") or {}).get("status") == "PASS"
            and (consolidation.get("provenance") or {}).get("status") == "PASS"
            and (consolidation.get("final_review") or {}).get("status") == "PASS"
        )
    else:
        finalized = (
            (data.get("provenance") or {}).get("status") == "PASS"
            and (data.get("final_review") or {}).get("status") == "PASS"
        )
    finalized = bool(
        finalized
        and phase in {
            "FINAL_SEVERE_REVIEW_PASS",
            "FINAL_REVIEWED",
            "VALIDATING",
            "ARTIFACT_REGISTERED",
            "MATERIALIZING",
        }
    )

    requirements = _materialization_requirements(state)
    missing = [
        str(requirement.get("instance_key") or requirement.get("role") or "artifact")
        for requirement in requirements
        if not any(_artifact_satisfies(requirement, artifact) for artifact in artifacts)
    ]
    stale = [
        str(artifact.get("id") or artifact.get("role") or "artifact")
        for artifact in artifacts
        if artifact.get("materialization_stale") or artifact.get("readback") == "STALE_RECOVERY"
    ]
    pending = bool(finalized and not complete and (missing or stale))
    return {
        "pending": pending,
        "status": MATERIALIZATION_PENDING if pending else ("COMPLETE" if complete else "NOT_PENDING"),
        "finalization_ready": finalized,
        "required_count": len(requirements),
        "missing": missing,
        "stale_artifact_ids": stale,
        "complete": complete and not pending,
        "continue_phrase": MATERIALIZATION_CONTINUE_PHRASE if pending else "",
    }


def _milestones(state: Any):
    data = _state(state)
    strategy = data.get("strategy") or {}
    consolidation = strategy.get("consolidation") or {} if isinstance(strategy, dict) else {}
    review = data.get("review") or {}
    return [
        ("BOOTSTRAP", "bootstrap validato", (data.get("admission") or {}).get("status") == "ACCEPTED"),
        ("MODE", "modalità selezionata", bool(data.get("mode"))),
        ("INPUT", "materiali acquisiti", bool(data.get("corpus"))),
        ("RETICULUM", "reticolo epistemico validato", (data.get("reticulum") or {}).get("status") == "PASS"),
        ("SETUP", "configurazione utente fissata", (data.get("setup") or {}).get("status") == "ACCEPTED"),
        (
            "CONTRACT",
            "contratti di lavoro pronti",
            (data.get("mode_contract") or {}).get("status") == "READY"
            or (data.get("generation_contract") or {}).get("status") == "READY",
        ),
        ("DOD", "DoD materializzati", bool(data.get("dod"))),
        (
            "WORK_PRODUCT",
            "prodotto di lavoro sigillato",
            bool(data.get("drafts")) or bool(consolidation.get("refined_candidates")),
        ),
        (
            "REVIEW",
            "review avviata o completata",
            bool(review.get("cycles")) or str(review.get("status") or "") not in {"", "NOT_STARTED"},
        ),
        (
            "FINALIZATION",
            "finalizzazione/provenance avviata",
            (data.get("final_review") or {}).get("status") == "PASS"
            or (data.get("provenance") or {}).get("status") == "PASS"
            or bool(data.get("artifacts")),
        ),
        ("COMPLETE", "consegna completa", bool((data.get("completion") or {}).get("eligible"))),
    ]


def _current_card(state: Any, phase: str) -> dict[str, Any]:
    if phase not in INTERACTION_PHASES:
        return {}
    interaction = _state(state).get("interaction") or {}
    if not isinstance(interaction, dict):
        return {}
    card = dict(interaction.get("card") or {})
    if not card:
        return {}
    card_phase = str(card.get("phase") or "").upper()
    if card_phase and card_phase != phase:
        return {}
    return card


def _default_next(phase: str, missing: str | None, complete: bool) -> str:
    if complete:
        return "Lavoro completato; apri gli artefatti, chiedi modifiche o crea un bundle di recupero."
    by_phase = {
        "TERMS_PRESENTED": "Leggi i termini e accetta solo con messaggio umano esplicito.",
        "PROBE_REQUIRED": "Verifica le capability dell'host.",
        "PROBED": "Inizializza la sessione.",
        "INITIALIZE_REQUIRED": "Inizializza la sessione.",
        "MODE_SELECTION_REQUIRED": "Seleziona una modalità canonica.",
        "MODE_SELECTED": "Fornisci i materiali richiesti dalla modalità.",
        "USER_SETUP_REQUIRED": "Accetta o modifica la configurazione utente proposta.",
        "HUMAN_DECISION_REQUIRED": "Fornisci la decisione umana materialmente necessaria.",
    }
    by_missing = {
        "BOOTSTRAP": "Completa bootstrap e binding dell'host.",
        "MODE": "Seleziona una modalità canonica.",
        "INPUT": "Fornisci i materiali richiesti dalla modalità.",
        "RETICULUM": "Il sistema completerà mining e reticolo epistemico.",
        "SETUP": "Conferma la configurazione utente proposta.",
        "CONTRACT": "Il sistema congelerà i contratti di lavoro.",
        "DOD": "Il sistema materializzerà e congelerà i DoD.",
        "WORK_PRODUCT": "Il sistema produrrà o rifattorizzerà il candidato.",
        "REVIEW": "Il sistema eseguirà review e saturazione.",
        "FINALIZATION": "Il sistema completerà provenance, review finale e materializzazione.",
        "COMPLETE": "Il sistema verificherà completion e consegna.",
    }
    return by_phase.get(
        phase,
        by_missing.get(missing, "Il sistema proseguirà autonomamente fino al prossimo gate umano o alla consegna."),
    )


def _how(card: dict[str, Any], blocking: bool, complete: bool) -> str:
    if complete:
        return "Nessuna azione obbligatoria; usa RECOVERY BUNDLE per uno snapshot o richiedi modifiche."
    choices = [
        str(value).strip()
        for value in card.get("choices") or []
        if str(value).strip() and str(value).strip() != "ALTRO"
    ]
    if blocking:
        return (
            "Scegli " + " / ".join(choices[:3]) + " oppure usa ALTRO."
            if choices
            else "Rispondi alla decisione richiesta oppure usa ALTRO."
        )
    return "Automatico: nessuna decisione umana richiesta; Juriscribe prosegue. Usa STATO o RECOVERY BUNDLE quando vuoi."


def project_iteration(state: Any) -> dict[str, Any]:
    data = _state(state)
    phase = str(data.get("phase") or "UNKNOWN").upper()
    milestones = _milestones(state)
    done = [(key, label) for key, label, value in milestones if value]
    missing = next((key for key, _label, value in milestones if not value), None)
    card = _current_card(state, phase)
    complete = bool((data.get("completion") or {}).get("eligible")) or phase == "COMPLETE"
    materialization = materialization_status(state)
    pending = materialization["pending"]
    blocking = bool(card.get("blocking"))

    next_text = (
        str(card.get("summary") or "").strip()
        if blocking and card.get("summary")
        else _default_next(phase, missing, complete)
    )
    if pending:
        next_text = "Iterazione conclusa; la materializzazione prevista dalla modalità non è ancora completa."

    actions: list[str] = []
    for value in list(card.get("choices") or []) + ["STATO", RECOVERY_ACTION, "ARTEFATTI", "AIUTO", "ALTRO"]:
        label = str(value).strip()
        if label and label not in actions:
            actions.append(label)

    archive_ok, archive_errors = validate_material_archive(state)
    recovery_ready = True if not data.get("corpus") else archive_ok
    status = "COMPLETE" if complete else (MATERIALIZATION_PENDING if pending else ("INPUT" if blocking else "WORKING"))

    projection = {
        "schema": ITERATION_SCHEMA,
        "authority": ITERATION_AUTHORITY,
        "checkpoint_id": checkpoint_id(state),
        "where": {
            "phase": phase,
            "mode": str(data.get("mode") or ""),
            "stage": "MATERIALIZATION" if pending else (done[-1][0] if done else "START"),
            "status": status,
        },
        "done": {
            "milestones": [key for key, _label in done],
            "summary": "; ".join(label for _key, label in done[-3:]) if done else "nessun milestone sostanziale ancora completato",
        },
        "next": {
            "stage": "MATERIALIZATION" if pending else (missing or "COMPLETE"),
            "summary": next_text,
            "how": (
                f'Indica esattamente: "{MATERIALIZATION_CONTINUE_PHRASE}"'
                if pending
                else _how(card, blocking, complete)
            ),
            "requires_user_input": pending or (blocking and not complete),
        },
        "actions": actions,
        "materialization": materialization,
        "recovery": {
            "on_demand": True,
            "action": RECOVERY_ACTION,
            "resume_ready": recovery_ready,
            "errors": [] if recovery_ready else archive_errors,
            "material_count": len(material_index(state)),
        },
    }
    projection["digest"] = canonical_digest(projection)
    return projection


def validate_iteration_projection(state: Any, projection: dict[str, Any]) -> tuple[bool, list[str]]:
    if not projection:
        return False, ["iteration projection missing"]
    errors: list[str] = []
    where = projection.get("where") or {}
    next_state = projection.get("next") or {}
    actions = [str(value) for value in projection.get("actions") or []]
    if projection.get("schema") != ITERATION_SCHEMA:
        errors.append("iteration projection schema mismatch")
    if projection.get("authority") != ITERATION_AUTHORITY:
        errors.append("iteration projection authority escalation")
    if not all(key in where for key in ("phase", "mode", "stage", "status")):
        errors.append("iteration where state incomplete")
    if not isinstance(projection.get("done"), dict) or not all(
        key in projection["done"] for key in ("summary", "milestones")
    ):
        errors.append("iteration done state incomplete")
    if not all(key in next_state for key in ("summary", "how", "stage", "requires_user_input")):
        errors.append("iteration next state incomplete")
    if RECOVERY_ACTION not in actions or "ALTRO" not in actions:
        errors.append("iteration control actions incomplete")
    if (projection.get("recovery") or {}).get("on_demand") is not True:
        errors.append("iteration recovery must be on demand")
    if projection != project_iteration(state):
        errors.append("iteration projection is stale or not state-derived")
    return not errors, list(dict.fromkeys(errors))

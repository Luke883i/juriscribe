from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class SetupParameter:
    key: str
    label: str
    recommended: Any
    rationale: str
    choices: list[Any]

    def record(self) -> dict[str, Any]:
        return asdict(self)


def propose_setup(mining: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    surface = mining.get("surface", {})
    style = mining.get("style", {})
    prior_words = int(surface.get("word_count", 0) or 0)
    target = max(1200, int(prior_words * 1.6)) if prior_words else 2500
    length_range = [int(target * 0.85), int(target * 1.15)]
    function = "sviluppo coerente della traiettoria argomentativa"
    if "capitolo" in (request.get("raw", "").lower()):
        function = "capitolo successivo in continuità sistematica"
    research = "verifica mirata dei claim materiali"
    posture = "continuità critica controllata"
    params = [
        SetupParameter("chapter_function", "Funzione del capitolo", function, "Derivata dalla richiesta e dalla funzione relazionale del testo precedente.", [function, "ricostruzione sistematica", "capitolo critico/autonomo"]),
        SetupParameter("length_words", "Lunghezza", length_range, "Stimata da estensione, densità e ruolo del capitolo precedente.", [length_range, [1200, 1800], [2500, 3500]]),
        SetupParameter("research_depth", "Ricerca e fonti", research, "Il default verifica i claim che possono cambiare o richiedono autorità esterna.", [research, "solo corpus fornito", "ricerca estesa e aggiornata"]),
        SetupParameter("argumentative_posture", "Postura argomentativa", posture, "Mantiene la voce dell'opera senza irrigidire il modello in una replica meccanica.", [posture, "prevalentemente ricostruttiva", "prevalentemente critica"]),
    ]
    return {
        "status": "USER_SETUP_REQUIRED",
        "recommended": {p.key: p.recommended for p in params},
        "parameters": [p.record() for p in params],
        "simple_options": ["ACCETTA CONSIGLIATI", "MODIFICA"],
        "style_register": style.get("register"),
    }


def accept_setup(proposal: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    accepted = dict(proposal.get("recommended", {}))
    accepted.update(overrides or {})
    return {"status": "ACCEPTED", "accepted": accepted, "source": "recommended" if not overrides else "recommended_with_user_overrides"}


def parameter_dods(accepted_setup: dict[str, Any]) -> list[dict[str, Any]]:
    accepted = accepted_setup.get("accepted", {})
    return [{"id": f"DOD-PARAM-{key.upper()}", "kind": "USER_PARAMETER", "parameter": key, "expected": value, "status": "OPEN", "evidence": [], "blocking": True} for key, value in accepted.items()]

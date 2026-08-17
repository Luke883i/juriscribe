from __future__ import annotations

import hashlib
import html
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .artifact_atlas import build_artifact_atlas
from .dashboard import dashboard_state_digest, render_session_dashboard
from .delivery import refresh_dashboard_artifact

PROFILE_ID = "JURISCRIBE_PERSISTENT_SESSION_DASHBOARD_V1"
SCHEMA = "juriscribe-persistent-session-dashboard/v1"


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _visible_atlas_projection(state: Any) -> dict[str, Any]:
    s = _payload(state)
    atlas = build_artifact_atlas(state)

    def record_view(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "titolo": record.get("titolo"),
            "sintesi_compressa": record.get("sintesi_compressa"),
            "stato": record.get("stato"),
            "tipo": record.get("tipo"),
            "funzione": record.get("funzione"),
            "descrizione_completa": record.get("descrizione_completa"),
            "richiamo_dashboard": record.get("richiamo_dashboard"),
            "richiamo_artefatto": record.get("richiamo_artefatto"),
        }

    request = s.get("request") or {}
    return {
        "mandato": request.get("summary") or request.get("raw"),
        "modalita": s.get("mode"),
        "titolo": atlas.get("titolo"),
        "finalita": atlas.get("finalita"),
        "sintesi_compressa": atlas.get("sintesi_compressa") or [],
        "artefatti_materiali": [record_view(item) for item in atlas.get("artefatti_materiali") or []],
        "artefatti_epistemici": [record_view(item) for item in atlas.get("artefatti_epistemici") or []],
    }


def _visible_leaf_strings(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from _visible_leaf_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _visible_leaf_strings(item)
    elif isinstance(value, bool):
        yield "si" if value else "no"
    elif value not in (None, ""):
        yield str(value)


def _semantic_witnesses(state: Any) -> list[str]:
    s = _payload(state)
    candidates: list[Any] = []
    request = s.get("request") or {}
    candidates.append(request.get("summary") or request.get("raw"))
    candidates.append(s.get("mode"))
    candidates.extend(item.get("text") for item in (s.get("epistemic_units") or [])[:12])
    candidates.extend(item.get("text") for item in (s.get("claim_ledger") or [])[:12])
    candidates.extend(item.get("title") for item in (s.get("sources") or [])[:12])
    setup = s.get("setup") or {}
    configuration = setup.get("generation_configuration") or setup.get("generation_preview") or {}
    candidates.append(configuration.get("abstract"))
    candidates.extend(configuration.get("key_concepts") or [])
    for artifact in s.get("artifacts") or []:
        if str(artifact.get("delivery_class") or "").upper() == "INTERNAL":
            continue
        candidates.append(artifact.get("summary"))
    seen: set[str] = set()
    out: list[str] = []
    for value in candidates:
        token = " ".join(str(value or "").split())
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def _public_material_roles(state: Any) -> set[str]:
    s = _payload(state)
    return {
        str(item.get("role") or "")
        for item in s.get("artifacts") or []
        if item.get("role") and str(item.get("delivery_class") or "").upper() != "INTERNAL"
    }


def dashboard_materialization_report(state: Any, page: str) -> dict[str, Any]:
    body = page.split("<body>", 1)[1].split("</body>", 1)[0] if "<body>" in page and "</body>" in page else ""
    leaves = []
    seen = set()
    projection = _visible_atlas_projection(state)
    for leaf in _visible_leaf_strings(projection):
        token = " ".join(str(leaf).split())
        if not token or token in seen:
            continue
        seen.add(token)
        leaves.append(token)
    missing = []
    for leaf in leaves:
        encoded = html.escape(leaf, quote=True)
        if encoded not in body:
            missing.append(leaf)
            if len(missing) >= 20:
                break

    witnesses = _semantic_witnesses(state)
    missing_witnesses = []
    for witness in witnesses:
        if html.escape(witness, quote=True) not in body:
            missing_witnesses.append(witness)
            if len(missing_witnesses) >= 20:
                break

    atlas = build_artifact_atlas(state)
    atlas_roles = {str(item.get("ruolo") or "") for item in atlas.get("artefatti_materiali") or [] if item.get("ruolo")}
    registered_roles = _public_material_roles(state)
    missing_roles = sorted(registered_roles - atlas_roles)
    return {
        "public_leaf_count": len(leaves),
        "missing_public_leaf_count": len(missing),
        "missing_public_leaf_samples": missing,
        "semantic_witness_count": len(witnesses),
        "missing_semantic_witness_count": len(missing_witnesses),
        "missing_semantic_witness_samples": missing_witnesses,
        "registered_public_material_roles": len(registered_roles),
        "atlas_material_roles": len(atlas_roles),
        "missing_public_material_roles": missing_roles,
        "body_present": bool(body.strip()),
    }


def verify_persistent_dashboard(state: Any, path: str | Path) -> tuple[bool, list[str], dict[str, Any]]:
    target = Path(path)
    errors: list[str] = []
    if not target.exists() or not target.is_file():
        return False, ["persistent session dashboard is missing"], {}
    try:
        page = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return False, [f"persistent dashboard read failed: {type(exc).__name__}"], {}
    if "<html" not in page.lower() or "<body>" not in page:
        errors.append("persistent dashboard is not recognizable HTML")
    expected_digest = dashboard_state_digest(state)
    marker = f'name="juriscribe-state-digest" content="{expected_digest}"'
    if marker not in page:
        errors.append("persistent dashboard is stale relative to current session state")
    report = dashboard_materialization_report(state, page)
    if not report.get("body_present"):
        errors.append("persistent dashboard body is empty")
    if report.get("missing_public_leaf_count"):
        sample = "; ".join(report.get("missing_public_leaf_samples") or [])
        errors.append("persistent dashboard omitted public artifact information: " + sample)
    if report.get("missing_semantic_witness_count"):
        sample = "; ".join(report.get("missing_semantic_witness_samples") or [])
        errors.append("persistent dashboard omitted real session semantic witnesses: " + sample)
    if report.get("missing_public_material_roles"):
        errors.append("persistent dashboard atlas omitted registered material roles: " + ", ".join(report["missing_public_material_roles"]))
    return not errors, list(dict.fromkeys(errors)), report


def _ensure_dashboard_record(state: Any, out: Path) -> None:
    artifacts = getattr(state, "artifacts")
    record = next((item for item in artifacts if item.get("role") == "session_dashboard"), None)
    if record is None:
        artifacts.append({
            "id": "dashboard",
            "role": "session_dashboard",
            "summary": "Fascicolo leggibile e persistente della sessione",
            "path": str(out),
            "readback": "PASS",
        })
        return
    record["path"] = str(out)
    record["readback"] = "PASS"


def persist_dashboard_generation(ws, state, *, trigger: str = "runtime-mutation") -> Path:
    """Atomically materialize one dashboard generation, persist state, then reload and verify it."""
    out = (ws.artifact_dir / "session-dashboard.html").resolve()
    ws.artifact_dir.mkdir(parents=True, exist_ok=True)
    _ensure_dashboard_record(state, out)

    current = dict(getattr(state, "dashboard_persistence", {}) or {})
    generation = int(current.get("generation", 0) or 0) + 1
    state.dashboard_persistence = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "status": "RENDERING",
        "generation": generation,
        "last_trigger": str(trigger or "runtime-mutation"),
    }

    tmp = out.with_name(f".{out.stem}.{uuid.uuid4().hex}.html")
    backup = out.with_name(f".{out.stem}.{uuid.uuid4().hex}.previous")
    had_previous = out.exists()
    try:
        render_session_dashboard(state.to_dict(), tmp)
        ok, errors, report = verify_persistent_dashboard(state, tmp)
        if not ok:
            raise ValueError("; ".join(errors))
        if had_previous:
            shutil.copyfile(out, backup)
        os.replace(tmp, out)
        refresh_dashboard_artifact(state, out)
        ok, errors, report = verify_persistent_dashboard(state, out)
        if not ok:
            raise ValueError("; ".join(errors))

        payload = out.read_bytes()
        state.dashboard_persistence = {
            "schema": SCHEMA,
            "profile": PROFILE_ID,
            "status": "PASS",
            "generation": generation,
            "last_trigger": str(trigger or "runtime-mutation"),
            "source_state_digest": dashboard_state_digest(state),
            "html_sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "public_leaf_count": int(report.get("public_leaf_count", 0) or 0),
            "missing_public_leaf_count": 0,
            "semantic_witness_count": int(report.get("semantic_witness_count", 0) or 0),
            "missing_semantic_witness_count": 0,
            "registered_public_material_roles": int(report.get("registered_public_material_roles", 0) or 0),
            "missing_public_material_roles": [],
        }
        ws.save(state)
        reloaded = ws.load()
        reloaded_ok, reloaded_errors, reloaded_report = verify_persistent_dashboard(reloaded, out)
        if not reloaded_ok:
            raise ValueError("persistent dashboard failed post-save reload verification: " + "; ".join(reloaded_errors))
        ws.append_ledger("dashboard-generations", {
            "schema": SCHEMA,
            "profile": PROFILE_ID,
            "generation": generation,
            "trigger": str(trigger or "runtime-mutation"),
            "phase": str(getattr(reloaded, "phase", "")),
            "source_state_digest": dashboard_state_digest(reloaded),
            "html_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "size_bytes": out.stat().st_size,
            "public_leaf_count": int(reloaded_report.get("public_leaf_count", 0) or 0),
            "semantic_witness_count": int(reloaded_report.get("semantic_witness_count", 0) or 0),
            "registered_public_material_roles": int(reloaded_report.get("registered_public_material_roles", 0) or 0),
            "status": "PASS",
        })
        backup.unlink(missing_ok=True)
        return out
    except Exception:
        tmp.unlink(missing_ok=True)
        if backup.exists():
            os.replace(backup, out)
        elif not had_previous:
            out.unlink(missing_ok=True)
        raise
    finally:
        tmp.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)

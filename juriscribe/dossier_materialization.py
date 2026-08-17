from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from . import delivery as _delivery
from .editorial_artifacts import DOSSIER_ROLES, PROFILE_ID, build_editorial_artifact_views, semantic_projection_digest

SCHEMA = "juriscribe-dossier-semantic-materialization/v1"
PROFILE = "JURISCRIBE_DOSSIER_SEMANTIC_MATERIALIZATION_V1"


def _normalize(value: Any) -> str:
    return " ".join(str(value if value is not None else "").split())


def _leaf_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _leaf_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _leaf_strings(item)
    elif isinstance(value, bool):
        yield "si" if value else "no"
    elif value not in (None, ""):
        token = _normalize(value)
        if token:
            yield token


def dossier_projection(state: Any, role: str) -> dict[str, Any]:
    role = str(role or "")
    if role not in DOSSIER_ROLES:
        raise ValueError(f"role {role} is not a canonical semantic dossier")
    return build_editorial_artifact_views(state)[role]


def dossier_semantic_leaves(state: Any, role: str) -> list[str]:
    seen: set[str] = set()
    leaves: list[str] = []
    for value in _leaf_strings(dossier_projection(state, role)):
        token = _normalize(value)
        if token and token not in seen:
            seen.add(token)
            leaves.append(token)
    return leaves


def render_dossier_text(state: Any, role: str) -> str:
    """Deterministic human-readable serialization of the canonical dossier projection.

    This is intentionally plain text: any DOCX writer may use it as source material,
    while the verifier below remains independent from a particular DOCX layout.
    """
    projection = dossier_projection(state, role)
    lines: list[str] = []

    def walk(value: Any, label: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, str(key).replace("_", " ").strip().capitalize())
            return
        if isinstance(value, (list, tuple, set)):
            for index, item in enumerate(value, 1):
                walk(item, f"{label} {index}".strip())
            return
        if value in (None, ""):
            return
        token = "si" if value is True else "no" if value is False else _normalize(value)
        if token:
            lines.append(f"{label}: {token}" if label else token)

    walk(projection)
    return "\n".join(lines).strip() + "\n"


def _extract_docx_text(state: Any, record: dict[str, Any]) -> str:
    ok, errors, metadata = _delivery.verify_materialized_artifact(state, record)
    if not ok:
        raise ValueError("; ".join(errors))
    path = Path(str(metadata.get("resolved_path") or record.get("path") or ""))
    with zipfile.ZipFile(path) as package:
        info = package.getinfo("word/document.xml")
        if info.file_size > _delivery.MAX_DOCUMENT_XML_BYTES:
            raise ValueError("canonical dossier word/document.xml exceeds readback limit")
        with package.open(info) as handle:
            raw = handle.read(_delivery.MAX_DOCUMENT_XML_BYTES + 1)
    if len(raw) > _delivery.MAX_DOCUMENT_XML_BYTES:
        raise ValueError("canonical dossier readback exceeded safety limit")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("canonical dossier text extraction failed: invalid WordprocessingML") from exc
    parts = [element.text for element in root.iter() if str(element.tag).rsplit("}", 1)[-1] == "t" and element.text]
    text = _normalize(" ".join(parts))
    if not text:
        raise ValueError("canonical dossier contains no extractable text")
    return text


def verify_dossier_semantic_materialization(state: Any, record: dict[str, Any]) -> dict[str, Any]:
    role = str(record.get("role") or "")
    if role not in DOSSIER_ROLES:
        return {"schema": SCHEMA, "profile": PROFILE, "role": role, "status": "NOT_APPLICABLE"}
    try:
        text = _extract_docx_text(state, record)
    except ValueError as exc:
        return {
            "schema": SCHEMA,
            "profile": PROFILE,
            "role": role,
            "semantic_profile": PROFILE_ID,
            "status": "FAIL",
            "public_leaf_count": 0,
            "missing_public_leaf_count": 0,
            "errors": [str(exc)],
        }
    leaves = dossier_semantic_leaves(state, role)
    missing = [leaf for leaf in leaves if _normalize(leaf) not in text][:20]
    errors: list[str] = []
    if missing:
        errors.append("canonical dossier DOCX omits semantic projection content: " + "; ".join(missing))
    return {
        "schema": SCHEMA,
        "profile": PROFILE,
        "role": role,
        "semantic_profile": PROFILE_ID,
        "semantic_projection_digest": semantic_projection_digest(state, role),
        "public_leaf_count": len(leaves),
        "missing_public_leaf_count": len(missing),
        "missing_public_leaf_samples": missing,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def dossier_semantic_materialization_gate(state: Any) -> tuple[bool, list[str]]:
    by_role = {str(item.get("role") or ""): item for item in getattr(state, "artifacts", []) if item.get("role")}
    errors: list[str] = []
    for role in DOSSIER_ROLES:
        record = by_role.get(role)
        if not record:
            continue
        proof = record.get("semantic_materialization") or {}
        if proof.get("status") != "PASS":
            errors.append(f"canonical dossier semantic materialization is not PASS: {role}")
            continue
        if proof.get("semantic_projection_digest") != semantic_projection_digest(state, role):
            errors.append(f"canonical dossier semantic materialization is stale: {role}")
        if int(proof.get("missing_public_leaf_count", 0) or 0) != 0:
            errors.append(f"canonical dossier semantic materialization is incomplete: {role}")
    return not errors, list(dict.fromkeys(errors))

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

NODE_H_VERSION = "2"
_REQUIRED = {
    "JURISCRIBE_NODE_H_VERSION",
    "JURISCRIBE_SESSION_ID",
    "JURISCRIBE_PHASE",
    "JURISCRIBE_CORPUS_SHA256",
    "JURISCRIBE_RETICULUM_SHA256",
    "JURISCRIBE_SETUP_SHA256",
    "JURISCRIBE_DOD_SHA256",
    "JURISCRIBE_GENERATION_CONTRACT_SHA256",
    "JURISCRIBE_CURRENT_CANDIDATE_SHA256",
    "JURISCRIBE_REVIEW_SHA256",
    "JURISCRIBE_BIBLIOGRAPHY_SHA256",
    "JURISCRIBE_SIMULATION_SHA256",
    "JURISCRIBE_COMPRESSION_SHA256",
    "JURISCRIBE_SOURCES_SHA256",
    "JURISCRIBE_CLAIMS_SHA256",
    "JURISCRIBE_SOURCE_INTELLIGENCE_SHA256",
    "JURISCRIBE_QUALITY_SHA256",
    "JURISCRIBE_BENCHMARK_SHA256",
    "JURISCRIBE_ARTIFACTS_SHA256",
    "JURISCRIBE_READY",
}
_DEFINE_RE = re.compile(r'^#define\s+(JURISCRIBE_[A-Z0-9_]+)\s+"?(.*?)"?\s*$')


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def node_values(state: dict[str, Any]) -> dict[str, str]:
    drafts = state.get("drafts", [])
    current = drafts[-1].get("digest", "") if drafts else ""
    review = state.get("review", {})
    bibliography = state.get("bibliography", {})
    reticulum = state.get("reticulum", {})
    generation = state.get("generation_contract", {})
    values = {
        "JURISCRIBE_NODE_H_VERSION": NODE_H_VERSION,
        "JURISCRIBE_SESSION_ID": str(state.get("session_id", "")),
        "JURISCRIBE_PHASE": str(state.get("phase", "")),
        "JURISCRIBE_CORPUS_SHA256": _digest(state.get("corpus", [])),
        "JURISCRIBE_SOURCES_SHA256": _digest(state.get("sources", [])),
        "JURISCRIBE_CLAIMS_SHA256": _digest(state.get("claim_ledger", [])),
        "JURISCRIBE_SOURCE_INTELLIGENCE_SHA256": _digest(state.get("source_intelligence", {})),
        "JURISCRIBE_RETICULUM_SHA256": str(reticulum.get("digest", "")),
        "JURISCRIBE_SETUP_SHA256": _digest((state.get("setup") or {}).get("accepted", {})),
        "JURISCRIBE_DOD_SHA256": _digest(state.get("dod", [])),
        "JURISCRIBE_GENERATION_CONTRACT_SHA256": str(generation.get("contract_digest", "")),
        "JURISCRIBE_CURRENT_CANDIDATE_SHA256": str(current),
        "JURISCRIBE_REVIEW_SHA256": _digest(review),
        "JURISCRIBE_BIBLIOGRAPHY_SHA256": str(bibliography.get("digest", _digest([]))),
        "JURISCRIBE_SIMULATION_SHA256": _digest(state.get("simulations", {})),
        "JURISCRIBE_COMPRESSION_SHA256": _digest(state.get("compression", {})),
        "JURISCRIBE_QUALITY_SHA256": _digest(state.get("quality", {})),
        "JURISCRIBE_BENCHMARK_SHA256": _digest(state.get("benchmark", {})),
        "JURISCRIBE_ARTIFACTS_SHA256": _digest(state.get("artifacts", [])),
        "JURISCRIBE_READY": "1" if (state.get("completion") or {}).get("eligible") else "0",
    }
    return values


def render_node_header(state: dict[str, Any]) -> str:
    v = node_values(state)
    lines = [
        "#ifndef JURISCRIBE_SESSION_NODE_H",
        "#define JURISCRIBE_SESSION_NODE_H",
        "/* Generated session integrity header. Metadata/digests only; no legal corpus text. */",
    ]
    for key in sorted(v):
        lines.append(f'#define {key} "{v[key]}"')
    lines.extend([
        '#define JURISCRIBE_STATE_PATH "state.json"',
        '#define JURISCRIBE_LEDGER_ROOT "ledger"',
        '#define JURISCRIBE_ARTIFACT_ROOT "artifacts"',
        "#endif",
        "",
    ])
    return "\n".join(lines)


def write_node_header(state: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_node_header(state), encoding="utf-8")
    return out


def parse_node_header(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = _DEFINE_RE.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2).strip('"')
    return values


def validate_node_header(state: dict[str, Any], text: str) -> tuple[bool, list[str]]:
    parsed = parse_node_header(text)
    expected = node_values(state)
    errors: list[str] = []
    missing = sorted(_REQUIRED - set(parsed))
    if missing:
        errors.append("node.h missing macros: " + ", ".join(missing))
    for key, value in expected.items():
        if parsed.get(key) != value:
            errors.append(f"node.h {key} mismatch")
    return not errors, errors

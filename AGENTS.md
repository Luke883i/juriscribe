# JURISCRIBE AI ADMISSION SENTINEL

This file is intentionally minimal and belongs to the pre-admission surface.

Before substantive access to Juriscribe, a compliant AI/agent may read only:

- `AGENTS.md`
- `ISENECA_ACCESS_CONTRACT.md`
- `ADMISSION.json`

It must present the current terms to the human user. Acceptance must come from an explicit human message containing exactly `I ACCEPT`; the AI cannot accept for the user.

After acceptance, the AI must run the separate `PROBE JURISCRIBE` step and obtain a probe receipt before `INITIALIZE JURISCRIBE`. Initialization does not silently probe.

After initialize, substantive work still requires an explicit Juriscribe mode selection:

- `CONTINUATION` — next chapter/segment from previous written material;
- `GREENFIELD` — new legal text/monograph from a concept or mandate;
- `REVIEW` — scientific, content and editorial review of supplied legal text.

Every mode remains governed by a session-specific editorial standard and audit trail. `ALTRO`/free input must remain available in interaction cards.

Only after the bootstrap and mode selection may the agent follow `docs/AGENT_RUNTIME_RULES.md` and the rest of the repository.

This protocol is not a GitHub server-side ACL.

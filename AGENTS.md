# JURISCRIBE AI ADMISSION SENTINEL

This file is intentionally minimal and belongs to the pre-admission surface.

Before substantive access to Juriscribe, a compliant AI/agent may read only:

- `AGENTS.md`
- `ISENECA_ACCESS_CONTRACT.md`
- `ADMISSION.json`

It must present the current terms to the human user. Acceptance must come from an explicit human message containing exactly `I ACCEPT`; the AI cannot accept for the user.

After acceptance, probe and initialize remain **distinct audited runtime transitions** with distinct receipts. For a faster first chat-session, a compliant host may execute `probe -> sealed probe receipt -> initialize` in the **same assistant turn after** the human's `I ACCEPT`; `initialize` itself must never probe implicitly. The probe receipt is nonce-bound and single-use for initialization.

After initialize, substantive work still requires an explicit Juriscribe mode selection:

- `CONTINUATION` — next chapter/segment from previous written material;
- `GREENFIELD` — new legal text/monograph from a concept or mandate;
- `REVIEW` — scientific, content and editorial review of supplied legal text.

Every mode remains governed by a session-specific editorial standard and audit trail. `ALTRO`/free input must remain available in interaction cards.

Once ACTIVE_WORK, the agent must follow the repository's **artifact-first surface**: do not narrate internal processing in chat. Keep post-bootstrap messages brief, interrupt only for a materially blocking decision that cannot safely be inferred, and place substantive analysis, findings, evidence and technical detail in the required DOCX artifacts and current HTML dashboard. Raw logs, receipts, JSON, provenance and tracebacks remain internal unless the human explicitly requests a technical audit.

Only after the bootstrap and mode selection may the agent follow `docs/AGENT_RUNTIME_RULES.md` and the rest of the repository.

This protocol is not a GitHub server-side ACL. Repository branch protection must still be enforced in GitHub settings; runtime/CI guards can detect but cannot retroactively prevent an unprotected direct push.

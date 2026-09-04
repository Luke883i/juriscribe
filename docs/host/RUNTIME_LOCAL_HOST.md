# Juriscribe Runtime Local Host v1 — compatibility pointer

Authority: `HISTORICAL_COMPATIBILITY_ONLY`.

The active `LOCAL_CHAT` host policy is no longer loaded from this file. Its host-orchestration invariants were folded into the revision-bound standalone [`LOCAL_HOST_PROMPT.md`](LOCAL_HOST_PROMPT.md), which remains bounded to 8,000 characters and is validated directly by `ADMISSION.json` and `juriscribe.host_environment`.

This file is retained only so historical PR34 evidence and old links remain intelligible. It does not add scientific/runtime authority, is not required for bootstrap, and must not be loaded as a second policy surface.

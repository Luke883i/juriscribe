# Juriscribe Host Execution Contract v1.2

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## Goal

For `LOCAL_CHAT`, reach the exact pinned Juriscribe method/runtime with the fewest truthful operations. Do not spend turns probing path classes that the host profile declares out-of-scope.

## Cold start

Before acceptance, resolve canonical `main` once to a full SHA and read only the current `pre_admission_allowlist` from that revision. `LOCAL_CHAT` assumes no preinstalled Juriscribe runtime and no local Git checkout/package; it does not probe those assumptions. Direct Git checkout/fetch, `gh`, DNS resolution, public-HTTP fallback and package installation are non-paths, not failure experiments.

Primary transport is connected GitHub repository/API bytes. Repository read never becomes runtime execution by label.

## Profile handoff

Immediately after exact human `I ACCEPT`, `LOCAL_CHAT` requires one explicit execution-profile choice:

- `LEAN`: identical Method Kernel and epistemic obligations, no runtime receipt/checkpoint/proof/canonical `COMPLETE` authority.
- `ATTESTED`: identical method/epistemic obligations plus real canonical runtime transitions, receipts, state and applicable gates.

These profiles are not scientific modes. The general `ATTESTED_PREFERRED` policy remains available to non-`LOCAL_CHAT` hosts; this host specialization does not auto-select.

## LEAN

Bind the same-revision `METHOD_KERNEL.json`; if `METHOD_ACCESS` is valid, skip runtime bootstrap entirely. Discover scientific modes dynamically from the current Method Kernel and record `METHOD_MODE_INTENT`, never synthetic runtime mode state. Runtime-search exhaustion is not a prerequisite because `LOCAL_CHAT` has an explicit user-selected LEAN path.

## ATTESTED byte transport

Materialize only `H0_HANDSHAKE_CLOSURE` first: `juriscribe/__init__.py`, `juriscribe/admission.py`, `juriscribe/bootstrap.py`, `juriscribe/host_bootstrap.py`, plus the bound access contract. Obtain each expected Git blob SHA from the pinned tree; verify fetched bytes with Git object hashing (`blob <len>\0<bytes>`) before import. Byte mismatch or revision mismatch fails closed.

H0 may emit real Admission/Probe receipts only through canonical code after revision, contract and human-acceptance binding succeed. Defer H1/session activation bytes until ATTESTED execution actually needs initialize/state.

A genuinely transient connector operation gets at most one retry. Otherwise record exact `INFRASTRUCTURE_DEBT` and offer LEAN; do not roam into Git/DNS/install/public-HTTP alternatives.

## Stop condition

LEAN stops transport work after Method Access is bound. ATTESTED stops bootstrap search at successful same-revision execution or a primary-transport blocker. Infrastructure limitations never weaken method or epistemic duties.

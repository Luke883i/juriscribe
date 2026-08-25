# Juriscribe

Juriscribe is an autonomous, repository-governed runtime for auditable legal/scientific/editorial work. The canonical entrypoint is `python -m juriscribe`; an optional local GPT may act as a host adapter, but it is not a second Juriscribe implementation.

## Bootstrap

Discovery is non-authorizing. Read the pre-admission surface, present the current terms, and wait for exact human `I ACCEPT`. After acceptance, `PROBE JURISCRIBE` and `INITIALIZE JURISCRIBE` remain distinct transitions; the runtime may use `bootstrap-after-acceptance` to execute them in one host turn while keeping separate receipts. Mode selection remains explicit.

## Canonical modes

- `CONTINUATION` — continue prior written material.
- `GREENFIELD` — create a new legal text from a concept or mandate.
- `REVIEW` — scientific/content/editorial review; supports `REPORT_ONLY` and `REPORT_AND_REVISED_TEXT`.
- `COMPRESSION_CONSOLIDATION` — ingest immutable canonical references plus refinable candidates, build a lossless joint reticulum, search for a minimal surgical refactoring, run 10,000,000 mutation instances plus M+1000/N+1000 saturation, calibrate with the user, and produce a refactoring report plus one refined candidate per candidate input.

`ALTRO` remains free input, not another mode. Current mode choices are derived from the runtime, not copied into host prompts.

## C&C semantics

A `canonical_material` is accepted as an immutable transformation reference for the session. That designation does not make it a verified legal authority. A `candidate_material` may be changed only on evidenced gaps and must retain semantic and required-relation recall of 1.0. `READY_FOR_PEER_REVIEW` means ready to be submitted to peer review; it does not claim peer review occurred.

## Editorial and epistemic core

All modes use `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` and the humanistic artifact projection `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`. Juriscribe keeps claims, sources, inference structure, transformation provenance and review evidence distinct. No fabricated authority, no silent mode changes, no hidden artifact suppression.

Historical specifications such as `FINAL_DELIVERY_V9_2` and `FINAL_DELIVERY_V9_4` remain compatibility/audit references; v0.11 adds the C&C overlay without weakening their delivery invariants.

## Artifacts and delivery

Common user-facing roles include evidence dossier, source register, inference register, transformation ledger and `session-dashboard.html`. Narrative/report documents are real `DOCX` with OOXML/readback verification. C&C adds `refactoring_report` and one `refined_candidate` DOCX per candidate source. `session.integrity.json` is internal.

The dashboard is a persistent inference-oriented workbench and does not replace DOCX delivery. At completion, attendi gli artefatti finali in the session chat tail; release is atomic and partial compliant delivery is forbidden.

## Host behavior

After bootstrap the conversation is a control surface. **NON narrare** mining, research, reticulum construction, review, simulations, saturation, compression, provenance or internal gates. Continue autonomously until a materially blocking human decision is necessary. Keep ordinary post-bootstrap chat to 1–3 lines.

## Validation

```bash
python -m unittest discover -s tests -v
python -m compileall -q juriscribe scripts tests
python scripts/check_contract.py
```

The repository also preserves its historical regression, saturation, Safari/browser delivery and external-evaluation boundaries.

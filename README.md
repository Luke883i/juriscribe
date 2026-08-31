# Juriscribe

> **Experimental open-source research software — human validation required.** Juriscribe uses AI-assisted workflows and can produce substantive errors, omissions, hallucinations, stale or incorrect authorities, citation defects and faulty inferences. Do not treat a runtime `PASS`, receipt, proof, readiness label or completed workflow as a certification of legal/factual truth. Every material artifact must be reviewed and validated by a competent human before consequential reliance; the final decision to use an artifact and responsibility for that artifact remain human. See [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md), [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md), and [`LICENSE`](LICENSE).

Juriscribe is an autonomous, repository-governed runtime for auditable legal/scientific/editorial work. The canonical entrypoint is `python -m juriscribe`; the repository is also packageable through `pyproject.toml` and exposes the `juriscribe` console script. An optional local GPT may act as a host adapter, but it is not a second Juriscribe implementation.

## Project status and licensing

Juriscribe is an experimental research project under active development. The repository work is licensed under **Apache License 2.0**. The open-source license and the project's responsible-use model are intentionally separate: `RESPONSIBLE_USE.md` states the human-validation and reliance boundary without adding a field-of-use restriction to Apache-2.0. Juriscribe is tooling, not professional advice, a legal authority, peer review, or certification. Host/model providers may impose separate terms and data-handling rules, especially for confidential or privileged material.

## Bootstrap

Discovery is non-authorizing. Read the pre-admission surface, present the current terms, and wait for exact human `I ACCEPT`. After acceptance, `PROBE JURISCRIBE` and `INITIALIZE JURISCRIBE` remain distinct transitions; the runtime may use `bootstrap-after-acceptance` to execute them in one host turn while keeping separate receipts. Mode selection remains explicit.

For source-transport hosts, `ADMISSION.json` declares a pinned minimal bootstrap import closure. When `SESSION_CONTEXT=AVAILABLE`, the host may materialize only that closure, complete admission/probe/initialize, render mode choices, and defer the rest of the pinned runtime until substantive work. This is a transport optimization only: revision binding, contract binding, single-use receipts and sealed capabilities are unchanged.

### Initialize from a GPT-like chat

A cooperative GPT-like host may treat the following as equivalent UX intents:

```text
Initialize Juriscribe https://github.com/Luke883i/juriscribe
```

or, when the canonical repository is already configured by the host adapter:

```text
Initialize Juriscribe
```

Italian aliases such as `Inizializza Juriscribe` and `Avvia Juriscribe` are host-level UX aliases only; they never bypass the exact human `I ACCEPT`, real probe receipts or runtime initialize transition.

A GitHub connector is **not a Juriscribe dependency**. Public byte-exact repository access may be used when the host can genuinely execute the pinned runtime source. Repository readability alone is not execution capability: an insufficient host must expose a real blocker rather than simulate Juriscribe.

Current host reachability is capability-derived and distinguishes `DISCOVERY_READY`, `BOOTSTRAP_READY`, `WORK_READY`, `MATERIALIZATION_READY`, `DELIVERY_READY` and `RECOVERY_READY`. Provider, browser and OS names are diagnostic only; at equal observed capabilities they do not change the runtime decision. A memory-only chat can therefore be validly `WORK_READY` without being allowed to promise DOCX materialization or durable recovery.

See [`docs/LOCAL_GPT_HOST_ADAPTER.md`](docs/LOCAL_GPT_HOST_ADAPTER.md) for the minimal host adapter and [`docs/PHYSICAL_CONVERGENCE_V11.md`](docs/PHYSICAL_CONVERGENCE_V11.md) for the v1.1 convergence contract and mutation evidence.

## Canonical modes

- `CONTINUATION` — continue prior written material.
- `GREENFIELD` — create a new legal text from a concept or mandate.
- `REVIEW` — scientific/content/editorial review; supports `REPORT_ONLY` and `REPORT_AND_REVISED_TEXT`.
- `COMPRESSION & CONSOLIDATION` — ingest immutable canonical references plus refinable candidates, build a lossless joint reticulum, search for a minimal surgical refactoring, exercise mutation/stress classes, saturate search, calibrate with the user, derive structural semantic-preservation proof from the refined text, and produce a refactoring report plus one refined candidate per candidate input.

`ALTRO` remains free input, not another mode. Current mode choices are derived from the runtime, not copied into host prompts. The historical serialized spelling with an underscore is accepted only as a compatibility input and normalizes to `COMPRESSION & CONSOLIDATION`.

## Proof-carrying semantics

Current C&C seals no longer accept caller-supplied `semantic_recall=1.0` / `relation_recall=1.0` as proof. The runtime recomputes a structural preservation proof bound to the current candidate source, source inventory, refactoring plan, reticulum, canonical inventory set, refined text digest and explicit refined semantic projection. Material unit IDs and required relations must be preserved; every refined output object must have a text-bound semantic witness; unsupported new material units/relations fail closed.

This is deliberately a **structural semantic-preservation claim**, not an assertion that Juriscribe independently proved legal truth, substantive equivalence or entailment. Scientific/editorial review, source verification and human professional judgment remain separate gates.

## Stress evidence

C&C retains the minimum 10,000,000 mutation-instance volume, but the instance count is explicitly a soak-volume measure rather than a claim of 10,000,000 unique semantic scenarios. Current receipts expose executed equivalence classes, class counts, mismatch status and a digest. Mutation classes and proof mutations are tested separately so repeated volume cannot masquerade as semantic diversity.

## C&C semantics

A `canonical_material` is accepted as an immutable transformation reference for the session. That designation does not make it a verified legal authority. A `candidate_material` may be changed only on evidenced gaps and must retain structural material-unit and required-relation recall of 1.0 under the runtime-derived proof. `READY_FOR_PEER_REVIEW` means ready to be submitted to peer review; it does not claim peer review occurred.

## Editorial and epistemic core

All modes use `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` and the humanistic artifact projection `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`. Juriscribe keeps claims, sources, inference structure, transformation provenance and review evidence distinct. No fabricated authority, no silent mode changes, no hidden artifact suppression.

Historical specifications such as `FINAL_DELIVERY_V9_2` and `FINAL_DELIVERY_V9_4` remain compatibility/audit references. `MANIFEST.json.active_surface` identifies the small current surface; hosts should not traverse historical audit material during ordinary bootstrap or active work.

## Artifacts and delivery

Common user-facing roles include evidence dossier, source register, inference register, transformation ledger and `session-dashboard.html`. Narrative/report documents are real `DOCX` with OOXML/readback verification. C&C adds `refactoring_report` and one `refined_candidate` DOCX per candidate source. `session.integrity.json` is internal.

The dashboard is a persistent inference-oriented workbench and does not replace DOCX delivery. At completion, attendi gli artefatti finali in the session chat tail; release is atomic and partial compliant delivery is forbidden.

Snapshot/recovery is a cross-mode session control, not a fifth mode. `recovery-bundle` creates a verified local ZIP snapshot and recovery resume requires a fresh host probe; a memory-only session must not claim durable recovery.

## Host behavior

After bootstrap the conversation is a control surface. **NON narrare** mining, research, reticulum construction, review, simulations, saturation, compression, provenance or internal gates. Continue autonomously until a materially blocking human decision is necessary. Keep ordinary post-bootstrap chat to 1–3 lines.

Autonomy is workflow autonomy, not authority to waive human validation. A host must not present an AI-generated artifact as independently verified, professionally certified, or safe for consequential reliance merely because Juriscribe reached a runtime gate.

## Packaging

The runtime remains stdlib-only. `pyproject.toml` packages the Python runtime and an immutable copy of the current access contract as package data. Source checkout uses the root contract; installed execution falls back to the bundled byte-equivalent contract resource. CI verifies parity.

## Validation

```bash
python -m unittest discover -s tests -v
python -m compileall -q juriscribe scripts tests
python scripts/check_contract.py
python scripts/check_physical_convergence_v11.py
python -m unittest tests.test_physical_convergence_v11 -v
python -m unittest tests.test_runtime_semantics_v12 -v
python scripts/simulate_runtime_semantics_v12.py --cases 100000
```

The dedicated v1.1 workflow additionally executes 1,000,000 capability/lifecycle mutations split across edge, typical and degraded/stress campaigns. These are executable runtime-classifier validations, not claims of one million physical AI providers, browsers, operating systems, legal matters or LLM sessions.

The repository also preserves its historical regression, saturation, Safari/browser delivery and external-evaluation boundaries.

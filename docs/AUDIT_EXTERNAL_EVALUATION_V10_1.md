# Audit v0.10.1 — external evaluation boundary and fine-tuning readiness

## Finding

The v0.10 runtime has strong regression, mutation, saturation and artifact-governance coverage, but a substantial part of that evidence is produced by code that shares Juriscribe's own data model, builders or validators. This creates oracle-correlation risk: a wrong assumption can be present in both the implementation and the machinery that declares the implementation correct.

The existing v0.9.9 “fine-tuning” explicitly means runtime hardening on 100 real-text sessions, not statistical model training. This patch preserves that contract and introduces only the smallest independent boundary needed to move the product toward future statistical fine-tuning.

## Minimal convergent pattern

The change is a sidecar, not a runtime feature.

1. No file under `juriscribe/` changes.
2. Admission, modes, pipeline, session state, dashboard, artifact materialization and delivery remain unchanged.
3. No historical validation receipt changes.
4. The GitHub Actions workflow remains unchanged; the existing unittest discovery automatically exercises the new boundary on Python 3.10 and 3.12 before all historical saturation jobs.
5. `evaluation/reference_oracle.py` is forbidden from importing `juriscribe` and validates only evaluation-data governance.
6. `train`, `eval` and `holdout` are separate. Reserved cases can never be exported by the training-seed path.
7. A training example is eligible only when its ideal output comes from an independent human/external label, has at least two reviewers, reaches AGREED/ADJUDICATED status, and is not runtime-generated.
8. A model-agnostic JSONL seed is materializable without binding the repository to a model vendor or training API.

## Why this reduces auto-correlation

The runtime can no longer certify that a label is suitable for training merely because its own validator accepted the session. The new boundary treats runtime-generated gold as contamination and fails closed. The evaluator is executable code with an import firewall, not a prose convention.

This is intentionally weaker than an independent legal oracle: the receipt states that it proves mechanical independence and train/eval contamination controls, not substantive legal correctness. Human double-blind gold, an N-version legal validator, code mutation score and temporal holdouts remain future evaluation layers rather than claims made by this PR.

## Metamorphic property

The seed suite includes an order-invariance relation: reordering cases may change the dataset digest but cannot change validity, counts or training eligibility. Negative mutations also prove that runtime-generated gold and single-reviewer gold become ineligible.

## Fine-tuning trajectory

The product can now evolve in a non-self-distilling sequence:

`runtime session/output -> external projection -> independent annotation/adjudication -> split lock -> training seed export -> model-specific adapter -> training -> reserved eval/holdout assessment`

The key direction is that training consumes independently adjudicated examples, while `eval` and `holdout` remain unavailable to the exporter. This makes future statistical fine-tuning possible without weakening the current artifact-first runtime or turning self-produced outputs into unquestioned gold.

## Non-regression criterion

The PR is acceptable only if the same head passes the existing `runtime-tests` matrix and all downstream Safari, simulation and saturation jobs. No existing threshold may be reduced to make the new boundary pass.

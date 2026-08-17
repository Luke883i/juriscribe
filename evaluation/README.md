# Juriscribe external evaluation boundary

This directory is intentionally outside `juriscribe/` and must not import runtime code.

Its role is narrow: provide a mechanically independent sidecar for evaluation-data governance and future statistical fine-tuning. It does **not** claim to determine substantive legal truth.

## Invariants

- `evaluation/*.py` must not import `juriscribe`.
- `eval` and `holdout` cases are never exported as training records.
- training records require labels from an independent human/external origin, at least two reviewers, and an adjudicated status.
- runtime-generated ideal outputs are ineligible as gold labels.
- dataset receipts disclose that the oracle proves independence/contamination controls only.

Run:

```bash
python evaluation/reference_oracle.py evaluation/cases_v101.json
python evaluation/reference_oracle.py evaluation/cases_v101.json --training-jsonl /tmp/juriscribe-training-seed.jsonl
```

The JSONL format is deliberately model-agnostic. A future model-specific adapter may convert independently adjudicated training records without changing the reserved evaluation corpus.

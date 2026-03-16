---
name: excel-regression-harness
description: This skill should be used when adding or updating Excel fixtures, regenerating JSON reference KPIs, or debugging regression mismatches between Python outputs and Excel references.
---

# Excel Regression Harness

Execute a repeatable workflow for Excel-based regression updates and mismatch triage.

## Use When

- Add a new Excel project under `tests/data/projects/`.
- Update an existing Excel fixture and need fresh reference KPIs.
- Investigate failing tests in `tests/regression/test_excel_comparison.py`.
- Confirm regression health after pipeline or formula changes.

## Required Inputs

- One or more `.xlsx` files in `tests/data/projects/`.
- Matching reference file expectation in `tests/data/references/`.

## Workflow

1. Validate fixture layout using `references/fixture-layout.md`.
2. Extract or refresh references:
   - `python scripts/extract_excel_kpis.py tests/data/projects/*.xlsx`
3. Run regression suite:
   - `pytest tests/regression/ -v`
4. If failures occur, isolate layer:
   - Re-run `test_physics_layer` first.
   - Re-run `test_financial_kpis` next.
5. Apply tolerance interpretation from `references/tolerances.md`.
6. If extracted values are `None`, apply cached-formula recovery from `references/common-failures.md`.

## Output Contract

- Report list of projects processed.
- Report created/updated reference files.
- Report pass/fail status for regression tests.
- For failures, report KPI key, actual, expected, diff mode, and tolerance tier.

## Constraints

- Keep KPI key names aligned with `scripts/extract_excel_kpis.py` and regression tests.
- Do not silently change tolerance tiers.
- Prefer deterministic script/test commands over ad hoc workbook edits.

## References

- `references/fixture-layout.md`
- `references/tolerances.md`
- `references/common-failures.md`

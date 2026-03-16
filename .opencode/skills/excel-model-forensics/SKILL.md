---
name: excel-model-forensics
description: This skill should be used when reverse-engineering an Excel financial model, auditing formula dependencies, or investigating anomalies such as lifecycle jumps and toggle-driven revenue drops.
---

# Excel Model Forensics

Investigate Excel model structure, formulas, dependencies, and anomalies with repeatable output artifacts.

## Use When

- Analyze a new workbook in `data/`.
- Generate architecture/anomaly reports from formulas and cached values.
- Investigate suspicious lifetime jumps or sheet-level inconsistencies.

## Workflow

1. Run high-level analyzer script for full workbook mapping.
2. Run targeted investigation scripts for known anomaly classes.
3. Correlate results with `model_architecture.md` and implementation assumptions.
4. Produce markdown findings in `docs/` with explicit formula evidence.
5. Convert findings into test candidates and validation checks where applicable.

## Primary Tools

- `scripts/analyze_excel_model.py`
- `scripts/investigate_besstoload.py`

## Output Contract

- Report workbook flow across inputs, calc, aggregation, and financial sheets.
- Report key formula references for affected metrics.
- Report root-cause hypothesis with traceable evidence.
- Report recommended implementation or validation actions.

## Constraints

- Separate observed facts from assumptions.
- Quote exact formulas/cells for critical conclusions.
- Preserve reproducibility of analysis steps.

## References

- `references/forensics-checklist.md`
- `references/anomaly-patterns.md`

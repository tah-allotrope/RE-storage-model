---
name: model-report-generator
description: This skill should be used when generating or updating self-contained HTML model reports that summarize KPIs, reference comparisons, lifetime charts, and hourly profiles.
---

# Model Report Generator

Generate stakeholder-ready, offline HTML reports from pipeline outputs.

## Use When

- Produce a report after running JSON or Excel model workflows.
- Update report sections, chart content, or print formatting.
- Recreate Emivest-style comparison output for a new project.

## Workflow

1. Execute pipeline and collect scalar KPIs plus hourly/lifetime dataframes.
2. Load optional reference KPI JSON for comparison.
3. Build report using `src/re_storage/reporting/html_report.py` functions.
4. Ensure output is self-contained with inline CSS and inline chart images.
5. Write report to `reports/` and validate browser open/print behavior.

## Required Sections

- Project summary card.
- KPI dashboard.
- Python vs reference comparison table (if reference provided).
- Lifetime projection charts.
- Sample hourly profile.

## Output Contract

- HTML file renders from local filesystem without network access.
- Comparison table uses tolerance-aware pass/fail labels.
- Report remains readable in both screen and print modes.

## Constraints

- Avoid external CSS/JS/font dependencies.
- Keep chart generation compatible with headless execution.
- Keep KPI names consistent with pipeline output keys.

## References

- `references/report-checklist.md`
- `references/section-contracts.md`

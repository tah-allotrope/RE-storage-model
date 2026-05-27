# Sprint 3: Go/No-Go Assessment + Dispatch Charts + Client Branding

## Objective
Complete the client-facing DPPA assessment workbook with three polish layers:
1. Automated go/no-go verdicts that interpret KPIs against hurdle rates
2. Dispatch profile charts embedded in assessment sheets
3. Allotrope-branded formatting across all sheets

## Grill Me Answers
- **Q-001 (Logo):** Proceed without logo. Use text-only header. Optional `--logo` flag deferred to future sprint.

## Progress

### PHASE-01 — Go/No-Go Assessment Module
- [ ] TASK-01-01: Create `src/re_storage/reporting/assessment.py`
- [ ] TASK-01-02: Implement `assess_project()` logic
- [ ] TASK-01-03: Write `tests/unit/test_assessment.py`
- [ ] TASK-01-04: Run tests, report skill, git commit/push

### PHASE-02 — Dispatch Chart Generator for Excel
- [ ] TASK-02-01: Create `src/re_storage/reporting/charts.py`
- [ ] TASK-02-02: Implement `generate_average_day_dispatch()`
- [ ] TASK-02-03: Implement `generate_dscr_line_chart()`
- [ ] TASK-02-04: Implement `generate_monthly_generation_bar()`
- [ ] TASK-02-05: Write `tests/unit/test_reporting_charts.py`
- [ ] TASK-02-06: Run tests, report skill, git commit/push

### PHASE-03 — Branding + Integration
- [x] TASK-03-01: Create `src/re_storage/reporting/styles.py`
- [x] TASK-03-02: Refactor `excel_writer.py` to use styles
- [x] TASK-03-03: Update `write_cover_sheet()` with verdict
- [x] TASK-03-04: Update `write_assessment_sheet()` with chart embedding
- [x] TASK-03-05: Check/add Pillow dependency (already installed v12.1.0)
- [x] TASK-03-06: Update `scripts/generate_dppa_assessment.py`
- [x] TASK-03-07: Update `tests/unit/test_excel_writer.py`
- [x] TASK-03-08: Run full test suite — 359 passed, 3 pre-existing failures, 4 skipped
- [ ] TASK-03-09: Manual verification, report skill, git commit/push

## Notes
- Pillow is already installed (v12.1.0), no need to add to pyproject.toml
- Hourly df columns: solar_gen_kw, load_kw, soc_kwh, discharged_kw, pv_charged_kw, grid_load_after_re_kw
- Annual df columns include: dscr, dppa_revenue_usd, grid_savings_usd, demand_charge_savings_usd, year
- Brand colors from plan: primary green #2E7D32, accent dark #1B5E20, header bg #E8F5E9, text dark #212121, text light #757575
- Conditional formatting: PASS/GO = #C8E6C9 (green), CAUTION = #FFE0B2 (amber), FAIL/NO-GO = #FFCDD2 (red)

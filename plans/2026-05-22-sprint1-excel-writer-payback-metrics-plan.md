---
title: "Sprint 1: Excel Writer Foundation + Payback Metrics"
date: "2026-05-22"
status: "draft"
request: "GAP-01 (Excel output writer) + GAP-06 (payback/cash-on-cash metrics) from DPPA assessment gap analysis"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-05-22-dppa-assessment-excel-gap-analysis.md"
---

# Plan: Sprint 1 — Excel Writer Foundation + Payback Metrics

## Objective

Add the ability to generate formatted `.xlsx` workbooks from pipeline outputs, and implement missing payback/cash-on-cash financial metrics. This is the foundation for all subsequent DPPA assessment deliverables — nothing ships to the client without an Excel writer.

## Context Snapshot
- **Current state:** All pipeline outputs are Python dicts/DataFrames serialized to JSON, HTML, or PPTX. The pipeline already surfaces `_annual_df`, `_hourly_df`, and `_lifetime_df` in results dicts. `openpyxl>=3.1.0` is already in `pyproject.toml` dependencies. Financial metrics module has IRR/NPV/DSCR but no payback or cash-on-cash yield.
- **Desired state:** A `src/re_storage/reporting/excel_writer.py` module that can write multi-sheet formatted workbooks. A `scripts/generate_dppa_assessment.py` CLI that runs the pipeline and produces a client-ready `.xlsx`. Three new metric functions in `financial/metrics.py`.
- **Key repo surfaces:**
  - `src/re_storage/reporting/html_report.py` — existing report module with KPI formatting patterns
  - `src/re_storage/reporting/__init__.py` — package exports
  - `src/re_storage/financial/metrics.py` — IRR/NPV/DSCR implementations
  - `src/re_storage/financial/waterfall.py` — annual waterfall DataFrame schema (12 columns: year through capex_usd)
  - `src/re_storage/pipeline.py` — `_run_financial()` returns `_annual_df` at line 911
  - `src/re_storage/scenarios/runner.py` — `run_all_scenarios()` returns `{option_id: kpi_dict}`
  - `src/re_storage/scenarios/sensitivity.py` — `run_sensitivity()` / `run_sensitivity_for_values()`
  - `results/baseline/emivest_tou2024.json` — reference KPI output schema
- **Out of scope:** Onsite vs offsite logic (Sprint 2), go/no-go assessment logic (Sprint 3), dispatch chart embedding (Sprint 3), client branding polish (Sprint 3), two-component tariff (Sprint 4).

## Research Inputs
- `reports/2026-05-22-dppa-assessment-excel-gap-analysis.md` — Defines the 5 sheet types the writer must support (Cover, Assessment, Comparison, Sensitivity, Assumptions), identifies `openpyxl` as already in deps, and confirms that `_annual_df`/`_hourly_df`/`_lifetime_df` are surfaced by the pipeline.

## Assumptions and Constraints
- **ASM-001:** `openpyxl>=3.1.0` is already installed — no dependency changes needed. Confirmed in `pyproject.toml:29`.
- **ASM-002:** The Excel writer receives fully computed Python dicts and DataFrames — it does not run the pipeline itself. The orchestration script (`generate_dppa_assessment.py`) handles pipeline execution.
- **ASM-003:** The `_annual_df` DataFrame returned by `_run_financial()` contains columns: `year`, `total_revenue_usd`, `total_opex_usd`, `ebitda_usd`, `interest_usd`, `principal_usd`, `total_debt_service_usd`, `cfads_usd`, `taxes_usd`, `mra_contribution_usd`, `free_cash_flow_to_equity_usd`, `capex_usd`, `dppa_revenue_usd`, `grid_savings_usd`, `demand_charge_savings_usd`, `dscr`.
- **CON-001:** No VBA macros or Excel formulas in the output — all values are static. This is intentional for assessment deliverables (client reviews numbers, not a live model).
- **DEC-001:** Use `openpyxl` exclusively for Excel writing. No `xlsxwriter` or other library.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Payback & cash-on-cash metrics | None | 3 new functions in `financial/metrics.py`, unit tests |
| PHASE-02 | Core Excel writer module | None | `reporting/excel_writer.py` with 5 sheet-writer functions |
| PHASE-03 | CLI script + integration test | PHASE-01, PHASE-02 | `scripts/generate_dppa_assessment.py`, end-to-end test |

## Detailed Phases

### PHASE-01 — Payback & Cash-on-Cash Metrics
**Goal**
Add three financial metric functions that the assessment workbook needs but are currently missing.

**Tasks**
- [ ] TASK-01-01: Add `calculate_simple_payback(total_capex_usd: float, year1_ebitda_usd: float) -> float` to `src/re_storage/financial/metrics.py`. Returns `total_capex / year1_ebitda`. Returns `float('inf')` if EBITDA ≤ 0.
- [ ] TASK-01-02: Add `calculate_discounted_payback(cashflows: pd.Series, dates: pd.Series, discount_rate_pct: float) -> int | None` to `src/re_storage/financial/metrics.py`. Iterates year-by-year cumulative discounted cashflow; returns the first year index where cumulative turns non-negative. Returns `None` if never recovers.
- [ ] TASK-01-03: Add `calculate_cash_on_cash_yield(year1_fcfe_usd: float, equity_invested_usd: float) -> float` to `src/re_storage/financial/metrics.py`. Returns `year1_fcfe / equity_invested`. Returns 0.0 if equity ≤ 0.
- [ ] TASK-01-04: Wire new metrics into `_run_financial()` in `src/re_storage/pipeline.py` — add `simple_payback_years`, `discounted_payback_year`, `cash_on_cash_yield` to the results dict.
- [ ] TASK-01-05: Write `tests/unit/test_financial_payback.py` with tests:
  - `test_simple_payback_positive_ebitda` — known CAPEX/EBITDA → expected years
  - `test_simple_payback_zero_ebitda` — returns inf
  - `test_discounted_payback_recovers` — cashflows that cross zero → correct year
  - `test_discounted_payback_never_recovers` — all-negative → None
  - `test_cash_on_cash_positive` — known FCFE/equity → expected ratio
  - `test_cash_on_cash_zero_equity` — returns 0.0
- [ ] TASK-01-06: Run `pytest tests/unit/test_financial_payback.py -v` — all pass.

**Files / Surfaces**
- `src/re_storage/financial/metrics.py` — add 3 functions after existing `calculate_dscr_series()`
- `src/re_storage/pipeline.py` — modify `_run_financial()` near line 903 to compute and store new metrics
- `tests/unit/test_financial_payback.py` — new file

**Dependencies**
- None

**Exit Criteria**
- [ ] `pytest tests/unit/test_financial_payback.py -v` → 6+ tests pass
- [ ] `pytest tests/unit/ -q` → no regressions (existing tests still pass)
- [ ] New metrics appear in pipeline output dict when running `run_full_model()` or `run_model_from_json()`

**Phase Risks**
- **RISK-01-01:** Discounted payback with non-standard cashflow patterns (multiple sign changes) could return an early false positive. Mitigation: use cumulative sum, not sign-change detection. Document that this is the first crossing point.

---

### PHASE-02 — Core Excel Writer Module
**Goal**
Create `src/re_storage/reporting/excel_writer.py` with functions to write each of the 5 assessment sheet types into an `openpyxl` workbook.

**Tasks**
- [ ] TASK-02-01: Create `src/re_storage/reporting/excel_writer.py` with these public functions:
  ```python
  def create_workbook() -> openpyxl.Workbook
  def write_cover_sheet(wb, project_name, project_metadata, kpis) -> None
  def write_assessment_sheet(wb, sheet_name, kpis, annual_df) -> None
  def write_comparison_sheet(wb, scenario_results) -> None
  def write_sensitivity_sheet(wb, sensitivity_results) -> None
  def write_assumptions_sheet(wb, assumptions_dict) -> None
  def save_workbook(wb, output_path) -> Path
  ```
- [ ] TASK-02-02: Implement `create_workbook()` — creates a new `Workbook`, removes the default sheet, sets default font to Calibri 10pt.
- [ ] TASK-02-03: Implement `write_cover_sheet()`:
  - Row 1-2: Project name (merged, bold, 16pt)
  - Row 3: Date and confidentiality notice
  - Row 5+: KPI summary table (2 columns: Metric, Value) with number formatting:
    - IRR fields: percentage with 2 decimals
    - NPV: USD currency with commas
    - DSCR: ratio with 2 decimals
    - Payback: years with 1 decimal
  - Column widths auto-sized
- [ ] TASK-02-04: Implement `write_assessment_sheet()`:
  - Section 1 (rows 1-12): KPI cards table — same as cover but with all available metrics
  - Section 2 (row 14+): Annual proforma table from `_annual_df` DataFrame
    - Header row: bold, bottom border
    - Data rows: number-formatted (USD currency for monetary, ratio for DSCR)
    - Totals row: bold, top border, SUM-style values
    - Alternating row fill (light gray / white) for readability
- [ ] TASK-02-05: Implement `write_comparison_sheet()`:
  - Takes `scenario_results: dict[int, dict]` from `run_all_scenarios()`
  - Header row: "Metric" | "Option 1: Bundled" | "Option 2: Separate" | "Option 3: DPPA CfD" | "Option 4: Fixed EVN"
  - Rows: one per KPI (project_irr, equity_irr, npv_usd, dscr_min, year1_dppa_revenue_usd, year1_grid_savings_usd, year1_opex_usd, year1_ebitda_usd, simple_payback_years, debt_amount_usd)
  - Conditional formatting: highlight the best value per row in green fill
- [ ] TASK-02-06: Implement `write_sensitivity_sheet()`:
  - Takes results from `run_sensitivity_for_values()` — dict mapping `{test_value: kpi_dict}`
  - One section per sensitivity variable (strike_price, interest_rate, pv_capex, bess_capex, fx_rate)
  - Each section: header row with variable name, then data table of test_value → IRR / NPV / DSCR
  - Number formatting matching assessment sheet conventions
- [ ] TASK-02-07: Implement `write_assumptions_sheet()`:
  - Takes a flat dict of assumption key-value pairs
  - Writes as 2-column table: Parameter | Value
  - Groups by category using section headers (System, DPPA, Financial, Dispatch)
- [ ] TASK-02-08: Add internal helper `_apply_number_format(cell, key)` that maps KPI key names to Excel number format strings:
  - `*_irr*`, `*_pct*` → `'0.00%'`
  - `*_usd*` → `'#,##0'`
  - `*dscr*` → `'0.00'`
  - `*_years*` → `'0.0'`
  - `*_mwh*`, `*_kwh*` → `'#,##0.0'`
- [ ] TASK-02-09: Update `src/re_storage/reporting/__init__.py` to export the new functions.
- [ ] TASK-02-10: Write `tests/unit/test_excel_writer.py` with tests:
  - `test_create_workbook_has_no_default_sheet` — verify empty workbook
  - `test_write_cover_sheet_has_project_name` — verify cell A1 contains project name
  - `test_write_assessment_sheet_has_kpi_and_proforma` — verify both sections present
  - `test_write_comparison_sheet_has_all_options` — verify 4 option columns
  - `test_write_sensitivity_sheet_writes_data_tables` — verify sections present
  - `test_write_assumptions_sheet_has_parameters` — verify key-value rows
  - `test_save_workbook_creates_file` — verify file exists on disk (tmp path)
  - `test_number_format_irr` — verify percentage format applied
  - `test_number_format_usd` — verify currency format applied
  - All tests use small synthetic data (no pipeline run needed)

**Files / Surfaces**
- `src/re_storage/reporting/excel_writer.py` — new file, ~300–400 lines
- `src/re_storage/reporting/__init__.py` — add exports
- `tests/unit/test_excel_writer.py` — new file

**Dependencies**
- None (can be developed in parallel with PHASE-01)

**Exit Criteria**
- [ ] `pytest tests/unit/test_excel_writer.py -v` → 9+ tests pass
- [ ] `ruff check src/re_storage/reporting/excel_writer.py` → clean
- [ ] Manual: calling `write_assessment_sheet()` with a sample `_annual_df` produces a readable `.xlsx` when opened in Excel

**Phase Risks**
- **RISK-02-01:** `openpyxl` conditional formatting API is verbose and version-sensitive. Mitigation: use `openpyxl.formatting.rule.CellIsRule` with `PatternFill`; test against openpyxl 3.1+.
- **RISK-02-02:** Column auto-sizing is not natively supported in openpyxl. Mitigation: implement a helper that estimates width from max string length per column, capped at 30 characters.

---

### PHASE-03 — CLI Script + Integration Test
**Goal**
Create the orchestration script that ties the pipeline to the Excel writer, producing a complete assessment workbook from a single command.

**Tasks**
- [ ] TASK-03-01: Create `scripts/generate_dppa_assessment.py` with:
  - Argument parser: `--input` (path to Excel or JSON project dir), `--output` (output .xlsx path, default `reports/dppa_assessment_{date}.xlsx`), `--project-name` (string), `--ppa-options` (comma-separated list, default "1,2,3,4")
  - Main flow:
    1. Detect input type (`.xlsx` → Excel path, directory → JSON path)
    2. Run pipeline via `run_full_model()` or `run_model_from_json()` for default PPA option
    3. Run `run_all_scenarios()` for comparison sheet
    4. Run `run_sensitivity_for_values()` for 3–5 key variables (strike_price, interest_rate, initial_capex_usd)
    5. Call Excel writer functions to build workbook
    6. Save to output path
    7. Print output path and summary KPIs to stdout
- [ ] TASK-03-02: Add `if __name__ == "__main__":` block with argparse.
- [ ] TASK-03-03: Write `tests/integration/test_dppa_assessment_script.py`:
  - `test_generate_assessment_from_json` — runs the script with the Emivest JSON fixture at `tests/data/projects/emivest/`, verifies output `.xlsx` exists, has 5+ sheets, and the Cover sheet contains non-empty KPI values
  - Uses `subprocess.run()` or direct function import
  - Cleans up the generated file in teardown
- [ ] TASK-03-04: Run `pytest tests/integration/test_dppa_assessment_script.py -v` — passes.
- [ ] TASK-03-05: Run `python scripts/generate_dppa_assessment.py --input tests/data/projects/emivest/ --project-name "Test DPPA Assessment"` and manually verify the output workbook opens correctly in Excel.

**Files / Surfaces**
- `scripts/generate_dppa_assessment.py` — new file, ~150 lines
- `tests/integration/test_dppa_assessment_script.py` — new file

**Dependencies**
- PHASE-01 (payback metrics must be in pipeline output)
- PHASE-02 (Excel writer must be functional)

**Exit Criteria**
- [ ] `python scripts/generate_dppa_assessment.py --input tests/data/projects/emivest/ --project-name "Test"` → produces a `.xlsx` file with 5 sheets
- [ ] Output workbook opens without errors in Excel/LibreOffice
- [ ] Cover sheet shows non-NaN values for project_irr, equity_irr, npv_usd, dscr_min, simple_payback_years
- [ ] Comparison sheet shows 4 PPA option columns with numeric values
- [ ] `pytest tests/integration/test_dppa_assessment_script.py -v` → pass

**Phase Risks**
- **RISK-03-01:** Full pipeline run for 4 scenarios + sensitivity takes 30-60 seconds — integration test may be slow. Mitigation: mark test with `@pytest.mark.slow` and exclude from default `pytest` runs via `-m "not slow"`.
- **RISK-03-02:** Emivest JSON fixture path may differ across environments. Mitigation: use `Path(__file__).parent / "../../tests/data/projects/emivest"` relative resolution.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_financial_payback.py -v` — payback metric unit tests
- **TEST-002:** `pytest tests/unit/test_excel_writer.py -v` — Excel writer unit tests
- **TEST-003:** `pytest tests/integration/test_dppa_assessment_script.py -v` — end-to-end integration
- **TEST-004:** `pytest tests/unit/ -q` — full unit suite, no regressions
- **MANUAL-001:** Open the generated `.xlsx` in Excel or LibreOffice Calc and verify: (a) all 5 sheets are present and navigable, (b) number formatting is correct (percentages, currencies, ratios), (c) the annual proforma table has 25 data rows + totals, (d) the comparison table has 4 option columns.
- **OBS-001:** `ruff check src/re_storage/reporting/excel_writer.py src/re_storage/financial/metrics.py` — lint clean

## Risks and Alternatives
- **RISK-001:** If the Emivest JSON pipeline returns NaN for equity_irr (known issue from `activeContext.md` ISSUE-4), the assessment workbook will show NaN in some cells. Mitigation: the Excel writer should format NaN as "N/A" with a note, not crash.
- **ALT-001:** Could use `xlsxwriter` instead of `openpyxl` for better chart support. Not chosen because `openpyxl` is already a project dependency and handles both read and write, reducing the dependency surface.
- **ALT-002:** Could generate the workbook entirely from the web frontend (client-side JS). Not chosen because: (a) the web app is not deployed yet, (b) Python-side generation gives full control over formatting, and (c) the client expects a standalone file, not a web app.

## Grill Me
1. **Q-001:** Should the sensitivity sheet include all 9 variables from `scenarios/sensitivity.py`, or just the top 3-5 most impactful ones?
   - **Recommended default:** Top 5 (strike_price, interest_rate, initial_capex_usd, exchange_rate, bundled_discount_pct) to keep the sheet readable.
   - **Why this matters:** Running all 9 variables × 7 test points = 63 pipeline runs = ~5-10 minutes of computation.
   - **If answered differently:** If all 9, the script will take longer and the sheet will need sub-sections or a second sheet.

2. **Q-002:** What currency should be the primary display — USD or VND — and should the workbook include both?
   - **Recommended default:** USD primary with a VND conversion column using a fixed exchange rate from assumptions.
   - **Why this matters:** Number formatting, column headers, and KPI labels all depend on this choice.
   - **If answered differently:** If VND-primary, all format strings change and the KPI names need VND suffixes.

## Suggested Next Step
Answer the Grill Me questions, then begin PHASE-01 and PHASE-02 in parallel (they are independent). PHASE-03 follows after both complete.

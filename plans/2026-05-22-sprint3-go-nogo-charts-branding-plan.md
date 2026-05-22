---
title: "Sprint 3: Go/No-Go Assessment Logic + Dispatch Charts + Client Branding"
date: "2026-05-22"
status: "draft"
request: "GAP-03 (go/no-go logic) + GAP-05 (dispatch charts) + GAP-08 (branding) from DPPA assessment gap analysis"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-05-22-dppa-assessment-excel-gap-analysis.md"
---

# Plan: Sprint 3 — Go/No-Go Assessment + Dispatch Charts + Client Branding

## Objective

Complete the client-facing DPPA assessment workbook with three polish layers: (1) automated go/no-go verdicts that interpret KPIs against hurdle rates, (2) dispatch profile charts embedded in assessment sheets, and (3) Allotrope-branded formatting across all sheets. After this sprint, the workbook is client-ready.

## Context Snapshot
- **Current state:** Sprint 1 provides the Excel writer and payback metrics. Sprint 2 provides onsite/offsite topology and detailed proforma export. The workbook has all the data but lacks: interpretive assessment logic, visual dispatch charts, and professional formatting.
- **Desired state:** The Cover sheet shows a green/amber/red go/no-go verdict. Each assessment sheet includes embedded dispatch profile charts (average day). All sheets use Allotrope-branded formatting (Calibri fonts, green accent, confidentiality footer, conditional formatting).
- **Key repo surfaces:**
  - `src/re_storage/reporting/excel_writer.py` — Sprint 1+2 output
  - `src/re_storage/financial/metrics.py` — all KPIs including Sprint 1 payback metrics
  - `src/re_storage/reporting/html_report.py` — `_to_base64_png()` for matplotlib chart generation
  - `scripts/run_vietnam_tou2026_analysis.py` — has matplotlib dispatch chart generation code
  - `results/make_presentation_v2.js` — Allotrope brand spec (colors, fonts)
  - `scripts/generate_dppa_assessment.py` — Sprint 2 output, the orchestration script
- **Out of scope:** Two-component tariff (Sprint 4), wind generation, factory NPV, viability frontier heatmap.

## Research Inputs
- `reports/2026-05-22-dppa-assessment-excel-gap-analysis.md` — Documents the go/no-go threshold structure (equity IRR vs hurdle, DSCR vs covenant, NPV sign, payback vs project life). Notes that the PPTX generator at `results/make_presentation_v2.js` contains Allotrope color codes.

## Assumptions and Constraints
- **ASM-001:** Go/no-go thresholds are configurable, not hardcoded. Defaults: equity IRR hurdle = 12%, DSCR covenant = 1.2x, max payback = 15 years.
- **ASM-002:** Dispatch charts are embedded as PNG images (via `openpyxl.drawing.image.Image`), not native Excel charts. This gives full matplotlib control over stacked area/line formatting.
- **ASM-003:** Allotrope brand colors from `results/make_presentation_v2.js`: primary green `#2E7D32`, accent dark `#1B5E20`, header background `#E8F5E9`, text dark `#212121`, text light `#757575`. Fonts: Calibri Light for headers, Calibri for body.
- **CON-001:** `Pillow` (`PIL`) is required by `openpyxl` for image insertion. It may need to be added to dependencies.
- **DEC-001:** Conditional formatting uses cell fill colors: green `#C8E6C9` for PASS/GO, amber `#FFE0B2` for CAUTION, red `#FFCDD2` for FAIL/NO-GO.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Go/no-go assessment module | None | `reporting/assessment.py`, unit tests |
| PHASE-02 | Dispatch chart generator for Excel | None | `reporting/charts.py`, unit tests |
| PHASE-03 | Allotrope branding + wire everything into workbook | PHASE-01, PHASE-02, Sprint 2 | Updated `excel_writer.py`, updated script |

## Detailed Phases

### PHASE-01 — Go/No-Go Assessment Module
**Goal**
Create a standalone assessment logic module that interprets KPIs into structured verdicts.

**Tasks**
- [ ] TASK-01-01: Create `src/re_storage/reporting/assessment.py` with:
  ```python
  @dataclass
  class AssessmentThresholds:
      equity_irr_hurdle: float = 0.12
      dscr_covenant: float = 1.2
      max_payback_years: float = 15.0
      npv_floor_usd: float = 0.0

  @dataclass
  class AssessmentVerdict:
      overall: str  # "GO" | "CAUTION" | "NO-GO"
      equity_irr_status: str  # "PASS" | "MARGINAL" | "FAIL"
      dscr_status: str
      npv_status: str
      payback_status: str
      details: list[str]  # Human-readable explanation lines

  def assess_project(kpis: dict, thresholds: AssessmentThresholds | None = None) -> AssessmentVerdict
  ```
- [ ] TASK-01-02: Implement `assess_project()` logic:
  - equity_irr ≥ hurdle → PASS; equity_irr ≥ hurdle × 0.8 → MARGINAL; else → FAIL
  - dscr_min ≥ covenant → PASS; dscr_min ≥ covenant × 0.9 → MARGINAL; else → FAIL
  - npv_usd ≥ 0 → PASS; npv_usd ≥ -capex × 0.05 → MARGINAL; else → FAIL
  - payback ≤ max_payback → PASS; payback ≤ max_payback × 1.2 → MARGINAL; else → FAIL
  - Overall: all PASS → GO; any FAIL → NO-GO; else → CAUTION
  - Handle NaN/None KPIs gracefully → treated as FAIL with explanation
- [ ] TASK-01-03: Write `tests/unit/test_assessment.py`:
  - `test_all_pass_returns_go` — strong KPIs → GO
  - `test_one_fail_returns_nogo` — one below threshold → NO-GO
  - `test_marginal_returns_caution` — one near threshold → CAUTION
  - `test_nan_irr_returns_nogo` — NaN equity_irr → NO-GO with explanation
  - `test_custom_thresholds` — override defaults
  - `test_details_explain_each_verdict` — verify human-readable strings
- [ ] TASK-01-04: Run `pytest tests/unit/test_assessment.py -v` — all pass.

**Files / Surfaces**
- `src/re_storage/reporting/assessment.py` — new file, ~100 lines
- `tests/unit/test_assessment.py` — new file

**Dependencies**
- None

**Exit Criteria**
- [ ] `pytest tests/unit/test_assessment.py -v` → 6+ tests pass
- [ ] `assess_project({"equity_irr": 0.15, "dscr_min": 1.5, "npv_usd": 1e6, "simple_payback_years": 8})` → `AssessmentVerdict(overall="GO", ...)`

**Phase Risks**
- **RISK-01-01:** Threshold sensitivity — marginal bands (80-100% of hurdle) may be too narrow or too wide for specific client expectations. Mitigation: thresholds are configurable via `AssessmentThresholds` dataclass.

---

### PHASE-02 — Dispatch Chart Generator for Excel
**Goal**
Create a chart generation module that produces matplotlib dispatch profile PNGs suitable for embedding in Excel sheets.

**Tasks**
- [ ] TASK-02-01: Create `src/re_storage/reporting/charts.py` with:
  ```python
  def generate_average_day_dispatch(hourly_df: pd.DataFrame, title: str = "Average Day Dispatch") -> Path
  def generate_monthly_generation_bar(annual_df: pd.DataFrame, title: str = "Monthly Generation") -> Path
  def generate_dscr_line_chart(annual_df: pd.DataFrame, covenant: float = 1.3, title: str = "DSCR Profile") -> Path
  ```
- [ ] TASK-02-02: Implement `generate_average_day_dispatch()`:
  - Input: `_hourly_df` from pipeline results
  - Compute average hourly profile (24 values) across the year for: solar_gen_kw, load_kw, soc_kwh, discharge_kw, charge_kw, grid_load_after_re_kw
  - Plot as a stacked area chart: solar (yellow), discharge (blue), grid (gray) meeting load (black line)
  - Add SoC as secondary y-axis (green dashed line)
  - Save to temp file, return path
  - Use `matplotlib.use("Agg")` for headless rendering
- [ ] TASK-02-03: Implement `generate_dscr_line_chart()`:
  - Input: `_annual_df` with `dscr` column
  - Plot DSCR as a line over project years
  - Add horizontal covenant line (dashed red)
  - Shade area below covenant in light red
  - Save to temp file, return path
- [ ] TASK-02-04: Implement `generate_monthly_generation_bar()`:
  - Input: `_annual_df` with revenue columns
  - Stacked bar chart: DPPA Revenue + Grid Savings + Demand Charge Savings per year
  - Save to temp file, return path
- [ ] TASK-02-05: All chart functions should:
  - Use Allotrope color palette (green `#2E7D32`, blue `#1565C0`, gray `#9E9E9E`, yellow `#F9A825`)
  - Set figure size to 8×4 inches (fits well in Excel columns A–L)
  - Use Calibri font if available, fall back to sans-serif
  - Return a `Path` to a temp PNG file
- [ ] TASK-02-06: Write `tests/unit/test_reporting_charts.py`:
  - `test_average_day_dispatch_creates_png` — verify file exists and is a valid PNG
  - `test_dscr_chart_creates_png` — verify file exists
  - `test_revenue_bar_creates_png` — verify file exists
  - Use small synthetic DataFrames (24 rows for hourly, 25 rows for annual)
- [ ] TASK-02-07: Run `pytest tests/unit/test_reporting_charts.py -v` — all pass.

**Files / Surfaces**
- `src/re_storage/reporting/charts.py` — new file, ~200 lines
- `tests/unit/test_reporting_charts.py` — new file

**Dependencies**
- None (can be developed in parallel with PHASE-01)

**Exit Criteria**
- [ ] All 3 chart functions produce valid PNG files from synthetic data
- [ ] Charts use Allotrope color palette
- [ ] `pytest tests/unit/test_reporting_charts.py -v` → 3+ tests pass

**Phase Risks**
- **RISK-02-01:** `_hourly_df` column names may vary between Excel and JSON pipeline paths. Mitigation: use the column names from the `_hourly_df` that the pipeline actually produces (check both paths in tests).
- **RISK-02-02:** Matplotlib font availability for Calibri on Linux/CI. Mitigation: fall back to `sans-serif` with a try/except on font setup.

---

### PHASE-03 — Branding + Integration
**Goal**
Apply Allotrope branding across all Excel sheets, wire go/no-go verdicts into the Cover sheet, embed charts into assessment sheets, and polish the final workbook.

**Tasks**
- [ ] TASK-03-01: Create `src/re_storage/reporting/styles.py` with Allotrope style constants:
  ```python
  BRAND_GREEN = "2E7D32"
  BRAND_GREEN_LIGHT = "E8F5E9"
  HEADER_FONT = Font(name="Calibri Light", size=12, bold=True, color="FFFFFF")
  HEADER_FILL = PatternFill("solid", fgColor=BRAND_GREEN)
  BODY_FONT = Font(name="Calibri", size=10)
  ALT_ROW_FILL = PatternFill("solid", fgColor="F5F5F5")
  PASS_FILL = PatternFill("solid", fgColor="C8E6C9")
  CAUTION_FILL = PatternFill("solid", fgColor="FFE0B2")
  FAIL_FILL = PatternFill("solid", fgColor="FFCDD2")
  THIN_BORDER = Border(bottom=Side(style="thin", color="BDBDBD"))
  ```
- [ ] TASK-03-02: Refactor `excel_writer.py` to use styles from `styles.py`:
  - Apply `HEADER_FONT` + `HEADER_FILL` to all header rows across all sheets
  - Apply `ALT_ROW_FILL` to alternating data rows
  - Apply `THIN_BORDER` to section dividers
  - Set print area and page margins on each sheet
- [ ] TASK-03-03: Update `write_cover_sheet()` in `excel_writer.py`:
  - Accept `verdict: AssessmentVerdict` parameter
  - Write verdict section after KPI table:
    - Row: "ASSESSMENT VERDICT" (merged, bold)
    - Row: Overall verdict with fill color (GO=green, CAUTION=amber, NO-GO=red)
    - Rows: Individual status lines (Equity IRR, DSCR, NPV, Payback) with per-item fill
    - Rows: Detail explanation lines from `verdict.details`
  - Add confidentiality footer at bottom: "CONFIDENTIAL — Prepared by Allotrope Ventures"
- [ ] TASK-03-04: Update `write_assessment_sheet()` in `excel_writer.py`:
  - Accept optional `charts: list[Path]` parameter
  - After the proforma table, insert each chart PNG using `openpyxl.drawing.image.Image`
  - Position charts below the data table with 2-row spacing
  - Set chart image dimensions to fit columns A–L (~800px wide)
- [ ] TASK-03-05: Check if `Pillow` is in dependencies. If not, add `Pillow>=10.0.0` to `pyproject.toml` dependencies (required by openpyxl for image insertion).
- [ ] TASK-03-06: Update `scripts/generate_dppa_assessment.py`:
  - After pipeline runs, call `assess_project()` for each topology
  - Generate dispatch, DSCR, and revenue charts for each topology
  - Pass verdicts and chart paths to the Excel writer functions
  - Clean up temp chart files after workbook is saved
- [ ] TASK-03-07: Update `tests/unit/test_excel_writer.py`:
  - `test_cover_sheet_has_verdict_section` — verify verdict rows present
  - `test_assessment_sheet_has_embedded_chart` — verify image anchor exists
  - `test_branding_header_fill` — verify header cells use green fill
- [ ] TASK-03-08: Run full test suite: `pytest tests/ -q --ignore=tests/unit/test_battery.py` — no regressions.
- [ ] TASK-03-09: Generate final workbook and manually verify in Excel:
  - Cover sheet has green/amber/red verdict
  - Assessment sheets have charts below proforma
  - All sheets have consistent header formatting
  - Print preview shows clean page breaks

**Files / Surfaces**
- `src/re_storage/reporting/styles.py` — new file, ~40 lines
- `src/re_storage/reporting/excel_writer.py` — refactor formatting, add verdict + chart support
- `src/re_storage/reporting/__init__.py` — update exports
- `scripts/generate_dppa_assessment.py` — wire verdicts and charts
- `pyproject.toml` — possibly add Pillow dependency
- `tests/unit/test_excel_writer.py` — extend

**Dependencies**
- PHASE-01 (assessment module for verdicts)
- PHASE-02 (chart generator for PNGs)
- Sprint 2 complete (dual-topology + proforma in workbook)

**Exit Criteria**
- [ ] Generated workbook has go/no-go verdict on Cover sheet with color coding
- [ ] Assessment sheets have 2-3 embedded chart images
- [ ] All sheets use Allotrope-branded header formatting
- [ ] Confidentiality footer present on Cover sheet
- [ ] `pytest tests/ -q --ignore=tests/unit/test_battery.py` → no regressions
- [ ] Manual Excel/LibreOffice verification passes

**Phase Risks**
- **RISK-03-01:** `openpyxl` image insertion requires `Pillow`. If not installed, `from openpyxl.drawing.image import Image` raises `ImportError`. Mitigation: add Pillow to deps in TASK-03-05; add a graceful fallback that skips chart embedding if Pillow is unavailable.
- **RISK-03-02:** Chart image sizing in Excel is approximate — different screen DPIs may render differently. Mitigation: set explicit pixel dimensions (800×400) and test on both Windows Excel and LibreOffice Calc.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_assessment.py -v` — go/no-go logic
- **TEST-002:** `pytest tests/unit/test_reporting_charts.py -v` — chart generation
- **TEST-003:** `pytest tests/unit/test_excel_writer.py -v` — formatting and embedding
- **TEST-004:** `pytest tests/ -q --ignore=tests/unit/test_battery.py` — full suite no regressions
- **MANUAL-001:** Open final workbook in Excel, verify verdict colors, chart presence, header formatting, print layout.
- **MANUAL-002:** Open in LibreOffice Calc to verify cross-platform compatibility.

## Risks and Alternatives
- **RISK-001:** Allotrope logo file is not in the repo. The cover sheet will have a text-only header until a logo PNG is provided. The writer should accept an optional `logo_path` parameter.
- **ALT-001:** Could use native Excel charts (via openpyxl.chart) instead of embedded PNGs. Not chosen because: matplotlib gives more control over stacked dispatch profiles, and the dispatch chart is complex (dual y-axis, stacked areas). Native Excel charts via openpyxl are limited to simpler chart types.

## Grill Me
1. **Q-001:** Do you have an Allotrope logo PNG file to embed in the workbook cover sheet?
   - **Recommended default:** Proceed without logo; use text-only header "Allotrope Ventures — DPPA Feasibility Assessment". Add optional `--logo` CLI flag for future use.
   - **Why this matters:** Visual polish on the cover sheet.
   - **If answered differently:** If a logo path is provided, embed it in cell A1 and shift the project name down.

## Suggested Next Step
Complete Sprint 2 first. Then begin PHASE-01 and PHASE-02 in parallel. PHASE-03 is the integration phase that depends on both.

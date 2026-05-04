---
title: "TOU Analysis Excel Showcase Workbook"
date: "2026-05-04"
status: "draft"
request: "Review TOU analysis and evoke /plan skill to replicate the analysis in an Excel file for showcase"
plan_type: "multi-phase"
research_inputs:
  - "plans/vietnam_tou2026_analysis_plan.md" - Established the 6-phase Python analysis that this Excel showcase replicates
  - "results/vietnam_tou2026_impact_report.md" - Defines the exact tables, drivers, and summary metrics the workbook must present
  - "docs/vietnam_tou_2026.md" - Canonical tariff hour mapping required for the Tariff Comparison sheet
---

# Plan: TOU Analysis Excel Showcase Workbook

## Objective

Build a single, self-contained Excel workbook (`results/vietnam_tou2026_showcase.xlsx`) that replicates the complete Vietnam TOU 2026 revenue-impact analysis currently encoded in Python outputs. The workbook must be presentation-ready: a stakeholder can open it, navigate across sheets, and read the tariff change, baseline-vs-new KPI deltas, revenue driver decomposition, and average-day dispatch profiles without running any code.

## Context Snapshot

- **Current state:** All 6 phases of the Python TOU analysis are complete. Artifacts exist at:
  - `results/vietnam_tou2026_analysis.json` — full structured payload with baseline + new-tariff KPIs, hourly frames, and average-day dispatch.
  - `results/vietnam_tou2026_impact_report.md` — markdown summary with per-case comparison tables and driver decomposition.
  - `results/figures/avg_day_dispatch_comparison.png` — Matplotlib chart.
  - `docs/vietnam_tou_2026.md` — canonical old-vs-new tariff hour mapping.
- **Desired state:** A reproducible Python script that reads the JSON payload and emits a formatted `.xlsx` workbook with multiple sheets, embedded charts, and Allotrope-style visual polish.
- **Key repo surfaces:**
  - `results/vietnam_tou2026_analysis.json` — primary data source.
  - `scripts/run_vietnam_tou2026_analysis.py` — generation script for the JSON payload; already deterministic.
  - `pyproject.toml` — `openpyxl>=3.1.0` is already a dependency.
  - `results/vietnam_tou2026_presentation_v2.pptx` / `.html` — existing visual style references (green title rule, Calibri typography).
- **Out of scope:**
  - Re-running the physics/financial model (JSON is the source of truth).
  - Modifying the existing PPTX or HTML presentations.
  - Adding VBA macros or interactive form controls.
  - Translations or multi-language support.

## Research Inputs

- `plans/vietnam_tou2026_analysis_plan.md` — Confirmed that the 6-phase Python analysis is complete. Phase 5 (delta analysis) and Phase 6 (reporting) outputs are the exact content to replicate in Excel.
- `results/vietnam_tou2026_impact_report.md` — Provides the precise table schemas: Executive Summary bullets, Tariff Change Description, Per-Case Results (9 columns), Revenue Decomposition By Driver (4 columns), and Recommended Mitigations.
- `docs/vietnam_tou_2026.md` — Supplies the canonical hour mapping (0–23) for both old and new schedules, plus the JSON block format and Excel sheet conventions.
- No other applicable research briefs were found in `research/`.

## Assumptions and Constraints

- **ASM-001:** The Excel workbook will be built by a Python script using `openpyxl`, which is already installed and used throughout the repo for reading/writing `.xlsx` files.
- **ASM-002:** The showcase workbook is read-only for stakeholders; formulas are optional. Static values copied from the JSON payload are acceptable and preferred for simplicity.
- **ASM-003:** Visual style should align with existing Allotrope presentation standards observed in `results/vietnam_tou2026_presentation_v2.pptx` (green title bar `#2f7d32`, Calibri/Calibri Light fonts, neutral body text `#333333`).
- **CON-001:** `openpyxl` charting capabilities are limited compared to Matplotlib or native Excel chart editing. Complex multi-series charts may require simplification or static image insertion.
- **CON-002:** The workbook must stay under ~5 MB to remain email-friendly.
- **DEC-001:** The JSON payload at `results/vietnam_tou2026_analysis.json` is the single source of truth; the Excel generator script will not re-run the model.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Design workbook sheet structure, layouts, and formatting spec | None | `docs/tou_showcase_workbook_spec.md` |
| PHASE-02 | Build JSON-to-structured-data export layer | None | `scripts/tou_showcase_data.py` + unit test |
| PHASE-03 | Implement openpyxl workbook generator | PHASE-01, PHASE-02 | `scripts/generate_tou_showcase_xlsx.py` |
| PHASE-04 | Add embedded charts and visual polish | PHASE-03 | `results/vietnam_tou2026_showcase.xlsx` with charts |
| PHASE-05 | QA, test, and deliver | PHASE-04 | Verified workbook + regeneration command documented |

## Detailed Phases

### PHASE-01 - Design Workbook Structure

**Goal**
Define the exact sheet inventory, cell layouts, table schemas, and color/formatting rules before writing any generation code.

**Tasks**
- [ ] TASK-01-01: Inventory all data entities needed from the JSON payload (cases, scenarios, KPIs, drivers, dispatch profiles, tariff mappings).
- [ ] TASK-01-02: Design 6–8 sheets with explicit row/column layouts:
  - `Cover` — title, date, project names, confidentiality footer.
  - `Tariff Comparison` — old-vs-new hour mapping (0–23) with color-coded bands.
  - `Baseline KPIs` — Emivest + Ecoplexus Year 1 and lifetime metrics under TOU 2024.
  - `New Tariff KPIs` — Same cases under TOU 2026.
  - `Delta Analysis` — computed deltas (revenue, IRR, NPV, DSCR) with conditional formatting.
  - `Driver Decomposition` — revenue driver table for Emivest Bundled Discount.
  - `Dispatch Profiles` — average-day dispatch data (24 rows) for old vs new.
  - `Charts` — embedded Excel charts or references to external image files.
- [ ] TASK-01-03: Document the Allotrope-style formatting spec (fonts, colors, number formats, header fill, border styles).
- [ ] TASK-01-04: Decide chart strategy: (a) native `openpyxl.chart` objects for bar/line charts, or (b) insert `avg_day_dispatch_comparison.png` as an image object, or (c) both.

**Files / Surfaces**
- `results/vietnam_tou2026_analysis.json` — inspect payload shape to confirm all required keys exist.
- `results/vietnam_tou2026_impact_report.md` — derive exact table schemas.
- `results/vietnam_tou2026_presentation_v2.pptx` — extract style references (not required to open, use known Allotrope conventions).

**Dependencies**
- None

**Exit Criteria**
- [ ] `docs/tou_showcase_workbook_spec.md` exists and contains per-sheet layout diagrams (ASCII or markdown tables) with column headers and row ranges.
- [ ] Formatting spec is documented with exact hex codes and font names.
- [ ] Chart strategy is decided and recorded.

**Phase Risks**
- **RISK-01-01:** JSON payload may be missing a needed field (e.g., `average_day_dispatch` for Ecoplexus). Mitigation: inspect JSON keys early and flag gaps in the spec.

---

### PHASE-02 - Build Data Export Layer

**Goal**
Create a thin, tested Python module that reads `results/vietnam_tou2026_analysis.json` and exposes clean dataclasses/dicts for workbook generation.

**Tasks**
- [ ] TASK-02-01: Create `scripts/tou_showcase_data.py` with functions:
  - `load_analysis_payload(path) -> dict`
  - `extract_baseline_kpis(payload) -> list[CaseKpi]`
  - `extract_new_tariff_kpis(payload) -> list[CaseKpi]`
  - `extract_comparison_rows(payload) -> list[dict]` (replicates the markdown comparison table)
  - `extract_driver_rows(payload) -> list[dict]`
  - `extract_dispatch_profiles(payload) -> tuple[pd.DataFrame, pd.DataFrame]`
  - `extract_tariff_mappings() -> tuple[dict, dict]` (from `docs/vietnam_tou_2026.md` or hardcoded canonical mapping)
- [ ] TASK-02-02: Add `tests/unit/test_tou_showcase_data.py` with assertions that:
  - All expected keys exist in the payload.
  - Extracted tables have the correct row counts (e.g., 5 comparison rows: 4 Emivest options + 1 Ecoplexus).
  - Dispatch DataFrames have exactly 24 rows (hours 0–23).
  - No `None` values leak into currency/percentage columns.

**Files / Surfaces**
- `scripts/tou_showcase_data.py` — new file.
- `tests/unit/test_tou_showcase_data.py` — new test file.
- `results/vietnam_tou2026_analysis.json` — read-only data source.

**Dependencies**
- PHASE-01 (spec must define required data shapes, but coding can start in parallel once shapes are stable).

**Exit Criteria**
- [ ] `pytest tests/unit/test_tou_showcase_data.py -q` passes with 100% of assertions green.
- [ ] Script runs in <1 second and produces validated data structures.

**Phase Risks**
- **RISK-02-01:** JSON payload uses mixed numeric types (`float`, `int`, `None`). Mitigation: normalize all financial values to `float` with `0.0` default in the export layer.

---

### PHASE-03 - Implement openpyxl Workbook Generator

**Goal**
Write `scripts/generate_tou_showcase_xlsx.py` that consumes the export layer and writes a fully formatted `.xlsx` workbook.

**Tasks**
- [ ] TASK-03-01: Scaffold the generator script with `argparse` for optional `--input-json` and `--output-xlsx` paths (defaults to repo-standard paths).
- [ ] TASK-03-02: Implement `build_cover_sheet(wb, metadata)` — title, subtitle, date, project list, confidentiality footer, green title bar.
- [ ] TASK-03-03: Implement `build_tariff_comparison_sheet(wb, old_map, new_map)` — 24-row hour table with color fills per period (off-peak = light blue, standard = light yellow, peak = light red).
- [ ] TASK-03-04: Implement `build_kpi_sheet(wb, sheet_name, kpis)` — generic KPI sheet builder used for both Baseline and New Tariff sheets. Columns: Case, Scenario, Year 1 Solar MWh, Year 1 Revenue, Year 1 EBITDA, Project IRR, Equity IRR, NPV, Min DSCR.
- [ ] TASK-03-05: Implement `build_delta_sheet(wb, comparison_rows)` — delta table with conditional formatting: revenue deltas negative → red text, positive → green text; IRR deltas in basis points.
- [ ] TASK-03-06: Implement `build_driver_sheet(wb, driver_rows)` — driver decomposition with horizontal bar representation (optional: use data bars via conditional formatting).
- [ ] TASK-03-07: Implement `build_dispatch_sheet(wb, baseline_df, new_df)` — 24-row side-by-side average-day dispatch (solar direct, BESS discharge, grid import).
- [ ] TASK-03-08: Apply global formatting: freeze panes on data sheets, auto-filter on tables, column auto-width, number formats (`#,##0` for currency, `0.00%` for IRR, `0.00x` for DSCR).

**Files / Surfaces**
- `scripts/generate_tou_showcase_xlsx.py` — new generator script.
- `scripts/tou_showcase_data.py` — import and use.
- `results/vietnam_tou2026_showcase.xlsx` — output artifact.

**Dependencies**
- PHASE-01 (formatting spec and sheet layouts).
- PHASE-02 (data export layer functions).

**Exit Criteria**
- [ ] Script runs without errors: `python scripts/generate_tou_showcase_xlsx.py`.
- [ ] Output file opens in Excel / LibreOffice without corruption warnings.
- [ ] All data values visually match the markdown report (`results/vietnam_tou2026_impact_report.md`) when spot-checked.
- [ ] `ruff check scripts/generate_tou_showcase_xlsx.py` passes.

**Phase Risks**
- **RISK-03-01:** `openpyxl` conditional formatting for data bars or color scales is verbose and error-prone. Mitigation: use simple solid-fill conditional formatting (green/red text) first; upgrade to data bars only if time permits.
- **RISK-03-02:** Column auto-width in `openpyxl` requires manual calculation. Mitigation: implement a helper `adjust_column_widths(ws)` that measures max cell content length.

---

### PHASE-04 - Add Embedded Charts and Visual Polish

**Goal**
Insert native Excel charts and/or reference images so the workbook tells the story visually, not just numerically.

**Tasks**
- [ ] TASK-04-01: Add a **Clustered Bar Chart** on the `Delta Analysis` sheet (or a dedicated `Charts` sheet) showing Δ Revenue % and Δ IRR (pp) for each case/scenario.
- [ ] TASK-04-02: Add a **Stacked Area Chart** on the `Dispatch Profiles` sheet showing average-day dispatch (solar direct, BESS discharge, grid import) for old vs new tariff side by side or as two separate sub-charts.
- [ ] TASK-04-03: If `openpyxl` charting proves too limited for the stacked area, insert `results/figures/avg_day_dispatch_comparison.png` as an image object anchored to the `Dispatch Profiles` sheet.
- [ ] TASK-04-04: Apply final polish pass: merge and center title cells, add thin borders to all data tables, set print area and page setup (landscape, fit-to-page).

**Files / Surfaces**
- `scripts/generate_tou_showcase_xlsx.py` — extend with chart builders.
- `results/figures/avg_day_dispatch_comparison.png` — optional image source.

**Dependencies**
- PHASE-03 (workbook skeleton and data population must be complete).

**Exit Criteria**
- [ ] Opening the workbook in Excel shows at least 2 native charts with correct data series and axis labels.
- [ ] Charts are legible without manual resizing.
- [ ] Image insertion (if used) renders clearly and does not distort row heights.

**Phase Risks**
- **RISK-04-01:** `openpyxl` charts do not support all Excel features (e.g., secondary axes, complex legends). Mitigation: keep charts simple (single axis, clear legend, no 3D effects).

---

### PHASE-05 - QA, Test, and Deliver

**Goal**
Verify numerical accuracy, visual fidelity, and reproducibility; document the regeneration command; commit the deliverables.

**Tasks**
- [ ] TASK-05-01: Spot-check 10+ cells against the JSON payload and the markdown report (revenue, IRR, NPV, driver values, dispatch hour 18).
- [ ] TASK-05-02: Run the generator script on a clean checkout and confirm deterministic output (same file hash given same input JSON).
- [ ] TASK-05-03: Add a README section or inline docstring documenting the regeneration command: `python scripts/generate_tou_showcase_xlsx.py [--input-json PATH] [--output-xlsx PATH]`.
- [ ] TASK-05-04: Run the full test suite for modified/new files: `pytest tests/unit/test_tou_showcase_data.py -q` and `ruff check scripts/generate_tou_showcase_xlsx.py scripts/tou_showcase_data.py`.
- [ ] TASK-05-05: Commit the generator script, data module, test file, and the generated workbook to the branch.

**Files / Surfaces**
- `results/vietnam_tou2026_showcase.xlsx` — final deliverable.
- `scripts/generate_tou_showcase_xlsx.py` — generator.
- `scripts/tou_showcase_data.py` — data layer.
- `tests/unit/test_tou_showcase_data.py` — tests.
- `docs/tou_showcase_workbook_spec.md` — spec.

**Dependencies**
- PHASE-04 (charts and polish complete).

**Exit Criteria**
- [ ] All spot-checks pass with zero discrepancies > $1 or > 1 bps.
- [ ] `pytest` and `ruff check` pass.
- [ ] `results/vietnam_tou2026_showcase.xlsx` is present and opens correctly.
- [ ] Regeneration command is documented and reproducible.

**Phase Risks**
- **RISK-05-01:** Excel file may have subtle platform-specific rendering differences (Windows vs macOS). Mitigation: test open in both Excel desktop and LibreOffice; document any known visual deltas.

---

## Verification Strategy

- **TEST-001:** `pytest tests/unit/test_tou_showcase_data.py -q` — validates data extraction completeness and type safety.
- **TEST-002:** `python scripts/generate_tou_showcase_xlsx.py` — end-to-end generator smoke test.
- **MANUAL-001:** Open `results/vietnam_tou2026_showcase.xlsx` in Excel; verify that all 6–8 sheets are present, tables are formatted, and charts render.
- **MANUAL-002:** Spot-check key figures against `results/vietnam_tou2026_impact_report.md`:
  - Emivest Bundled Discount delta revenue = -$63,305
  - Ecoplexus project IRR old = 6.26%, new = 9.31%
  - Driver: Loss of morning peak uplift = -$65,343
- **OBS-001:** File size check: `results/vietnam_tou2026_showcase.xlsx` must be < 5 MB.

## Risks and Alternatives

- **RISK-001:** The JSON payload may become stale if the underlying model is re-run with different inputs. Mitigation: tie the generator script to the deterministic analysis runner (`scripts/run_vietnam_tou2026_analysis.py`) and document the dependency.
- **RISK-002:** `openpyxl` charting limitations may produce charts that look unprofessional compared to Matplotlib. Mitigation: fallback to embedding the existing `avg_day_dispatch_comparison.png` and keep native charts simple.
- **ALT-001:** Use `xlsxwriter` instead of `openpyxl`. Rejected because `openpyxl` is already the project's standard dependency and is used for both reading and writing workbooks.
- **ALT-002:** Generate the Excel file via `pandas.ExcelWriter` with minimal formatting. Rejected because the showcase requirement demands presentation-grade formatting (colors, charts, borders) that pandas alone cannot provide.

## Grill Me

No open clarification questions.

## Interpretation Note: Showcase vs Live Model

"Replicate the TOU analysis in an Excel model" admits two readings. This plan takes reading **(A)** explicitly:

- **(A) Showcase workbook (chosen).** A read-only `.xlsx` whose cells hold *static values* copied from `results/vietnam_tou2026_analysis.json`. The Python model remains the source of truth; the workbook is a presentation artifact. This is what ASM-002 and DEC-001 encode.
- **(B) Live formula workbook (NOT in scope).** An `.xlsx` whose cells re-derive the TOU 2024 vs 2026 deltas via Excel formulas — solar generation, BESS dispatch, hour-by-hour tariff lookup, settlement, IRR/NPV — so a stakeholder can change a tariff cell and watch outputs recompute. This would be a port of the Python physics + settlement layers (`src/re_storage/physics/`, `src/re_storage/settlement/`) into Excel and is materially larger than the current plan.

If the requester actually wants (B), this plan must be rejected and replaced; reuse of `model_architecture.md` (the existing Excel-model reference doc) would be the starting point. If the goal is a stakeholder-readable presentation of the completed TOU 2026 impact analysis — which the recent commit history (`feat: add final TOU 2026 impact analysis report`, `feat: add v2 Vietnam TOU presentation outputs`) suggests — reading (A) is correct and this plan stands.

## Claude Execution Playbook

Recommended ordering when a Claude session executes this plan end-to-end:

1. **Spawn an `Explore` subagent** to read `results/vietnam_tou2026_analysis.json` and report the exact key tree, presence of `average_day_dispatch` for each case, and any `None`/missing fields. Output feeds PHASE-01 and de-risks RISK-01-01 before any code is written.
2. **PHASE-01 in main context** — author `docs/tou_showcase_workbook_spec.md`. Small, design-heavy, benefits from main-context coherence.
3. **PHASE-02 + PHASE-03 sequentially in main context** — data layer first, then generator. Avoid parallel subagents here: the generator imports the data layer, so the dependency is tight.
4. **PHASE-04** — incremental. After each chart added, regenerate and visually verify (open the workbook locally, or convert one sheet to PNG via LibreOffice headless if a screenshot is needed).
5. **PHASE-05** — checklist run; commit only after spot-checks pass.

Per-phase commands:

```bash
# After PHASE-02
pytest tests/unit/test_tou_showcase_data.py -q

# After PHASE-03 / PHASE-04
python scripts/generate_tou_showcase_xlsx.py
ruff check scripts/generate_tou_showcase_xlsx.py scripts/tou_showcase_data.py

# Final smoke
python scripts/generate_tou_showcase_xlsx.py \
    --input-json results/vietnam_tou2026_analysis.json \
    --output-xlsx results/vietnam_tou2026_showcase.xlsx
ls -lh results/vietnam_tou2026_showcase.xlsx   # confirm < 5 MB (OBS-001)
```

Deterministic-output check (TASK-05-02): hash the file twice across two clean runs.

```bash
python scripts/generate_tou_showcase_xlsx.py && \
    sha256sum results/vietnam_tou2026_showcase.xlsx
# rerun and compare hashes
```

## Suggested Next Step

Approve this plan, then begin implementation with PHASE-01 (design the workbook spec) while I (or another agent) read the JSON payload to confirm data shapes.

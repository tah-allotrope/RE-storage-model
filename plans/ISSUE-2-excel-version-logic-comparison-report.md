# ISSUE-2: Excel Version Logic Extraction + HTML Comparison Report

## 1. Objective

Build a reproducible workflow that:

1. Detects the latest and previous Excel workbooks in `data/`
2. Extracts material model logic changes (not noisy full-cell diffs)
3. Quantifies KPI impacts between versions
4. Produces a self-contained HTML report at `reports/excel_logic_comparison.html`

This report is for model-forensics and handoff use, not for replacing existing JSON pipeline reporting.

---

## 2. Confirmed Baseline (From Current Investigation)

### 2.1 Workbook Pair

- Latest: `data/llm 20260129 SOLAR BESS MODEL - Editing - for processing test.xlsx`
- Previous: `data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx`

Selection rule used: newest `.xlsx` by modified timestamp.

### 2.2 Sheet-Level Structural Changes

- Added sheets in latest: `Claude Log`, `Quick Start`, `Dashboard`, `Scenarios`
- Removed sheets: none
- Shared core model sheets remain: `Assumption`, `Data Input`, `Calc`, `Helper`, `Other Input`, `Loss`, `DPPA`, `Measures`, `Lifetime`, `Financial`, `Output`, `Cover`, `NAV`

### 2.3 Material KPI Deltas (Latest - Previous)

From `scripts/extract_excel_kpis.py`:

- `project_irr`: `0.0507355422` -> `0.0895217389` (delta `+0.0387861967`)
- `equity_irr`: `0.0463760525` -> `0.0839941889` (delta `+0.0376181364`)
- `unlevered_irr`: `0.0883317977` -> `0.1940252244` (delta `+0.1056934267`)
- `npv_usd`: `-2,653,309.37` -> `22,033,885.71` (delta `+24,687,195.08`)
- `measures_total_grid_savings`: `109,095,714,470.12` -> `154,932,264,321.04`
- `measures_bau_grid_expense`: `308,435,590,914.52` -> `353,029,759,046.16`

Notably stable:

- `calc_solar_gen_sum_kwh`, `calc_soc_min_kwh`, `calc_soc_max_kwh`
- DPPA revenue components (`measures_market_energy_payment`, `measures_cfd_payment`)

Interpretation: major movement is concentrated in financial/grid-expense layers, not core physics generation.

### 2.4 High-Signal Logic Evidence

1. Financial solver freshness signal appears in latest:
   - Added `Financial!H1` formula: freshness status based on `ABS(G170)`
   - Added `Financial!J1` formula: mirrors `G170`
2. `Financial!G170` cached value:
   - Previous: `-8,373,198.664090492`
   - Latest: `0`
3. Latest `Financial!H1` cached status: `"✅ FRESH"`

This strongly suggests the previous file may contain stale/unsolved debt-sizing state while latest reflects a fresh solve, which can explain large IRR/NPV differences.

---

## 3. Scope for Next Session

### In Scope

- Create a new script that generates one standalone HTML comparison report from two Excel files
- Material-change focused sections (no exhaustive full-cell appendix)
- Evidence tables with exact cell references/formulas/values
- KPI delta table with absolute and relative changes
- Structural summary (sheet add/remove/dimension changes)

### Out of Scope

- Modifying workbook contents
- Recalculating formulas in Excel
- Changing existing JSON pipeline report (`src/re_storage/reporting/html_report.py`)
- Full forensic markdown replacement of `model_architecture.md`

---

## 4. Implementation Design

### 4.1 New Script

Create:

- `scripts/compare_excel_versions.py`

CLI contract:

```bash
python scripts/compare_excel_versions.py \
  --latest "data/<latest>.xlsx" \
  --previous "data/<previous>.xlsx" \
  --output "reports/excel_logic_comparison.html"
```

Optional convenience mode:

- If `--latest/--previous` omitted, auto-pick newest two `.xlsx` files in `data/`.

### 4.2 Core Functions

Implement with strict type hints and docstrings:

1. `discover_workbook_pair(data_dir: Path) -> tuple[Path, Path]`
2. `load_workbooks(path: Path) -> tuple[Workbook, Workbook]` (formula + cached values)
3. `collect_structure_diff(...) -> dict[str, Any]`
4. `collect_defined_name_diff(...) -> list[dict[str, Any]]`
5. `collect_formula_diff_for_sheet(...) -> dict[str, Any]`
6. `collect_material_logic_changes(...) -> dict[str, Any]`
7. `extract_kpi_bundle(path: Path) -> dict[str, float | None]` (reuse `extract_all_kpis`)
8. `compute_kpi_deltas(...) -> list[dict[str, Any]]`
9. `render_html_report(...) -> str`
10. `write_report(html: str, output_path: Path) -> None`

### 4.3 Material-Change Heuristics (Required)

Classify each detected change as one of:

- `Structural`: added sheet, shifted table header rows, defined-name target moved but value unchanged
- `Potentially Material`: formula changed in key sheets but value impact unclear
- `Material`: KPI-linked change with clear downstream value movement

Key sheets to prioritize in material analysis:

- `Assumption`, `Loss`, `Lifetime`, `Financial`, `Measures`, `Helper`

Suppress low-value noise:

- Skip bulk repeated formula copies unless represented as one grouped pattern
- Group same-formula-pattern changes by row/column span

---

## 5. HTML Report Contract

Output file:

- `reports/excel_logic_comparison.html`

Must be self-contained (inline CSS, no CDN).

### Required Sections

1. **Comparison Overview**
   - Latest vs previous filenames, timestamps, file sizes
   - Selected by explicit args or auto-discovery
2. **Structure Diff**
   - Added/removed sheets
   - Shared sheet dimension deltas
3. **KPI Delta Dashboard**
   - Table: KPI, previous, latest, absolute delta, relative delta, significance tag
4. **Material Logic Changes**
   - Grouped findings by subsystem:
     - Financial solver state
     - Loss/Lifetime reference-window shifts
     - Assumption formula edits
     - Grid-expense path notes
   - Each finding must include at least one exact cell reference and formula text
5. **Defined Names Retargeting**
   - Name, previous ref/value, latest ref/value, interpretation
6. **Risk & Interpretation Notes**
   - Explicitly separate observed facts from assumptions
   - Call out confidence level for each conclusion
7. **Reproducibility Footer**
   - Command used, generation timestamp, workbook hashes or file sizes

### Styling

- Clean readable tables
- Severity chips (`Structural`, `Potentially Material`, `Material`)
- Print-friendly `@media print` rules

---

## 6. Evidence Items to Include Verbatim

Include these in report body as high-priority evidence:

1. `Financial!G170` values previous vs latest
2. `Financial!H1` formula/value (latest) and absence in previous
3. IRR/NPV cells (`Financial!G123`, `G136`, `G189`, `G193`) values both files
4. Example Lifetime reference shift:
   - Previous uses `Loss!$A$3:$A$27`
   - Latest uses `Loss!$A$9:$A$33`
5. Example Assumption formula normalization:
   - `Assumption!K43` from hardcoded `0.16*...` to `K45*...`

---

## 7. Validation Checklist (Next Session)

1. Run script with explicit file paths and with auto-discovery mode.
2. Confirm HTML opens locally with no network dependency.
3. Verify KPI table numbers match direct `extract_excel_kpis.py` outputs.
4. Verify solver-status narrative matches extracted `Financial` cells.
5. Confirm no crashes if some optional sheets are absent.
6. Run lint/tests for touched files:
   - `pytest` (or targeted tests if full suite is too slow)
   - `ruff check`
   - `mypy --strict` (if script is type-checked scope)

---

## 8. Risks / Caveats

1. `openpyxl data_only=True` relies on cached values; if workbook was not recalculated before save, some values may be stale/None.
2. Formula-diff volume in large sheets (`Financial`, `Lifetime`) can be noisy; grouping logic is essential.
3. Windows console encoding can break Unicode output; keep CLI logs ASCII-safe where practical.

---

## 9. Suggested Execution Order for Next Session

1. Implement `scripts/compare_excel_versions.py` skeleton and data classes.
2. Add extraction routines (structure, names, material formulas, KPIs).
3. Add HTML renderer with required sections.
4. Run script on current workbook pair and inspect generated report.
5. Refine grouping/severity thresholds to reduce noise.
6. Final validation and handoff notes.

---

## 10. Definition of Done

- One command produces `reports/excel_logic_comparison.html` from latest vs previous workbook pair.
- Report clearly explains material logic changes with cell/formula evidence.
- KPI delta section is accurate and reproducible.
- Output is readable on screen and print preview.

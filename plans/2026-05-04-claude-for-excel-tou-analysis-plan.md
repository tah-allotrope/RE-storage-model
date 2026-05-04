---
title: "Claude for Excel — TOU 2024 vs 2026 Analysis on Ecoplexus 40MW Workbook"
date: "2026-05-04"
status: "draft"
request: "Draft a markdown plan for Claude for Excel to conduct TOU analysis for the same rooftop solar project in the Excel model and compare key financials"
plan_type: "multi-phase"
target_runtime: "Claude for Excel (in-workbook agent)"
target_workbook: "data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx"
research_inputs:
  - "docs/vietnam_tou_2026.md - Canonical hour-by-hour mapping for old vs new TOU"
  - "docs/2026-04-25_vietnam-tou-rooftop-ppa.md - Decision 963/QĐ-BCT context, multipliers, BESS cycle implications"
  - "results/vietnam_tou2026_impact_report.md - Python-side answer key for comparison"
  - "results/baseline/ecoplexus_tou2024.json - Python TOU2024 KPIs (validation target)"
  - "results/new_tariff/ecoplexus_tou2026.json - Python TOU2026 KPIs (validation target)"
---

# Plan: Claude for Excel — TOU 2024 vs 2026 Analysis on Ecoplexus 40MW Workbook

## Objective

Run a complete Time-of-Use tariff-change analysis **inside the Ecoplexus 40MW Solar+BESS Excel model** using Claude for Excel as the executing agent. The agent must add a parallel TOU 2026 scenario to the existing workbook, recompute hourly dispatch and settlement under the new tariff windows, and produce a side-by-side comparison of key project financials (revenue, IRR, NPV, DSCR, BESS cycles) against the existing TOU 2024 baseline that already lives in the workbook. The Python-side analysis already in `results/` is the *answer key*, not a dependency.

## Context Snapshot

- **Project under analysis:** Ecoplexus 40MW rooftop/C&I Solar + BESS (the only project with a complete operating Excel model in `data/`).
- **Source workbook:** `data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx` (~9.8 MB). This is an audited financial model containing tariff schedule, hourly dispatch, settlement waterfall, debt sizing, and IRR/NPV outputs. It currently encodes the **TOU 2024** tariff windows.
- **Tariff change:** Decision 963/QĐ-BCT (effective 22 April 2026) replaces the split peak (09:30–11:30 + 17:00–20:00) with a single consolidated evening peak (17:30–22:30) and shifts off-peak from 22:00–04:00 to 00:00–06:00. Full hour-by-hour mapping in `docs/vietnam_tou_2026.md`.
- **Validation answer key (Python):**
  - TOU 2024 baseline: `results/baseline/ecoplexus_tou2024.json` — Project IRR 6.26%, NPV $6.01M, Year-1 DPPA revenue $2.547M, Min DSCR 1.28x, Year-1 solar 71,808 MWh.
  - TOU 2026 new: `results/new_tariff/ecoplexus_tou2026.json` — Python computes Project IRR 9.31% (+3.06 pp), revenue +$1.348M (+24.32%), NPV +$11.80M.
  - Driver decomposition and per-case breakdown in `results/vietnam_tou2026_impact_report.md`.
- **Out of scope:**
  - Re-running the Python model. JSON files are the trusted comparator.
  - Touching `data/llm 20260129 SOLAR BESS MODEL - Editing - for processing test.xlsx` (separate workbook used for LLM-editing experiments).
  - Modifying retail tariff *multipliers* — the new tariff multipliers under Decision 14/2025 are unconfirmed for the new windows; this analysis assumes the same VND/kWh rate per period as TOU 2024 and re-buckets only the *hours*. Sensitivity to revised multipliers is a follow-up plan.
  - Writing any Python, openpyxl, or VBA. Claude for Excel performs all work via formulas, named ranges, and native Excel charts.

## Execution Environment: Claude for Excel

This plan is written for the **Claude for Excel** add-in agent operating directly inside the open workbook. The agent's primitives:

- Inspect cells, named ranges, defined names, and sheet structure via the in-workbook context.
- Add/duplicate sheets, write cell values and formulas, define new named ranges.
- Apply conditional formatting and number formats.
- Insert native Excel charts.
- Re-evaluate the workbook (Excel handles recalculation; the agent does not write iteration code).

Constraints implied by this runtime:

- **No file writes outside the workbook.** All artifacts live in new sheets within the .xlsx.
- **No Python.** If the existing model has hard-coded period assignments embedded in formulas (e.g., `IF(HOUR(t)>=10, ...)`) those must be re-expressed as `VLOOKUP`/`XLOOKUP` against a tariff-schedule table so a scenario switch can drive both regimes.
- **Workbook integrity.** Save under a new filename (`data/AUDIT 20260504 40MW Ecoplexus TOU2024-vs-2026.xlsx`) and never overwrite the audited source.

## Research Inputs

- `docs/vietnam_tou_2026.md` — supplies the integer-hour mapping convention (whole-hour rounding for 09:30 / 17:30 boundaries) and the JSON `tariff_schedule` blocks. The agent must encode `peak`/`standard`/`off_peak` exactly per the "Summary" lines for each schedule.
- `docs/2026-04-25_vietnam-tou-rooftop-ppa.md` — narrative context for the change; informs interpretation of the BESS-cycle reduction (2 → 1) and the loss of the morning peak overlap with solar generation.
- `results/vietnam_tou2026_impact_report.md` — exact KPI deltas the in-Excel result must reproduce (within tolerance).
- `results/baseline/ecoplexus_tou2024.json` and `results/new_tariff/ecoplexus_tou2026.json` — numerical validation targets.

## Assumptions and Constraints

- **ASM-001:** The audit workbook contains an addressable "Tariff Schedule" sheet (or equivalent) and an hourly dispatch/settlement block where each hour is assigned a period via formula. PHASE-01 verifies and, if absent, restructures the formulas before any tariff swap.
- **ASM-002:** Per-period VND/kWh prices are unchanged between regimes (same Decision-14/2025 multipliers re-applied to new windows). This is the explicit "tariff-windows-only" sensitivity case — see "Out of scope".
- **ASM-003:** BESS dispatch logic in the workbook is rule-based ("charge during off-peak, discharge during peak"). The cycle count drops from 2 → 1 automatically once the new schedule has only one peak block per day. No manual dispatch-strategy edits should be required; if the workbook hard-codes two-cycle dispatch, PHASE-04 must restructure it.
- **ASM-004:** Year-1 solar generation (71,808 MWh) is invariant to tariff regime — solar physics is unchanged. Any deviation in solar MWh between scenarios indicates a formula error to be flagged.
- **CON-001:** Excel formula precision diverges from Python's float64 on long IRR/NPV cash-flow chains. Tolerance bands: revenue ±0.5%, IRR ±10 bps, NPV ±0.5%, DSCR ±0.01x.
- **CON-002:** No structural model changes (debt sizing, opex, capex schedules) — only tariff-window re-bucketing.
- **DEC-001:** Comparison surface is a new `TOU Comparison` sheet, not edits to existing audited summary cells.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Map workbook structure; locate tariff-driving cells | None | Inventory note (in `Notes` sheet) listing every cell/range that consumes the tariff period |
| PHASE-02 | Add `Tariff Schedule 2026` sheet and a `Scenario` switch | PHASE-01 | New sheet + named range `TOU_VERSION` toggling between 2024 and 2026 |
| PHASE-03 | Refactor period-lookup formulas to be schedule-driven | PHASE-02 | Hourly dispatch/settlement formulas reference the schedule table via lookup |
| PHASE-04 | Re-evaluate dispatch + settlement under TOU 2026 | PHASE-03 | Workbook recomputes cleanly under both scenarios |
| PHASE-05 | Build `TOU Comparison` sheet with KPI deltas | PHASE-04 | Side-by-side TOU 2024 vs 2026 table + Python validation column |
| PHASE-06 | Add charts and finalize deliverable | PHASE-05 | 2 native charts; saved as new .xlsx |

## Detailed Phases

### PHASE-01 — Inventory Tariff Touchpoints

**Goal**
Before changing anything, map every place in the workbook where the tariff period (peak/standard/off-peak) influences a calculation.

**Tasks for the agent**
- [ ] TASK-01-01: List all sheets in the workbook. Identify the existing tariff-schedule sheet (likely "Tariff Schedule", "TOU", or similar) and the hourly dispatch/settlement sheet(s).
- [ ] TASK-01-02: On the dispatch/settlement sheet, find the column or row that assigns a period to each hour. Record the exact formula (e.g., `=IF(OR(HOUR(A2)>=10, HOUR(A2)<12), "peak", ...)`).
- [ ] TASK-01-03: Trace the period assignment downstream: which cells multiply hourly kWh × per-period VND/kWh? Which cells aggregate to monthly/annual revenue?
- [ ] TASK-01-04: Trace BESS dispatch decisions: which cells decide "charge" vs "discharge" vs "idle" each hour, and how do they reference the period?
- [ ] TASK-01-05: Create a `Notes` sheet (if absent) and write a compact inventory: sheet name, cell range, role (period source / period consumer / aggregation / BESS rule).

**Exit Criteria**
- [ ] The `Notes` sheet contains a numbered list of every tariff-touched range, with role labels.
- [ ] At least one period source, one revenue consumer, one BESS dispatch rule, and one IRR-feeder cash-flow row are explicitly identified.

**Phase Risks**
- **RISK-01-01:** The workbook may use volatile or array formulas that obscure the period assignment. Mitigation: use Excel's "Trace Precedents" / "Trace Dependents" mentally by following named ranges; if blocked, ask the user to confirm the period-source cell range before proceeding.

### PHASE-02 — Add 2026 Schedule Sheet and Scenario Switch

**Goal**
Introduce the new TOU 2026 hour mapping and a single switchable scenario flag without modifying the existing TOU 2024 sheet.

**Tasks for the agent**
- [ ] TASK-02-01: Duplicate the existing `Tariff Schedule` sheet to `Tariff Schedule 2026`. Preserve all column headers and per-period prices (assumption ASM-002).
- [ ] TASK-02-02: On `Tariff Schedule 2026`, overwrite the `period` column per the new schedule from `docs/vietnam_tou_2026.md` (weekday): `off_peak = {0,1,2,3,4,5}`, `standard = {6..17, 23}`, `peak = {18,19,20,21,22}`. Apply the Sunday rule in the Sunday block if a separate Sunday schedule exists.
- [ ] TASK-02-03: On a new `Scenario` sheet (or top of an existing summary sheet), create a single cell containing the scenario name. Define a name `TOU_VERSION` for that cell. Validate values to `{2024, 2026}`.
- [ ] TASK-02-04: Define a named range `ACTIVE_TARIFF_SCHEDULE` that resolves to `Tariff Schedule` when `TOU_VERSION = 2024` and `Tariff Schedule 2026` when `TOU_VERSION = 2026`. Use `INDIRECT` or `CHOOSE`/`SWITCH` — prefer `SWITCH` if available to avoid `INDIRECT` volatility.

**Exit Criteria**
- [ ] Toggling `TOU_VERSION` between 2024 and 2026 changes the value Excel resolves through `ACTIVE_TARIFF_SCHEDULE` (verifiable with a temporary `=VLOOKUP(10, ACTIVE_TARIFF_SCHEDULE, 2, FALSE)` probe — should return `peak` under 2024 and `standard` under 2026).
- [ ] No existing audited cells have been modified.

### PHASE-03 — Refactor Period Lookups

**Goal**
Re-express all period-determining formulas identified in PHASE-01 to read from `ACTIVE_TARIFF_SCHEDULE` instead of hard-coded hour comparisons.

**Tasks for the agent**
- [ ] TASK-03-01: For each period-source cell from the PHASE-01 inventory, replace the hard-coded `IF(HOUR(...))` with `XLOOKUP(HOUR(timestamp), ACTIVE_TARIFF_SCHEDULE[hour], ACTIVE_TARIFF_SCHEDULE[period])` (or `VLOOKUP` if `XLOOKUP` is unavailable).
- [ ] TASK-03-02: For Sunday handling, wrap the lookup with `IF(WEEKDAY(timestamp,2)=7, ...)` referencing the Sunday block of the active schedule.
- [ ] TASK-03-03: With `TOU_VERSION = 2024`, confirm every KPI in the existing summary sheet matches the *audited* values byte-for-byte (refactor must be neutral when the active schedule equals the original).

**Exit Criteria**
- [ ] Setting `TOU_VERSION = 2024` reproduces the original audited Year-1 revenue, IRR, NPV, DSCR (within ±0.01% rounding).
- [ ] No `#REF!` / `#NAME?` / `#N/A` errors anywhere downstream of the refactor.

**Phase Risks**
- **RISK-03-01:** A small rounding drift may appear if the original used `IF` chains with implicit type coercion. Mitigation: identify the drift cell and adjust lookup result types; if drift exceeds 0.5%, halt and report.

### PHASE-04 — Recompute Under TOU 2026

**Goal**
Set `TOU_VERSION = 2026` and verify the workbook recalculates cleanly.

**Tasks for the agent**
- [ ] TASK-04-01: Switch `TOU_VERSION` to 2026. Force a full recalc (`Ctrl+Alt+F9` semantics).
- [ ] TASK-04-02: Spot-check hour-by-hour period assignments on a random weekday in the dispatch sheet: hour 10 should now be `standard` (was `peak`), hour 22 should be `peak` (was `off_peak`).
- [ ] TASK-04-03: Confirm Year-1 solar generation MWh is unchanged (ASM-004). If it differs, a formula reference is incorrectly tariff-coupled — fix before continuing.
- [ ] TASK-04-04: Verify BESS cycle count per day collapses from 2 to 1 (expected), and that BESS discharge is concentrated in 18:00–22:00.

**Exit Criteria**
- [ ] All three TOU 2026 spot-checks pass.
- [ ] Year-1 solar MWh identical between scenarios.
- [ ] No formula errors after recalc.

### PHASE-05 — Build TOU Comparison Sheet

**Goal**
Produce a compact side-by-side comparison of key financials under both scenarios, including a Python-validation column.

**Tasks for the agent**
- [ ] TASK-05-01: Create a new sheet `TOU Comparison`.
- [ ] TASK-05-02: Build the KPI table with the rows below. The "TOU 2024" and "TOU 2026" columns reference the summary cells from the existing model (under each scenario). The "Python TOU 2024" and "Python TOU 2026" columns are static literals from the JSONs (the agent enters them once, sourced from the validation files). The "Δ (Excel)" and "Δ (Python)" columns compute deltas. The "Reconcile" column flags any |Excel − Python| breach of CON-001 tolerance via conditional formatting (red fill).

  | KPI | Unit | TOU 2024 (Excel) | TOU 2026 (Excel) | Δ (Excel) | Python TOU 2024 | Python TOU 2026 | Δ (Python) | Reconcile |
  |---|---|---:|---:|---:|---:|---:|---:|:---:|
  | Year-1 solar generation | MWh | | | | 71,808.30 | 71,808.30 | 0.00 | |
  | Year-1 DPPA revenue | USD | | | | 2,547,078.53 | TBD-from-tou2026.json | | |
  | Year-1 grid savings | USD | | | | 2,996,562.98 | TBD | | |
  | Year-1 EBITDA | USD | | | | 2,109,568.53 | TBD | | |
  | Project IRR | % | | | | 6.26% | 9.31% | +3.06 pp | |
  | Equity IRR | % | | | | 5.71% | TBD | | |
  | NPV | USD | | | | 6,009,427.39 | TBD (+11.80M per impact report) | | |
  | Min DSCR | x | | | | 1.28 | 1.27 | -0.01 | |

  The agent fills the `TBD` cells by reading `results/new_tariff/ecoplexus_tou2026.json` (provide its contents to the agent as plain text alongside the workbook, since Claude for Excel cannot read repo files directly).
- [ ] TASK-05-03: Below the KPI table, add a **driver attribution** mini-table mirroring the impact report's decomposition for the closest analog case (Ecoplexus 40MW DPPA): morning-peak loss, BESS cycle reduction, evening peak shift, off-peak rate. Reference the impact report values; the in-Excel decomposition is a follow-up.
- [ ] TASK-05-04: Apply conditional formatting: red text for negative deltas, green for positive, on both Excel and Python delta columns.
- [ ] TASK-05-05: Generate the comparison snapshot under each scenario by toggling `TOU_VERSION` and pasting values into the table — *or* (preferred) build the table to read from the live model under each scenario via two named-range snapshots stored on a hidden `Snapshots` sheet (toggle, copy values, toggle back, copy values).

**Exit Criteria**
- [ ] All 8 KPI rows populated for TOU 2024 (Excel), TOU 2026 (Excel), Python TOU 2024, Python TOU 2026.
- [ ] Reconcile column shows green/checkmark on every row (within CON-001 tolerance bands).
- [ ] Any red cell triggers a written note in `Notes` explaining the discrepancy.

### PHASE-06 — Charts and Finalize

**Goal**
Add the two charts that make the comparison readable and save the deliverable.

**Tasks for the agent**
- [ ] TASK-06-01: On `TOU Comparison`, insert a **clustered column chart** showing Δ% for revenue, IRR (pp), NPV, DSCR for both Excel and Python computations side by side.
- [ ] TASK-06-02: On a new `Avg Day Dispatch` sheet, build a 24-row table with hour, solar generation kWh, BESS charge kWh, BESS discharge kWh, grid import kWh — averaged across the year — for each scenario (use `AVERAGEIFS` over the hourly dispatch sheet). Insert a **stacked area chart** for each scenario.
- [ ] TASK-06-03: Reset `TOU_VERSION = 2024` (default to baseline so the workbook opens in the audited state).
- [ ] TASK-06-04: `Save As` → `data/AUDIT 20260504 40MW Ecoplexus TOU2024-vs-2026.xlsx`. Do NOT overwrite the source file.

**Exit Criteria**
- [ ] Both charts render with correct axis labels and legends.
- [ ] New file exists at the target path; original audit file unchanged (verify file size + timestamp).
- [ ] `TOU_VERSION` defaults to 2024 on reopen.

## Verification Strategy

- **TEST-001:** Refactor neutrality — under `TOU_VERSION = 2024`, every KPI matches the original audited workbook to ±0.01%.
- **TEST-002:** Python reconciliation — under `TOU_VERSION = 2026`, every KPI matches `results/new_tariff/ecoplexus_tou2026.json` within CON-001 tolerance bands.
- **TEST-003:** Solar invariance — Year-1 solar MWh identical across scenarios (ASM-004 guard).
- **TEST-004:** BESS cycle count — daily cycles drop from 2 → 1 between TOU 2024 and TOU 2026.
- **MANUAL-001:** A human opens the deliverable, toggles `TOU_VERSION`, and confirms every chart and KPI updates without manual intervention.

## What to Hand Claude for Excel at Kickoff

The agent runs inside the workbook and cannot read repo files. Provide it (paste into the chat alongside attaching the workbook):

1. The full text of `docs/vietnam_tou_2026.md` (so it has the new schedule + integer-hour rounding convention).
2. The contents of `results/baseline/ecoplexus_tou2024.json` and `results/new_tariff/ecoplexus_tou2026.json` (validation targets for PHASE-05).
3. The "Per-Case Results" and "Revenue Decomposition By Driver" tables from `results/vietnam_tou2026_impact_report.md` (for the Ecoplexus row).
4. This plan.

## Risks and Alternatives

- **RISK-001:** The audit workbook may have hard-coded the two-cycle BESS dispatch in a way that doesn't gracefully collapse to one cycle. Mitigation: PHASE-04 includes an explicit cycle-count check; if dispatch logic doesn't adapt, escalate — the user must decide whether to keep the existing rule (sub-optimal under TOU 2026) or introduce a new dispatch heuristic.
- **RISK-002:** Excel-vs-Python KPI drift may exceed CON-001 tolerance because the Python model uses 8760-hour exact arithmetic while the Excel model may aggregate at month level. Mitigation: report the drift, decide whether to widen the tolerance or refactor the Excel aggregation grain.
- **RISK-003:** Tariff multiplier uncertainty (per `docs/2026-04-25_vietnam-tou-rooftop-ppa.md`, MOIT has not confirmed Decision 14/2025 multipliers carry over to Decision 963 windows). Mitigation: ASM-002 documents the assumption; the deliverable supports a follow-up sensitivity by editing the per-period prices on `Tariff Schedule 2026`.
- **ALT-001:** Build a fully formula-coupled snapshot (TOU 2024 and TOU 2026 KPIs both live in the comparison table simultaneously, no toggle) by hard-duplicating the dispatch + settlement block. Rejected: doubles workbook size, breaks audit traceability, and Claude for Excel handles the toggle-and-snapshot pattern adequately.
- **ALT-002:** Run the analysis in the existing Python pipeline and only display results in Excel. Rejected: that is the showcase plan (`plans/2026-05-04-tou-analysis-excel-showcase-plan.md`), a separate deliverable.

## Grill Me

- Should the agent extend the analysis to the **Emivest** rooftop cases as well? They are not in the workbook in `data/` and would require the user to provide the Emivest workbook. Default: out of scope for this plan.
- Should ASM-002 be relaxed to also test a multiplier sensitivity (e.g., +10% on the new peak rate)? Default: no — keep this plan as the windows-only case; spawn a separate sensitivity plan if needed.

## Suggested Next Step

Open `data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx` in Excel with the Claude for Excel add-in active. Paste the kickoff bundle from "What to Hand Claude for Excel at Kickoff" into the chat. Direct the agent to start at PHASE-01.

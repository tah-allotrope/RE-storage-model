---
title: "Sprint 2: Onsite vs Offsite DPPA Configuration + Annual Proforma Export"
date: "2026-05-22"
status: "draft"
request: "GAP-02 (onsite/offsite config) + GAP-04 (annual proforma export) from DPPA assessment gap analysis"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-05-22-dppa-assessment-excel-gap-analysis.md"
  - "research/2026-05-07_vietnam-tou-tariff-impact.md"
---

# Plan: Sprint 2 — Onsite vs Offsite DPPA Configuration + Annual Proforma Export

## Objective

Add a `dppa_topology` parameter ("onsite" / "offsite") that controls which revenue streams are active per run, and wire the annual proforma DataFrame into the Excel writer's assessment sheet with full financial detail. After this sprint, the assessment workbook can show side-by-side onsite and offsite DPPA results with year-by-year financials.

## Context Snapshot
- **Current state:** The pipeline runs all 4 PPA options but treats every run identically — grid savings, demand charge savings, and DPPA revenue are always computed regardless of physical topology. The `_annual_df` contains a full waterfall (revenue → EBITDA → CFADS → equity) but is only consumed by JSON serialization, not the Excel writer (built in Sprint 1).
- **Desired state:** A `dppa_topology` parameter on `run_full_model()` and `run_model_from_json()` that toggles revenue streams. The assessment script generates two assessment sheets ("Onsite DPPA" and "Offsite DPPA") in the same workbook. Each sheet includes a formatted 25-year annual proforma table.
- **Key repo surfaces:**
  - `src/re_storage/pipeline.py` — `run_full_model()` at line 920, `run_model_from_json()`, `_run_settlement()`, `_run_financial()`
  - `src/re_storage/settlement/grid.py` — `calculate_grid_savings()`, `calculate_bau_expense()`
  - `src/re_storage/settlement/demand_charge.py` — `calculate_annual_demand_savings()`
  - `src/re_storage/settlement/dppa.py` — `calculate_dppa_revenue()`
  - `src/re_storage/scenarios/runner.py` — `run_all_scenarios()`
  - `src/re_storage/financial/waterfall.py` — `build_cash_flow_waterfall()` output schema
  - `src/re_storage/reporting/excel_writer.py` — Sprint 1 output: `write_assessment_sheet()`
  - `scripts/generate_dppa_assessment.py` — Sprint 1 output
- **Out of scope:** Two-component tariff (Sprint 4), wind generation (backlog), factory-side NPV (backlog).

## Research Inputs
- `reports/2026-05-22-dppa-assessment-excel-gap-analysis.md` — Defines onsite = behind-the-meter (Options 1, 2) with grid savings + demand charge reduction; offsite = virtual PPA / front-of-meter (Options 3, 4) with no grid savings.
- `research/2026-05-07_vietnam-tou-tariff-impact.md` — Notes that the two-component tariff pilot would make demand charge savings material for onsite. Not in scope for Sprint 2 but informs the design: the topology flag should be extensible to handle 2-component tariff later.

## Assumptions and Constraints
- **ASM-001:** Onsite topology means: grid savings ARE included, demand charge savings ARE included (if Cp > 0), PPA options 1 (Bundled) and 2 (Separate) are the natural comparisons. Options 3 and 4 can still be run for reference.
- **ASM-002:** Offsite topology means: grid savings are ZEROED (generation goes to grid, not load), demand charge savings are ZEROED, PPA options 3 (DPPA CfD) and 4 (Fixed EVN) are the natural comparisons. Options 1 and 2 can still be run but will produce lower values (no grid offset benefit).
- **ASM-003:** The topology flag does NOT change physics — solar generation and BESS dispatch remain the same. It only changes which revenue streams enter the financial waterfall.
- **CON-001:** Sprint 1 (Excel writer + payback metrics) must be complete before the assessment script can produce dual-topology workbooks.
- **DEC-001:** Topology is a string literal, not an enum. Values: `"onsite"`, `"offsite"`. Default is `"onsite"` to preserve backward compatibility.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Add topology parameter to pipeline | None | Modified `pipeline.py`, new tests |
| PHASE-02 | Wire topology into scenario runner | PHASE-01 | Modified `scenarios/runner.py`, tests |
| PHASE-03 | Enhanced proforma in Excel writer + dual-topology assessment script | PHASE-01, PHASE-02, Sprint 1 | Modified `excel_writer.py`, updated script |

## Detailed Phases

### PHASE-01 — Topology Parameter in Pipeline
**Goal**
Add a `dppa_topology` parameter to the public pipeline API that controls revenue stream inclusion.

**Tasks**
- [ ] TASK-01-01: Add `dppa_topology: str = "onsite"` parameter to `run_full_model()` signature in `src/re_storage/pipeline.py`.
- [ ] TASK-01-02: Add `dppa_topology: str = "onsite"` parameter to `run_model_from_json()` signature.
- [ ] TASK-01-03: In `_run_settlement()`, after computing grid savings and demand charge savings, apply topology masking:
  ```python
  if dppa_topology == "offsite":
      # Zero out grid savings — generation goes to grid, not load
      settlement_result["grid_savings_usd"] = 0.0
      # Zero out demand charge savings — no behind-the-meter peak shaving
      demand_charge_savings = 0.0
  ```
- [ ] TASK-01-04: Pass `dppa_topology` through `_run_settlement()` and into `_run_financial()` so the value is recorded in the results dict as `results["dppa_topology"] = dppa_topology`.
- [ ] TASK-01-05: Validate `dppa_topology` value at the top of each public function — raise `ValueError` if not in `{"onsite", "offsite"}`.
- [ ] TASK-01-06: Write `tests/unit/test_pipeline_topology.py`:
  - `test_onsite_includes_grid_savings` — run with `dppa_topology="onsite"`, assert `year1_grid_savings_usd > 0`
  - `test_offsite_zeros_grid_savings` — run with `dppa_topology="offsite"`, assert `year1_grid_savings_usd == 0.0`
  - `test_offsite_zeros_demand_charge_savings` — assert demand charge savings are 0
  - `test_invalid_topology_raises` — assert `ValueError` for `"invalid"`
  - `test_default_topology_is_onsite` — assert default behavior unchanged
  - Use Emivest JSON fixture for test runs
- [ ] TASK-01-07: Run `pytest tests/unit/test_pipeline_topology.py -v` — all pass.
- [ ] TASK-01-08: Run `pytest tests/regression/test_emivest.py -q` — no regressions (default "onsite" preserves prior behavior).

**Files / Surfaces**
- `src/re_storage/pipeline.py` — add parameter, thread through internal functions, apply masking
- `tests/unit/test_pipeline_topology.py` — new file

**Dependencies**
- None

**Exit Criteria**
- [ ] `pytest tests/unit/test_pipeline_topology.py -v` → 5+ tests pass
- [ ] `pytest tests/regression/test_emivest.py -q` → no regressions
- [ ] `run_full_model(path, dppa_topology="offsite")` returns `year1_grid_savings_usd == 0.0`

**Phase Risks**
- **RISK-01-01:** Zeroing grid savings for offsite may cause equity_irr to become NaN if revenue drops below OPEX. Mitigation: this is correct behavior for an unviable offsite project — the assessment should show it.

---

### PHASE-02 — Topology in Scenario Runner
**Goal**
Thread topology through `run_all_scenarios()` and `run_sensitivity_for_values()` so multi-scenario comparison respects the topology setting.

**Tasks**
- [ ] TASK-02-01: Add `dppa_topology: str = "onsite"` parameter to `run_all_scenarios()` in `src/re_storage/scenarios/runner.py`. Pass it through to `run_full_model()` / `run_model_from_json()` calls.
- [ ] TASK-02-02: Add `dppa_topology: str = "onsite"` parameter to `run_sensitivity()` and `run_sensitivity_for_values()` in `src/re_storage/scenarios/sensitivity.py`. Pass through to pipeline calls.
- [ ] TASK-02-03: Each scenario result dict should include `"dppa_topology": topology` for traceability.
- [ ] TASK-02-04: Add tests to `tests/unit/test_scenarios_sensitivity.py`:
  - `test_run_all_scenarios_offsite_zeros_grid_savings` — verify all 4 options have `year1_grid_savings_usd == 0.0` when topology is offsite
  - `test_sensitivity_respects_topology` — verify sensitivity sweep with offsite topology
- [ ] TASK-02-05: Run `pytest tests/unit/test_scenarios_sensitivity.py -v` — all pass.

**Files / Surfaces**
- `src/re_storage/scenarios/runner.py` — add parameter, pass through
- `src/re_storage/scenarios/sensitivity.py` — add parameter, pass through
- `tests/unit/test_scenarios_sensitivity.py` — extend with topology tests

**Dependencies**
- PHASE-01 (pipeline must accept topology parameter)

**Exit Criteria**
- [ ] `pytest tests/unit/test_scenarios_sensitivity.py -v` → all pass including new topology tests
- [ ] `run_all_scenarios(project_dir=..., dppa_topology="offsite")` returns 4 results, all with `year1_grid_savings_usd == 0.0`

**Phase Risks**
- **RISK-02-01:** Running all 4 scenarios × 2 topologies in tests is slow (~60s). Mitigation: topology tests can use a single PPA option (`ppa_options=[3]`) to reduce test time.

---

### PHASE-03 — Enhanced Proforma + Dual-Topology Assessment Script
**Goal**
Enhance the Excel writer's assessment sheet with detailed proforma rows, and update the CLI script to produce a workbook with both onsite and offsite assessment sheets.

**Tasks**
- [ ] TASK-03-01: Enhance `write_assessment_sheet()` in `src/re_storage/reporting/excel_writer.py` to write the full annual proforma from `_annual_df`:
  - Revenue breakdown: DPPA Revenue, Grid Savings, Demand Charge Savings, Total Revenue
  - OPEX breakdown: O&M, Insurance, Land Lease, Management Fees, Total OPEX
  - EBITDA
  - Taxes, MRA Contribution
  - CFADS
  - Debt Service: Interest, Principal, Total Debt Service
  - DSCR
  - Free Cash Flow to Equity
  - CAPEX
  - Row grouping: Revenue block, OPEX block, Cash Flow block, Debt block
  - Section headers with bold formatting and colored fill
  - Totals row with SUM-equivalent values (Python-computed, not Excel formulas)
- [ ] TASK-03-02: Add a `write_proforma_section()` internal helper that takes a DataFrame subset and writes it with proper number formatting, alternating row fills, and section headers.
- [ ] TASK-03-03: Update `scripts/generate_dppa_assessment.py` to run the pipeline twice:
  1. `run_full_model(..., dppa_topology="onsite")` → write "Onsite DPPA" assessment sheet
  2. `run_full_model(..., dppa_topology="offsite")` → write "Offsite DPPA" assessment sheet
  3. `run_all_scenarios(..., dppa_topology="onsite")` → onsite comparison
  4. `run_all_scenarios(..., dppa_topology="offsite")` → offsite comparison
  5. Write both comparison tables into the Comparison sheet (stacked: onsite block, then offsite block, with a section divider)
  6. Sensitivity runs use onsite topology by default (configurable via `--topology` flag)
- [ ] TASK-03-04: Add `--topology` CLI argument to `scripts/generate_dppa_assessment.py` with values `"both"` (default), `"onsite"`, `"offsite"`. When `"both"`, produce both assessment sheets. When single, produce only one.
- [ ] TASK-03-05: Update `tests/unit/test_excel_writer.py`:
  - `test_assessment_sheet_has_proforma_revenue_rows` — verify revenue breakdown rows present
  - `test_assessment_sheet_has_proforma_opex_rows` — verify OPEX breakdown rows present
  - `test_assessment_sheet_totals_row` — verify totals present
- [ ] TASK-03-06: Update `tests/integration/test_dppa_assessment_script.py`:
  - `test_dual_topology_workbook` — verify output has both "Onsite DPPA" and "Offsite DPPA" sheets
  - `test_onsite_only_workbook` — verify `--topology onsite` produces only one assessment sheet
- [ ] TASK-03-07: Run integration test and manually verify the output workbook.

**Files / Surfaces**
- `src/re_storage/reporting/excel_writer.py` — enhance `write_assessment_sheet()`, add `write_proforma_section()`
- `scripts/generate_dppa_assessment.py` — dual-topology orchestration
- `tests/unit/test_excel_writer.py` — extend
- `tests/integration/test_dppa_assessment_script.py` — extend

**Dependencies**
- PHASE-01 (topology in pipeline)
- PHASE-02 (topology in scenario runner)
- Sprint 1 PHASE-02 (Excel writer exists)
- Sprint 1 PHASE-03 (CLI script exists)

**Exit Criteria**
- [ ] `python scripts/generate_dppa_assessment.py --input tests/data/projects/emivest/ --project-name "Test" --topology both` → produces workbook with "Onsite DPPA" and "Offsite DPPA" sheets
- [ ] Each assessment sheet has 25 proforma data rows with revenue, OPEX, and cash flow breakdowns
- [ ] Comparison sheet shows both onsite and offsite scenario tables
- [ ] Onsite sheet has non-zero grid savings; Offsite sheet has zero grid savings
- [ ] `pytest tests/ -q --ignore=tests/unit/test_battery.py` → no regressions

**Phase Risks**
- **RISK-03-01:** Running 2 topologies × 4 scenarios × pipeline = 8 full runs. Script execution time ~2-4 minutes. Mitigation: add a progress logger to the script. Consider caching the physics stage (same for both topologies) in a future optimization.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_pipeline_topology.py -v` — topology unit tests
- **TEST-002:** `pytest tests/unit/test_scenarios_sensitivity.py -v` — scenario topology tests
- **TEST-003:** `pytest tests/unit/test_excel_writer.py -v` — proforma formatting tests
- **TEST-004:** `pytest tests/integration/test_dppa_assessment_script.py -v` — end-to-end dual-topology
- **TEST-005:** `pytest tests/regression/test_emivest.py -q` — no regressions
- **MANUAL-001:** Open generated workbook, verify that "Onsite DPPA" sheet shows positive grid savings and "Offsite DPPA" sheet shows zero grid savings in Year 1.

## Risks and Alternatives
- **RISK-001:** Offsite topology with Options 1/2 (Bundled/Separate) will produce lower revenue than onsite because those options depend on direct PV consumption behind the meter. The assessment should note this in the Methodology sheet rather than hiding it.
- **ALT-001:** Could model onsite/offsite as entirely separate pipeline entry points (two different functions). Not chosen because the physics and dispatch are identical — only the revenue stream selection changes, which is a thin orchestration layer.

## Grill Me
1. **Q-001:** For offsite topology, should the BESS dispatch strategy change (e.g., pure arbitrage instead of peak shaving), or keep the same dispatch and just zero out grid savings?
   - **Recommended default:** Keep the same dispatch strategy. The BESS dispatch is driven by `strategy_mode` in the input assumptions, which the user controls independently.
   - **Why this matters:** If dispatch should change, we need to modify `BatteryConfig` per topology, adding complexity.
   - **If answered differently:** If dispatch changes per topology, add a `_select_dispatch_strategy(topology)` helper in the pipeline.

## Suggested Next Step
Complete Sprint 1 first. Then begin PHASE-01 and PHASE-02 of this sprint (they can be parallelized after PHASE-01 is done). PHASE-03 depends on both.

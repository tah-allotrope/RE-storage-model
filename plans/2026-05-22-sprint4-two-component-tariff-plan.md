---
title: "Sprint 4: Two-Component Tariff Settlement Path"
date: "2026-05-22"
status: "draft"
request: "GAP-07 (two-component tariff) from DPPA assessment gap analysis"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-05-22-dppa-assessment-excel-gap-analysis.md"
  - "research/2026-05-07_vietnam-tou-tariff-impact.md"
---

# Plan: Sprint 4 — Two-Component Tariff Settlement Path

## Objective

Add support for Vietnam's Decree 146/2025 two-component tariff (capacity charge Cp + lower energy charges Ca), enabling accurate DPPA assessment for clients whose offtakers are in the pilot scope (22 kV+, ≥200 MWh/month). This makes the BESS demand-charge reduction a material revenue driver in the assessment workbook.

## Context Snapshot
- **Current state:** The settlement layer computes grid savings using single-component energy rates (`tariff_rates` dict of `TimePeriod → USD/kWh`). The `demand_charge.py` module exists and computes demand charge savings, but always receives `cp_demand_vnd_per_kw = 0` for current projects, returning zero savings. The Emivest JSON fixture already encodes `retail_tariff_matrix` with two-component pilot rates (Cp=235,414 VND/kW/month, Ca_normal=1,275 VND/kWh).
- **Desired state:** A `tariff_mode` parameter ("1-component" / "2-component") that switches energy rates to Ca values and activates Cp demand charge savings. The assessment workbook shows the impact of two-component tariff on project economics.
- **Key repo surfaces:**
  - `src/re_storage/settlement/grid.py` — `calculate_bau_expense()`, `calculate_grid_savings()`
  - `src/re_storage/settlement/demand_charge.py` — `calculate_annual_demand_savings()` (ready, just needs non-zero Cp)
  - `src/re_storage/pipeline.py` — `_run_settlement()` where tariff rates are applied
  - `src/re_storage/inputs/schemas.py` — `SystemAssumptions` Pydantic model
  - `src/re_storage/inputs/json_loader.py` — `load_tariff_rates_from_json()`
  - `src/re_storage/inputs/loaders.py` — `load_tariff_rates_from_cells()`
  - `src/re_storage/aggregation/monthly.py` — `aggregate_hourly_to_monthly()` (produces peak demand data)
  - `research/2026-05-07_vietnam-tou-tariff-impact.md` — documents exact Cp and Ca values
- **Out of scope:** Circular 62/2025 BESS-specific two-part tariff (low confidence on rates), wind generation, factory NPV.

## Research Inputs
- `research/2026-05-07_vietnam-tou-tariff-impact.md` — Key data:
  - Two-component pilot rates at 22 kV: Cp = 235,414 VND/kW/month, Ca_normal = 1,275, Ca_peak = 2,182, Ca_offpeak = 859 VND/kWh
  - Energy rates are ~30-38% lower than single-component rates
  - Demand charge share of bill ≈ 29-35%
  - Pilot scope: ~7,000 manufacturing customers at 22 kV+, ≥200 MWh/month
  - Phase 3 actual billing starts July 2026
  - BESS gains demand-charge reduction value under two-component tariff

## Assumptions and Constraints
- **ASM-001:** Two-component tariff rates are sourced from published Decree 146 pilot values. The Emivest JSON fixture at `tests/data/projects/emivest/` already contains `retail_tariff_matrix` with these values.
- **ASM-002:** Demand charge savings = Σ_months [(baseline_peak_kW - post_RE_peak_kW) × Cp] / FX_rate. This formula is already implemented in `demand_charge.py`.
- **ASM-003:** The two-component tariff ONLY affects onsite topology projects. Offsite projects sell to grid at FMP/CfD and do not pay retail tariff.
- **CON-001:** Sprints 1-3 must be complete before this sprint can be fully integrated into the assessment workbook.
- **DEC-001:** `tariff_mode` is a string parameter: `"1-component"` (default) or `"2-component"`. Not an enum to keep the API simple.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Add tariff mode to pipeline | None | Modified `pipeline.py`, `schemas.py`, tests |
| PHASE-02 | Load two-component rates from inputs | PHASE-01 | Modified loaders, tests |
| PHASE-03 | Wire into assessment workbook + comparison | PHASE-01, PHASE-02, Sprint 3 | Updated script, new sensitivity variable |

## Detailed Phases

### PHASE-01 — Tariff Mode in Pipeline
**Goal**
Add a `tariff_mode` parameter that switches between single-component and two-component energy rates and activates demand charge computation.

**Tasks**
- [ ] TASK-01-01: Add `tariff_mode: str = "1-component"` to `SystemAssumptions` in `src/re_storage/inputs/schemas.py`. Add `cp_demand_vnd_per_kw: float = 0.0` and `exchange_rate_usd_vnd: float = 25_000.0` fields (with defaults that preserve current behavior).
- [ ] TASK-01-02: Add `tariff_mode: str = "1-component"` parameter to `run_full_model()` and `run_model_from_json()` in `src/re_storage/pipeline.py`.
- [ ] TASK-01-03: In `_run_settlement()`, when `tariff_mode == "2-component"`:
  - Use Ca-rate tariff dict instead of standard tariff dict for `calculate_bau_expense()` and `calculate_re_expense()`
  - Pass non-zero `cp_demand_vnd_per_kw` to `calculate_annual_demand_savings()`
  - The Ca rates and Cp value come from the assumptions or financial params
- [ ] TASK-01-04: Add validation: `tariff_mode` must be in `{"1-component", "2-component"}`. Raise `ValueError` otherwise.
- [ ] TASK-01-05: When `tariff_mode == "2-component"`, record `results["tariff_mode"] = "2-component"` and `results["demand_charge_savings_usd"] = demand_savings_value`.
- [ ] TASK-01-06: Write `tests/unit/test_pipeline_tariff_mode.py`:
  - `test_1component_default_no_demand_savings` — default mode returns zero demand charge savings
  - `test_2component_activates_demand_savings` — 2-component mode with Cp > 0 returns positive demand charge savings
  - `test_2component_lowers_energy_rates` — grid savings differ from 1-component (Ca rates are lower)
  - `test_invalid_tariff_mode_raises` — ValueError for bad input
- [ ] TASK-01-07: Run tests — all pass.

**Files / Surfaces**
- `src/re_storage/inputs/schemas.py` — add `tariff_mode`, `cp_demand_vnd_per_kw`, `exchange_rate_usd_vnd`
- `src/re_storage/pipeline.py` — add parameter, conditional rate selection
- `tests/unit/test_pipeline_tariff_mode.py` — new file

**Dependencies**
- None

**Exit Criteria**
- [ ] `pytest tests/unit/test_pipeline_tariff_mode.py -v` → 4+ tests pass
- [ ] Default behavior (1-component) produces identical output to current pipeline
- [ ] 2-component mode produces non-zero demand charge savings when Cp > 0

**Phase Risks**
- **RISK-01-01:** Adding `tariff_mode` to `SystemAssumptions` with `extra="forbid"` may break existing JSON fixtures that don't include the field. Mitigation: use `default="1-component"` so the field is optional.

---

### PHASE-02 — Load Two-Component Rates from Inputs
**Goal**
Enable JSON and Excel loaders to supply Ca-rate tariff dicts and Cp values when two-component tariff is selected.

**Tasks**
- [ ] TASK-02-01: Update `load_tariff_rates_from_json()` in `src/re_storage/inputs/json_loader.py`:
  - When `tariff_mode == "2-component"` is indicated in the project JSON, load from `retail_tariff_matrix` keys: `Ca_normal`, `Ca_peak`, `Ca_offpeak`
  - Return a separate `ca_tariff_rates` dict alongside the standard `tariff_rates`
  - Load `Cp_demand` value from `retail_tariff_matrix`
- [ ] TASK-02-02: Update `load_tariff_rates_from_cells()` in `src/re_storage/inputs/loaders.py`:
  - The function already supports Ca-style labels (`Ca_normal/Ca_peak/Ca_offpeak`) added in ISSUE-2
  - Add a return key `cp_demand_vnd_per_kw` extracted from `Other Input` or `Assumption` sheet if present
  - Return both standard and Ca tariff rate dicts
- [ ] TASK-02-03: Update `load_financial_params_from_cells()` to return `tariff_mode` if detectable from the workbook (e.g., presence of Cp value in the tariff section).
- [ ] TASK-02-04: Update pipeline to use the appropriate tariff dict based on `tariff_mode`:
  ```python
  if tariff_mode == "2-component" and ca_tariff_rates:
      effective_tariff_rates = ca_tariff_rates
  else:
      effective_tariff_rates = tariff_rates
  ```
- [ ] TASK-02-05: Write/extend `tests/unit/test_json_loader.py`:
  - `test_load_ca_tariff_rates_from_emivest` — verify Ca rates extracted from retail_tariff_matrix
  - `test_load_cp_from_emivest` — verify Cp value extracted
- [ ] TASK-02-06: Write/extend `tests/unit/test_inputs_loaders.py`:
  - `test_load_ca_labels_tariff` — verify Ca-style labels produce correct tariff dict
- [ ] TASK-02-07: Run loader tests — all pass.

**Files / Surfaces**
- `src/re_storage/inputs/json_loader.py` — add Ca-rate and Cp loading
- `src/re_storage/inputs/loaders.py` — extend tariff loading
- `src/re_storage/pipeline.py` — use tariff_mode to select rate dict
- `tests/unit/test_json_loader.py` — extend
- `tests/unit/test_inputs_loaders.py` — extend

**Dependencies**
- PHASE-01 (pipeline accepts tariff_mode)

**Exit Criteria**
- [ ] JSON loader returns `ca_tariff_rates` and `cp_demand_vnd_per_kw` from Emivest fixture
- [ ] Pipeline uses Ca rates when `tariff_mode == "2-component"`
- [ ] All loader tests pass

**Phase Risks**
- **RISK-02-01:** The Emivest `retail_tariff_matrix` format may not match the expected key names exactly. Mitigation: inspect the actual fixture during implementation and adapt key mapping.

---

### PHASE-03 — Assessment Workbook Integration
**Goal**
Add two-component tariff as a scenario dimension in the assessment workbook, showing the impact alongside onsite/offsite topology.

**Tasks**
- [ ] TASK-03-01: Add `--tariff-mode` CLI argument to `scripts/generate_dppa_assessment.py` with values `"1-component"` (default), `"2-component"`, `"both"`. When `"both"`, run each topology under both tariff modes.
- [ ] TASK-03-02: When `tariff_mode == "both"`, add extra comparison rows in the Comparison sheet:
  - "Onsite (1-component)" vs "Onsite (2-component)" vs "Offsite (1-component)" vs "Offsite (2-component)"
  - This shows the tariff mode impact side-by-side with topology impact
- [ ] TASK-03-03: Add `tariff_mode` as a sensitivity variable in `src/re_storage/scenarios/sensitivity.py`:
  - This is a categorical variable (not a numeric sweep) — implement as a special case that runs the pipeline twice (1-component vs 2-component) and returns the delta
- [ ] TASK-03-04: Update `write_comparison_sheet()` in `excel_writer.py` to handle the expanded comparison matrix (topology × tariff mode × PPA option).
- [ ] TASK-03-05: Add a "Tariff Mode" row in the Assumptions sheet documenting which mode was used.
- [ ] TASK-03-06: Update integration test to verify 2-component tariff workbook generation.
- [ ] TASK-03-07: Run full test suite — no regressions.

**Files / Surfaces**
- `scripts/generate_dppa_assessment.py` — add `--tariff-mode` flag
- `src/re_storage/scenarios/sensitivity.py` — add categorical tariff_mode comparison
- `src/re_storage/reporting/excel_writer.py` — expand comparison sheet
- `tests/integration/test_dppa_assessment_script.py` — extend

**Dependencies**
- PHASE-01 (pipeline accepts tariff_mode)
- PHASE-02 (loaders supply Ca rates)
- Sprint 3 complete (workbook is fully functional)

**Exit Criteria**
- [ ] `python scripts/generate_dppa_assessment.py --input tests/data/projects/emivest/ --tariff-mode both --topology both` → workbook with 4 assessment sheets (2 topologies × 2 tariff modes)
- [ ] Comparison sheet shows demand charge savings > 0 for 2-component onsite rows
- [ ] Comparison sheet shows demand charge savings = 0 for 1-component and offsite rows
- [ ] `pytest tests/ -q --ignore=tests/unit/test_battery.py` → no regressions

**Phase Risks**
- **RISK-03-01:** Running 2 topologies × 2 tariff modes × 4 PPA options = 16 pipeline runs. Script takes ~4-8 minutes. Mitigation: show progress to user, consider limiting PPA options per topology (onsite: 1,2; offsite: 3,4).
- **RISK-03-02:** The expanded comparison matrix (16 columns) may be too wide for a single Excel sheet. Mitigation: stack vertically (one section per topology, with 1-component vs 2-component columns within each section).

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_pipeline_tariff_mode.py -v` — tariff mode unit tests
- **TEST-002:** `pytest tests/unit/test_json_loader.py tests/unit/test_inputs_loaders.py -v` — loader tests
- **TEST-003:** `pytest tests/integration/test_dppa_assessment_script.py -v` — end-to-end
- **TEST-004:** `pytest tests/ -q --ignore=tests/unit/test_battery.py` — full suite
- **MANUAL-001:** Open workbook, verify demand charge savings column is non-zero in 2-component onsite rows and zero in 1-component/offsite rows.
- **MANUAL-002:** Compare total project economics: 2-component should show lower grid energy savings but positive demand charge savings, with a net effect depending on the project's peak demand profile.

## Risks and Alternatives
- **RISK-001:** Two-component pilot rates may change before July 2026 billing launch. Mitigation: rates are parameterized, not hardcoded — they can be updated in the input fixture without code changes.
- **ALT-001:** Could model two-component tariff as a completely separate settlement module rather than a mode flag. Not chosen because the math is the same (energy × rate + demand × Cp) — only the rate values change. A mode flag is simpler and avoids code duplication.

## Grill Me
1. **Q-001:** Is the client's offtaker confirmed to be in the two-component pilot scope (22 kV+, ≥200 MWh/month)?
   - **Recommended default:** Include both tariff modes in the assessment workbook as a comparison, regardless of confirmation. This shows the client the impact of the upcoming tariff change.
   - **Why this matters:** If the offtaker is NOT in scope, the two-component results are hypothetical. The Methodology sheet should state this.
   - **If answered differently:** If confirmed in scope, make 2-component the default and 1-component the sensitivity comparison.

2. **Q-002:** Should the Cp demand charge value (235,414 VND/kW/month at 22 kV) be hardcoded from the research brief, or loaded from the input JSON/Excel?
   - **Recommended default:** Load from input (the Emivest fixture already has it). Hardcode only as fallback default.
   - **Why this matters:** Different voltage tiers have different Cp values. A 110 kV client would have a lower Cp.
   - **If answered differently:** If hardcoded, the workbook only works for 22 kV projects without manual editing.

## Suggested Next Step
Complete Sprints 1-3 first. Then begin PHASE-01 and PHASE-02 (they can overlap once PHASE-01 is done). PHASE-03 integrates everything into the final workbook.

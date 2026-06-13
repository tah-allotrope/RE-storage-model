---
title: "Web GAP-03: Expose Two-Component Tariff Path"
date: "2026-06-13"
status: "draft"
request: "Create a multi-phase plan for GAP-03 (two-component tariff) from reports/2026-06-13-reopt-web-interface-gap-analysis.md"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-06-13-reopt-web-interface-gap-analysis.md"
---

# Plan: Web GAP-03: Expose Two-Component Tariff Path

## Objective
Make the Sprint 4 two-component tariff (Ca energy + Cp demand charge) reachable from the web tool. The pipeline fully supports `tariff_mode`, `cp_demand_vnd_per_kw`, `ca_tariff_rates`, surfaces `demand_charge_savings_usd`, and ships a categorical `run_tariff_mode_comparison()` — but the web form hardcodes `"1-component"` and `Cp_demand: 0.0`, so the most recent shipped feature is completely dark in the UI.

## Context Snapshot
- **Current state:** [web/functions/handlers/project_payload.py:104](../web/functions/handlers/project_payload.py) hardcodes `"tariff_structure": "1-component"` and `Cp_demand: 0.0`. `tariff_mode`/`cp_demand_vnd_per_kw` are never read from the form; `demand_charge_savings_usd` is always zero. `run_tariff_mode_comparison()` ([sensitivity.py:723](../src/re_storage/scenarios/sensitivity.py)) is unused by any handler.
- **Desired state:** Form exposes a tariff-mode selector (1-component / 2-component / both) plus Cp demand and Ca-rate inputs; `tariff_mode`/`cp_demand_vnd_per_kw` thread through `build_project_payload` and all run/scenario/sensitivity handlers; a tariff-mode comparison view shows the demand-charge-savings delta via `run_tariff_mode_comparison()`.
- **Key repo surfaces:** `run_model_from_json`/`run_full_model` (already accept `tariff_mode`, `cp_demand_vnd_per_kw`, `ca_tariff_rates`), `run_all_scenarios`/`run_tariff_mode_comparison` (accept `tariff_mode`), `project_payload.py`, `DppaStep.tsx`, `formTypes.ts`, `ScenarioComparisonTable.tsx`, `serialise.py` (already lists `demand_charge_savings_usd` in `ANNUAL_COLUMNS`).
- **Out of scope:** Auto-loading Ca/Cp from an uploaded EVN tariff matrix beyond what `retail_tariff_matrix` already supports; onsite/offsite topology (GAP-06).

## Research Inputs
- [reports/2026-06-13-reopt-web-interface-gap-analysis.md](../reports/2026-06-13-reopt-web-interface-gap-analysis.md) — GAP-03 (HIGH). Confirms the hardcode location and that Sprint 4 pipeline/loader support + `run_tariff_mode_comparison` already exist.
- [activeContext.md](../activeContext.md) — Sprint 4 reality: `retail_tariff_matrix.tariff_options` is keyed by `voltage_level` (e.g. `"22kV-2-component"`); Ca rates → USD/kWh by dividing by `exchange_rate_USD_VND`; 22 kV connection. Loader auto-loads 2-component rates when `tariff_mode="2-component"` and rates not passed.

## Assumptions and Constraints
- **DEC-001:** When `tariff_mode="2-component"` and Ca/Cp not explicitly passed, `run_model_from_json` auto-loads them from `retail_tariff_matrix` (Sprint 4 PHASE-02) — the form can rely on this rather than requiring every rate.
- **ASM-001:** The structured payload's `grid_connection_and_tariff.tariff_structure` and `evn_retail_tariff_VND.Cp_demand` are the fields the loader reads; setting these correctly is sufficient to activate 2-component.
- **CON-001:** `_validate_tariff_mode` raises `ValueError` for anything outside `{1-component, 2-component}`; the "both" UI option maps to a comparison call, not a single `tariff_mode` value.
- **DEC-002:** `demand_charge_savings_usd` is already a serialised annual column and a top-level KPI — no serialiser change needed to display it once it's non-zero.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Thread tariff_mode/Cp through payload + run handlers | None | Parameterised `build_project_payload`; 2-component runs work |
| PHASE-02 | Form fields for tariff mode + Cp/Ca rates | PHASE-01 | `DppaStep.tsx` controls; `formTypes.ts` defaults |
| PHASE-03 | Tariff-mode comparison view (both modes + delta) | PHASE-01 | `/api/compare-tariff-modes`; comparison UI |

## Detailed Phases

### PHASE-01 - Backend: parameterise the tariff path
**Goal**
`build_project_payload` honors a tariff mode and Cp demand value; handlers pass them through.

**Tasks**
- [ ] TASK-01-01: In [project_payload.py](../web/functions/handlers/project_payload.py), replace the hardcoded `"tariff_structure": "1-component"` with `to_str(form, "tariff_mode", "1-component")` and set `Cp_demand` from `to_float(form, "cp_demand_vnd_per_kw", 0.0)`.
- [ ] TASK-01-02: Allow Ca rate overrides (`Ca_normal/Ca_peak/Ca_offpeak`) from the form while keeping current defaults; otherwise rely on auto-load.
- [ ] TASK-01-03: Validate `tariff_mode ∈ {1-component, 2-component}` in the handler and return 400 on bad input (mirror `_validate_tariff_mode`).
- [ ] TASK-01-04: Confirm `run_model_from_json` picks up the mode from the payload (no extra kwarg needed) and that `demand_charge_savings_usd` becomes non-zero for a 2-component Emivest run.

**Files / Surfaces**
- `web/functions/handlers/project_payload.py`, `web/functions/handlers/run_json.py`, `tests/unit/test_web_handlers.py`.

**Dependencies**
- None.

**Exit Criteria**
- [ ] New unit test: a 2-component payload yields `kpis.demand_charge_savings_usd > 0` and `kpis.tariff_mode == "2-component"`.
- [ ] A 1-component payload is unchanged (regression guard).

**Phase Risks**
- **RISK-01-01:** Voltage-tier matching — non-22kV connections may lack a `2-component` entry in `retail_tariff_matrix`; surface the loader's error/warning to the client rather than silently running 1-component.

### PHASE-02 - Frontend: tariff-mode and demand inputs
**Goal**
Users select tariff mode and enter Cp demand + Ca rates in the DPPA step.

**Tasks**
- [ ] TASK-02-01: Add `tariff_mode` (select: `1-component`/`2-component`/`both`), `cp_demand_vnd_per_kw`, and `evn_tariff_standard_vnd`/`peak`/`offpeak` fields to [formTypes.ts](../web/frontend/src/components/inputs/formTypes.ts) with sensible defaults (e.g. `tariff_mode="1-component"`, Cp from a 22kV reference).
- [ ] TASK-02-02: Render the controls in [DppaStep.tsx](../web/frontend/src/components/inputs/DppaStep.tsx); show Cp/Ca inputs only when mode ≠ `1-component`.
- [ ] TASK-02-03: When `tariff_mode="both"`, route the run to the comparison endpoint (PHASE-03) instead of `/api/run-json`.
- [ ] TASK-02-04: Display `demand_charge_savings_usd` as a KPI card in [KpiGrid.tsx](../web/frontend/src/components/results/KpiGrid.tsx)/`ResultsDashboard.tsx` (annual chart already supports the column).

**Files / Surfaces**
- `web/frontend/src/components/inputs/formTypes.ts`, `DppaStep.tsx`, `KpiGrid.tsx`, `ResultsDashboard.tsx`.

**Dependencies**
- PHASE-01.

**Exit Criteria**
- [ ] `npm run build` passes; selecting 2-component reveals Cp/Ca inputs and a non-zero demand-charge KPI after a run.

**Phase Risks**
- **RISK-02-01:** Unit confusion (VND/kW vs USD) — label every field with its unit; Ca inputs are VND, converted server-side.

### PHASE-03 - Tariff-mode comparison view
**Goal**
"Both" mode runs the pipeline under both tariffs and shows the delta.

**Tasks**
- [ ] TASK-03-01: Create `web/functions/handlers/compare_tariff_modes.py` calling `run_tariff_mode_comparison(project_dir=..., ppa_option=...)`; serialise `{"1-component", "2-component", "delta"}`.
- [ ] TASK-03-02: Register `compareTariffModes` in [main.py](../web/functions/main.py) and add `/api/compare-tariff-modes` to [firebase.json](../firebase.json).
- [ ] TASK-03-03: Add `compareTariffModes(formData)` to [api/client.ts](../web/frontend/src/api/client.ts) and reuse [ScenarioComparisonTable.tsx](../web/frontend/src/components/results/ScenarioComparisonTable.tsx) to show the two modes side-by-side with the demand-charge-savings delta row.

**Files / Surfaces**
- `web/functions/handlers/compare_tariff_modes.py` (new), `main.py`, `firebase.json`, `web/frontend/src/api/client.ts`, `ScenarioComparisonTable.tsx`, `useModelRun.ts`.

**Dependencies**
- PHASE-01, PHASE-02.

**Exit Criteria**
- [ ] Comparison view shows both modes' KPIs and a delta highlighting the demand-charge-savings trade-off (per the Sprint 4 Emivest result: ~$303.9k → ~$203.1k grid savings for ~$8.0k demand-charge savings).
- [ ] Unit test asserts the handler returns all three keys.

**Phase Risks**
- **RISK-03-01:** `run_tariff_mode_comparison` runs the model twice — keep within timeout; it is two runs, not a full sweep, so headroom is fine.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_web_handlers.py -v` — 2-component run produces demand-charge savings; comparison handler returns the delta.
- **MANUAL-001:** Run Emivest at 22kV in 2-component and confirm the demand-charge KPI and reduced grid-energy savings match the Sprint 4 report.
- **OBS-001:** Surface loader warnings (voltage-tier mismatch) in the API response so silent 1-component fallback is visible.

## Risks and Alternatives
- **RISK-001:** Hidden fallback to 1-component when a voltage tier lacks 2-component rates — mitigate by propagating loader warnings (ties to GAP analysis Risk R6/R8).
- **ALT-001:** Require users to enter all Ca/Cp rates manually. Rejected: the Sprint 4 auto-load from `retail_tariff_matrix` already does voltage-tier matching; manual entry is an override, not the default.

## Grill Me
1. **Q-001:** Confirm the target offtaker is in the 22 kV two-component pilot scope (open product question carried from Sprint 4 / activeContext Q-001).
   - **Recommended default:** Default UI to 1-component; expose 2-component as an opt-in.
   - **Why this matters:** Determines whether 2-component is the default mode or an advanced option, and which voltage tiers must have rates.
   - **If answered differently:** If 2-component is the primary scenario, make it the form default and ensure all supported voltage tiers have matrix entries.

## Suggested Next Step
Answer Q-001, then implement PHASE-01 with a TDD 2-component test against the Emivest fixture before adding form controls.

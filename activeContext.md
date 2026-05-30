# Active Context — Sprint 4: Two-Component Tariff Settlement Path

**Plan:** `plans/2026-05-22-sprint4-two-component-tariff-plan.md`
**Branch:** `sprint4-two-component-tariff`
**Grill-Me answers:** Q-001 default (include both tariff modes as comparison), Q-002 default (load Cp from input, hardcode fallback).
**Workflow:** TDD per phase → run tests → `/report` → git commit + push per phase.

## Fixture reality (adapted from plan)
`retail_tariff_matrix.tariff_options` is a **list keyed by `voltage_level`** (e.g. `"22kV-2-component"`), not flat keys. Each entry has `Ca_normal`/`Ca_peak`/`Ca_offpeak`/`Cp_demand` (all VND). The `22kV-1-component` entry has `active: true`. Emivest connection voltage = 22 kV. Ca rates → USD/kWh by dividing by `exchange_rate_USD_VND`.

## PHASE-01 — Tariff Mode in Pipeline ✅
- [x] Add `tariff_mode`, `cp_demand_vnd_per_kw`, `exchange_rate_usd_vnd` to `SystemAssumptions`
- [x] Add `tariff_mode` / `cp_demand_vnd_per_kw` / `ca_tariff_rates` params to `run_full_model` + `run_model_from_json`
- [x] Select Ca rates for settlement when 2-component; activate Cp demand savings
- [x] Validate `tariff_mode ∈ {1-component, 2-component}` → ValueError
- [x] Surface `results["tariff_mode"]`, `results["demand_charge_savings_usd"]`
- [x] `tests/unit/test_pipeline_tariff_mode.py` (4 tests) green
- [x] Verified no regressions: 17 pre-existing failures confirmed identical on baseline (pandas `freq="H"`, emivest 2-JSON dir, missing Ecoplexus workbook) — none caused by this change
- [x] Report: `reports/2026-05-30-sprint4-phase01.html`
- [x] Commit + push

## PHASE-02 — Load Two-Component Rates from Inputs ✅
- [x] `load_two_component_tariff_from_json()` → `ca_tariff_rates` + `cp_demand_vnd_per_kw` from `retail_tariff_matrix`, matched on connection voltage tier
- [x] Auto-wire JSON loader output into `run_model_from_json` (2-component mode loads rates when not passed)
- [x] Excel loader: `load_financial_params_from_cells` surfaces `cp_demand_vnd_per_kw` + `tariff_mode`; `load_tariff_rates_from_cells` already selects Ca rates
- [x] Extended `tests/unit/test_json_loader.py` (+2), `test_inputs_loaders.py` (+2), `test_pipeline_tariff_mode.py` (+1 autoload) — 51 passed / 3 skipped
- [x] Report: `reports/2026-05-31-sprint4-phase02.html`
- [x] Commit + push

## PHASE-03 — Assessment Workbook Integration
- [ ] `--tariff-mode {1-component,2-component,both}` in `scripts/generate_dppa_assessment.py`
- [ ] Thread `tariff_mode` through `run_all_scenarios` + `run_sensitivity_for_values`
- [ ] Comparison sheet shows demand-charge savings per mode
- [ ] Categorical `tariff_mode` sensitivity (run twice, return delta)
- [ ] Extend integration test
- [ ] Report + commit + push

## Review / Results
_(to be filled in after each phase)_

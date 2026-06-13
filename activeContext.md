# Active Context — GAP-03: Expose Two-Component Tariff Path (Web)

**Plan:** `plans/2026-06-13-web-two-component-tariff-plan.md`
**Gap analysis:** `reports/2026-06-13-reopt-web-interface-gap-analysis.md`
**Scope decision (Q-001):** Default UI to **1-component**; 2-component is an opt-in via a `tariff_mode` select. 22 kV reference rates seeded as defaults so the opt-in works out of the box on the Emivest fixture.
**Workflow:** TDD per phase → run tests → git commit + push per phase → final synthesis report at end.

## PHASE-01 — Backend: parameterise the tariff path ✅
- [x] `build_project_payload` reads `tariff_mode` (default `1-component`) and `cp_demand_vnd_per_kw` (default `0.0`) from the form
- [x] Replaced hardcoded `"tariff_structure": "1-component"` and `Cp_demand: 0.0`
- [x] New `resolve_tariff_mode(form)` helper validates against `VALID_TARIFF_MODES = {"1-component", "2-component"}` and raises `ValueError` (→ 400) on invalid input
- [x] Threaded `tariff_mode` + `cp_demand_vnd_per_kw` kwargs through all 5 backend handlers: `run_json`, `run_excel`, `run_report`, `export_workbook`, `compare_scenarios`, `run_sensitivity` (so 2-component honored across every web surface, not just `/api/run-json`)
- [x] Tests: 5 new (defaults regression, 2-component threading, invalid-mode rejection, handler passes kwarg, handler 400s on bad mode) + updated existing test fakes to accept `**kwargs` — **34 passed**
- [x] ruff clean

## PHASE-02 — Frontend: tariff-mode + demand inputs ✅
- [x] `formTypes.ts`: added `tariff_mode` (default `"1-component"`), `cp_demand_vnd_per_kw` (default `"0"`), `evn_tariff_off_peak_vnd`/`standard_vnd`/`peak_vnd` (seeded with 22 kV reference 1190 / 1833 / 3398 VND/kWh)
- [x] `DppaStep.tsx`: tariff-mode select (1-component / 2-component / Compare both); Cp + 3 Ca rate inputs grayed out when mode = `1-component` via the existing `field-disabled` pattern
- [x] `model.ts`: `ModelKpis` extended with optional `demand_charge_savings_usd` and `tariff_mode`
- [x] `KpiGrid.tsx`: Year-1 Demand Charge Savings card appears only when `kpis.tariff_mode === "2-component"` (single-mode runs); for `both`, PHASE-03's comparison view carries the delta
- [x] `npm run build` clean (no type errors, only pre-existing chunk-size warning)

## PHASE-03 — Tariff-mode comparison view
- [ ] `web/functions/handlers/compare_tariff_modes.py` calls `run_tariff_mode_comparison`, returns `{"1-component", "2-component", "delta"}`
- [ ] Register `compareTariffModes` in `main.py` + `/api/compare-tariff-modes` rewrite in `firebase.json`
- [ ] `api/client.ts`: `compareTariffModes(formData)`
- [ ] New `TariffModeComparison.tsx` showing both modes' headline KPIs + delta row highlighting demand-charge savings vs grid-savings trade-off
- [ ] Tests: handler returns all three keys

## Review / Results
(populated at end of sprint)

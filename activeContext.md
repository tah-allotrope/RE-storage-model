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

## PHASE-03 — Tariff-mode comparison view ✅
- [x] `web/functions/handlers/compare_tariff_modes.py` `handle_compare_tariff_modes(request)` calls `run_tariff_mode_comparison(project_dir, ppa_option)` and returns the `{"1-component", "2-component", "delta"}` payload with NaN sanitised to `null`
- [x] Registered `compareTariffModes` in `main.py` with `@cross_origin()`
- [x] Added `/api/compare-tariff-modes` rewrite to `firebase.json`
- [x] `api/client.ts`: `compareTariffModes(formData)` returns `TariffModeComparisonResponse`
- [x] `useModelRun`: when `formData.tariff_mode === "both"`, route to the comparison endpoint instead of `/api/run-json`; new `tariffComparison` state exposed
- [x] `model.ts`: `TariffModeKpis` (extends `Partial<ModelKpis>` + `error?`) and `TariffModeComparisonResponse` types
- [x] New `TariffModeComparison.tsx` component renders a 4-column table (Metric / 1C / 2C / Delta) over the 5 headline KPIs incl. demand-charge savings; surfaces per-mode `error` strings
- [x] `App.tsx`: when `result === null` and `tariffComparison !== null`, render `TariffModeComparison` in the results panel
- [x] Tests: 4 new (method check, missing csv, success with delta, NaN sanitisation) — **38 passed**
- [x] `npm run build` clean

## Review / Results

**GAP-03 complete — PHASE-01 + PHASE-02 + PHASE-03 shipped (Q-001 1-component default).**
- **PHASE-01:** `tariff_mode` + `cp_demand_vnd_per_kw` threaded through 6 backend handlers (`run_json`, `run_excel`, `run_report`, `export_workbook`, `compare_scenarios`, `run_sensitivity`). `resolve_tariff_mode` validates against the pipeline's `VALID_TARIFF_MODES` and returns 400 on bad input. Required because the JSON loader does NOT auto-read `tariff_structure` from the payload (only the Excel loader does). 5 TDD tests, suite 29 → 34.
- **PHASE-02:** Form gets a tariff-mode select + 4 VND inputs (Cp + Ca off-peak/standard/peak) seeded with the Sprint 4 22 kV reference rates; inputs gray out for 1-component via the existing `field-disabled` pattern. `KpiGrid` shows "Year 1 Demand Charge Savings" when `kpis.tariff_mode === "2-component"`. `model.ts` ModelKpis extended with optional `demand_charge_savings_usd` + `tariff_mode`.
- **PHASE-03:** `/api/compare-tariff-modes` runs the model twice via `run_tariff_mode_comparison` and returns `{"1-component", "2-component", "delta"}`. Frontend auto-routes when `tariff_mode === "both"`. New `TariffModeComparison.tsx` table headlines the Decree 146/2025 trade-off: negative grid-savings + positive demand-charge-savings. 4 TDD tests, suite 34 → 38.
- **Verification:** `pytest tests/unit/test_web_handlers.py` 38 passed (16 → 38 across GAP-01/02/03); `npm run build` clean.
- **Deferred:** Excel-upload path for `/api/compare-tariff-modes` (`run_tariff_mode_comparison` accepts `excel_path` already; surface in a follow-up if users ask). Voltage-tier warning propagation (RISK-01-01 in plan) — currently silent fallback to 1-component if the matrix lacks 2-component rates for a non-22kV connection; needs a separate logging plumbing PR.
- **Recommended manual check before deploy:** Run Emivest at 22 kV with `tariff_mode=2-component` and confirm `Year 1 Demand Charge Savings` card shows ~$8k (Sprint 4 reference). Then switch to `Compare both modes` and confirm the comparison table shows ~$303.9k → ~$203.1k grid-savings delta.

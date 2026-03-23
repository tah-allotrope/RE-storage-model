# Next Session Plan: Emivest Financial Parity

**Date:** 2026-03-23
**Status:** Ready for implementation

---

## 1. Objective

Resume the Emivest JSON-path parity work by fixing the two currently failing regression signals first, then wiring the missing JSON financial inputs that still prevent trustworthy IRR/NPV outputs.

Current high-risk symptoms:
- `project_irr` is finite but still not parity-grade.
- `equity_irr = nan`.
- `year1_solar_generation_mwh ~ 137,245`, which is clearly overstated for the Emivest JSON fixture.

---

## 2. Confirmed Findings From Current Review

### 2.1 Solar generation is being scaled twice

- `SystemAssumptions.scale_factor` is `actual_capacity_kwp / simulation_capacity_kwp = 3221 / 100 = 32.21` in `src/re_storage/inputs/schemas.py`.
- `_run_physics()` already applies that factor once when building `solar_gen_kw` in `src/re_storage/pipeline.py`.
- `_run_aggregation()` then passes `scale_factor=assumptions.scale_factor` into `calculate_year1_totals()` in `src/re_storage/pipeline.py`.
- `calculate_total_solar_generation_mwh()` multiplies by `scale_factor` again in `src/re_storage/aggregation/annual.py`.

Why this matters:
- The raw CSV annual simulation profile sum is `132,286.53`.
- After one correct scaling pass: `132,286.53 x 32.21 ~= 4.26 GWh`, which is directionally consistent with `energy_yield_kWh_pa = 4,578,435` in `tests/data/projects/emivest/Emivest.json`.
- After the current double scaling: `~137,245 MWh`, matching the failing regression output.

Conclusion:
- The regression expectation band in `tests/regression/test_emivest.py` is directionally correct.
- The bug is in the model path, not in the test.

### 2.2 `equity_irr = nan` is likely caused by missing JSON leverage wiring

- The Emivest JSON contains `financial_assumptions.debt_sizing.maximum_leverage_pct = 0.7`.
- `load_financial_params_from_json()` in `src/re_storage/inputs/json_loader.py` does not currently load that field.
- `run_model_from_json()` therefore falls back to `max_leverage_ratio = 1.0` when calling `_run_financial()` in `src/re_storage/pipeline.py`.
- `_run_financial()` caps debt by `initial_capex_usd * max_leverage_ratio`.
- If debt reaches full capex, year-0 equity becomes zero via:
  - `equity_cf.iloc[0] = -(initial_capex_usd - debt_amount_usd)`
- The equity cashflow series then lacks both signs, and `calculate_equity_irr()` rejects it.

Conclusion:
- Before debugging the waterfall more deeply, first load and honor JSON leverage.

### 2.3 The JSON path still ignores several material financial inputs

`tests/data/projects/emivest/Emivest.json` contains inputs that are still not loaded or not wired through `run_model_from_json()`:

- `active_ppa_option`
- Option 1 bundled discount inputs
- Option 2 PV/BESS discount inputs
- Option 4 fixed PPA inputs
- tax schedule inputs
- OPEX detail inputs
- MRA buildup schedule
- `land_acquisition_USD` and `bop_USD`

This means the JSON path is still materially different from the workbook path even after the recent financial-module additions.

### 2.4 JSON runs are still forced onto PPA option 3 by default

- Emivest declares `active_ppa_option = 1` in `tests/data/projects/emivest/Emivest.json`.
- `run_model_from_json()` currently defaults to option 3 unless a caller override is passed.

Conclusion:
- Revenue parity for Emivest cannot be trusted until JSON runs honor the fixture's active PPA option and option-specific parameters.

### 2.5 Regression safety gap: NaN actual values can be silently skipped

- `_compare_kpi()` in `tests/regression/test_emivest.py` currently treats NaN as a skip condition.

Conclusion:
- After the main fixes land, tighten the regression so NaN actuals fail loudly.

---

## 3. Recommended Implementation Order

### Step 1 - Fix double solar scaling

Target files:
- `src/re_storage/pipeline.py`
- `src/re_storage/aggregation/annual.py`
- `tests/regression/test_emivest.py`

Implementation intent:
- Ensure annual aggregation uses already-scaled `solar_gen_kw` without applying `scale_factor` a second time.
- Keep the physics-stage scaling as the single source of truth.

Expected result:
- `year1_solar_generation_mwh` should drop from `~137,245` into the expected low-thousands MWh range for this fixture.

### Step 2 - Load and apply JSON maximum leverage

Target files:
- `src/re_storage/inputs/json_loader.py`
- `src/re_storage/pipeline.py`
- `tests/unit/test_json_loader.py`

Implementation intent:
- Load `financial_assumptions.debt_sizing.maximum_leverage_pct` as `max_leverage_ratio`.
- Pass it through unchanged to `_run_financial()`.

Expected result:
- Year-0 equity cashflow becomes negative again.
- `equity_irr` should stop failing purely due to one-signed cashflows.

### Step 3 - Honor `active_ppa_option` and option-specific JSON pricing inputs

Target files:
- `src/re_storage/inputs/json_loader.py`
- `src/re_storage/pipeline.py`
- relevant settlement tests if behavior changes

Implementation intent:
- Load `active_ppa_option`.
- Load and wire:
  - bundled discount
  - PV discount
  - BESS discount
  - fixed PPA price
- Make `run_model_from_json()` default to the JSON-declared option when no explicit override is provided.

Expected result:
- Emivest revenue path should reflect the fixture's actual commercial structure instead of hard-defaulting to DPPA option 3.

### Step 4 - Extend JSON financial loader for parity-critical inputs

Target files:
- `src/re_storage/inputs/json_loader.py`
- `src/re_storage/pipeline.py`
- `tests/unit/test_json_loader.py`

Load and wire next:
- OPEX inputs:
  - `solar_om_USD_per_MWp_pa`
  - `bess_om_USD_per_MWh_pa`
  - `other_opex_USD_per_MWp_pa`
  - `asset_management_USD_per_MWp_pa`
  - `land_lease_pct_of_revenue`
  - `opex_escalation_cpi_pct_pa`
- tax inputs:
  - `corporate_tax_rate_pct`
  - `tax_holiday_years`
  - `first_discount_year`
  - `first_discount_rate`
  - `second_discount_year`
  - `second_discount_rate`
- MRA inputs:
  - reserve percentages
  - buildup schedule from `retail_tariff_matrix.mra_buildup_assumption`
- CAPEX inputs:
  - `land_acquisition_USD`
  - `bop_USD`

Important note on tax mapping:
- The JSON expresses discount points as absolute years.
- The current tax builder expects duration-style fields.
- Convert JSON year markers into durations explicitly before passing them into `build_tax_rate_schedule()`.

### Step 5 - Tighten regression handling for NaN

Target files:
- `tests/regression/test_emivest.py`

Implementation intent:
- Keep `None` references skippable.
- Make NaN actual KPI values fail instead of skipping.

Expected result:
- Future parity regressions fail loudly instead of hiding broken outputs.

---

## 4. Suggested Verification Sequence

After Step 1:
- Run `pytest tests/regression/test_emivest.py -q`
- Confirm `year1_solar_generation_mwh` moves into a physically reasonable band.

After Step 2:
- Run `pytest tests/regression/test_emivest.py -q`
- Inspect `_annual_df` from `run_model_from_json()` and confirm year-0 equity is negative and FCFE changes sign.

After Step 3:
- Compare `year1_dppa_revenue_usd` and lifetime revenue movement versus prior output.
- Confirm the selected PPA option matches the JSON fixture.

After Step 4:
- Re-run:
  - `pytest tests/unit/test_json_loader.py -q`
  - `pytest tests/regression/test_emivest.py -q`
- Then capture a fresh KPI snapshot for:
  - `project_irr`
  - `equity_irr`
  - `npv_usd`
  - `dscr_min`
  - `year1_opex_usd`
  - `year1_ebitda_usd`

Only after outputs look credible:
- Update `tests/data/references/emivest.json`

---

## 5. Expected First Wins

If the next session only completes the first three items, the likely improvements are:
- solar generation becomes physically credible
- `equity_irr` becomes solvable again
- Emivest revenue follows the intended PPA scenario instead of a forced default

That should make the remaining IRR/NPV gap much easier to debug as a true financial-parity problem rather than a loader/wiring problem.

# RE-Storage Model: Gap Analysis & Implementation Roadmap

> **Document purpose:** Comprehensive analysis of features present in the Excel model (`llm 20260129 SOLAR BESS MODEL - Editing - for processing test.xlsx` and `emivest_model_with_emivest_inputs.xlsx`) that are missing or incomplete in the Python `re_storage` package, plus frontend UX gaps. Includes a phased implementation plan with specific tasks, cell/sheet references, and a testing strategy to verify Excel parity.
>
> **Based on:** Full read of `src/re_storage/pipeline.py`, all Python modules, `web/frontend/src/`, both Excel files (17 sheets each), `model_architecture.md`, and all existing `/plans/` documents.
>
> **Date:** 2026-03-20

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Python Implementation: What Exists Today](#2-python-implementation-what-exists-today)
3. [Gap Analysis: Excel Features Missing from Python](#3-gap-analysis-excel-features-missing-from-python)
4. [Frontend Gap Analysis](#4-frontend-gap-analysis)
5. [Implementation Phases](#5-implementation-phases)
6. [Testing Strategy](#6-testing-strategy)
7. [Appendix: Excel Cell Reference Index](#7-appendix-excel-cell-reference-index)

---

## 1. Executive Summary

The Python `re_storage` package faithfully implements the **physics and dispatch core** (Calc sheet) and **DPPA/CfD settlement** (Option 3 only), but is **significantly incomplete** in the financial, revenue scenario, and output layers. The Excel model contains at least **13 material feature areas** absent from Python, and the React frontend lacks the dashboard, scenario comparison, and sensitivity analysis UI that are present in the Excel Dashboard and Scenarios sheets.

The highest-priority gaps in order of business impact are:

1. OPEX model (currently all zeros — makes all IRR/NPV values wrong)
2. Revenue escalation over the project lifetime (currently flat — understates long-term revenue)
3. Tax model (post-tax IRR not computed; a key investor metric)
4. CAPEX-based MRA contributions (currently zero)
5. Alternative PPA Scenarios (Options 1, 2, 4 — only DPPA Option 3 is implemented)
6. Sensitivity analysis engine
7. Scenario comparison engine
8. Frontend dashboard, GO/NO-GO, and scenario UI

---

## 2. Python Implementation: What Exists Today

### 2.1 Implemented Correctly

| Module | Replicates | Status |
|--------|-----------|--------|
| `physics/solar.py` | `Calc!F` — solar gen scaling | ✅ Complete |
| `physics/battery.py` | `Calc!G–M` — battery dispatch, SoC | ✅ Complete |
| `physics/balance.py` | `Calc!I,Q,S,V,Y,AB` — energy balance | ✅ Complete |
| `settlement/dppa.py` | `DPPA!G–Q` — CfD settlement (Option 3 only) | ✅ Complete |
| `settlement/grid.py` | `Helper!E,M` — BAU/RE grid expenses | ✅ Complete |
| `aggregation/monthly.py` | `Helper` — monthly peak/savings | ✅ Complete |
| `aggregation/annual.py` | `Measures` — Year 1 totals | ✅ Complete |
| `aggregation/lifetime.py` | `Lifetime` — PV/battery degradation factors | ✅ Complete |
| `financial/debt.py` | Amortization + DSCR-constrained debt sizing | ✅ Complete |
| `financial/metrics.py` | XIRR/XNPV (project, equity, unlevered) | ✅ Complete |
| `financial/waterfall.py` | Revenue → EBITDA → CFADS → equity | ✅ Schema complete |

### 2.2 Stubbed / Placeholder (Columns exist but always zero)

| Python Location | Missing Data | Excel Source |
|-----------------|-------------|--------------|
| `pipeline._build_placeholder_opex()` | All OPEX line items → **zero** | `Financial!F106–F113` (see §3.1) |
| `waterfall.build_cash_flow_waterfall()` | `taxes_usd` → **zero** | `Financial!F132,F150` |
| `waterfall.build_cash_flow_waterfall()` | `mra_contribution_usd` → **zero** | `Financial!F101–F103` |
| `waterfall.build_cash_flow_waterfall()` | `demand_charge_savings_usd` → **zero** | `Financial!F59` |
| `lifetime.build_lifetime_projection()` | Revenue is degradation-only, no price escalation | `Financial!I16` (Price Escalation 5% p.a.) |

---

## 3. Gap Analysis: Excel Features Missing from Python

### 3.1 OPEX Model — All Zeros (HIGH PRIORITY)

**Excel location:** `Financial!F105–F113`, `Assumption!K26–K34`

**What the Excel computes:**

```
O&M_PV ($/yr)          = Assumption!K26 ($/MWp p.a.) × Installed PV MWp    = 6,000 × 40.36 = $241,800/yr
O&M_BESS ($/yr)        = Assumption!K27 ($/MWh p.a.) × BESS MWh            = 2,000 × 66    = $132,000/yr
Insurance_PV ($/yr)    = Assumption!K29 (% CAPEX) × Total CAPEX             = 0.25% × CAPEX
Insurance_BESS ($/yr)  = Assumption!K30 (% CAPEX) × Total CAPEX             = 0.25% × CAPEX
Other Opex ($/yr)      = Assumption!K31 ($/MWp p.a.) × PV MWp              = 1,000 × 40.36 = $40,360/yr
Asset Mgmt ($/yr)      = Assumption!K32 ($/MWp p.a.) × PV MWp              = 3,000 × 40.36 = $121,080/yr
Land Lease ($/yr)      = Assumption!K33 (% of revenue) × Total Revenue      = 0% × Revenue
Total Opex Year N      = (above sum) × (1 + OPEX_Escalation_Rate)^(N-1)
```

**OPEX Escalation:** `Assumption!K34` = 4% p.a. (`Financial!H17`)

**Python gap:** `_build_placeholder_opex()` returns zeros for all 8 columns in every year. This is the single biggest cause of IRR/NPV divergence from Excel because OPEX reduces EBITDA which drives debt sizing.

**What to implement:**

1. **Load OPEX parameters** from `Assumption!I/K` in `loaders.load_financial_params_from_cells()`:
   - `om_solar_usd_per_mwp` (K26)
   - `om_bess_usd_per_mwh` (K27)
   - `insurance_solar_pct_capex` (K29)
   - `insurance_bess_pct_capex` (K30)
   - `other_opex_usd_per_mwp` (K31)
   - `asset_management_usd_per_mwp` (K32)
   - `land_lease_pct_revenue` (K33)
   - `opex_escalation_pct` (K34)

2. **Create `financial/opex.py`** with `build_opex_schedule(params, project_years, installed_mwp, bess_mwh, total_capex, year1_revenue_series)`:
   - Computes each OPEX line item per year
   - Applies compound escalation: `value_yr1 × (1 + escalation_rate)^(year-1)`
   - Returns `AnnualTimeSeries` matching `OPEX_COLUMNS` schema

3. **Replace the placeholder call** in `pipeline._build_placeholder_opex()` once loader and opex module are ready.

---

### 3.2 Revenue Escalation / Price Trajectory (HIGH PRIORITY)

**Excel location:** `Financial!H15–H18`, `Assumption!Q25, Q41`

**What the Excel computes (Financial rows 15–18):**

```
Price Escalation (general revenue):  H16 = Assumption!Q25 = 5% p.a.
Opex Escalation:                     H17 = Assumption!K34 = 4% p.a.
Market Price Descent (FMP/CFMP):     H18 = Assumption!Q41 = -5% p.a.
```

Applied in Lifetime/Financial: each year's revenue = Year 1 × (1 + escalation)^(year-1) × pv_degradation_factor.

**Python gap:** `lifetime.build_lifetime_projection()` applies only the `pv_factor` degradation. No price escalation is applied. For a 25-year project at 5% annual escalation, the last year's revenue is ~3.4× year 1. Missing escalation understates long-term revenue by ~30–40% on a NPV-weighted basis.

**What to implement:**

1. Add `revenue_escalation_pct` and `fmp_descent_pct` parameters to `build_lifetime_projection()`.
2. Compound escalation: `revenue_yr_n = year1_revenue × (1 + revenue_esc)^(n-1) × pv_factor_n`
3. Load escalation rates from `Assumption!Q25` and `Q41` in `load_financial_params_from_cells()`.
4. Separate escalation for DPPA revenue vs grid savings vs demand savings (they may have different escalation drivers).

---

### 3.3 Tax Model (MEDIUM-HIGH PRIORITY)

**Excel location:** `Financial!F125–F136` (unlevered), `Financial!F138–F150` (levered)

**What the Excel computes:**

```
Corporate Tax Rate:     Assumption!K62 = 20%
Tax Holiday:            Assumption!K63 = 5 years at 0%
First Discount Period:  Assumption!J64 = 13 years at Assumption!K64 = 5%
Second Discount:        Assumption!J65 = 15 years at Assumption!K65 = 10%

Annual Depreciation = Total CAPEX / Depreciation_Tenor (Assumption!K44 = 20 yrs)

Unlevered taxes:
  EBIT = EBITDA - Depreciation
  Tax = MAX(0, EBIT × applicable_rate)  [with tax holiday]
  After-tax FCF = EBITDA - Tax

Levered taxes:
  EBIT = EBITDA - Depreciation
  EBT  = EBIT - Debt Interest
  Levered Tax = MAX(0, EBT × applicable_rate)
  CFADS = EBITDA - Levered Tax

Applicable rate schedule:
  Years 1–5:  0%  (tax holiday)
  Years 6–13: 5%  (first discount period)
  Years 14–15: 10% (second discount period)
  Years 16+:  20% (standard rate)
```

**Python gap:** `waterfall.build_cash_flow_waterfall()` has `taxes_usd` column but it's always 0. No depreciation, no EBT calculation, no tax holiday logic. The Equity IRR in Python is pre-tax only.

**What to implement:**

1. **Create `financial/taxes.py`** with:
   - `build_tax_rate_schedule(project_years, tax_rate, holiday_years, first_discount_years, first_discount_rate, second_discount_years, second_discount_rate)` → returns Series of annual tax rates
   - `calculate_depreciation_schedule(total_capex, tenor_years, project_years)` → straight-line depreciation Series
   - `calculate_unlevered_taxes(ebitda, depreciation, tax_rates)` → Series
   - `calculate_levered_taxes(ebitda, depreciation, debt_interest, tax_rates)` → Series

2. **Add to waterfall** the after-tax FCF computation.
3. **Add `after_tax_project_irr` and `after_tax_equity_irr`** to the KPI dict in `pipeline.py`.
4. **Load tax params** from `Assumption!K62–K65, K44`.

---

### 3.4 MRA (Maintenance Reserve Account) (MEDIUM PRIORITY)

**Excel location:** `Financial!F98–F103`, `Assumption!K46–K47`, `Other Input!B5–B8`

**What the Excel computes:**

```
BESS MRA Target   = Assumption!K46 (% of BESS CAPEX) × BESS CAPEX  = 60% × 13.2M = $7.92M
PV MRA Target     = Assumption!K47 (% of PV CAPEX) × PV CAPEX      = 10% × 30.27M = $3.027M

Build-up Schedule (Other Input!B5–B8):
  Year 0: 10% of target funded (from equity at FC)
  Year 1: 30% of target
  Year 2: 30%
  Year 3: 30%

MRA Cash Flow each year:
  BESS_MRA_addition[yr] = BESS_MRA_Target × schedule_pct[yr]
  PV_MRA_addition[yr]   = PV_MRA_Target × schedule_pct[yr]
  Total MRA addition[yr] = BESS + PV
```

**Python gap:** `mra_contribution_usd` is always 0.0 in the waterfall. This understates equity cash outflows in years 0–3, making the equity IRR appear higher than it should be.

**What to implement:**

1. **Load MRA parameters** from `Assumption!K46–K47` and `Other Input!B5–B8` (build-up schedule).
2. **Create `financial/mra.py`** with `build_mra_schedule(bess_capex, pv_capex, bess_pct, pv_pct, buildup_schedule, project_years)`.
3. **Wire into pipeline** by passing `mra_contribution_usd` Series to `build_cash_flow_waterfall()`.

---

### 3.5 Alternative PPA Revenue Scenarios (MEDIUM-HIGH PRIORITY)

**Excel location:** `Assumption!Q20`, `Financial!F64–F88`, `Scenarios!B–E` sheet

The Excel has **4 revenue scenarios** selectable via `Assumption!Q20`:

| Option | Name | Key Parameter | Revenue Logic |
|--------|------|--------------|---------------|
| 1 | Bundled Discount to EVN | `Q30` = 15% discount | `Revenue = Load_kWh × EVN_Tariff × (1 - discount)` |
| 2 | Separate PV + BESS pricing | `Q33` = PV disc, `Q34` = BESS disc | PV and BESS revenues discounted separately at different rates |
| 3 | DPPA (CfD) | `Q39` = Strike 1800 VND/kWh | CfD: `R = Q_Khc × (Strike + Rg)` (already implemented) |
| 4 | Fixed PPA with EVN | `Q61` = 70 $/MWh fixed | `Revenue = Generation_MWh × fixed_price × (1 - curtailment - tx_loss)` |

**Python gap:** Only Option 3 (DPPA) is implemented. Options 1, 2, and 4 don't exist in Python.

**What to implement:**

**Option 1 — Bundled Discount:**
```python
# settlement/bundled.py
def calculate_bundled_revenue(hourly_data, tariff_rates, discount_pct):
    # Revenue = delivered_kwh × tariff_by_period × (1 - discount)
    # This is similar to grid_savings but expressed as a positive revenue stream
    # delivered_kwh = direct_pv_consumption_kw + discharged_kw
```

**Option 2 — Separate PV + BESS:**
```python
# settlement/separate.py
def calculate_separate_revenue(hourly_data, tariff_rates, pv_discount_pct, bess_discount_pct):
    # PV_revenue = PV_to_load_kw × tariff × (1 - pv_discount)
    # BESS_revenue = BESS_to_load_kw × tariff × (1 - bess_discount)
```

**Option 4 — Fixed PPA:**
```python
# settlement/fixed_ppa.py
def calculate_fixed_ppa_revenue(generation_mwh, fixed_price_usd_per_mwh, curtailment_pct, tx_loss_pct):
    # Revenue = generation_mwh × (1 - curtailment) × (1 - tx_loss) × fixed_price
```

**Scenario selector in pipeline:**
- Add `ppa_option: int = 3` parameter to `run_full_model()` and `run_model_from_json()`
- Load `ppa_option` from `Assumption!Q20` in `load_financial_params_from_cells()`
- Dispatch to the appropriate settlement function based on `ppa_option`

---

### 3.6 Scenario Comparison Engine (MEDIUM PRIORITY)

**Excel location:** `Scenarios!A1–N73`, `Dashboard!O16–R22` (Scenario Comparison table)

**What the Excel shows:**

```
For each of the 4 PPA options, the Scenarios sheet computes and displays:
  - Year-1 Revenue ($M)
  - 20-Year Total Revenue ($M)
  - Year-1 OPEX ($M)
  - Year-1 EBITDA ($M)
  - EBITDA Margin (%)
  - Total CAPEX ($M)
  - Simple ROI (Total Revenue / CAPEX)
  - Currently Active? marker
```

**What to implement:**

1. **Create `scenarios/runner.py`** with `run_all_scenarios(excel_path_or_json_params)`:
   - Runs the pipeline 4 times, once per PPA option (1–4)
   - Returns a dict of `{option_id: kpi_dict}` for each scenario
   - Reuses existing pipeline stages; only settlement layer changes

2. **Add `ScenarioComparisonResponse`** to `web/functions/utils/serialise.py`.
3. **New API endpoint** `POST /compareScenarios` in `web/functions/main.py`.

---

### 3.7 Sensitivity Analysis Engine (MEDIUM PRIORITY)

**Excel location:** `Scenarios!A17–N35`

**What the Excel documents (9 sensitivity variables with 7 test values each):**

| Variable | Cell Ref | Current Value | Unit | Solver Required |
|----------|----------|--------------|------|----------------|
| PV CAPEX | K41 | 750,000 | $/MWp | ⚠ Yes |
| BESS CAPEX | K42 | 200,000 | $/MWh | ⚠ Yes |
| Bundled Discount (Opt 1) | Q30 | 15% | % | Optional |
| DPPA Strike Price (Opt 3) | Q39 | 1,800 | VND/kWh | Optional |
| Interest Rate Base | K53 | 6.5% | % p.a. | ⚠ Yes |
| FX Rate | K9 | 26,000 | VND/$ | ⚠ Yes |
| EVN Tariff Escalation | Q25 | 5% | % p.a. | No |
| Demand Reduction Target | E38 | 20% | % | No |
| Max Leverage | K48 | 70% | % | ⚠ Yes |

**What to implement:**

1. **Create `scenarios/sensitivity.py`** with `run_sensitivity(base_params, variable_name, test_values)`:
   - Overrides one parameter at a time
   - Runs full pipeline for each test value
   - Returns `{value: kpi_dict}` for each test value
   - Core logic: deep-copy `base_params`, mutate the target field, run pipeline

2. **Sensitivity API endpoint** `POST /runSensitivity` in `web/functions/main.py`.
3. **Supported variables for v1:** strike_price, interest_rate, pv_capex_per_mwp, bess_capex_per_mwh, fx_rate, max_leverage, opex_escalation, revenue_escalation.

---

### 3.8 Demand Charge Savings (MEDIUM PRIORITY)

**Excel location:** `Financial!F54, F59`, `Assumption!O13` (Cp_demand), `Other Input!B13` (Cp_demand table)

**What the Excel computes:**

```
Baseline Capacity Demand (Financial!F26) = MAXIFS(Calc!Load, month) monthly peak demand
Peak Shaving Capacity (Financial!F42) = MAXIFS(Calc!GridLoadAfterRE, month) after BESS

Capacity Saving = (Baseline_Peak - Post_RE_Peak) × Cp_demand × 12
```

Where `Cp_demand` from `Other Input!B13`: for 110kV-2-component = 209,459 VND/MW, for 22kV-2-component = 235,414 VND/MW. For 1-component tariff (current test project) = 0.

**Python gap:** `demand_charge_savings_usd` is always 0.0. The monthly aggregation correctly computes `peak_demand_after_re_kw` and `baseline_peak_kw` but they never feed into a demand savings calculation.

**What to implement:**

1. **Load `Cp_demand`** from `Assumption!O13` (or `Other Input!B13`) in `load_financial_params_from_cells()`.
2. **Create `settlement/demand_charge.py`** with `calculate_annual_demand_savings(monthly_data, cp_demand_vnd_per_kw, exchange_rate)`.
3. **Wire into pipeline:** compute `demand_charge_savings_usd` in `_run_financial()` and pass to lifetime projection.

---

### 3.9 CAPEX Breakdown in Loaders (LOW-MEDIUM PRIORITY)

**Excel location:** `Assumption!K40–K43, K45`, `Financial!F92–F95`

**What the Excel uses to compute CAPEX:**

```
Land acquisition (all-in): K40 = $1,200,000 (lump sum)
Solar CAPEX:               K41 = 750,000 $/MWp × 40.36 MWp = $30,270,000
BESS CAPEX:                K42 = 200,000 $/MWh × 66 MWh   = $13,200,000
BOP:                       K43 = 4,843,200 (or K45 = 16% × Solar CAPEX)
Total CAPEX = Land + Solar + BESS + BOP = $49,513,200
```

**Python status:** `load_financial_params_from_cells()` already reads these fields and sums them into `initial_capex_usd`. The individual components are available in local variables but not returned. The OPEX formulas need per-component values (O&M_PV depends on MWp, O&M_BESS depends on MWh, Insurance depends on Total CAPEX).

**What to implement:**

1. **Extend `load_financial_params_from_cells()`** to return `capex_breakdown` dict:
   ```python
   {"land_usd": ..., "solar_usd": ..., "bess_usd": ..., "bop_usd": ...,
    "solar_usd_per_mwp": ..., "bess_usd_per_mwh": ..., "installed_pv_mwp": ..., "installed_bess_mwh": ...}
   ```
2. Pass this to `build_opex_schedule()` for OPEX calculations.
3. Pass `bess_usd` and `solar_usd` to `build_mra_schedule()`.

---

### 3.10 Blended Interest Rate / Hedging (LOW PRIORITY)

**Excel location:** `Financial!F157–F161`, `Assumption!K58–K59`

```
Hedging Ratio = K58 = 50%
Fixed Swap Rate = K59 = 6.5%
Floating Base Rate = K56 = 6.5%
All-in Rate = (hedging × fixed + (1-hedging) × floating) + Debt Margin
           = (0.5 × 6.5% + 0.5 × 6.5%) + 2% = 8.5%
```

**Python status:** Uses a flat `interest_rate_pct`. No hedging computation.

**What to implement:** Load `hedging_ratio`, `fixed_swap_rate`, `base_rate`, `debt_margin` separately and compute the blended rate in `load_financial_params_from_cells()`. The blended rate is already the final parameter fed to the debt module — this is a loader fix, not a new module.

---

### 3.11 Missing Output KPIs (LOW PRIORITY)

**Excel location:** `Financial!H198, H195, H136, H123`, `Output!various`

KPIs computed in Excel but absent from the Python KPI dict:

| KPI | Excel Location | Formula |
|-----|---------------|---------|
| Payback Period (years) | `Financial!H198` | First year where Cumulative FCFE > 0 |
| Cash-on-Cash Yield | `Financial!H195` | Total FCFE / Equity Invested / Project Years |
| After-tax Unlevered IRR | `Financial!G136` | XIRR on after-tax FCF |
| After-tax Equity IRR (same as Levered) | `Financial!G189` | XIRR on net FCFE |
| Solar Utilization Rate (w/ BESS) | `Output!E30` | Solar consumed / Total solar generated |
| Clean Energy Delivered (GWh) | `Output!E22` | Solar-to-load + BESS-to-load |
| Pre-BESS Curtailment | `Output!E30` | `MAX(Solar - Load, 0)` annually |
| Post-BESS Curtailment | `Output!E32` | Surplus after battery charging |
| Load Coverage (%) | `Output!E28` | Clean energy / Total load |
| BESS Round-trip Efficiency | `Dashboard!L22` | `charge_eff² = 0.95² = 0.9025` |

**What to implement:**

1. **Add `calculate_payback_period(cumulative_fcfe_series)`** to `financial/metrics.py`.
2. **Add `calculate_coc_yield(total_fcfe, equity_invested, project_years)`** to `financial/metrics.py`.
3. **Add energy performance metrics** computation in `pipeline._run_physics()` or `_run_aggregation()`.
4. **Add all new KPIs to the returned dict** in `run_full_model()`.

---

### 3.12 Net Billing Revenue (LOW PRIORITY)

**Excel location:** `Financial!F55, F67`, `Assumption!O26–O27`

```
Net Billing Rate = Assumption!O26 = $38.46/MWh
Export Share     = Assumption!O27 = 0%  (in current model)
Net Billing Rev  = Surplus_kWh × export_share × net_billing_rate
```

Currently 0 in test project (export share = 0%), but may be non-zero for other projects.

**What to implement:** Add `net_billing_usd_per_mwh` and `net_billing_export_share` to `SystemAssumptions` schema. Implement in settlement layer as optional revenue stream.

---

### 3.13 Other Input Sheet Loader (LOW PRIORITY)

**Excel location:** `Other Input!B3–C25`

The `Other Input` sheet contains:
- ① MRA Build-up Schedule (Year 0–3 with percentages)
- ② Full EVN Retail Tariff Table (110kV, 22kV, 1-component and 2-component, with Cp_demand)
- ③ TOU Hour Boundaries (hardcoded reference)

**Python gap:** No loader reads `Other Input`. Tariff rates are read from `Assumption!O/Q` only. The full tariff table and MRA schedule are ignored.

**What to implement:** Add `load_other_input(path)` function in `loaders.py` that returns `{mra_buildup: [], tariff_table: {}}`.

---

## 4. Frontend Gap Analysis

### 4.1 Current Frontend State

The React frontend (`web/frontend/src/`) has:
- **6-step wizard form** for manual parameter entry (System → DPPA → Financial → Degradation → CSV → Review)
- **Excel upload tab** (parallel to manual entry)
- **Results dashboard** with: 10 KPI cards, 3 Recharts charts (Lifetime Revenue bar, Generation bar, Battery Capacity line)
- **Download JSON** button

### 4.2 Missing UX Features (vs Excel Dashboard/Scenarios)

#### 4.2.1 Dashboard & GO/NO-GO (HIGH — core decision tool)

**Excel:** `Dashboard` sheet shows a clear GO/NO-GO header based on Equity IRR vs Target IRR.

**Missing in frontend:**
- No GO/NO-GO indicator with color coding (green/red)
- No Project Identity panel (Project Name, Owner, Location, COD)
- No CAPEX breakdown pie or waterfall chart
- No Buyer Electricity Bill comparison (BAU vs After Solar vs After RE)
- No Energy Performance summary section (curtailment, utilization, clean energy share)
- No Financing Structure summary (debt/equity split, leverage %)

**Recommendations:**
- Add a `<GoNoGoIndicator>` component that compares `equity_irr` vs user's `target_irr` input
- Add a `<ProjectSummaryPanel>` at top of ResultsDashboard
- Add a `<CapexWaterfallChart>` using Recharts bar (stacked: Land, PV, BESS, BOP)
- Add a `<BuyerBillChart>` comparing BAU/Solar/RE annual bills (3 bar groups per year)

#### 4.2.2 Scenario Comparison UI (HIGH — key use case)

**Excel:** `Scenarios` sheet shows all 4 PPA scenarios side by side.

**Missing in frontend:**
- No scenario selector (radio/toggle for Options 1–4)
- No side-by-side comparison table
- No "active scenario" highlight
- Active scenario number isn't a user-editable field in the form

**Recommendations:**
- Add `ppa_option` (1–4) to `SystemStep.tsx` or a new `ScenarioStep`
- Add `<ScenarioComparisonTable>` component showing Year-1 revenue, EBITDA, Total 20Y revenue for all options
- Wire to new `/compareScenarios` API endpoint (see §3.6)

#### 4.2.3 Sensitivity Analysis UI (MEDIUM)

**Excel:** `Scenarios!A17–N35` has 9 sensitivity variables with 7 test values each.

**Missing in frontend:** No sensitivity analysis of any kind.

**Recommendations:**
- Add a `<SensitivityPanel>` component (below Results Dashboard)
- Let user pick 1 variable from a dropdown (e.g., Strike Price, Interest Rate, PV CAPEX)
- Show a tornado chart or spider/line chart of IRR vs variable value
- Wire to `/runSensitivity` API endpoint

#### 4.2.4 Missing KPI Cards

Current KPI grid shows 10 metrics. The following are in Excel but missing from the frontend:

| Missing KPI | Excel Location |
|-------------|---------------|
| Payback Period (years) | `Financial!H198` |
| Cash-on-Cash Yield (%) | `Financial!H195` |
| After-tax Unlevered IRR | `Financial!G136` |
| Year 1 OPEX Total | `Financial!F113` |
| Year 1 EBITDA | `Financial!F117` |
| EBITDA Margin (%) | `Financial!F119` |
| Solar Utilization (%) | `Output!E30` |
| Clean Energy Delivered (GWh) | `Output!E22` |
| Total CAPEX | `Financial!F96` |
| Equity Contribution | `Financial!H186` |

**Recommendations:**
- Add a second KPI section "Energy Performance" and "Financial Detail"
- Update `ModelKpis` interface in `types/model.ts` to include new fields

#### 4.2.5 Chart Improvements

| Current Chart | Problem | Recommended Fix |
|---------------|---------|----------------|
| `LifetimeRevenueChart` | Shows DPPA + Grid Savings only; missing OPEX | Add OPEX as negative bars (waterfall style) |
| `GenerationChart` | Shows generation only | Add load baseline line and clean energy delivered |
| `BatteryCapacityChart` | Shows capacity curve | Add replacement event markers at years 11 and 22 |
| (missing) | No DSCR chart | Add `<DscrChart>` showing DSCR by year vs 1.3 covenant |
| (missing) | No cash flow waterfall | Add `<AnnualCashFlowChart>` for EBITDA/Debt Service/FCFE |

#### 4.2.6 Form UX Issues

- **Degradation step** uses a raw textarea for JSON — poor UX. Should default-populate with a standard 25-year table and allow per-row editing.
- **Review step** shows only 6 fields. Should show a full parameter summary.
- **No validation feedback** inline — errors only appear on submission.
- **No progress indicator** during model run (the backend can take 3–10 seconds for 8760-row simulation).
- **Hourly CSV upload** has no format preview or column validation before submission.
- **No project save/load** — user must re-enter everything each session.

---

## 5. Implementation Phases

### Phase 1: Critical Financial Parity (Weeks 1–3)

These fix the largest numerical divergences from Excel. All existing tests will need updating because OPEX and escalation fundamentally change IRR/NPV outputs.

**Tasks:**

1. **P1-1:** Extend `load_financial_params_from_cells()` to return OPEX parameters and CAPEX breakdown (Assumption!K26–K34, K40–K45). Add corresponding JSON loader equivalent.

2. **P1-2:** Create `financial/opex.py` with `build_opex_schedule()`. Replace `_build_placeholder_opex()` in `pipeline.py`.

3. **P1-3:** Add `revenue_escalation_pct` and `opex_escalation_pct` to `build_lifetime_projection()`. Load from Assumption!Q25, K34.

4. **P1-4:** Update regression reference JSON files (`tests/data/references/`) after verifying parity with new OPEX+escalation values against Excel.

5. **P1-5:** Create `financial/taxes.py` with `build_tax_rate_schedule()` and `calculate_unlevered_taxes()`. Add `after_tax_project_irr` to pipeline output.

6. **P1-6:** Create `financial/mra.py`. Load MRA params from Assumption!K46–K47 and Other Input. Wire into waterfall.

**Test targets after Phase 1:**
- `year1_opex_usd` within 1% of Excel `Financial!F113` Year 1
- `project_irr` within 0.5% of Excel `Financial!H123` (`0.08952`)
- `equity_irr` within 0.5% of Excel `Financial!H189` (`0.19403`)
- `npv_usd` within 2% of Excel `Financial!H193` (`$22.03M`)

---

### Phase 2: Revenue Scenarios (Weeks 4–5)

**Tasks:**

7. **P2-1:** Create `settlement/bundled.py` — Option 1 (Bundled Discount). Unit test against `Financial!F68` Year 1 value.

8. **P2-2:** Create `settlement/separate.py` — Option 2 (Separate PV + BESS). Unit test against `Financial!F80` Year 1.

9. **P2-3:** Create `settlement/fixed_ppa.py` — Option 4 (Fixed Price PPA). Unit test against `Financial!F74` Year 1.

10. **P2-4:** Add `ppa_option: int` to `SystemAssumptions` schema (or as a separate financial param). Load from `Assumption!Q20`. Add scenario dispatch to pipeline.

11. **P2-5:** Update `web/functions/handlers/run_json.py` to pass `ppa_option` and new PPA params (discount_pct, fixed_price) through the handler.

12. **P2-6:** Update `web/frontend/src/components/inputs/SystemStep.tsx` to add PPA option selector (radio group, Options 1–4 with labels).

---

### Phase 3: Scenario Comparison & Sensitivity (Weeks 6–8)

**Tasks:**

13. **P3-1:** Create `scenarios/runner.py` — `run_all_scenarios()` that runs all 4 PPA options in a single call and returns a comparison dict.

14. **P3-2:** Create `scenarios/sensitivity.py` — `run_sensitivity(base_params, variable, test_values)`.

15. **P3-3:** Add `POST /compareScenarios` and `POST /runSensitivity` Flask routes to `web/functions/main.py`.

16. **P3-4:** Add `<ScenarioComparisonTable>` React component. Display Year-1 Revenue, EBITDA, Margin, and 20-year total for all 4 options.

17. **P3-5:** Add `<SensitivityPanel>` React component with variable picker and tornado/line chart (using Recharts LineChart).

---

### Phase 4: Dashboard & Missing KPIs (Weeks 9–11)

**Tasks:**

18. **P4-1:** Add missing financial KPIs to pipeline: payback period, CoC yield, blended interest rate, after-tax IRR.

19. **P4-2:** Add energy performance KPIs to pipeline: solar utilization, curtailment (pre/post-BESS), clean energy delivered, load coverage %.

20. **P4-3:** Update `ModelKpis` TypeScript interface and `KpiGrid.tsx` to display new KPIs in grouped sections.

21. **P4-4:** Add `<GoNoGoIndicator>` component to `ResultsDashboard.tsx`.

22. **P4-5:** Add `<ProjectSummaryPanel>` (project name, system size, COD, financing summary).

23. **P4-6:** Add `<BuyerBillChart>` — stacked bar comparing BAU / After Solar / After RE grid bills by year.

24. **P4-7:** Improve chart set: add `<DscrChart>`, `<AnnualCashFlowChart>`, update `BatteryCapacityChart` to show replacement events.

---

### Phase 5: UX Improvements & Demand Charges (Weeks 12–13)

**Tasks:**

25. **P5-1:** Load `Other Input` sheet — `load_other_input()` in `loaders.py`.

26. **P5-2:** Implement demand charge savings — `settlement/demand_charge.py`.

27. **P5-3:** Implement net billing revenue — add to `SystemAssumptions` and `settlement/`.

28. **P5-4:** Fix form UX: default-populated degradation table, inline validation, CSV preview, progress bar during model run.

29. **P5-5:** Add project save/load functionality (LocalStorage or Firebase Firestore) so users don't re-enter parameters.

30. **P5-6:** Add Excel-format report download (or PDF export of Dashboard view).

---

## 6. Testing Strategy

### 6.1 Regression Test Framework

The project already has a strong regression test structure at `tests/regression/`. Extend it for each new feature:

**Pattern for each new module:**
```
tests/
  unit/
    test_financial_opex.py          # Unit tests for build_opex_schedule()
    test_financial_taxes.py         # Unit tests for tax calculations
    test_financial_mra.py           # Unit tests for MRA schedule
    test_settlement_bundled.py      # Unit tests for Option 1
    test_settlement_separate.py     # Unit tests for Option 2
    test_settlement_fixed_ppa.py    # Unit tests for Option 4
    test_scenarios_runner.py        # Unit tests for run_all_scenarios()
    test_scenarios_sensitivity.py   # Unit tests for run_sensitivity()
  regression/
    test_excel_parity_full.py       # End-to-end vs Excel KPIs
```

### 6.2 Excel Parity Verification

For each Phase 1–2 feature, verify against Excel computed values using `scripts/extract_excel_kpis.py`. Define tolerance bounds:

| KPI | Tolerance | Rationale |
|-----|-----------|-----------|
| Annual solar generation (MWh) | ±0.01% | Pure arithmetic, should be near-exact |
| Year 1 OPEX | ±0.5% | Small rounding in CAPEX products |
| Year 1 DPPA Revenue | ±0.5% | Already tested; maintain this |
| Project IRR | ±0.2 percentage points | XIRR solver tolerance |
| Equity IRR | ±0.2 percentage points | XIRR solver tolerance |
| NPV | ±1% | Cumulative effect of small discrepancies |
| Payback Period | ±1 year (integer) | Discrete annual step |
| DSCR min | ±0.05 | Debt sizing solver tolerance |

### 6.3 Scenario Comparison Testing

Verify the Scenarios sheet values from Excel:

```python
# From Scenarios!B5–E5 (Year-1 Revenue for each option)
EXPECTED_YEAR1_REVENUE = {
    1: 5_056_417.72,   # Bundled Discount
    2: 5_651_290.39,   # Separate PV + BESS
    3: 4_576_659.86,   # DPPA (CfD) — already tested
    4: 4_688_546.62,   # Fixed EVN PPA
}
```

### 6.4 Sensitivity Analysis Testing

Verify Python sensitivity outputs match manual Excel override tests for at least 3 variables:
- Strike price at 1,400 VND/kWh: verify Year-1 DPPA revenue matches Excel manual override
- Interest rate at 9.5%: verify DSCR min and debt amount match
- FX rate at 24,000: verify all VND→USD conversions are consistent

### 6.5 Unit Test Standards

Follow existing patterns in `tests/unit/`:
- Use `hypothesis` for property-based testing where bounds matter (e.g., DSCR must be positive, tax rate between 0–1)
- Use `pytest.approx(rel=1e-4)` for floating-point comparisons
- Each new function must have ≥5 unit tests: happy path, edge cases (zero values, boundary values, errors)

### 6.6 Frontend Tests

- Add Playwright tests for the scenario selector in `ProjectForm`
- Add snapshot tests for `ScenarioComparisonTable` and `KpiGrid`
- Add API contract tests for new endpoints (`/compareScenarios`, `/runSensitivity`)

---

## 7. Appendix: Excel Cell Reference Index

### Key Named Ranges and Cell Locations

| Parameter | Sheet | Cell | Current Value |
|-----------|-------|------|--------------|
| PPA Option | Assumption | Q20 | 1 (Bundled Discount) |
| Bundled Discount % | Assumption | Q30 | 15% |
| PV Discount % | Assumption | Q33 | 5% |
| BESS Discount % | Assumption | Q34 | 5% |
| DPPA Active Toggle | Assumption | Q37 | 1 |
| Strike Price (VND/kWh) | Assumption | Q39 | 1,800 |
| Fixed PPA Price ($/MWh) | Assumption | Q61 | 70 |
| O&M Solar ($/MWp p.a.) | Assumption | K26 | 6,000 |
| O&M BESS ($/MWh p.a.) | Assumption | K27 | 2,000 |
| Insurance Solar (% CAPEX) | Assumption | K29 | 0.25% |
| Insurance BESS (% CAPEX) | Assumption | K30 | 0.25% |
| Other Opex ($/MWp p.a.) | Assumption | K31 | 1,000 |
| Asset Management ($/MWp p.a.) | Assumption | K32 | 3,000 |
| Land Lease (% revenue) | Assumption | K33 | 0% |
| OPEX Escalation (% p.a.) | Assumption | K34 | 4% |
| Price Escalation (% p.a.) | Assumption | Q25 | 5% |
| Market Price Descent (% p.a.) | Assumption | Q41 | -5% |
| Corporate Tax Rate | Assumption | K62 | 20% |
| Tax Holiday (years) | Assumption | K63 | 5 |
| First Tax Discount Rate | Assumption | K64 | 5% |
| First Tax Discount Tenor | Assumption | J64 | 13 years |
| Second Tax Discount Rate | Assumption | K65 | 10% |
| Depreciation Tenor | Assumption | K44 | 20 years |
| BESS MRA % CAPEX | Assumption | K46 | 60% |
| PV MRA % CAPEX | Assumption | K47 | 10% |
| Hedging Ratio | Assumption | K58 | 50% |
| Fixed Swap Rate | Assumption | K59 | 6.5% |
| Max Leverage | Assumption | K51 | 70% |
| Debt Tenor | Assumption | K52 | 10 years |
| Target DSCR | Assumption | K53 | 1.3x |
| Land Acquisition | Assumption | K40 | $1.2M |
| Solar CAPEX ($/MWp) | Assumption | K41 | $750,000 |
| BESS CAPEX ($/MWh) | Assumption | K42 | $200,000 |
| MRA Build-up Y0 | Other Input | C5 | 10% |
| MRA Build-up Y1 | Other Input | C6 | 30% |
| MRA Build-up Y2 | Other Input | C7 | 30% |
| MRA Build-up Y3 | Other Input | C8 | 30% |
| Cp_demand 110kV | Other Input | C13 | 209,459 VND/MW |
| Cp_demand 22kV | Other Input | D13 | 235,414 VND/MW |

### Financial Sheet Output Cells

| KPI | Cell | Value (current Excel) |
|-----|------|-----------------------|
| Unlevered pre-tax IRR | G123 / H123 | 8.952% |
| Unlevered after-tax IRR | G136 / H136 | 8.399% |
| Equity (Levered) IRR | G189 / H189 | 19.403% |
| NPV @ 10% | G193 / H193 | $22.03M |
| Payback Period | H198 | 6 years |
| Cash-on-Cash Yield | H195 | 4.598% per year |
| DSCR Solver Target | G170 | 0 (converged) |
| Final Debt Size | H169 | $22.04M |
| Total OPEX Year 1 | F113 (col K onward) | ~$0.64M |
| Total Revenue Year 1 (Active) | F115 (col K) | $5.056M |
| EBITDA Year 1 | F117 (col K) | $4.412M |

### Scenarios Sheet Reference Values

| Metric | Option 1 | Option 2 | Option 3 | Option 4 |
|--------|---------|---------|---------|---------|
| Year-1 Revenue ($M) | 5.056 | 5.651 | 4.577 | 4.689 |
| 20-Year Total Revenue ($M) | 153.46 | 171.52 | 139.09 | 87.69 |
| EBITDA Margin (%) | 87.3% | 88.6% | 85.9% | 86.3% |

---

*End of Gap Analysis & Implementation Roadmap*

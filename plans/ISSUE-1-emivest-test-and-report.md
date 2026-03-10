# ISSUE-1: Emivest Project Testing & HTML Report Generation

## 1. Objective

Add support for loading the Emivest (Saigon18) project from its JSON+CSV data files (not Excel), run it through the existing RE-Storage simulation pipeline, compare results against an external reference JSON, and generate a professional HTML report (print-friendly / PDF-exportable) showing the model outputs and comparison analysis.

---

## 2. Mathematical Formulation / Logic

### 2.1 Data Loading from JSON+CSV (New Loader)

The Emivest project uses a **different input format** from the existing Excel-based pipeline. Instead of an `.xlsx` file, it has:
- `Emivest.json` — project configuration & assumptions (269 lines)
- `Emivest additional data.csv` — 8760 hourly time series (6 columns)

The new loader must translate JSON fields into the same `SystemAssumptions` Pydantic model the pipeline expects:

| JSON Path | SystemAssumptions Field | Formula / Transform |
|-----------|------------------------|---------------------|
| `system_input.simulation_capacity_kWp` | `simulation_capacity_kwp` | Direct: `100` |
| `system_input.actual_installation_capacity_kWp` | `actual_capacity_kwp` | Direct: `3221` |
| `bess_parameters.total_bess_storage_capacity_kWh × bess_parameters.depth_of_discharge_pct` | `usable_bess_capacity_kwh` | `2150 × 0.85 = 1827.5 kWh` |
| `bess_parameters.total_bess_power_output_kW` | `bess_power_rating_kw` | Direct: `1000` |
| `bess_parameters.half_cycle_efficiency_pct` | `charge_efficiency` | Direct: `0.95` (ratio, NOT percent) |
| `bess_parameters.half_cycle_efficiency_pct` | `discharge_efficiency` | Same: `0.95` |
| `bess_operation_strategy.strategy_mode` | `strategy_mode` | Direct: `1` (Energy Arbitrage) |
| `bess_operation_strategy.charge.solar_active_charging.pv2bess_pre_charge_mode` | `charging_mode` | Direct: `1` (Fixed share in window) |
| `bess_operation_strategy.charge.solar_active_charging.pre_charge_start_hour_1` | `charge_start_hour` | Direct: `10` |
| `bess_operation_strategy.charge.solar_active_charging.pre_charge_end_hour_1` | `charge_end_hour` | Direct: `16` |
| `bess_operation_strategy.charge.solar_active_charging.precharge_target_hour_2` | `precharge_target_hour` | Direct: `17` |
| `bess_operation_strategy.charge.solar_active_charging.precharge_target_soc_kWh_2` | `precharge_target_soc_kwh` | Direct: `1500` |
| `bess_operation_strategy.charge.solar_active_charging.min_pv_directly_to_load_pct` | `min_direct_pv_share` | Direct: `0.1` (ratio) |
| `bess_operation_strategy.charge.solar_active_charging.pre_charge_share_of_pv_1_pct` | `active_pv2bess_share` | Direct: `0.3` (ratio) |
| `ppa_settings.option_3_dppa.strike_price_VND / financial_input.exchange_rate_USD_VND` | `strike_price_usd_per_kwh` | `1800 / 26000 = 0.069230769 USD/kWh` |
| `ppa_settings.option_3_dppa.regulation_parameters.k` | `k_factor` | Direct: `1.02` |
| `ppa_settings.option_3_dppa.regulation_parameters.Kpp_22kv` | `kpp` | `1.027263` (use 22kV since `grid_connection_and_tariff.connection_voltage_level_kV = 22`) |
| `system_input.bess_included` | `bess_enabled` | Direct: `true` |
| `ppa_settings.option_3_dppa.model_active` | `dppa_enabled` | Direct: `true` |
| Hardcode `0.0` | `demand_reduction_target` | `0.0` (strategy_mode=1 is arbitrage, no demand reduction; `peak_shaving.demand_reduction_target_pct = 0`) |

**Scale factor**: `actual_capacity_kwp / simulation_capacity_kwp = 3221 / 100 = 32.21`

### 2.2 CSV Hourly Data Normalization

The CSV columns must map to the internal hourly DataFrame format:

| CSV Column | Internal Column | Transform |
|------------|----------------|-----------|
| `DateTime` | `datetime` | Parse as datetime (format: `M/D/YYYY H:MM`) |
| `SimulationProfile_kW` | `simulation_profile_kw` | Direct (float) |
| `Irradiation_W/m2` | `irradiation_wh_m2` | Direct (note: column name says W/m2 but internal name says wh_m2 — the existing loader `_HOURLY_COLUMN_ALIASES` maps `irradiation_w/m2` → `irradiation_wh_m2`; follow same convention) |
| `Load_kW` | `load_kw` | Direct (float) |
| `FMP` | `fmp_usd_per_kwh` | Direct (float; these are VND values but the column name in the internal schema says usd — follow existing convention as the DPPA module handles the actual units) |
| `CFMP` | `cfmp_usd_per_kwh` | Direct (float) |

The CSV has a trailing comma after CFMP creating an empty 7th column — the loader must handle/drop this.

### 2.3 Degradation Table Construction

Build a degradation DataFrame from `Emivest.json` → `degradation_and_loss.annual_table` with 20 rows:

| JSON Field | Internal Column |
|------------|----------------|
| `year` | `year` |
| `pv_retention` | `pv_factor` |
| `battery_retention` | `battery_factor_no_replacement` |
| `battery_with_replacement` | `battery_factor_with_replacement` |

**Important**: The project is 20 years (not 25). The pipeline's `load_degradation_table` validates coverage for `project_years`. Pass `project_years=20` throughout.

### 2.4 Tariff Schedule

Build the tariff hour classification from Vietnam EVN standard schedule. The existing pipeline default is:
- OFF_PEAK: hours 0–6 (22:00–04:00 in Vietnam, but model uses 0-indexed hours)
- STANDARD: hours 7–16
- PEAK: hours 17–23

Use this default schedule since the JSON doesn't specify hourly tariff classification.

Tariff rates (USD/MWh → USD/kWh by dividing by 1000):

| Period | JSON Path | Value (USD/MWh) | Value (USD/kWh) |
|--------|-----------|-----------------|-----------------|
| OFF_PEAK | `grid_connection_and_tariff.current_applied_evn_tariff_USD_MWh.off_peak` | 45.769... | 0.045769... |
| STANDARD | `grid_connection_and_tariff.current_applied_evn_tariff_USD_MWh.standard` | 70.5 | 0.0705 |
| PEAK | `grid_connection_and_tariff.current_applied_evn_tariff_USD_MWh.peak` | 130.692... | 0.130692... |

### 2.5 Financial Parameters

Extract from the JSON for the financial stage:

| Parameter | JSON Path | Value |
|-----------|-----------|-------|
| `project_years` | `financial_input.timing.project_lifetime_years` | `20` |
| `interest_rate_pct` | `financial_assumptions.interest_rate.base_rate_floating + financial_assumptions.interest_rate.debt_margin_pct` | `0.065 + 0.02 = 0.085` → `8.5%` |
| `tenor_years` | `financial_assumptions.debt_sizing.maximum_debt_tenor_years` | `10` |
| `target_dscr` | `financial_assumptions.debt_sizing.target_dscr_x` | `1.3` |
| `initial_capex_usd` | `capex.solar_USD_per_MWp × (actual_capacity / 1000) + capex.bess_USD_per_MWh × (total_bess / 1000)` | `450000 × 3.221 + 200000 × 2.15 = 1,449,450 + 430,000 = 1,879,450 USD` |
| `discount_rate_pct` | Use `8.0%` (standard) | `8.0` |
| `cod_date` | Parse `financial_input.timing.commercial_operation_date_excel_serial` (Excel serial `46023`) | Excel date serial 46023 = `2026-01-02` (days since 1899-12-30) |

**Excel date serial conversion formula**: `date = datetime(1899, 12, 30) + timedelta(days=serial_number)`

### 2.6 Pipeline Execution

The pipeline runs the same 4 stages (physics → settlement → aggregation → financial) as the existing `run_full_model()`, but parameterized with Emivest-specific values instead of reading from Excel. Create a new `run_model_from_json()` function that:
1. Calls the JSON/CSV loaders to build `SystemAssumptions`, hourly DataFrame, and degradation table
2. Calls `_run_physics()`, `_run_settlement()`, `_run_aggregation()`, `_run_financial()` with the loaded data
3. Returns the same flat KPI dict as `run_full_model()`

### 2.7 HTML Report Structure

The report must present:

**Section A — Project Summary Card**
- Project name, developer, location, capacity, COD
- Key system parameters (PV capacity, BESS capacity, strategy)

**Section B — Model Results (KPI Dashboard)**
- Year 1 Energy: Solar generation (MWh), direct PV consumption, BESS discharge
- Year 1 Financial: DPPA revenue (USD), grid savings (USD), total first-year revenue
- Return Metrics: Project IRR (%), Equity IRR (%), Unlevered IRR (%), NPV (USD), DSCR (min)

**Section C — Comparison Table (Python vs Reference)**
- Side-by-side table for each KPI: Reference value, Python value, difference, pass/fail
- Use the same tolerance tiers as `test_excel_comparison.py`
- Color-coded: green for pass, red for fail

**Section D — Lifetime Projection Charts** (embedded as inline SVG or base64 PNG via matplotlib)
- 20-year solar generation (MWh) bar chart
- 20-year revenue waterfall (DPPA + grid savings)
- Battery capacity degradation curve

**Section E — Hourly Profile Samples** (optional but valuable)
- Sample day (e.g., Jan 15) showing solar gen, load, SoC, charge/discharge

The HTML must be self-contained (inline CSS, no external dependencies) so it renders correctly when opened in any browser and prints cleanly to PDF via browser print dialog (Ctrl+P).

---

## 3. File Changes

### 3.1 `src/re_storage/inputs/json_loader.py` — **CREATE**

New module for loading project data from JSON+CSV format.

**What to add:**
- `load_assumptions_from_json(json_path: Path) -> SystemAssumptions` — parses `Emivest.json` into the `SystemAssumptions` Pydantic model using the field mapping from §2.1
- `load_hourly_data_from_csv(csv_path: Path) -> pd.DataFrame` — reads the CSV, renames columns per §2.2, handles trailing comma, validates 8760 rows
- `load_degradation_from_json(json_path: Path, project_years: int) -> pd.DataFrame` — builds degradation DataFrame from the JSON `annual_table` per §2.3
- `load_tariff_rates_from_json(json_path: Path) -> dict[TimePeriod, float]` — extracts tariff rates in USD/kWh per §2.4
- `load_financial_params_from_json(json_path: Path) -> dict[str, Any]` — extracts financial parameters per §2.5
- `_excel_serial_to_date(serial: int) -> str` — converts Excel date serial to ISO date string

**What to leave alone:** Do not modify `loaders.py` — the Excel loaders remain untouched.

### 3.2 `src/re_storage/pipeline.py` — **MODIFY**

**What to add:**
- `run_model_from_json(project_dir: Path) -> dict[str, Any]` — new public function that:
  1. Discovers the `.json` and `.csv` files in the given directory
  2. Calls json_loader functions to build assumptions, hourly data, degradation table, tariff rates, financial params
  3. Reuses the existing private functions `_run_physics()`, `_run_settlement()`, `_run_aggregation()`, `_run_financial()`
  4. Returns the same flat KPI dict format

**What to leave alone:** Do not modify `run_full_model()` or any existing private functions. Only add the new `run_model_from_json()` function and its import.

### 3.3 `src/re_storage/reporting/__init__.py` — **CREATE**

Empty `__init__.py` to make `reporting` a subpackage.

### 3.4 `src/re_storage/reporting/html_report.py` — **CREATE**

New module for generating the HTML comparison report.

**What to add:**
- `generate_report(project_config: dict, model_results: dict, reference_kpis: dict | None, lifetime_df: pd.DataFrame, hourly_df: pd.DataFrame) -> str` — returns a complete self-contained HTML string
- `_render_project_summary(config: dict) -> str` — builds Section A HTML
- `_render_kpi_dashboard(results: dict) -> str` — builds Section B HTML
- `_render_comparison_table(results: dict, reference: dict) -> str` — builds Section C HTML with pass/fail coloring
- `_render_lifetime_charts(lifetime_df: pd.DataFrame) -> str` — builds Section D with inline base64 PNG charts using matplotlib
- `_render_hourly_profile(hourly_df: pd.DataFrame, sample_date: str) -> str` — builds Section E
- `_format_number(value: float, fmt: str) -> str` — number formatting helper (e.g., `1,234,567.89`, `12.34%`)
- `_comparison_status(actual: float, expected: float, mode: str, tolerance: float) -> tuple[str, str]` — returns (status_text, css_class) for a KPI comparison

**Styling requirements:**
- Use inline CSS in a `<style>` tag within `<head>`
- Professional styling: clean table borders, alternating row colors, responsive layout
- Print-friendly: `@media print` rules to hide non-essential elements, ensure page breaks work
- Color scheme: Use a professional palette (dark navy headers, light grey alternating rows, green/red for pass/fail)
- Page size: A4 landscape for charts, portrait for tables
- No external fonts, images, or stylesheets — everything inline

### 3.5 `scripts/run_emivest.py` — **CREATE**

CLI script that ties everything together.

**What to add:**
- Argparse CLI with:
  - `--project-dir` (default: `tests/data/projects/emivest`)
  - `--reference` (optional path to reference JSON for comparison)
  - `--output` (default: `reports/emivest_report.html`)
- Main flow:
  1. Load project config JSON (for report metadata)
  2. Call `run_model_from_json(project_dir)`
  3. Optionally load reference JSON
  4. Generate HTML report
  5. Write to output file

### 3.6 `tests/data/references/emivest.json` — **CREATE**

Reference KPI file for the Emivest project. This file must be created manually by the implementer based on external reference values provided by the user. Initially create a **placeholder** with `null` values for all KPIs — the user will fill in the actual reference values.

**Structure** (must match the existing reference format):
```json
{
  "_source_file": "Emivest.json",
  "_note": "Reference KPIs from external model — fill in actual values",
  "project_irr": null,
  "equity_irr": null,
  "unlevered_irr": null,
  "npv_usd": null,
  "dscr_min": null,
  "calc_solar_gen_sum_kwh": null,
  "calc_soc_min_kwh": null,
  "calc_soc_max_kwh": null,
  "year1_solar_generation_mwh": null,
  "year1_dppa_revenue_usd": null,
  "year1_grid_savings_usd": null
}
```

### 3.7 `tests/regression/test_emivest.py` — **CREATE**

Dedicated regression test for the Emivest project (JSON+CSV format).

**What to add:**
- `TestEmivestRegression` class with:
  - `test_model_runs_without_error` — smoke test that `run_model_from_json()` completes
  - `test_kpi_dict_has_expected_keys` — verify all expected KPI keys are present
  - `test_physics_kpis` — solar gen, SoC bounds
  - `test_financial_kpis` — IRR, NPV, DSCR (only runs if reference has non-null values)
  - `test_all_kpis_against_reference` — full comparison using same tolerance tiers as `test_excel_comparison.py`

### 3.8 `tests/unit/test_json_loader.py` — **CREATE**

Unit tests for the new JSON+CSV loader.

**What to add:**
- Tests for each loader function with the actual Emivest data files
- Edge case tests: missing keys, invalid values, wrong CSV row count

### 3.9 `pyproject.toml` — **MODIFY**

**What to add:** Add `matplotlib>=3.7.0` to the `dependencies` list (needed for chart generation in the HTML report).

**What to leave alone:** All other configuration.

---

## 4. Function Signatures

### `src/re_storage/inputs/json_loader.py`

```python
def load_assumptions_from_json(json_path: Path) -> SystemAssumptions:
    """
    Parse a project JSON config file into SystemAssumptions.

    Returns a validated SystemAssumptions instance with all fields
    populated from the JSON structure.
    """

def load_hourly_data_from_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load and normalize hourly time series from a CSV file.

    Returns a DataFrame with 8760 rows and columns matching the
    internal naming convention (datetime, simulation_profile_kw,
    irradiation_wh_m2, load_kw, fmp_usd_per_kwh, cfmp_usd_per_kwh).
    """

def load_degradation_from_json(
    json_path: Path,
    project_years: int = 20,
) -> pd.DataFrame:
    """
    Build degradation table from JSON annual_table.

    Returns a DataFrame with columns: year, pv_factor,
    battery_factor_no_replacement, battery_factor_with_replacement.
    """

def load_tariff_rates_from_json(
    json_path: Path,
) -> dict[TimePeriod, float]:
    """
    Extract tariff rates in USD/kWh from JSON config.

    Returns a mapping of TimePeriod -> rate (USD/kWh).
    Converts from the JSON's USD/MWh values by dividing by 1000.
    """

def load_financial_params_from_json(
    json_path: Path,
) -> dict[str, Any]:
    """
    Extract financial parameters from JSON config.

    Returns a dict with keys: project_years (int), interest_rate_pct (float),
    tenor_years (int), target_dscr (float), initial_capex_usd (float),
    discount_rate_pct (float), cod_date (str, ISO format).
    """

def _excel_serial_to_date(serial: int) -> str:
    """
    Convert an Excel date serial number to ISO date string (YYYY-MM-DD).

    Excel serial 1 = 1900-01-01. Uses the 1899-12-30 epoch convention
    (accounting for the Excel Lotus-123 leap year bug).
    Returns ISO format string, e.g. '2026-01-02'.
    """
```

### `src/re_storage/pipeline.py` (addition)

```python
def run_model_from_json(
    project_dir: Path,
    tariff_rates: dict[TimePeriod, float] | None = None,
) -> dict[str, Any]:
    """
    Run the full RE-Storage pipeline using JSON+CSV project inputs.

    This is the JSON-format equivalent of run_full_model(). It loads
    inputs from a project directory containing a .json config and a .csv
    hourly data file, then runs the same physics/settlement/aggregation/
    financial pipeline.

    Returns the same flat KPI dict format as run_full_model(), plus
    additional keys 'hourly_df' and 'lifetime_df' (DataFrames stored
    in the dict for report generation — not used by regression tests).
    """
```

### `src/re_storage/reporting/html_report.py`

```python
def generate_report(
    project_config: dict[str, Any],
    model_results: dict[str, Any],
    reference_kpis: dict[str, Any] | None,
    lifetime_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    output_path: Path | None = None,
) -> str:
    """
    Generate a self-contained HTML report for a project.

    If output_path is provided, writes the HTML to that file.
    Returns the HTML string in all cases.
    """

def _render_project_summary(config: dict[str, Any]) -> str:
    """
    Render the project summary card as an HTML fragment.

    Returns an HTML string containing project name, capacity,
    developer, and key system parameters in a styled card layout.
    """

def _render_kpi_dashboard(results: dict[str, Any]) -> str:
    """
    Render the KPI dashboard as an HTML fragment.

    Returns an HTML string with Year 1 energy metrics, financial
    metrics, and return metrics in a grid layout.
    """

def _render_comparison_table(
    results: dict[str, Any],
    reference: dict[str, Any],
) -> str:
    """
    Render the Python vs Reference comparison table as HTML.

    Returns an HTML table with columns: KPI, Reference, Python,
    Difference, Tolerance, Status. Rows colored green/red.
    """

def _render_lifetime_charts(
    lifetime_df: pd.DataFrame,
) -> str:
    """
    Render lifetime projection charts as inline base64 PNG images.

    Returns an HTML fragment containing 2-3 charts:
    generation bar chart, revenue stacked bar, battery capacity line.
    """

def _render_hourly_profile(
    hourly_df: pd.DataFrame,
    sample_date: str = "2024-01-15",
) -> str:
    """
    Render a sample day's hourly profile as an inline chart.

    Returns an HTML fragment with a multi-line chart showing
    solar_gen_kw, load_kw, soc_kwh, and discharged_kw for one day.
    """

def _format_number(value: float, fmt: str = ",.2f") -> str:
    """
    Format a number for display in the report.

    Returns the formatted string. Handles NaN gracefully (returns 'N/A').
    fmt examples: ',.2f' for 1,234.56, '.2%' for 12.34%, ',.0f' for 1,235.
    """

def _comparison_status(
    actual: float,
    expected: float,
    mode: str,
    tolerance: float,
) -> tuple[str, str]:
    """
    Determine pass/fail status for a KPI comparison.

    Returns (status_text, css_class) where status_text is 'PASS' or 'FAIL'
    and css_class is 'status-pass' or 'status-fail'.
    """
```

---

## 5. Test Specifications

### 5.1 `tests/unit/test_json_loader.py`

**Test: `test_load_assumptions_from_json_returns_valid_schema`**
- Input: `tests/data/projects/emivest/Emivest.json`
- Expected: Returns `SystemAssumptions` instance
- Check fields:
  - `simulation_capacity_kwp == 100.0`
  - `actual_capacity_kwp == 3221.0`
  - `usable_bess_capacity_kwh == 1827.5` (2150 × 0.85)
  - `bess_power_rating_kw == 1000.0`
  - `charge_efficiency == 0.95`
  - `discharge_efficiency == 0.95`
  - `strategy_mode == 1`
  - `charging_mode == 1`
  - `charge_start_hour == 10`
  - `charge_end_hour == 16`
  - `min_direct_pv_share == 0.1`
  - `active_pv2bess_share == 0.3`
  - `strike_price_usd_per_kwh ≈ 0.069230769` (1800/26000, tolerance 1e-6)
  - `k_factor == 1.02`
  - `kpp == 1.027263`
  - `bess_enabled == True`
  - `dppa_enabled == True`
  - `scale_factor == 32.21` (3221/100)

**Test: `test_load_hourly_data_from_csv_shape`**
- Input: `tests/data/projects/emivest/Emivest additional data.csv`
- Expected:
  - DataFrame has 8760 rows
  - Columns include all of: `datetime`, `simulation_profile_kw`, `irradiation_wh_m2`, `load_kw`, `fmp_usd_per_kwh`, `cfmp_usd_per_kwh`
  - No NaN values in any required column
  - First row datetime parses to `2024-01-01 00:00`
  - First row `load_kw == 1020.0`
  - First row `simulation_profile_kw == 0.0`

**Test: `test_load_hourly_csv_no_negative_values`**
- Input: same CSV
- Expected: No negative values in `simulation_profile_kw`, `irradiation_wh_m2`, `load_kw`

**Test: `test_load_degradation_from_json`**
- Input: `Emivest.json`
- Expected:
  - DataFrame has 20 rows (years 1-20)
  - Columns: `year`, `pv_factor`, `battery_factor_no_replacement`, `battery_factor_with_replacement`
  - Year 1: `pv_factor == 1.0`, `battery_factor_with_replacement == 1.0`
  - Year 2: `pv_factor == 0.98`, `battery_factor_with_replacement == 0.9745`
  - Year 11: `battery_factor_with_replacement == 0.9745` (replacement resets)
  - Year 20: `pv_factor == 0.881`
  - All factors in range (0, 1]

**Test: `test_load_tariff_rates_from_json`**
- Input: `Emivest.json`
- Expected:
  - `TimePeriod.OFF_PEAK: ≈ 0.045769` (45.769.../1000)
  - `TimePeriod.STANDARD: 0.0705` (70.5/1000)
  - `TimePeriod.PEAK: ≈ 0.130692` (130.692.../1000)

**Test: `test_load_financial_params_from_json`**
- Input: `Emivest.json`
- Expected:
  - `project_years == 20`
  - `interest_rate_pct == 8.5` (6.5 + 2.0, as percentage)
  - `tenor_years == 10`
  - `target_dscr == 1.3`
  - `initial_capex_usd ≈ 1,879,450.0` (tolerance ±1.0)
  - `cod_date == "2026-01-02"` (from Excel serial 46023)

**Test: `test_excel_serial_to_date`**
- Input/Expected pairs:
  - `46023 → "2026-01-02"`
  - `44927 → "2023-01-01"` (known reference)
  - `1 → "1900-01-01"`
  - `60 → "1900-02-28"` (before the Lotus-123 bug date)

### 5.2 `tests/regression/test_emivest.py`

**Test: `test_model_runs_without_error`**
- Input: `tests/data/projects/emivest/` directory
- Expected: `run_model_from_json()` returns a dict without raising any exception

**Test: `test_kpi_dict_has_expected_keys`**
- Expected keys present: `project_irr`, `equity_irr`, `unlevered_irr`, `npv_usd`, `dscr_min`, `calc_solar_gen_sum_kwh`, `calc_soc_min_kwh`, `calc_soc_max_kwh`, `year1_solar_generation_mwh`, `year1_dppa_revenue_usd`, `year1_grid_savings_usd`

**Test: `test_solar_generation_reasonable`**
- Expected: `year1_solar_generation_mwh` is between 3,000 and 6,000 MWh (the JSON says `energy_yield_kWh_pa = 4,578,435` → ~4,578 MWh; allow wide tolerance for model differences)

**Test: `test_soc_bounds`**
- Expected:
  - `calc_soc_min_kwh >= 0.0`
  - `calc_soc_max_kwh <= 1827.5` (usable capacity)

**Test: `test_irr_values_reasonable`**
- Expected: `project_irr` and `equity_irr` are between -0.5 and 1.0 (sanity check — not NaN, not extreme)

**Test: `test_all_kpis_against_reference`**
- Loads reference from `tests/data/references/emivest.json`
- Skips if all reference values are `null`
- Uses same tolerance tiers as `test_excel_comparison.py`:
  - IRR: absolute ±0.0001
  - Energy: relative ±0.01%
  - Revenue: relative ±0.01%
  - NPV: relative ±0.01%
  - DSCR: absolute ±0.001

---

## 6. Implementation Order

1. **Add `matplotlib` dependency to `pyproject.toml`** — add `"matplotlib>=3.7.0"` to the `dependencies` list. Run `pip install -e ".[dev]"` to verify installation.

2. **Create `src/re_storage/inputs/json_loader.py`** — implement all loader functions per §4. Write the `_excel_serial_to_date` helper first (simplest, no dependencies), then `load_assumptions_from_json`, then `load_hourly_data_from_csv`, then `load_degradation_from_json`, then `load_tariff_rates_from_json`, then `load_financial_params_from_json`.

3. **Create `tests/unit/test_json_loader.py`** — write and run all unit tests from §5.1. Every test must pass before proceeding. Verify: `pytest tests/unit/test_json_loader.py -v`

4. **Modify `src/re_storage/pipeline.py`** — add `run_model_from_json()` function. Import the json_loader module. The function must call the existing `_run_physics`, `_run_settlement`, `_run_aggregation`, `_run_financial` in sequence with the JSON-loaded inputs. Also store `hourly_df` and `lifetime_df` in the returned dict (for report generation).

5. **Create `tests/data/references/emivest.json`** — placeholder file with all-null values per §3.6.

6. **Create `tests/regression/test_emivest.py`** — write regression tests per §5.2. Run smoke test and bounds checks: `pytest tests/regression/test_emivest.py -v`. The reference comparison test should skip gracefully when all values are null.

7. **Create `src/re_storage/reporting/__init__.py`** — empty file.

8. **Create `src/re_storage/reporting/html_report.py`** — implement the report generator per §4. Build the HTML as string concatenation (no template engine dependency). Charts use matplotlib with `savefig()` to a `BytesIO` buffer, then base64-encode.

9. **Create `scripts/run_emivest.py`** — CLI script per §3.5. Run it: `python scripts/run_emivest.py` and verify the output HTML opens in a browser and prints cleanly to PDF.

10. **Run full test suite** — `pytest -v` to verify nothing is broken. All existing 175 tests must still pass.

---

## 7. Gotchas

### 7.1 Unit Confusion: VND vs USD

The JSON stores tariff rates in both VND and USD/MWh. The model pipeline expects tariff rates in **USD/kWh** (not USD/MWh, not VND). The conversion is: `USD_per_kWh = USD_per_MWh / 1000`. Getting this wrong by a factor of 1000 will make grid savings ~1000x too large or too small.

The FMP and CFMP columns in the CSV are in **VND** (not USD) — values like 1377.55 VND. The DPPA settlement module (`settlement/dppa.py`) handles the VND→USD conversion internally using the exchange rate. Do NOT pre-convert these columns to USD.

### 7.2 Degradation Table: `null` values in Year 1

In the JSON, Year 1 has `battery_loss_cumulative: null` and `pv_loss_annual: null`. The retention values (1.0) are still valid. The loader must handle `null` JSON values gracefully — use the retention columns (`pv_retention`, `battery_retention`, `battery_with_replacement`), not the loss columns.

### 7.3 Project Lifetime: 20 years, not 25

The Emivest project is 20 years (not the default 25 used by the existing Ecoplexus project). Every function call in the pipeline that accepts `project_years` must receive `20`. The degradation table only has 20 rows — passing `project_years=25` will raise a `DegradationTableError` because years 21–25 are missing.

### 7.4 CSV Trailing Comma

The CSV file has a trailing comma on every row (including the header), which creates an empty unnamed column. When loading with `pd.read_csv()`, pandas will create an `Unnamed: 6` column. Drop any columns whose name starts with `Unnamed` before proceeding.

### 7.5 Scale Factor Magnitude

The Emivest scale factor is `32.21` (3221 kWp actual / 100 kWp simulation). This is much larger than the Ecoplexus project (scale factor = 1.0). Verify that the physics engine handles this correctly — solar generation values will be ~32x the simulation profile values.

### 7.6 Excel Date Serial Conversion

The Excel date serial `46023` should convert to `2026-01-02`. The standard formula is `datetime(1899, 12, 30) + timedelta(days=serial)`. Be aware of the [Lotus 1-2-3 leap year bug](https://en.wikipedia.org/wiki/Leap_year_bug): Excel incorrectly treats 1900 as a leap year. For dates after March 1, 1900, the serial is off by 1 day from the true date. Since `46023` is well past 1900, use the `1899-12-30` epoch (which accounts for this bug).

### 7.7 Usable BESS Capacity vs Total

`usable_bess_capacity_kwh = total_capacity × depth_of_discharge = 2150 × 0.85 = 1827.5 kWh`. The SoC must never exceed 1827.5. Do NOT use the total capacity (2150) as the upper bound.

### 7.8 Matplotlib Backend for Headless Environments

When generating charts, set `matplotlib.use('Agg')` **before** importing `matplotlib.pyplot`. This ensures it works in headless environments (CI, servers) without a display. Put this at the top of `html_report.py`.

### 7.9 HTML Self-Containment

The report HTML must work when opened from a file system (no web server). This means:
- No external CSS/JS CDN links
- No `fetch()` calls
- Charts must be base64-encoded inline (`<img src="data:image/png;base64,...">`)
- All styles in a `<style>` tag

### 7.10 Print-to-PDF Layout

Use `@media print` CSS rules:
- Set `@page { size: A4; margin: 15mm; }`
- Use `page-break-before: always` before chart sections
- Hide interactive elements (if any)
- Ensure tables don't split across pages: `table { page-break-inside: avoid; }`

### 7.11 Existing Pipeline Coupling

`run_model_from_json()` should NOT call `run_full_model()`. It should call the internal `_run_physics()`, `_run_settlement()`, `_run_aggregation()`, `_run_financial()` directly. The `run_full_model()` function starts by calling Excel-specific loaders (`load_assumptions_from_cells`, `load_hourly_data`, etc.) which will fail on JSON/CSV inputs.

### 7.12 Monthly Aggregation Requires Specific Columns

The `aggregate_hourly_to_monthly()` function expects columns like `load_kw`, `solar_gen_kw`, `grid_load_after_solar_kw`, `grid_load_after_re_kw`, `grid_savings_usd` in the hourly DataFrame. These are created by `_run_physics()` and `_run_settlement()`. Ensure the column names match exactly.

### 7.13 The `demand_reduction_target` for Arbitrage Mode

For `strategy_mode=1` (Energy Arbitrage), `demand_reduction_target` should be `0.0`. The JSON's `peak_shaving.demand_reduction_target_pct` is `0`, confirming this. Setting it to any non-zero value would incorrectly activate demand charge reduction logic.

### 7.14 Naming Convention: File Discovery in `run_model_from_json()`

The function receives a directory path. It needs to find the `.json` and `.csv` files inside. Do NOT hardcode `Emivest.json` — use glob patterns (e.g., `*.json`, `*.csv`) to discover the files, but assert there is exactly one of each. This makes the loader reusable for future JSON-based projects.

### 7.15 Return Dict Must Include DataFrames for Reporting

The `run_model_from_json()` function must return more than just scalar KPIs. For the HTML report, it also needs the hourly DataFrame (for profile charts) and lifetime DataFrame (for projection charts). Store these as `results["_hourly_df"]` and `results["_lifetime_df"]` with underscore prefix to distinguish them from scalar KPIs. The regression test should ignore keys starting with `_`.

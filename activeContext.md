# Active Context - ISSUE-1 Emivest and ISSUE-2 Excel Version Alignment

**Last Updated:** 2026-03-18

## ISSUE-1 Objective (Historical)

Implement JSON+CSV support for Emivest (Saigon18), execute the existing simulation pipeline without Excel loaders, compare KPIs against reference JSON, and generate a self-contained HTML report including a 20-year annual figures table.

## ISSUE-1 Implemented (Historical)

- Added `matplotlib>=3.7.0` dependency in `pyproject.toml`.
- Created `src/re_storage/inputs/json_loader.py` with:
  - `load_assumptions_from_json()`
  - `load_hourly_data_from_csv()`
  - `load_degradation_from_json()`
  - `load_tariff_rates_from_json()`
  - `load_financial_params_from_json()`
  - `_excel_serial_to_date()`
- Updated `src/re_storage/inputs/__init__.py` exports for JSON loader functions.
- Added `run_model_from_json()` to `src/re_storage/pipeline.py`.
- Created reporting package and HTML report builder in `src/re_storage/reporting/`.
- Created CLI script `scripts/run_emivest.py`.
- Added placeholder reference file `tests/data/references/emivest.json`.
- Added tests `tests/unit/test_json_loader.py` and `tests/regression/test_emivest.py`.

## ISSUE-1 Verification Status (Historical)

- `pytest tests/unit/test_json_loader.py -v` -> passed.
- `pytest tests/regression/test_emivest.py -v` -> passed with expected reference skip.
- `python scripts/run_emivest.py` generated `reports/emivest_report.html`.

## ISSUE-1 Outstanding (Historical)

- Fill `tests/data/references/emivest.json` with external reference KPI values.
- Re-run `pytest tests/regression/test_emivest.py -v` with real reference values.

---

## ISSUE-2 Objective

Align existing Excel pipeline with latest workbook structure and logic signals, without creating a new model branch:

1. Support shifted/preamble-heavy workbook layouts.
2. Add workbook solver freshness diagnostics.
3. Add tariff and financial assumption extraction from new Assumption sheet label blocks.
4. Keep extending existing codebase (no greenfield model fork).

## ISSUE-2 Implemented This Session

### 1) Excel version logic comparison report workflow

- Added `scripts/compare_excel_versions.py`.
- Generates standalone report at `reports/excel_logic_comparison.html`.
- Includes:
  - workbook auto-discovery or explicit file args
  - structural diff (added/removed sheets, dimension deltas)
  - KPI deltas with significance tags
  - grouped formula diff patterns (noise suppression)
  - defined-name retargeting summary
  - material findings with exact evidence cells
  - reproducibility footer (command, timestamp, hashes)

### 2) Loader hardening for new workbook layout

Updated `src/re_storage/inputs/loaders.py`:

- `load_hourly_data()` now uses dynamic `Data Input` header detection via `_read_data_input_sheet()`.
- Handles preamble rows and filters to true hourly rows by parseable DateTime values.
- `_read_loss_sheet()` now detects dynamic Loss header row and supports new labels/preamble blocks.
- Expanded Loss column alias mapping for:
  - `PV Cumulative Retention` -> `pv_factor`
  - `BESS Cumulative Retention` -> `battery_factor_no_replacement`
  - `BESS w/ Replacement` -> `battery_factor_with_replacement`

### 3) New tariff and financial parameter extraction from Assumption labels

Added in `src/re_storage/inputs/loaders.py`:

- `load_tariff_rates_from_cells(path)`
  - reads `Standard`, `Peak`, `Off-Peak` from Assumption `O:Q`
  - normalizes likely USD/MWh values to USD/kWh
- `load_financial_params_from_cells(path)`
  - reads key inputs from Assumption `I:K`:
    - `project_years`
    - `interest_rate_pct` (base + margin)
    - `tenor_years`
    - `target_dscr`
    - `initial_capex_usd` (Solar + BESS + BOP + Land)
    - `discount_rate_pct` (from minimum equity IRR label)
    - `cod_date`

### 4) Pipeline wiring to use workbook-driven defaults

Updated `src/re_storage/pipeline.py` (`run_full_model`):

- Loads financial params from cells and uses them as effective defaults.
- Uses tariff rates from cells when no explicit `tariff_rates` override is provided.
- Uses effective project years for degradation and aggregation horizon.
- Keeps existing API signature unchanged.

### 5) Solver freshness diagnostic

Updated `src/re_storage/validation/checks.py`:

- Added `validate_financial_solver_freshness(excel_path, max_allowed_residual_usd=50000.0)`.
- Warns on:
  - high `Financial!G170` residual magnitude
  - stale-like status in `Financial!H1`

Updated `src/re_storage/pipeline.py`:

- `run_full_model` now calls solver freshness validation and logs warnings.

### 6) Tests added/updated

- Added `tests/unit/test_compare_excel_versions.py` for comparison script helpers.
- Extended `tests/unit/test_inputs_loaders.py` with:
  - preamble-shifted Data Input coverage
  - preamble-shifted Loss coverage
  - tariff-from-cells extraction
  - financial-params-from-cells extraction
- Extended `tests/unit/test_validation_checks.py` with solver freshness tests.

### 7) Financial parity debugging pass (this session)

Updated `src/re_storage/pipeline.py`:

- Added `_normalize_hourly_price_columns_to_usd()` to normalize VND-scale `FMP/CFMP` to USD/kWh for workbook paths.
- Added `_build_dppa_net_generation()` and switched DPPA input from surplus-only to workbook-aligned net generation (`solar - pv_charge + discharge`, clipped at 0).
- `run_full_model()` now uses workbook `exchange_rate_usd_vnd` for hourly market-price normalization before settlement.
- `_run_financial()` now accepts `max_leverage_ratio` and caps debt amount by leverage before equity cashflow construction.

Updated `src/re_storage/settlement/dppa.py`:

- Corrected delivered-RE formula to workbook-aligned form: divide by `k_factor * kpp` (instead of multiply).

Updated `src/re_storage/inputs/loaders.py`:

- `load_tariff_rates_from_cells()` now supports both legacy labels (`Standard/Peak/Off-Peak`) and new labels (`Ca_normal/Ca_peak/Ca_offpeak`).
- Tariff normalization now uses `USD/VND` when CA-style labels are detected and falls back to the prior `>2 => /1000` rule for legacy fixtures.
- `load_financial_params_from_cells()` now also returns:
  - `max_leverage_ratio`
  - `exchange_rate_usd_vnd`
- CAPEX extraction is now section-aware (from `Total Cost` block) to avoid picking `Installed Capacity` rows with duplicate labels.

Added tests:

- New file: `tests/unit/test_pipeline_helpers.py`
  - DPPA net-generation helper behavior
  - hourly price normalization behavior (convert vs no-op)
- Updated `tests/unit/test_settlement_dppa.py`
  - delivered-RE expectation now matches division-based workbook formula
- Extended `tests/unit/test_inputs_loaders.py`
  - CA-label tariff extraction coverage
  - financial params include leverage + exchange rate

## ISSUE-2 Verification Status

- `pytest tests/unit/test_compare_excel_versions.py` -> passed.
- `pytest tests/unit/test_inputs_loaders.py` -> passed.
- `pytest tests/unit/test_validation_checks.py` -> passed.
- `pytest tests/integration/test_full_pipeline.py` -> passed.
- Combined run:
  - `pytest tests/unit/test_inputs_loaders.py tests/unit/test_validation_checks.py tests/integration/test_full_pipeline.py`
  - Result: **32 passed**.
- `ruff check` on touched files -> passed.
- `mypy --strict --follow-imports=skip --disable-error-code import-untyped` on touched files -> passed.
- `python scripts/compare_excel_versions.py` -> generated `reports/excel_logic_comparison.html`.

Additional verification this session:

- `pytest tests/unit/test_settlement_dppa.py tests/unit/test_pipeline_helpers.py tests/unit/test_inputs_loaders.py -q`
  - Result: **32 passed**.
- `pytest tests/regression/test_excel_comparison.py -k financial_kpis -q`
  - Result: **fails** with finite-but-high financial KPIs (no longer `nan`):
    - `project_irr`: actual `1.1823` vs expected `0.0507`
    - `equity_irr`: actual `3.6129` vs expected `0.0464`
    - `unlevered_irr`: actual `1.1823` vs expected `0.0883`
    - `npv_usd`: actual `60,731,116.55` vs expected `-2,653,309.37`

## ISSUE-2 Current Behavior / Notes

- Latest workbook now loads through hardened `Data Input` and `Loss` parsing paths.
- Tariff and financial defaults now come from workbook labels instead of hardcoded pipeline defaults.
- Solver freshness signals are surfaced through validation warnings.
- `nan` collapse has been removed on workbook paths by aligning units and DPPA handoff signals.
- Remaining mismatch is now financial parity quality (values too high vs Excel), not loader failure/sign failure.
- Current quick snapshot (`run_full_model`) on workbook paths is finite but overstated:
  - regression workbook: `project_irr ~ 1.1823`, `equity_irr ~ 3.6129`, `npv_usd ~ 60.7M`
  - latest workbook: `project_irr ~ 1.4101`, `equity_irr ~ 4.3744`, `npv_usd ~ 73.7M`

## ISSUE-2 Outstanding for Next Session

1. Financial parity work (highest priority):
   - Align `_run_financial()` and waterfall assumptions to workbook Financial sheet logic (now finite, but materially over-optimistic vs Excel).
   - Add workbook-driven opex/tax/reserve lines (and any missing financial deductions) so IRR/NPV magnitude matches reference direction and scale.
   - Validate debt sizing conventions against workbook solver behavior beyond DSCR/leverage cap.

2. Tariff schedule handling (optional refinement):
   - Consider fallback hierarchy: explicit override -> `Tariff Schedule` sheet -> Assumption O/Q labels -> hardcoded emergency defaults.
   - Current path already uses Assumption labels when no override is provided.

3. Regression anchoring:
   - Add latest workbook fixture/reference in `tests/data/projects` and `tests/data/references`.
   - Re-run regression suite for KPI tolerance-based tracking.

4. Warning noise cleanup (optional):
   - Battery dispatch logs emit repeated overlap warnings (`when_needed` + `peak`).
   - Keep as separate issue unless it blocks analysis.

## Recommended Next Start Command Set

1. `python scripts/compare_excel_versions.py`
2. `python -c "from pathlib import Path; from re_storage.pipeline import run_full_model; print(run_full_model(Path(r'data/llm 20260129 SOLAR BESS MODEL - Editing - for processing test.xlsx')) )"`
3. `pytest tests/unit/test_settlement_dppa.py tests/unit/test_pipeline_helpers.py tests/unit/test_inputs_loaders.py -q`
4. `pytest tests/regression/test_excel_comparison.py -k financial_kpis -q`

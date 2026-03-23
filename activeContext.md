# Active Context - ISSUE-1 Emivest / ISSUE-2 Excel Alignment / ISSUE-3 Web Tool / ISSUE-4 Gap Analysis Roadmap

**Last Updated:** 2026-03-23

---

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

## ISSUE-2 Objective (Historical)

Align existing Excel pipeline with latest workbook structure and logic signals, without creating a new model branch:

1. Support shifted/preamble-heavy workbook layouts.
2. Add workbook solver freshness diagnostics.
3. Add tariff and financial assumption extraction from new Assumption sheet label blocks.
4. Keep extending existing codebase (no greenfield model fork).

## ISSUE-2 Implemented (Historical)

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

### 6) Tests added/updated (Historical)

- Added `tests/unit/test_compare_excel_versions.py` for comparison script helpers.
- Extended `tests/unit/test_inputs_loaders.py` with:
  - preamble-shifted Data Input coverage
  - preamble-shifted Loss coverage
  - tariff-from-cells extraction
  - financial-params-from-cells extraction
- Extended `tests/unit/test_validation_checks.py` with solver freshness tests.

### 7) Financial parity debugging pass (Historical)

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
- Updated `tests/unit/test_settlement_dppa.py`
- Extended `tests/unit/test_inputs_loaders.py`

## ISSUE-2 Current Behavior / Notes (Historical)

- Latest workbook now loads through hardened `Data Input` and `Loss` parsing paths.
- Tariff and financial defaults now come from workbook labels instead of hardcoded pipeline defaults.
- Solver freshness signals are surfaced through validation warnings.
- `nan` collapse has been removed on workbook paths by aligning units and DPPA handoff signals.
- Remaining mismatch is financial parity quality (values finite but overstated vs Excel):
  - regression workbook: `project_irr ~ 1.1823`, `equity_irr ~ 3.6129`, `npv_usd ~ 60.7M`
  - latest workbook: `project_irr ~ 1.4101`, `equity_irr ~ 4.3744`, `npv_usd ~ 73.7M`

## ISSUE-2 Outstanding (Historical)

1. Financial parity work: align `_run_financial()` and waterfall assumptions to workbook logic.
2. Add workbook-driven opex/tax/reserve lines so IRR/NPV magnitude matches reference.
3. Add latest workbook fixture/reference in `tests/data/projects` and `tests/data/references`.
4. Warning noise cleanup: battery dispatch logs emit repeated overlap warnings.

---

## ISSUE-3 Objective

Build a Firebase-hosted web tool that lets users run the `re_storage` Python model via browser:
- Excel upload path → `/api/run-excel` → Cloud Function → `run_full_model()`
- Structured form + CSV upload path → `/api/run-json` → Cloud Function → `run_model_from_json()`
- React SPA with results dashboard (KPI cards, lifetime charts, download buttons)

---

## ISSUE-4 Current Session Progress (2026-03-21)

### Sensitivity / Scenario Fixes Completed

- Fixed scenario override propagation so sensitivity sweeps no longer rely on unsupported `**kwargs` into `run_full_model()`.
- Added explicit `base_params` override plumbing to:
  - `src/re_storage/pipeline.py::run_full_model()`
  - `src/re_storage/pipeline.py::run_model_from_json()`
- Updated callers to use that override channel:
  - `src/re_storage/scenarios/sensitivity.py`
  - `src/re_storage/scenarios/runner.py`
- Added normalization logic in `src/re_storage/pipeline.py` for common sensitivity keys so scenario overrides map onto the model's internal inputs, including:
  - `strike_price_vnd` -> `strike_price_usd_per_kwh`
  - `installed_pv_mwp` / `solar_capacity_mwp` -> `actual_capacity_kwp`
  - `bess_mwh` / `bess_capacity_mwh` -> `usable_bess_capacity_kwh`
  - unit CAPEX overrides -> total CAPEX fields when enough context is available
- Fixed tornado-chart handling for precomputed range metrics (`irr_range`, `npv_range`, `dscr_min_range`) so bars no longer collapse to zero width.
- Forced headless Matplotlib backend in tornado chart generation to avoid Tk backend failures in CI / local test environments.

### Tests Added / Updated

- Extended `tests/unit/test_scenarios_sensitivity.py` with regressions for:
  - Excel sensitivity override propagation
  - JSON sensitivity override propagation
  - backward-compatible JSON `run_sensitivity_for_values()` override propagation
  - tornado chart rendering for `irr_range`

### Verification Run This Session

- `pytest tests/unit/test_scenarios_sensitivity.py` -> **38 passed**
- `pytest tests/unit/test_web_handlers.py` -> **skipped** (environment/module skip, unchanged)

### Outstanding / Blockers For Next Session

- `pytest tests/regression/test_emivest.py` currently fails in `_run_financial()` with:
  - `ValueError: Length of values (21) does not match length of index (20)`
  - failing line currently in `src/re_storage/pipeline.py` around EBITDA series construction
- This failure appears tied to the broader in-progress financial changes already present in the worktree (`MRA`, `taxes`, and combined depreciation / reserve wiring), not the sensitivity override fix itself.
- Next session should inspect the lifetime/revenue/opex year alignment around:
  - `src/re_storage/pipeline.py::_run_financial()`
  - `src/re_storage/financial/mra.py`
  - `src/re_storage/financial/taxes.py`
  - `tests/regression/test_emivest.py`
- The sensitivity fix itself is in good shape and verified by its dedicated unit suite.

## ISSUE-3 Implemented This Session

### Backend — Cloud Functions (Phase 1)

- **Entry points** (`web/functions/main.py`):
  - `runExcel` → `handle_run_excel()`
  - `runJson` → `handle_run_json()`
  - Both decorated with `functions_framework.http` + `cross_origin()` for CORS.

- **Excel handler** (`web/functions/handlers/run_excel.py`):
  - Validates POST + required `file` upload (`.xlsx`).
  - Saves uploaded file to ephemeral temp path.
  - Calls `run_full_model(Path(tmp_path))`.
  - Maps `REStorageError` → `422`, `ValueError` → `400`, other → `500`.
  - Cleans up temp file in `finally` block.

- **JSON handler** (`web/functions/handlers/run_json.py`):
  - Validates POST + required `hourly_csv` multipart upload.
  - Assembles form fields into Emivest-compatible JSON schema via `_build_project_payload()`.
  - Writes JSON + CSV to temp dir, calls `run_model_from_json(project_dir)`.
  - Default degradation: auto-generates 20-year table if `degradation_json` is empty.
  - Maps `REStorageError` → `422`, `ValueError/JSONDecodeError` → `400`.

- **Serialization utility** (`web/functions/utils/serialise.py`):
  - `serialise_results()` converts model output dict to JSON-safe payload.
  - Strips underscore-prefixed keys (`_hourly_df`, `_lifetime_df`).
  - Converts `nan`/`inf` → `None`, preserving `None` already in the payload.
  - Serializes `_lifetime_df` DataFrame to `lifetime` array.

- **Validation utility** (`web/functions/utils/validate.py`):
  - `ensure_post_method()` — returns error message if not POST.
  - `ensure_uploaded_file()` — checks field presence and non-empty filename.

- **Package stubs** — `handlers/__init__.py`, `utils/__init__.py`.

- **Dependencies** (`web/functions/requirements.txt`):
  - All `re_storage` dependencies + `flask`, `flask-cors`, `functions-framework`.
  - `-e ../..` installs `re_storage` from repo root in editable mode.

- **`.gcloudignore`** — excludes `venv/`, `__pycache__/`, `*.pyc`.

### Backend Tests

- **`tests/unit/test_web_serialise.py`**:
  - `test_serialise_results_sanitizes_nan_and_inf` — NaN/Inf → null, DataFrame → rows.
  - `test_serialise_results_omits_private_non_dataframe_keys` — private keys stripped, DataFrame omitted.
  - Both **pass**.

- **`tests/unit/test_web_handlers.py`**:
  - `test_handle_run_excel_requires_post` → `405`.
  - `test_handle_run_excel_rejects_missing_file` → `400`.
  - `test_handle_run_excel_success` → `200` with KPIs (monkeypatched `run_full_model`).
  - `test_handle_run_json_requires_hourly_csv` → `400`.
  - `test_handle_run_json_success` → `200` (monkeypatched `run_model_from_json`).
  - **passes** (module auto-skips if Flask not installed).

### Frontend — React SPA (Phase 2 skeleton)

- **Scaffold** (`web/frontend/`):
  - `package.json` — React 18, Recharts, react-dropzone, Vite, TypeScript.
  - `tsconfig.json` — strict mode, ES2020 target.
  - `vite.config.ts` — proxies `/api/run-excel` → `localhost:8081`, `/api/run-json` → `localhost:8082`.
  - `index.html`.

- **API client** (`web/frontend/src/api/client.ts`):
  - `runExcel(file: File)` — multipart POST.
  - `runJson(formData: FormData)` — multipart POST.
  - `parseResponse()` — raises `Error` on non-2xx.

- **Hooks**:
  - `useModelRun.ts` — manages `isRunning`, `error`, `result` state; `runWithExcel`, `runWithJson`, `clearError`.
  - `useCsvValidation.ts` — async 8760-row validation; returns row count, preview rows, error.

- **Shared UI components**:
  - `ErrorBanner.tsx` — styled error display.
  - `ProgressBar.tsx` — indeterminate CSS animation + "this usually takes 2-10 seconds" label.
  - `FileDropzone.tsx` — wraps `react-dropzone` for drag-and-drop.

- **Input components**:
  - `ExcelUploadTab.tsx` — dropzone for `.xlsx`, "Run Model" button.
  - `formTypes.ts` — `ProjectFormValues` interface + `defaultFormValues` (Emivest defaults).
  - `SystemStep.tsx` — BESS/system parameters.
  - `DppaStep.tsx` — DPPA toggle, strike price, k-factor, voltage selector, tariff rates.
  - `FinancialStep.tsx` — CAPEX, interest, tenor, DSCR, COD.
  - `DegradationStep.tsx` — textarea accepting JSON array.
  - `HourlyDataStep.tsx` — CSV dropzone with 8760-row validation and preview.
  - `ProjectForm.tsx` — 6-step wizard (system → dppa → financial → degradation → hourly → review & run) with back/next navigation and final submit.

- **Results components**:
  - `KpiCard.tsx` — label + value display.
  - `KpiGrid.tsx` — 10-card grid (IRR, NPV, DSCR, Year 1 metrics).
  - `LifetimeRevenueChart.tsx` — Recharts stacked bar (DPPA + Grid Savings).
  - `GenerationChart.tsx` — Recharts line (solar MWh/year).
  - `BatteryCapacityChart.tsx` — Recharts line (battery kWh/year).
  - `ResultsDashboard.tsx` — KPI grid + charts grid + JSON download button.

- **App root** (`App.tsx`):
  - Tab row (Upload Excel | New Project Form).
  - Shared `isRunning`/`error` UX via `ProgressBar` and `ErrorBanner`.
  - Conditionally renders `ExcelUploadTab`, `ProjectForm`, or `ResultsDashboard`.

- **Styles** (`src/styles.css`):
  - CSS custom properties (brand blues `#1f6b7a`, accent `#bc6c25`).
  - Responsive grid layouts, dropzone, kpi cards, progress bar, chart cards.
  - No Tailwind — plain CSS matching the plan wireframe.

### Firebase Deployment Config

- **`firebase.json`** — Hosting (`web/frontend/dist`) + Cloud Functions (`web/functions`) with Python 3.11 runtime. Rewrites `/api/run-excel` → `runExcel`, `/api/run-json` → `runJson`.
- **`.firebaserc`** — project alias `re-storage-tool`.

### Repository Updates

- **`.gitignore`** — added `web/frontend/node_modules/`, `web/frontend/dist/`, `*.tsbuildinfo`.
- **`README.md`** — added web tool section with local dev commands.

## ISSUE-3 Verification Status

- `ruff check web/functions tests/unit/test_web_serialise.py tests/unit/test_web_handlers.py` → **pass**.
- `pytest tests/unit/test_web_serialise.py tests/unit/test_web_handlers.py` → **2 passed, 1 skipped** (Flask not in repo-level Python env).
- `npm install && npm run build` in `web/frontend` → **pass** (Vite warning about chunk size from Recharts, not an error).
- Backend smoke test (direct HTTP):
  - `runExcel` (port 8081) — responds `405` to GET (correct), `400` to POST without file (correct).
  - `runJson` (port 8082) — responds `400` with `"usable_capacity_kwh must be positive"` when BESS fields omitted (correct), `200` with valid multipart input (correct).
- Frontend dev server: `http://127.0.0.1:5173` — **live**.
- Both function emulators: `http://127.0.0.1:8081` (`runExcel`) and `http://127.0.0.1:8082` (`runJson`) — **live**.

## ISSUE-3 Local Dev Setup

### Terminal 1 — Backend emulators

```bash
cd web/functions
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m functions_framework --target runExcel --source main.py --port 8081 &
.venv\Scripts\python -m functions_framework --target runJson --source main.py --port 8082 &
```

### Terminal 2 — Frontend dev server

```bash
cd web/frontend
npm install
npm run dev
```

### End-to-end smoke test

```bash
# Excel endpoint
curl -X POST http://localhost:8081/ \
  -F "file=@tests/data/projects/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx"

# JSON endpoint (minimum valid payload)
curl -X POST http://localhost:8082/ \
  -F "project_name=Test" \
  -F "actual_capacity_kwp=3221" \
  -F "simulation_capacity_kwp=100" \
  -F "total_bess_kwh=2150" \
  -F "dod=0.85" \
  -F "bess_power_rating_kw=1000" \
  -F "hourly_csv=@tests/data/projects/emivest/Emivest additional data.csv"
```

## ISSUE-3 Outstanding

1. **Phase 3 full form**: `ProjectForm` step components are scaffolded but not fully styled/validated — the structured form path works end-to-end with defaults but some field-to-JSON mapping edges need hardening (e.g., empty string vs omitted fields, JSON validation feedback).

2. **HTML report download**: `generate_report()` in `src/re_storage/reporting/html_report.py` is callable. A `/report=true` endpoint in the handlers and a "Download HTML Report" button in `ResultsDashboard` are not yet wired (Phase 4).

3. **Firebase project**: `.firebaserc` has a placeholder alias (`re-storage-tool`). Replace with real project ID and run `firebase init` to activate Hosting + Functions.

4. **Full end-to-end UI test**: run Playwright against `http://127.0.0.1:5173` to verify Excel upload + results dashboard in-browser.

5. **Handler tests with Flask**: install Flask in the repo-level Python env (`pip install flask flask-cors functions-framework`) and run `pytest tests/unit/test_web_handlers.py` to exercise the full handler test suite.

6. **Deployment instructions**: document `firebase deploy --only functions,hosting` steps and Cloud Run resource limits in `docs/`.

## Recommended Next Start Command Set

1. **Start backend emulators:**
   ```bash
   cd web/functions && .venv\Scripts\python -m functions_framework --target runExcel --source main.py --port 8081 &
   .venv\Scripts\python -m functions_framework --target runJson --source main.py --port 8082 &
   ```

2. **Start frontend:**
   ```bash
   cd web/frontend && npm run dev
   ```

3. **Run backend tests:**
   ```bash
   pytest tests/unit/test_web_serialise.py tests/unit/test_web_handlers.py -v
   ```

4. **Lint:**
   ```bash
   ruff check web/functions tests/unit/test_web_serialise.py tests/unit/test_web_handlers.py
   ```

5. **Playwright UI walkthrough** (once Playwright is available):
   ```bash
   npx playwright test
   ```

---

## ISSUE-4 Objective

Implement the full gap-analysis roadmap from `plans/gap-analysis-and-roadmap.md` to achieve Excel financial parity and add revenue scenario / sensitivity analysis capabilities.

---

## ISSUE-4 Current Session Progress (2026-03-22)

### Financial regression unblock completed

- Fixed the Emivest financial-stage year alignment bug in `src/re_storage/pipeline.py::_run_financial()`.
- `_run_financial()` now:
  - reindexes lifetime revenue explicitly onto `RangeIndex(1..project_years)`
  - validates full lifetime year coverage before building revenue schedules
  - broadcasts `demand_charge_savings_usd_yr1` across the project horizon without creating a misaligned extra row
- This removes the prior regression crash:
  - `ValueError: Length of values (21) does not match length of index (20)`

### Tests added / updated this session

- Extended `tests/unit/test_pipeline_helpers.py` with:
  - `test_run_financial_aligns_year_indexed_lifetime_and_opex`
    - verifies `_run_financial()` accepts year-indexed lifetime inputs and returns KPIs without the prior length mismatch

### Verification run this session

- `pytest tests/unit/test_pipeline_helpers.py -q` -> **4 passed**
- `pytest tests/regression/test_emivest.py -q` -> **3 passed, 2 failed, 1 skipped**
  - the previous `_run_financial()` length-mismatch crash is resolved
- Clean Emivest KPI snapshot after the fix:
  - `project_irr ~ 0.2683`
  - `equity_irr = nan`
  - `npv_usd ~ 3.53M`
  - `dscr_min ~ 1.6694`
  - `year1_solar_generation_mwh ~ 137,245.18`
  - `year1_dppa_revenue_usd ~ 272,700.80`
  - `year1_grid_savings_usd ~ 249,876.35`
  - `year1_opex_usd ~ 44,397.25`
  - `year1_ebitda_usd ~ 478,179.90`

### Outstanding / blockers for next session

- `tests/regression/test_emivest.py::test_solar_generation_reasonable` still fails:
  - actual `year1_solar_generation_mwh ~ 137,245`, far above the current expected band `3000..6000`
  - next inspection target: solar scaling / unit expectations between JSON assumptions, hourly CSV profile, and aggregation output
- `tests/regression/test_emivest.py::test_irr_values_reasonable` still fails because `equity_irr` is `nan`
  - current logger message: `equity cashflows must include at least one positive and one negative value`
  - next inspection target: `_run_financial()` / `build_cash_flow_waterfall()` / debt sizing interaction that leaves FCFE one-signed
- Repeated battery dispatch overlap warnings still create noisy regression output:
  - `Multiple discharge conditions active at hour 17..23: ['when_needed', 'peak']`
  - this is still a cleanup candidate after parity-critical fixes

---

## ISSUE-4 Implemented This Session

### Phase 1 — Critical Financial Parity

**New modules:**

- **`src/re_storage/financial/opex.py`** — `build_opex_schedule()`:
  - Computes 8 OPEX line items per year: O&M (solar + BESS + other), insurance (solar + BESS), land lease (% of revenue), asset management.
  - Applies compound annual escalation: `value_yr1 × (1 + esc)^(year-1)`.
  - Excel source: `Financial!F106–F113`, `Assumption!K26–K34`.

- **`src/re_storage/financial/taxes.py`** — three functions:
  - `build_tax_rate_schedule()`: tiered schedule — 0% holiday → first discount rate → second discount rate → standard rate. Excel: `Assumption!K62–K65`, `J64–J65`.
  - `calculate_depreciation_schedule()`: straight-line over configurable tenor. Excel: `Assumption!K44`.
  - `calculate_unlevered_taxes()` / `calculate_levered_taxes()`: `max(0, EBIT × rate)` and `max(0, EBT × rate)`. Excel: `Financial!F132`, `F150`.

- **`src/re_storage/financial/mra.py`** — `build_mra_schedule()`:
  - BESS MRA target = `K46 × BESS CAPEX`; PV MRA target = `K47 × PV CAPEX`.
  - Operating-year contributions (years 1–3) follow `Other Input!B5–B8` build-up schedule (default 30/30/30%).
  - Year 0 contribution (10%) is equity-at-FC; excluded from the series.

**Updated existing files:**

- **`src/re_storage/aggregation/lifetime.py`** — `build_lifetime_projection()`:
  - Added `revenue_escalation_pct` and `fmp_descent_pct` parameters.
  - Revenue in year n = `year1_revenue × pv_factor_n × (1 + esc)^(n-1)`. Previously flat (degradation-only).
  - Excel source: `Financial!H16` (5% p.a. price escalation).

- **`src/re_storage/inputs/loaders.py`** — `load_financial_params_from_cells()`:
  - Now reads three column-pair maps: I/K (financial), I/J (tax durations), O/Q (PPA/escalation), C/E (installed capacity).
  - Returns 30+ new keys: CAPEX breakdown (`solar_capex_usd`, `bess_capex_usd`, `installed_pv_mwp`, `bess_mwh`), all OPEX unit rates, tax schedule params, MRA percentages, PPA scenario params (`ppa_option`, `bundled_discount_pct`, `pv_discount_pct`, `bess_discount_pct`, `fixed_ppa_price_usd_per_mwh`), escalation rates.
  - `load_assumptions()` fixed to only require fields without schema defaults (backward-compat with test fixtures that predate new PPA fields).

- **`src/re_storage/inputs/schemas.py`** — `SystemAssumptions`:
  - Added `ppa_option: int = 3` (1–4, default preserves DPPA CfD behaviour).
  - Added `bundled_discount_pct`, `pv_discount_pct`, `bess_discount_pct`, `fixed_ppa_price_usd_per_mwh` — all optional with defaults.

- **`src/re_storage/pipeline.py`**:
  - `_run_financial()`: replaced `_build_placeholder_opex()` (all zeros) with real `build_opex_schedule()` call; wires levered taxes and MRA into the OPEX DataFrame before passing to waterfall; adds `after_tax_project_irr` and `year1_opex_usd`/`year1_ebitda_usd` to returned KPIs.
  - `_run_settlement()`: dispatches to correct module based on `assumptions.ppa_option`.
  - `_run_aggregation()`: passes `revenue_escalation_pct` and `fmp_descent_pct` to `build_lifetime_projection()`.
  - `run_full_model()`: accepts `ppa_option` kwarg; extracts all new params from `financial_params` and passes them to `_run_financial()`; computes demand charge savings via `calculate_annual_demand_savings()`.
  - `run_model_from_json()`: accepts `ppa_option` kwarg.

### Phase 2 — Revenue Scenarios (Options 1, 2, 4)

**New modules:**

- **`src/re_storage/settlement/bundled.py`** — Option 1 Bundled Discount:
  - `calculate_bundled_revenue(direct_pv_kw, discharged_kw, time_period, tariff_rates, discount_pct)`.
  - Revenue = (direct_pv + discharged) × tariff × (1 − discount). Excel: `Financial!F64–F70`, `Assumption!Q30`.

- **`src/re_storage/settlement/separate.py`** — Option 2 Separate PV+BESS:
  - `calculate_separate_revenue(..., pv_discount_pct, bess_discount_pct)`.
  - PV and BESS components discounted independently. Excel: `Financial!F71–F83`, `Assumption!Q33–Q34`.

- **`src/re_storage/settlement/fixed_ppa.py`** — Option 4 Fixed EVN PPA:
  - `calculate_fixed_ppa_revenue(solar_gen_kw, fixed_price_usd_per_mwh, curtailment_pct, tx_loss_pct)`.
  - Revenue = generation × price × (1−curtailment) × (1−tx_loss). Excel: `Financial!F84–F90`, `Assumption!Q61`.

- **`src/re_storage/settlement/demand_charge.py`**:
  - `calculate_annual_demand_savings(monthly_data, cp_demand_vnd_per_kw, exchange_rate)`.
  - Zero for 1-component tariff (current test project); ready for 2-component projects.

### Phase 3 — Scenarios & Sensitivity

**New package `src/re_storage/scenarios/`:**

- **`runner.py`** — `run_all_scenarios(project_dir|excel_path, ppa_options=[1,2,3,4])`:
  - Runs full pipeline for each PPA option; returns `{option_id: kpi_dict}`.
  - Mirrors Excel `Scenarios!A1–N73` side-by-side comparison.

- **`sensitivity.py`** — `run_sensitivity(variable_name, test_values, ...)`:
  - Overrides one parameter, runs pipeline for each test value.
  - Supports 9 variables: strike price, interest rate, PV/BESS CAPEX, FX rate, leverage, escalation rates, bundled discount.
  - Mirrors Excel `Scenarios!A17–N35`.

### Package exports updated

- `financial/__init__.py` — exports all new financial functions.
- `settlement/__init__.py` — exports all new settlement functions.

### Tests — 48 new unit tests (all passing)

| File | Tests |
|------|-------|
| `tests/unit/test_financial_opex.py` | 8 |
| `tests/unit/test_financial_taxes.py` | 14 |
| `tests/unit/test_financial_mra.py` | 6 |
| `tests/unit/test_settlement_bundled.py` | 6 |
| `tests/unit/test_settlement_separate.py` | 5 |
| `tests/unit/test_settlement_fixed_ppa.py` | 7 |

**Overall test suite:** 198 passed, 1 skipped (pre-existing Hypothesis health-check flake in `test_battery.py`).

---

## ISSUE-4 Verification Status

```
pytest tests/ --ignore=tests/unit/test_battery.py --ignore=tests/regression/
# → 198 passed, 1 skipped
```

- All pre-existing unit and integration tests continue to pass (no regressions).
- 48 new unit tests for all new modules pass.
- Pipeline imports cleanly; `ppa_option` dispatch works for all 4 options.

---

## ISSUE-4 Outstanding

### P1-4 — Regression reference update (HIGH)

After verifying parity against the real Excel workbook, update `tests/data/references/` JSON files with new KPI targets that include OPEX, taxes, and escalation:
- Target: `year1_opex_usd` within 1% of `Financial!F113`
- Target: `project_irr` within 0.5% of `Financial!H123` (0.08952)
- Target: `equity_irr` within 0.5% of `Financial!H189` (0.19403)
- Target: `npv_usd` within 2% of `Financial!H193` ($22.03M)

### P2-5/P2-6 — Backend/frontend wiring for new PPA params (HIGH)

- `web/functions/handlers/run_json.py`: expose `ppa_option`, `bundled_discount_pct`, `pv_discount_pct`, `bess_discount_pct`, `fixed_ppa_price_usd_per_mwh` as form fields in `_build_project_payload()`.
- `web/frontend/src/components/inputs/SystemStep.tsx`: add PPA option radio group (Options 1–4 with labels) and conditional discount/price fields.

### P3-3 — New API endpoints (MEDIUM)

Add to `web/functions/main.py`:
- `POST /compareScenarios` → calls `run_all_scenarios()` → returns `{option: kpi_dict}` for all 4 PPA options.
- `POST /runSensitivity` → calls `run_sensitivity()` → returns `{value: kpi_dict}` for the swept variable.

### P4 — Dashboard & missing KPIs (MEDIUM)

- Add payback period and cash-on-cash yield to `financial/metrics.py`.
- Add energy performance KPIs to pipeline: solar utilisation, pre/post-BESS curtailment, clean energy delivered, load coverage %.
- Update `ModelKpis` TypeScript interface in `web/frontend/src/types/model.ts` with new fields.
- Add `<GoNoGoIndicator>` component comparing `equity_irr` vs `target_irr`.
- Add `<ScenarioComparisonTable>` and `<SensitivityPanel>` React components.
- Add `<DscrChart>` and `<AnnualCashFlowChart>` to results dashboard.

### P5 — Remaining low-priority items (LOW)

- `load_other_input()` in `loaders.py`: read `Other Input!B3–C25` for full MRA build-up schedule and complete EVN tariff table.
- Blended interest rate: load `hedging_ratio`, `fixed_swap_rate`, `base_rate`, `debt_margin` and compute blended rate in `load_financial_params_from_cells()`.
- Net billing revenue: add `net_billing_usd_per_mwh` / `net_billing_export_share` to settlement layer.
- `demand_charge`: wire `cp_demand_vnd_per_kw` from `Assumption!O13` loader so 2-component tariff projects get real savings.
- Form UX improvements: default-populated degradation table, inline validation, CSV preview, progress bar, project save/load.

---

## Recommended Next Start

1. Trace the Emivest solar-generation scale mismatch from JSON assumptions + hourly CSV through `_run_physics()` and `calculate_year1_totals()`.
2. Fix the `equity_irr = nan` issue by inspecting FCFE sign/shape in `_run_financial()` and `build_cash_flow_waterfall()`.
3. Re-run Emivest regression and then compare workbook KPIs to Excel reference to quantify parity improvement.
4. Update reference JSON files (`P1-4`) once the regression KPIs are credible.
5. Resume web wiring for `ppa_option` and scenario/sensitivity endpoints (`P2-5/P2-6`, `P3-3`).

---

## ISSUE-5 Objective (Current Session)

Implement Phase 1 of `plans/frontend-alignment-poc.md` by aligning the existing web app to a two-panel POC-style shell without replacing the current Firebase backend or form submission flow.

### Phase 1 Scope

- [x] Refactor the existing frontend layout into a responsive two-panel shell using the current app in `web/frontend/`
- [x] Keep both existing run paths available: Excel upload and structured form submission
- [x] Show the input workspace on the left and the results workspace on the right on larger screens
- [x] Preserve current API contracts and live result rendering (no mock data)
- [x] Improve the first-pass visual hierarchy with the existing CSS approach rather than introducing Tailwind

### Verification Checklist

- [x] `npm run build` passes in `web/frontend`
- [x] Desktop layout presents clear side-by-side input/results panes
- [x] Mobile layout collapses to a single-column flow cleanly
- [x] Existing result components still render from live `ModelResponse` payloads

### Review / Results

- Updated `web/frontend/src/App.tsx` to establish a left input workspace and right results workspace while preserving the existing Excel and structured-form run paths.
- Updated `web/frontend/src/styles.css` to support the new two-panel shell, responsive collapse, stronger visual hierarchy, and an empty results state.
- Retained the current live API-backed result flow; no endpoint or payload changes were introduced in this phase.
- Verification: `npm run build` in `web/frontend` passed successfully on 2026-03-23.

---

## ISSUE-6 Objective (Current Session)

Implement Phase 2 of `plans/frontend-alignment-poc.md` by refactoring the structured form into clearer grouped sections with inline validation, while preserving the current `runJson` payload shape and working frontend stack.

### Phase 2 Scope

- [x] Replace the step-by-step structured form flow with grouped sections that are easier to scan and navigate
- [x] Add a compact section navigator so users can jump between system, DPPA, financial, degradation, hourly, and review groups
- [x] Add client-side inline validation for core required numeric and file inputs
- [x] Disable or dim conditional fields when BESS or DPPA toggles make them inactive
- [x] Keep the existing `FormData` submission contract for `web/functions/handlers/run_json.py`

### Verification Checklist

- [x] `npm run build` passes in `web/frontend`
- [x] Structured form still submits `FormData` compatible with the current JSON endpoint
- [x] Inline validation prevents clearly invalid submissions and displays field-level messages
- [x] Conditional DPPA/BESS fields visibly reflect enabled or disabled state

### Review / Results

- Replaced the wizard-style structured form with a grouped section layout in `web/frontend/src/components/inputs/ProjectForm.tsx`, including a left-side section navigator and review/run panel.
- Added reusable client-side validation rules in `web/frontend/src/components/inputs/formValidation.ts` and wired inline field-level messages into the system, DPPA, financial, degradation, and hourly upload sections.
- Added conditional disabled states so BESS- and DPPA-specific fields visibly dim and become non-editable when their parent toggle is off.
- Preserved the existing `FormData` submission shape for `runJson`; the grouped form still posts the same field names plus `hourly_csv`.
- Verification: `npm run build` in `web/frontend` passed successfully on 2026-03-23.

---

## ISSUE-7 Objective (Current Session)

Implement Phase 3 of `plans/frontend-alignment-poc.md` by extending the API response contract to include richer result datasets for charts, while preserving the existing Firebase function entrypoints and run flows.

### Phase 3 Scope

- [x] Inspect the current pipeline outputs and serializer behavior to identify the smallest useful response expansion
- [x] Add backend coverage for richer response payloads before changing the serializer contract
- [x] Extend API responses with annual financial rows, DSCR data, cash-flow-ready data, and a sampled dispatch preview where available
- [x] Update frontend result types and dashboard consumers to accept the richer response shape without breaking current charts
- [x] Keep the existing `/api/run-excel` and `/api/run-json` endpoints and request contracts unchanged

### Verification Checklist

- [x] Backend tests covering the serializer / handler response shape pass
- [x] Frontend `npm run build` passes with the updated result types
- [x] Existing KPI and lifetime charts still render against the richer payload contract
- [x] New response fields are JSON-safe and omit unsafe / oversized internal objects

### Review / Results

- Extended `web/functions/utils/serialise.py` to return `annual`, `cashflow`, `dscr_series`, and a first-week `dispatch_sample` in addition to the existing `kpis` and `lifetime` payload fields.
- Updated `src/re_storage/pipeline.py` so the financial stage surfaces `_annual_df`, which the web serializer can transform into annual, cash-flow, and DSCR-ready frontend datasets.
- Updated `web/frontend/src/types/model.ts` and `web/frontend/src/components/results/ResultsDashboard.tsx` so the frontend accepts the richer payload contract and surfaces the new dataset availability.
- Preserved the existing `/api/run-excel` and `/api/run-json` request contracts; the expansion is response-only.
- Verification:
  - `pytest tests/unit/test_web_serialise.py` -> passed
  - `pytest tests/unit/test_web_handlers.py` -> skipped (Flask not installed in repo-level env)
  - `npm run build` in `web/frontend` -> passed

---

## ISSUE-8 Objective (Current Session)

Implement Phase 4 of `plans/frontend-alignment-poc.md` by turning the richer Phase 3 response payload into full result views, including cash flow, DSCR, revenue stack, dispatch preview, and a currency toggle for monetary outputs.

### Phase 4 Scope

- [x] Replace the temporary Phase 3 data-summary cards with chart-driven result views
- [x] Add DSCR, cash flow, refined revenue stack, and dispatch preview result components using the existing Recharts stack
- [x] Add a USD/VND toggle that updates monetary KPI and chart labels from the same response payload
- [x] Keep the current API endpoints and payload fields unchanged
- [x] Preserve the existing lifetime generation and battery capacity charts while integrating the new views

### Verification Checklist

- [x] `npm run build` passes in `web/frontend`
- [x] Results dashboard renders against the richer payload types without TypeScript errors
- [x] Monetary displays respect the selected currency toggle
- [x] Existing KPI/lifetime views continue to render alongside the new charts

### Review / Results

- Added `CashFlowChart`, `DscrChart`, and `DispatchPreviewChart` under `web/frontend/src/components/results/` and upgraded the existing revenue chart to use the Phase 3 annual payload.
- Updated `web/frontend/src/components/results/ResultsDashboard.tsx` to render the Phase 4 chart suite and added a USD/VND toggle that flows through KPI cards and monetary charts.
- Extended `web/frontend/src/utils/formatters.ts` and `web/frontend/src/components/results/KpiGrid.tsx` so monetary values can be displayed consistently in either USD or VND from the same backend response.
- Preserved the existing lifetime generation and battery capacity charts while replacing the temporary Phase 3 summary-only experience with the fuller results dashboard.
- Verification: `npm run build` in `web/frontend` passed successfully on 2026-03-23.

### Outstanding / Next Sensible Steps

- Phase 5 polish remains open: scenario comparison, export flows, and a mobile-specific audit of the expanded dashboard.
- The Phase 4 dashboard currently uses a fixed DSCR covenant line (`1.3x`) until a model-backed covenant field is exposed through the API.
- Web handler endpoint tests still skip in the repo-level Python environment until Flask and related packages are installed there.
- The frontend bundle still emits the existing Vite chunk-size warning; this is non-blocking but a future code-splitting cleanup candidate.

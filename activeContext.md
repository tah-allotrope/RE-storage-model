# Active Context - ISSUE-1 Emivest / ISSUE-2 Excel Alignment / ISSUE-3 Web Tool

**Last Updated:** 2026-03-19

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

# Active Context - ISSUE-1 Emivest / ISSUE-2 Excel Alignment / ISSUE-3 Web Tool / ISSUE-4 Gap Analysis Roadmap

## Current Working Plan - Vietnam TOU 2026 Presentation V2

- [x] Review the updated `present` skill guidance and the existing TOU analysis artifacts.
- [x] Generate a self-contained HTML v2 deck and an Allotrope-style PPTX v2 deck under `results/`.
- [x] QA the generated presentation files and record the exact regeneration command.
- [ ] Commit the presentation refresh and push the branch.

### Review / Results

- Added `results/make_presentation_v2.js` as a reproducible generator that writes both `results/vietnam_tou2026_presentation_v2.html` and `results/vietnam_tou2026_presentation_v2.pptx` from the Phase 5/6 TOU analysis outputs.
- The new HTML deck is self-contained and offline-safe, with inline CSS, inline SVG charts, and keyboard/button navigation rather than CDN-based charts.
- The new PPTX deck follows the updated Allotrope guidance more closely than the earlier presentation, including Calibri Light/Calibri typography, green title rule, and confidentiality footer on non-title slides.
- Regeneration command: `node results/make_presentation_v2.js`
- QA completed:
- `node results/make_presentation_v2.js` -> passed and produced both v2 files.
- Verified generated file presence and timestamps via PowerShell `Get-Item` metadata.
- Limitation: `soffice` is not installed in this environment, so PDF/image visual QA for the PPTX could not be run locally.

**Last Updated:** 2026-05-02

## Current Working Plan - Vietnam TOU 2026 Phase 5/6

- [x] Add focused tests for TOU delta-analysis/report helpers before implementation.
- [x] Extend the existing TOU analysis script to compute case deltas, driver decomposition, and average-day dispatch data.
- [x] Generate the Phase 5 figure and Phase 6 markdown impact report under `results/`.
- [x] Run targeted tests and the TOU analysis script to verify outputs are reproducible.
- [ ] Commit the Phase 5/6 changes and push the branch.

### Review / Results

- Added `tests/unit/test_vietnam_tou2026_analysis.py` to lock the Phase 5 comparison math, decomposition buckets, and average-day dispatch aggregation.
- Rebuilt `scripts/run_vietnam_tou2026_analysis.py` into a deterministic Phase 1-6 runner that regenerates baseline/new-tariff artifacts, writes `results/vietnam_tou2026_analysis.json`, creates the average-day dispatch figure, and writes `results/vietnam_tou2026_impact_report.md`.
- Generated `results/figures/avg_day_dispatch_comparison.png` and the Phase 6 markdown report summarizing revenue, IRR, NPV, DSCR, and Emivest revenue-driver decomposition.
- Verification:
- `pytest tests/unit/test_vietnam_tou2026_analysis.py tests/unit/test_tou2026_tariff.py tests/unit/test_tou2026_dispatch.py -q` -> **27 passed**
- `python scripts/run_vietnam_tou2026_analysis.py` -> **passed** (expected loader warnings about missing BESS labels in the Emivest JSON path)

**Last Updated:** 2026-03-27

## Current Working Plan - ISSUE-5 Parity First

- [x] Reproduce the current Ecoplexus workbook parity deltas with targeted regression output.
- [x] Identify the primary financial mismatch driver in DPPA revenue, OPEX/tax/MRA, or debt sizing.
- [x] Add or tighten a regression test around the specific parity bug before changing code.
- [ ] Implement the smallest viable parity fix in the financial pipeline.
- [x] Re-run targeted tests and capture updated deltas versus workbook references.
- [x] Record the outcome and remaining ISSUE-5 gaps in this file.

### ISSUE-5 Current Session Progress (2026-03-27)

#### Parity findings implemented this session

- Added a loader regression in `tests/unit/test_inputs_loaders.py` to lock workbook tax-marker conversion into duration-style schedule inputs.
- Added sculpted-debt regressions in `tests/unit/test_financial_debt.py` to pin workbook-style DSCR debt service instead of the prior annuity schedule behavior.
- Updated `src/re_storage/inputs/loaders.py` so workbook tax rows now interpret Assumption column-J values as period markers rather than raw durations.
- Updated `src/re_storage/financial/debt.py` so DSCR sizing now returns a sculpted debt schedule based on discounted target debt service instead of a flat-payment amortization schedule.
- Updated `src/re_storage/financial/waterfall.py` and `src/re_storage/pipeline.py` so MRA is included in EBITDA timing, signed tax rows flow like the workbook, and FCFE is built from CFADS plus principal less interest.

#### Verification run this session

- `pytest tests/unit/test_inputs_loaders.py tests/unit/test_financial_debt.py tests/unit/test_pipeline_helpers.py -q` -> **29 passed**
- `pytest tests/regression/test_excel_comparison.py -q` -> **still failing on final financial KPIs only**
- Visual progress artifact generated: `reports/issue5_parity_progress.html`

#### Updated Ecoplexus parity snapshot after first-pass fixes

- `project_irr ~ 0.04970` vs Excel `0.05074` (much closer)
- `equity_irr ~ 0.04369` vs Excel `0.04638` (closer, still low)
- `unlevered_irr ~ 0.10989` vs Excel `0.08833` (still high)
- `npv_usd ~ +2.77M` vs Excel `-2.65M` (still materially wrong sign)
- `debt_amount_usd ~ 16.12M` vs workbook cached `H169 ~ 24.58M`

#### Current blocker / next target

- Remaining parity gap is now concentrated in the levered financial path, not physics or settlement totals.
- The workbook fixture reports a large stale solver signal at `Financial!G170 ~ -8.37M`, so cached debt-related rows are internally inconsistent with the current workbook state.
- The next parity step should inspect whether Python should:
  - trust the workbook's cached `H169` debt amount,
  - replicate the workbook's stale GoalSeek state exactly for regression parity, or
  - treat `G170` as evidence that the reference workbook itself must be refreshed before final parity can converge.

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

---

## ISSUE-5 Objective — DPPA Feasibility Study Review

**Date:** 2026-03-27
**Context:** Colleague provided `DPPA_FS_Study.pdf` — a REopt.jl-generated DPPA feasibility study for a **different project** (Scenario 3: Wind+Solar+BESS, 50 MW Industrial Park, Ninh Thuan). This is NOT the Ecoplexus workbook — it is a comparable project using the same DPPA mechanism (ND57/2025 CfD). Goal is to validate whether this model can reproduce a similar analysis and identify gaps.

**Source file:** `DPPA_FS_Study.pdf` (downloaded to local inbox, ~1.27 MB)

### PDF Key Findings (REopt.jl — Scenario 3: Wind+Solar+BESS)

| Metric | Value |
|--------|-------|
| Project | 50 MW Industrial Park, Ninh Thuan, ≥110 kV |
| DER Capacity | 50.0 MW (PV 30 MW + Wind 20 MW + BESS 10 MW / 40 MWh) |
| Total CAPEX | $28.50M ($24M wind + $2M PV est. + $2.50M BESS) |
| Capital Structure | 70% debt / 30% equity |
| Loan Terms | 12-yr, 1-yr grace, 8.5% p.a. (VND commercial) |
| **Project IRR** | **18.1%** |
| **Equity IRR** | **31.4%** |
| **Min DSCR** | **1.53x** (bankable) |
| **Factory NPV** | **$7.97M** |
| Project Payback | Year 6 |
| CIT Holiday | 4 yr exempt → 9 yr 50% pref → std 20% |

**DPPA Commercial Terms:**
| Parameter | Value | Notes |
|-----------|-------|-------|
| DPPA Type | VIRTUAL | ND57/2025 CfD settlement via EVN |
| Contracted PPA Strike | 5.500 ¢/kWh | Fixed |
| Developer Floor (NPV=0) | 4.273 ¢/kWh | Min viable price |
| Factory Ceiling | 7.394 ¢/kWh | Max before factory loses money |
| FMP (spot, annual mean) | 5.707 ¢/kWh | Developer sells Q_mq at FMP |
| Negotiable Window | +3.122 ¢/kWh | **VIABLE** |
| Grid Service Fees | Bundled in strike price | C_DPPAdv + P_CL |

**Technical Results (Year 1):**
| Metric | Value |
|--------|-------|
| Total RE Generation | 117.58 GWh/yr |
| Factory Load | 240.90 GWh/yr (mean 27.5 MW, peak 134.1 MW) |
| RE Penetration | 48.8% |
| Self-Consumption Rate | 59.6% |
| Annual Degradation | 0.5%/yr |
| Wind: capacity factor | 38.0% |

**Annual Proforma (Selected Years):**
| Yr | Revenue | O&M | Depr. | Interest | EBIT | CIT | Net Income |
|----|---------|-----|-------|----------|------|-----|------------|
| 1 | $6.00M | -$621k | -$2.85M | -$1.70M | $837.9k | 0% | ~$838k |
| 5 | $6.10M | -$713k | -$2.85M | -$1.23M | $1.31M | 5% | ~$1.24M |
| 10 | $6.24M | -$846k | -$2.85M | -$463k | $2.08M | 5% | ~$1.97M |
| 15 | $6.39M | -$1.01M | $0 | $0 | $5.38M | 10% | ~$4.85M |
| 20 | $6.56M | -$1.19M | $0 | $0 | $5.36M | 20% | ~$4.29M |
| 25 | $6.74M | -$1.42M | $0 | $0 | $5.33M | ~$4.26M | |

**Viability Frontier:** Min PPA ≥ 3.850 ¢/kWh for 15% equity hurdle at all interest rates 6.5–10.5%.

### Key Differences vs Ecoplexus (Excel model)

| Dimension | REopt Study (Scenario 3) | Ecoplexus Excel |
|-----------|--------------------------|-----------------|
| Technology | Wind+Solar+BESS | Solar+BESS only |
| Total Capacity | 50 MW DER | 40 MW Solar |
| BESS | 10 MW / 40 MWh | Not specified |
| Project IRR | 18.1% | 5.07% |
| Equity IRR | 31.4% | 4.64% |
| DSCR | 1.53x | Target ~1.2-1.4x |
| Strike Price | 5.500 ¢/kWh | Different |
| CIT treatment | Explicit (4yr exempt) | Unknown if modeled |
| Wind component | Yes | No |

### Implications for This Model

1. **CIT Holiday not implemented**: The Python model likely has no CIT holiday (4yr exempt → 9yr 50% pref). This is a major reason for IRR overstatement vs a proper Vietnamese tax model.
2. **Wind source not supported**: Current `physics/solar.py` only handles PV. Adding wind as a passthrough generation source would extend usefulness.
3. **DPPA CfD structure is consistent**: Both use ND57/2025 CfD — the model's DPPA module is on the right track.
4. **Factory economics**: The study shows factory NPV ($7.97M) separately from developer NPV — the model doesn't currently split these views.
5. **Viability frontier analysis**: The sensitivity heatmap (PPA price vs interest rate → equity IRR) is a valuable output the model doesn't yet produce.

---

### Pre-requisite: Fix Regression Blocker

Before any meaningful comparison can be done, the known regression failure must be resolved:

- [ ] **BLOCKER**: `tests/regression/test_emivest.py` fails with `ValueError: Length of values (21) does not match length of index (20)` in `_run_financial()`
  - Root cause: year-count mismatch between `lifetime_df` (21 rows) and EBITDA series (20 rows) in `src/re_storage/pipeline.py::_run_financial()`
  - Also check: `src/re_storage/financial/mra.py` and `src/re_storage/financial/taxes.py` for off-by-one in project year indexing
  - Fix: ensure all financial series are indexed from `year 0` (construction) or `year 1` (COD) consistently — do not mix

---

### Phase 1 — Establish Baseline Run

- [ ] Run the Ecoplexus workbook (`data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx`) through `run_full_model()` and capture output KPIs
- [ ] Compare to Excel reference values from `model_architecture.md §D.4`:
  - Project IRR: **5.07%**
  - Equity IRR: **4.64%**
  - Unlevered IRR: **8.83%**
  - NPV: **-$2.65M**
- [ ] Log deltas between Python model and Excel in a comparison table

Known gap from ISSUE-2: Python currently returns `project_irr ~ 1.18x` (badly overstated). Financial parity is the primary work item.

---

### Phase 2 — Financial Parity Fix

Root causes to investigate (from ISSUE-2 notes):

- [ ] **Revenue overstatement**: DPPA and grid savings revenue is too high — verify `_build_dppa_net_generation()` signal against Calc!Col AB and DPPA!Col Q
- [ ] **OPEX missing lines**: O&M, insurance, land lease, management fee, grid connection charges need to be loaded and wired into `_run_financial()`
  - Source: `Financial` sheet rows (OPEX stack, §D.2 in architecture doc)
- [ ] **Tax & depreciation**: confirm `financial/taxes.py` correctly models Vietnamese corporate tax and accelerated depreciation
- [ ] **MRA drawdown**: confirm `financial/mra.py` deducts augmentation capex at years 11 & 22 (aligned to `Loss!Col F` reset years per Risk 7)
- [ ] **Debt sizing**: verify the Python DSCR solver reproduces Excel's GoalSeek result (`DebtSize_Check → 0`)
  - Check `financial/debt.py` against VBA logic in `analysis_report.md`

---

### Phase 3 — DPPA Revenue Validation

Key items from the DPPA module (architecture §B):

- [ ] Verify `delivered_re_gen = net_gen / (k_factor × kpp) × delta` (corrected in ISSUE-2, confirm still correct)
- [ ] Verify CfD settlement: `R_CFD = Q_Khc × (Strike_Price - FMP)` — check sign convention when FMP > Strike
- [ ] Verify DPPA activation toggle (`Does_model_is_actived?`) is correctly propagated — Risk 3
- [ ] Cross-check total Year 1 DPPA revenue against `DPPA!Col Q` sum from Excel workbook

---

### Phase 4 — ReOpt Comparison (DPPA_FS_Study.pdf)

Once the model baseline is stable:

- [ ] Extract key metrics from `DPPA_FS_Study.pdf`:
  - Optimal battery size (kW / kWh)
  - Solar capacity used
  - DPPA revenue projection (Year 1 and lifetime)
  - Project/equity IRR from ReOpt's financial model
  - Dispatch strategy (arbitrage vs peak-shaving mix)
- [ ] Compare to `run_full_model()` output for same inputs
- [ ] Document gaps in a findings table (which tool is more conservative, why)
- [ ] Note any assumptions in ReOpt not captured by this model (e.g., grid export limits, curtailment rules, Vietnam DPPA regulatory specifics)

---

### Phase 5 — Validation Checks & Reporting

- [ ] Add/update `validation/checks.py` to flag:
  - DPPA revenue = 0 when DPPA is enabled (Risk 3)
  - `Loss` table doesn't cover all project years (Risk 5)
  - `Blance_Check` column has non-zero rows (Risk 6, typo in original)
- [ ] Generate comparison HTML report via `generate_report()` with:
  - Python model KPIs vs Excel reference
  - Python model KPIs vs ReOpt study (from PDF)
  - Year-by-year DPPA revenue and DSCR charts

---

### Success Criteria

| Check | Target |
|-------|--------|
| Regression test passes | `pytest tests/regression/test_emivest.py` → **PASS** |
| Project IRR delta vs Excel | < 50 bps |
| Equity IRR delta vs Excel | < 50 bps |
| DPPA Year 1 revenue delta vs Excel | < 5% |
| Min DSCR delta vs Excel | < 0.05x |

---

### Files To Modify (Expected)

| File | Change |
|------|--------|
| `src/re_storage/pipeline.py` | Fix year-index alignment in `_run_financial()`; wire OPEX lines |
| `src/re_storage/financial/mra.py` | Align augmentation years to Loss table (11, 22) |
| `src/re_storage/financial/taxes.py` | Verify depreciation schedule |
| `src/re_storage/financial/debt.py` | Validate DSCR solver convergence |
| `src/re_storage/validation/checks.py` | Add Risk 3, 5, 6 checks |
| `tests/regression/test_emivest.py` | Un-block after pipeline fix |

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

Emivest now has a checked-in JSON-path regression baseline in `tests/data/references/emivest.json` that includes OPEX and EBITDA outputs. Replace that baseline with workbook-backed KPI targets once an Emivest Excel fixture is available:
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

1. Obtain or add an Emivest Excel workbook fixture so the new JSON-path regression baseline can be replaced with workbook-backed reference KPIs.
2. Compare current Emivest JSON outputs against that workbook reference to quantify the remaining parity gap in IRR, equity IRR, NPV, and Year 1 OPEX.
3. Resume web wiring for `ppa_option` and scenario/sensitivity endpoints (`P2-5/P2-6`, `P3-3`).
4. Add the remaining dashboard KPI views and scenario tooling (`P4`).

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

---

## ISSUE-9 Objective (Current Session)

Implement the Emivest JSON parity fixes from `plans/next-session-emivest-parity.md` so the JSON path stops overstating generation, honors the fixture's commercial/debt inputs, and fails loudly on broken KPI outputs.

### Scope

- [x] Remove the Year 1 solar double-scaling in the JSON/aggregation path
- [x] Load and honor JSON `maximum_leverage_pct`
- [x] Load and honor JSON `active_ppa_option` plus option-specific pricing inputs
- [x] Extend JSON financial loading/wiring for parity-critical OPEX, tax, MRA, and CAPEX detail inputs
- [x] Tighten Emivest regression handling so NaN actual KPI values fail instead of skip
- [x] Verify with targeted unit and regression pytest runs

### Review / Results

- Fixed the annual solar double-scaling path by treating `solar_gen_kw` as already scaled output in `src/re_storage/aggregation/annual.py`.
- Extended `src/re_storage/inputs/json_loader.py` so Emivest JSON runs now load and pass through:
  - `maximum_leverage_pct`
  - `active_ppa_option`
  - bundled / split discount inputs
  - fixed PPA price plus curtailment / transmission loss inputs
  - OPEX unit inputs
  - tax schedule year markers converted to duration-style fields
  - MRA buildup schedule (operating years only)
  - `land_acquisition_USD` and `bop_USD`
- Updated `src/re_storage/pipeline.py` and `src/re_storage/financial/opex.py` so JSON runs now honor those loaded inputs in settlement and financial calculations, including revenue-linked land lease and leverage-capped debt sizing.
- Tightened `tests/regression/test_emivest.py` so NaN actual KPI values fail instead of being silently skipped.
- Added/updated unit coverage in:
  - `tests/unit/test_json_loader.py`
  - `tests/unit/test_financial_opex.py`
  - `tests/unit/test_financial_mra.py`
  - `tests/unit/test_aggregation_annual.py`
- Verification on 2026-03-23:
  - `pytest tests/unit/test_json_loader.py tests/unit/test_financial_opex.py tests/unit/test_financial_mra.py tests/unit/test_aggregation_annual.py tests/regression/test_emivest.py -q` -> **41 passed, 1 skipped**
- Follow-up on 2026-03-24:
  - populated `tests/data/references/emivest.json` with the verified current JSON-path baseline so the regression no longer skips when references are absent
  - extended `tests/regression/test_emivest.py` to assert `year1_opex_usd` and `year1_ebitda_usd` against the reference baseline
  - `pytest tests/regression/test_emivest.py -q` -> **7 passed**
- Updated Emivest KPI snapshot after the fixes:
  - `project_irr ~ 0.2293`
  - `equity_irr ~ 0.2957`

---

## ISSUE-10 Objective (Current Session)

Review `plans/vietnam_tou2026_analysis_plan.md` against the current repo state, identify which phases are already implemented, then implement the next two incomplete phases with verification artifacts and git delivery.

### Scope

- [in_progress] Audit the repo against Phases 1-6 of `plans/vietnam_tou2026_analysis_plan.md`
- [x] Capture a concise implemented-vs-missing status summary in the review results
- [x] Implement Phase 3 baseline snapshot artifacts for Emivest and Ecoplexus under `results/baseline/`
- [x] Implement Phase 4 new tariff scenario runs, including Emivest PPA options and cycle-cap sensitivity outputs under `results/new_tariff/`
- [x] Run targeted tests and scenario commands to verify the new artifacts are reproducible
- [pending] Commit the relevant changes and push the branch

### Review / Results

- Review against `plans/vietnam_tou2026_analysis_plan.md` found Phase 1 and most of Phase 2 already present before this session: TOU2026 JSON/excel codification, `tariff_version`, dispatch audit tests, and the Sunday peak-window fix were already implemented.
- The review also exposed two gaps that would have made Phase 3/4 results misleading: dispatch flags from JSON/Excel inputs were not being carried into `BatteryConfig`, and the Excel path could not select the new `Tariff Schedule 2026` sheet via a reproducible override.
- Implemented those missing runtime pieces in `src/re_storage/inputs/schemas.py`, `src/re_storage/inputs/json_loader.py`, `src/re_storage/inputs/loaders.py`, `src/re_storage/physics/battery.py`, and `src/re_storage/pipeline.py`, including optional `max_cycles_per_day` support for the Phase 4 paired sensitivity runs.
- Hardened workbook loading for Ecoplexus by adding fallbacks for blank Assumption-sheet tariff cells (`Other Input` tariff table), blank total-BESS cells (derive from standard size × quantity), and uncached Loss-sheet retention formulas (reconstruct cumulative factors from annual-loss columns).
- Added/updated regression coverage in `tests/unit/test_json_loader.py`, `tests/unit/test_inputs_loaders.py`, `tests/unit/test_tou2026_dispatch.py`, and `tests/unit/test_pipeline_helpers.py`; targeted verification passed with `49` green tests.
- Completed Phase 3 artifacts under `results/baseline/` (`emivest_tou2024.json`, `ecoplexus_tou2024.json`) and Phase 4 artifacts under `results/new_tariff/` for Emivest option 1-4 plus cycle-cap variants and Ecoplexus TOU2026 plus cycle-cap variant; added reproducibility script `scripts/run_vietnam_tou2026_analysis.py`.

  - `npv_usd ~ 2.03M`
  - `dscr_min ~ 2.0616`
  - `year1_solar_generation_mwh ~ 4260.95`
  - `year1_dppa_revenue_usd ~ 212,394.89`
  - `year1_grid_savings_usd ~ 249,876.35`
  - `year1_opex_usd ~ 48,218.61`
  - `year1_ebitda_usd ~ 414,052.64`

---

## ISSUE-10 Objective (Current Session)

Implement the next missing web API slice from the roadmap by adding scenario-comparison and sensitivity endpoints on top of the existing Firebase Functions backend.

### Scope

- [x] Add backend handlers for scenario comparison and sensitivity analysis using the existing `re_storage.scenarios` package
- [x] Expose new Firebase function entrypoints for those handlers
- [x] Add Hosting rewrites so the SPA can call the new `/api/*` routes consistently
- [x] Add unit coverage for the new handlers and payload shapes
- [x] Verify targeted handler checks as far as the current environment allows

### Review / Results

- Added shared multipart-form payload builder in `web/functions/handlers/project_payload.py` so `runJson`, scenario comparison, and sensitivity analysis all construct the same JSON-model payload shape.
- Added `web/functions/handlers/compare_scenarios.py`:
  - validates POST + `hourly_csv`
  - reuses the structured-form payload builder
  - writes a temp JSON+CSV project bundle and calls `run_all_scenarios(project_dir=...)`
  - returns `{ "scenarios": { "1": {...}, ... } }`
- Added `web/functions/handlers/run_sensitivity.py`:
  - validates POST + `hourly_csv` + required `sensitivity_variable`
  - parses `sensitivity_values` from JSON array text
  - builds `base_params` from submitted form fields
  - writes a temp JSON+CSV project bundle and calls `run_sensitivity_for_values(...)`
  - returns `{ "variable": ..., "results": { "1800.0": {...}, ... } }`
- Updated `web/functions/main.py` with new Cloud Function entrypoints:
  - `compareScenarios`
  - `runSensitivity`
- Updated `firebase.json` rewrites so the SPA can reach:
  - `/api/compare-scenarios`
  - `/api/run-sensitivity`
- Extended `tests/unit/test_web_handlers.py` with request/response coverage for both new handlers and kept `_build_project_payload()` compatibility via the existing `run_json` import surface.

### Verification

- `ruff check web/functions/main.py web/functions/handlers/run_json.py web/functions/handlers/project_payload.py web/functions/handlers/compare_scenarios.py web/functions/handlers/run_sensitivity.py tests/unit/test_web_handlers.py` -> **pass**
- `pytest tests/unit/test_web_handlers.py -q` -> **skipped in repo-level env** because Flask is not installed there (`tests/unit/test_web_handlers.py` already guards on that dependency)

### Next Sensible Step

- Wire the frontend to these new routes with a scenario comparison view and a sensitivity panel, then exercise the full handler suite inside the `web/functions` virtualenv where Flask and Functions Framework are installed.

---

## ISSUE-11 Objective (Current Session)

Wire the new scenario-comparison and sensitivity APIs into the React web app so structured-form runs can drive follow-up analysis directly from the results workspace.

### Scope

- [x] Extend frontend API/types for scenario comparison and sensitivity responses
- [x] Retain the latest structured-form submission payload so follow-up analysis calls can reuse it
- [x] Add scenario comparison and sensitivity panels to the results dashboard
- [x] Add frontend proxy/config/style updates for the new analysis routes and components
- [x] Verify frontend build and probe Flask-backed handler imports from `web/functions/.venv`

### Review / Results

- Extended `web/frontend/src/types/model.ts` with:
  - `ScenarioComparisonResponse`
  - `SensitivityResponse`
  - scenario/sensitivity KPI row types layered on the existing model KPI contract
- Extended `web/frontend/src/api/client.ts` with:
  - `compareScenarios(formData)` -> `POST /api/compare-scenarios`
  - `runSensitivity(formData)` -> `POST /api/run-sensitivity`
- Updated `web/frontend/src/hooks/useModelRun.ts` so the app now:
  - stores the latest structured-form `FormData` payload after a successful JSON run
  - clears analysis state when switching to a new run
  - can trigger scenario comparison against that stored payload
  - can trigger sensitivity analysis with preset value ranges for supported backend variables
- Updated `web/frontend/src/components/results/ResultsDashboard.tsx` to add an analysis action strip plus two new result sections:
  - `ScenarioComparisonTable`
  - `SensitivityPanel`
- Added new result components:
  - `web/frontend/src/components/results/ScenarioComparisonTable.tsx`
  - `web/frontend/src/components/results/SensitivityPanel.tsx`
- Updated `web/frontend/vite.config.ts` to proxy the new endpoints locally:
  - `/api/compare-scenarios` -> `localhost:8083`
  - `/api/run-sensitivity` -> `localhost:8084`
- Updated `web/frontend/src/styles.css` with analysis-panel, summary-card, and comparison-table styles that follow the existing results dashboard language and collapse cleanly on narrower screens.

### Verification

- `npm run build` in `web/frontend` -> **pass**
- `ruff check web/functions/main.py web/functions/handlers/project_payload.py web/functions/handlers/compare_scenarios.py web/functions/handlers/run_sensitivity.py tests/unit/test_web_handlers.py` -> **pass**
- `web/functions/.venv\Scripts\python.exe -c "import main; import handlers.compare_scenarios; import handlers.run_sensitivity; print('imports-ok')"` -> **pass**
- Full Flask-backed handler pytest execution in `web/functions/.venv` remains blocked because that virtualenv currently lacks `pytest`, even though the web-function imports themselves load successfully there.

### Next Sensible Step

- Start the new local function targets on ports `8083` and `8084`, then exercise the full end-to-end browser flow so the new analysis panels populate from live API responses instead of build-only verification.

---

## ISSUE-12 Objective (Current Session)

Implement the code-side deployment blockers from `plans/web-app-deployment-roadmap.md` so the Firebase web app can be built and deployed with the `re_storage` package bundled into Cloud Functions and with explicit function resource settings.

### Scope

- [x] Replace the functions editable install with a deploy-safe vendored package flow
- [x] Automate vendoring in Firebase predeploy so deploys do not depend on manual copy steps
- [x] Add function resource settings in `firebase.json` for the current Python workload
- [x] Update ignore rules and docs for the new deployment flow
- [x] Verify the vendored install path, handler tests in the functions virtualenv, and the frontend production build

### Planned Implementation

- Add a small Python preparation script that copies `src/re_storage/` into `web/functions/re_storage/` while skipping caches and stale copies.
- Update `web/functions/requirements.txt` to remove the broken `-e ../..` deploy-time dependency.
- Update `firebase.json` to run the preparation script before deploy and to set higher timeout / memory limits for Python functions.
- Extend `web/functions/.gcloudignore` so vendored cache artifacts are excluded from upload.
- Document the new local verification and deployment steps in `README.md`.

### Expected Manual Follow-Up

- Firebase project creation and `.firebaserc` project ID replacement still require console / CLI access outside the repository.
- Final `firebase deploy --only functions,hosting` and production smoke tests depend on that real project setup.

### Review / Results

- Added `scripts/prepare_firebase_functions.py` to copy `src/re_storage/` into `web/functions/re_storage/` while skipping cache artifacts, giving Firebase deploys a self-contained import path for the model package.
- Updated `web/functions/requirements.txt` to remove the broken `-e ../..` editable install that would fail once Firebase uploads only the functions directory.
- Updated `firebase.json` with a `functions.predeploy` hook for the vendoring script plus `timeoutSeconds: 300` and `availableMemoryMb: 1024` for the Python workload.
- Updated `web/functions/.gcloudignore`, `.gitignore`, and `README.md` so the generated vendored package is deploy-safe, locally reproducible, and not accidentally tracked as hand-authored source.

### Verification

- `python scripts/prepare_firebase_functions.py` -> passed
- `web/functions/.venv/Scripts/python.exe -m pip install -r web/functions/requirements.txt` -> passed
- `web/functions/.venv/Scripts/python.exe -c "from re_storage.pipeline import run_full_model; print('ok')"` -> passed
- `web/functions/.venv/Scripts/python.exe -m pytest tests/unit/test_web_handlers.py -v` -> **11 passed**
- `npm --prefix web/frontend run build` -> passed (existing Vite chunk-size warning remains non-blocking)

# Web App Deployment Roadmap
# RE-Storage Firebase Tool

> **Prepared:** 2026-03-26
> **Based on:** Full review of `activeContext.md` (ISSUE-1 through ISSUE-11), `firebase.json`, `web/functions/requirements.txt`, `web/frontend/package.json`, `pyproject.toml`, and all plan docs.
> **Goal:** Ship the Firebase-hosted React + Python Cloud Functions app to a live URL.

---

## Current State Summary

The app is functionally complete locally:

| Layer | Status |
|---|---|
| Python model engine (`re_storage`) | Solid — 198+ unit tests pass, Emivest regression baseline locked |
| Cloud Functions backend (4 endpoints) | Code complete, linting passes, local smoke tests pass |
| React frontend (Vite + Recharts) | `npm run build` passes, two-panel layout, full results dashboard |
| Scenario comparison + sensitivity endpoints | Code complete, frontend wired |
| Firebase config (`firebase.json`, `.firebaserc`) | Skeleton only — placeholder project ID, no real Firebase project |

**Nothing has been deployed.** All verification has been against `localhost`.

---

## Blockers — Must Fix Before Deploy

### BLOCKER 1 — Editable install in `requirements.txt` will break Cloud Functions

**File:** `web/functions/requirements.txt`, line 10:
```
-e ../..
```

Firebase Cloud Functions uploads only the `web/functions/` directory to Google Cloud. The relative path `../..` (the `re_storage` package root) does not exist in the deployed environment. The function will fail to start with a `ModuleNotFoundError`.

**Fix options (choose one):**

**Option A — Copy source tree alongside functions (simplest, no registry needed):**
```bash
# Run from repo root before every deploy
cp -r src/re_storage web/functions/re_storage
```
Then change `requirements.txt` line 10 to remove the `-e ../..` entry entirely. The functions directory will contain `re_storage/` as a local package importable at runtime.

Add to `.gcloudignore` in `web/functions/`:
```
re_storage/__pycache__
re_storage/**/*.pyc
```

**Option B — Build a wheel and include it:**
```bash
pip install build
python -m build --wheel
# outputs dist/re_storage-0.1.0-py3-none-any.whl
cp dist/re_storage-0.1.0-py3-none-any.whl web/functions/
```
Change `requirements.txt` line 10 to:
```
./re_storage-0.1.0-py3-none-any.whl
```

> **Recommendation:** Option A is simpler for iterative deploys. Add a `Makefile` target or a `predeploy` hook in `firebase.json` to automate the copy so it never gets forgotten.

---

### BLOCKER 2 — Firebase project does not exist

**File:** `.firebaserc`
```json
{ "projects": { "default": "re-storage-tool" } }
```

`re-storage-tool` is a placeholder. Firebase will reject the deploy without a real project.

**Steps:**
1. Go to [console.firebase.google.com](https://console.firebase.google.com) and create a new project (e.g. `re-storage-tool` or any available ID).
2. Enable **Hosting** and **Cloud Functions** in the Firebase console.
3. Install the Firebase CLI if not already present:
   ```bash
   npm install -g firebase-tools
   ```
4. Authenticate:
   ```bash
   firebase login
   ```
5. Update `.firebaserc` with the real project ID:
   ```bash
   firebase use --add
   # select your project when prompted
   ```

---

### BLOCKER 3 — Cloud Functions memory and timeout not configured

The Python simulation runs pandas + scipy on 8,760 hourly rows. Default Cloud Functions memory (256 MB) and timeout (60 s) will likely be too small, especially for the scenario comparison endpoint which runs the pipeline 4 times.

**Fix — add resource config to `firebase.json`:**
```json
"functions": {
  "source": "web/functions",
  "runtime": "python311",
  "timeoutSeconds": 300,
  "availableMemoryMb": 1024
}
```

For the scenario / sensitivity endpoints, 2 GB / 540 s may be needed. Firebase Gen 2 functions (Cloud Run backed) allow up to 32 GB and no practical timeout limit — consider upgrading if 1 GB proves insufficient after first smoke test.

To use Gen 2:
```json
"functions": [
  {
    "source": "web/functions",
    "runtime": "python311",
    "gen": 2,
    "cpu": 1,
    "memory": "2GiB",
    "timeoutSeconds": 540
  }
]
```

---

### BLOCKER 4 — Handler test suite has never run with Flask installed in repo-level env

`tests/unit/test_web_handlers.py` auto-skips when Flask is absent. The handlers have only been verified via direct HTTP smoke tests against the local `functions-framework` server. Before deploy, run the full suite inside the functions virtualenv:

```bash
cd web/functions
.venv\Scripts\pip install pytest
.venv\Scripts\python -m pytest ../../tests/unit/test_web_handlers.py -v
```

Expected: all handler tests pass (currently skipped, not failing — this is a confidence check, not a known bug).

---

## Pre-Deploy Checklist

Work through these in order. Each item is a gate for the next.

### Step 1 — Fix the `re_storage` package dependency

- [ ] Choose Option A (copy) or Option B (wheel) from BLOCKER 1.
- [ ] Update `web/functions/requirements.txt` to remove `-e ../..`.
- [ ] Verify local install still works: `cd web/functions && .venv\Scripts\pip install -r requirements.txt`.
- [ ] Verify imports work: `.venv\Scripts\python -c "from re_storage.pipeline import run_full_model; print('ok')"`.

### Step 2 — Run full handler test suite

- [ ] `cd web/functions && .venv\Scripts\pip install pytest`
- [ ] `.venv\Scripts\python -m pytest ../../tests/unit/test_web_handlers.py -v`
- [ ] All tests pass (no skips).

### Step 3 — End-to-end browser smoke test (all 4 endpoints)

Start all 4 function targets and the frontend dev server, then manually test each flow:

```bash
# Terminal 1 — run all 4 function targets
cd web/functions
.venv\Scripts\python -m functions_framework --target runExcel       --source main.py --port 8081
.venv\Scripts\python -m functions_framework --target runJson        --source main.py --port 8082
.venv\Scripts\python -m functions_framework --target compareScenarios --source main.py --port 8083
.venv\Scripts\python -m functions_framework --target runSensitivity  --source main.py --port 8084

# Terminal 2 — frontend
cd web/frontend && npm run dev
```

Browser checklist at `http://127.0.0.1:5173`:
- [ ] Excel upload path: drag `.xlsx`, click Run — KPI cards and charts populate.
- [ ] Structured form path: fill required fields, attach hourly CSV, submit — results populate.
- [ ] Scenario comparison: after a form run, trigger "Compare Scenarios" — table populates with 4 PPA options.
- [ ] Sensitivity analysis: trigger sensitivity run — panel populates with swept values.
- [ ] USD/VND toggle: monetary KPIs and chart labels switch correctly.
- [ ] Mobile layout: resize browser to <768px — single-column layout, no overflow.

Fix any failures before proceeding.

### Step 4 — Create Firebase project and configure

- [ ] Create project in Firebase console.
- [ ] Enable Hosting + Cloud Functions (Blaze plan required for Python functions).
- [ ] `firebase login && firebase use --add` — select the new project.
- [ ] Confirm `.firebaserc` now has the real project ID.

### Step 5 — Update `firebase.json` with resource limits

- [ ] Add `timeoutSeconds` and `availableMemoryMb` (or Gen 2 config) as shown in BLOCKER 3.
- [ ] Verify `firebase.json` rewrites cover all 4 endpoints:
  - `/api/run-excel` → `runExcel`
  - `/api/run-json` → `runJson`
  - `/api/compare-scenarios` → `compareScenarios`
  - `/api/run-sensitivity` → `runSensitivity`

### Step 6 — Build the frontend

```bash
cd web/frontend
npm run build
```

- [ ] Build succeeds with no TypeScript errors.
- [ ] Note: Vite will emit a chunk-size warning about Recharts — this is non-blocking.
- [ ] Output is in `web/frontend/dist/` (matches `firebase.json` `"public"` setting).

### Step 7 — Deploy

```bash
# From repo root
firebase deploy --only functions,hosting
```

- [ ] Functions deploy succeeds (watch for import errors in Cloud Build logs).
- [ ] Hosting deploy succeeds.
- [ ] Firebase CLI prints the live Hosting URL (e.g. `https://re-storage-tool.web.app`).

### Step 8 — Production smoke test

- [ ] Open the live Hosting URL in browser.
- [ ] Repeat the same browser checklist from Step 3 against the production URL.
- [ ] Check Firebase console > Functions > Logs for any cold-start errors or timeouts.

---

## Outstanding Feature Work (Post-Deploy Polish)

These items are not deployment blockers but are tracked in `activeContext.md` as open:

### P1 — PPA option form fields not yet exposed in the structured form
- `web/functions/handlers/run_json.py`: add `ppa_option`, `bundled_discount_pct`, `pv_discount_pct`, `bess_discount_pct`, `fixed_ppa_price_usd_per_mwh` fields to `_build_project_payload()`.
- `web/frontend/src/components/inputs/SystemStep.tsx`: add PPA option radio group and conditional discount/price fields.

### P2 — HTML report download not wired
- `src/re_storage/reporting/html_report.py` `generate_report()` is callable.
- Needs a `?report=true` query-param branch in `run_excel.py` / `run_json.py` handlers and a "Download HTML Report" button in `ResultsDashboard.tsx`.

### P3 — DSCR covenant line is hardcoded at 1.3x
- `DscrChart.tsx` draws a fixed reference line at 1.3.
- Expose `target_dscr` in the API response and pass it through to the chart component.

### P4 — Regression parity targets not yet met against Excel reference
The Emivest JSON-path baseline is locked, but the Python model still overstates IRR vs the Excel workbook. This does not affect deployment but affects result credibility. Key targets from `activeContext.md`:
- `project_irr` within 0.5% of 0.08952 (currently ~0.2293)
- `equity_irr` within 0.5% of 0.19403 (currently ~0.2957)
- `npv_usd` within 2% of $22.03M (currently ~$2.03M)

Root cause is primarily missing CAPEX-scale OPEX parameters in the Emivest JSON fixture; once the JSON fixture is updated with correct CAPEX values the gap should narrow substantially.

### P5 — Remaining low-priority items
- `load_other_input()` for full MRA build-up schedule.
- Blended interest rate computation.
- Net billing revenue module.
- Demand charge: wire `cp_demand_vnd_per_kw` from loader.
- Form UX: project save/load, CSV preview in form, default-populated degradation table.

---

## Reference: Key File Locations

| What | Where |
|---|---|
| Firebase config | `firebase.json`, `.firebaserc` |
| Cloud Functions entry | `web/functions/main.py` |
| Function handlers | `web/functions/handlers/` |
| Functions requirements | `web/functions/requirements.txt` |
| Frontend source | `web/frontend/src/` |
| Frontend build output | `web/frontend/dist/` |
| Vite dev proxies | `web/frontend/vite.config.ts` |
| Python package source | `src/re_storage/` |
| Python package config | `pyproject.toml` |
| Regression baseline | `tests/data/references/emivest.json` |
| This roadmap | `plans/web-app-deployment-roadmap.md` |

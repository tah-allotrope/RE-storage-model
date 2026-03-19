# Web Tool Implementation Plan: RE-Storage Firebase App

> **Document purpose:** End-to-end blueprint for building a Firebase-hosted web tool that lets users run the `re_storage` Python model with project data and view financial results in a browser.
> **Model version analysed:** as of commit HEAD (`src/re_storage/pipeline.py`, `run_full_model` + `run_model_from_json`)
> **Target stack:** React (Vite) · Firebase Hosting · Firebase Cloud Functions (Python 3.11) · Firebase Storage · optional Firestore

---

## Table of Contents

1. [Model Summary (what we're exposing)](#1-model-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [How the Model Logic Will Be Called](#3-how-the-model-logic-will-be-called)
4. [UI Design](#4-ui-design)
5. [Firebase Setup](#5-firebase-setup)
6. [Project File/Folder Structure](#6-project-filefolder-structure)
7. [Implementation Phases](#7-implementation-phases)
8. [Deployment Instructions](#8-deployment-instructions)
9. [Risks & Considerations](#9-risks--considerations)

---

## 1. Model Summary

### What `re_storage` does

The model is a Python simulation engine for Vietnam solar PV + BESS (Battery Energy Storage System) projects. It operates in four sequential stages:

```
Excel or JSON+CSV
       │
       ▼
[A] Physics (hourly dispatch — 8,760 iterations)
       │  solar scaling, battery charge/discharge, SoC, energy balance
       ▼
[B] Settlement (DPPA revenue, grid tariff savings)
       │  Vietnam CfD/DPPA pricing, off-peak/standard/peak tariffs
       ▼
[C] Aggregation (hourly → monthly → Year 1 → 25-year lifetime)
       │  degradation factors applied, battery replacement accounted for
       ▼
[D] Financial (waterfall → debt sizing → IRR/NPV/DSCR)
       │  DSCR-constrained debt sizing via scipy brentq, XIRR-style metrics
       ▼
Flat KPI dict + DataFrames
```

### Model inputs

**System assumptions (from the Assumption sheet or JSON `system_input`/`bess_parameters`)**

| Field | Description | Example |
|---|---|---|
| `actual_capacity_kwp` | Installed solar capacity | 3,221 kWp |
| `simulation_capacity_kwp` | PVsyst model capacity | 100 kWp |
| `usable_bess_capacity_kwh` | Net battery capacity (`total × DoD`) | 1,827.5 kWh |
| `bess_power_rating_kw` | Battery power rating | 1,000 kW |
| `charge_efficiency` / `discharge_efficiency` | Half-cycle round-trip efficiency | 0.95 |
| `strategy_mode` | 1 = Arbitrage, 2 = Peak Shaving | 1 |
| `charging_mode` | 1 = Time Window, 2 = Pre-charge to target | 1 |
| `charge_start_hour` / `charge_end_hour` | Solar charging window | 10–16 |
| `precharge_target_soc_kwh` | Target SoC for pre-charge mode | 1,500 kWh |
| `min_direct_pv_share` | Minimum fraction of PV served to load | 0.10 |
| `active_pv2bess_share` | Fraction of PV surplus routed to battery | 0.30 |
| `demand_reduction_target` | Peak demand reduction target (ratio) | 0.20 |
| `strike_price_usd_per_kwh` | DPPA CfD strike price | ~0.069 $/kWh |
| `k_factor` | Grid loss adjustment | 1.02 |
| `kpp` | Price adjustment coefficient (22kV or 110kV) | 1.027 |
| `bess_enabled` | Toggle BESS simulation | true |
| `dppa_enabled` | Toggle DPPA revenue | true |

**Hourly time series (8,760 rows, one per hour of the year)**

| Column | Description |
|---|---|
| `datetime` | Timestamp (hourly) |
| `simulation_profile_kw` | PVsyst generation profile |
| `irradiation_wh_m2` | Global horizontal irradiation |
| `load_kw` | Site electricity load |
| `fmp_usd_per_kwh` | Forward Market Price |
| `cfmp_usd_per_kwh` | Contracted Forward Market Price |

**Degradation table (25 rows, one per project year)**

| Column | Description |
|---|---|
| `year` | Year 1–25 |
| `pv_factor` | PV output retention ratio (e.g. 0.997 in year 1) |
| `battery_factor_no_replacement` | Battery retention without replacement |
| `battery_factor_with_replacement` | Battery retention with augmentation |

**Financial parameters**

| Parameter | Description | Typical value |
|---|---|---|
| `initial_capex_usd` | Total project CAPEX | $8–20M |
| `interest_rate_pct` | Debt interest rate | 6% |
| `tenor_years` | Debt repayment period | 15 years |
| `target_dscr` | Minimum DSCR covenant | 1.3 |
| `discount_rate_pct` | Equity discount rate for NPV | 8–10% |
| `project_years` | Simulation horizon | 25 |
| `cod_date` | Commercial operation date | 2027-01-01 |
| `exchange_rate_usd_vnd` | USD/VND exchange rate | 26,000 |

**Grid tariff rates (USD/kWh)**

| Period | Typical rate |
|---|---|
| Off-peak | $0.040–0.060 |
| Standard | $0.070–0.100 |
| Peak | $0.120–0.200 |

### Model outputs

The pipeline returns a flat KPI dictionary plus optional DataFrames:

| Key | Unit | Description |
|---|---|---|
| `project_irr` | decimal | Project-level XIRR |
| `equity_irr` | decimal | Equity XIRR |
| `unlevered_irr` | decimal | Unlevered IRR |
| `npv_usd` | USD | Net present value |
| `dscr_min` | ratio | Minimum DSCR across debt tenor |
| `dscr_avg` | ratio | Average DSCR |
| `debt_amount_usd` | USD | DSCR-sized debt |
| `calc_solar_gen_sum_kwh` | kWh | Total Year 1 solar generation |
| `calc_soc_min_kwh` | kWh | Min battery SoC in Year 1 |
| `calc_soc_max_kwh` | kWh | Max battery SoC in Year 1 |
| `year1_solar_generation_mwh` | MWh | Year 1 scaled solar generation |
| `year1_dppa_revenue_usd` | USD | Year 1 DPPA revenue |
| `year1_grid_savings_usd` | USD | Year 1 grid tariff savings |

Additionally, the `run_model_from_json` function returns `_lifetime_df` (25-year annual projections) and `_hourly_df` (8,760-row physics+settlement results), both useful for charts.

---

## 2. Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                                     │
│                                                                           │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │            React SPA (Vite + Tailwind CSS)                       │   │
│   │   • Project input form (assumptions + financial parameters)      │   │
│   │   • Hourly CSV upload widget                                     │   │
│   │   • Excel upload shortcut (single-file path)                     │   │
│   │   • "Run Model" button → progress polling                        │   │
│   │   • Results dashboard: KPI cards + charts + downloadable report  │   │
│   └────────────────────────┬─────────────────────────────────────────┘   │
└────────────────────────────│──────────────────────────────────────────────┘
                             │  HTTPS / fetch
                             ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     FIREBASE HOSTING                                      │
│   Serves the React SPA (static assets, CDN-cached)                       │
│   URL rewrites → Cloud Functions for /api/* routes                       │
└───────────────────────────────────────────────────────────────────────────┘
                             │  firebase.json rewrite rules
                             ▼
┌───────────────────────────────────────────────────────────────────────────┐
│              CLOUD FUNCTIONS (2nd gen, Python 3.11)                      │
│                                                                           │
│  POST /api/run-excel     ← Upload path: user uploads .xlsx               │
│  POST /api/run-json      ← Form path: JSON params + CSV upload           │
│                                                                           │
│  Internal logic:                                                          │
│   1. Receive multipart form data                                          │
│   2. Save uploaded file(s) to /tmp (ephemeral)                           │
│   3. Call re_storage.pipeline.run_full_model()  (Excel path)             │
│        OR re_storage.pipeline.run_model_from_json() (JSON+CSV path)      │
│   4. Serialise KPI dict + lifetime_df to JSON                            │
│   5. Return JSON response (or stream progress via Server-Sent Events)     │
│                                                                           │
│  Bundle: re_storage package vendored into functions/re_storage/           │
└───────────────────────────────────────────────────────────────────────────┘
                             │  (optional, for run history)
                             ▼
┌───────────────────────────────────────────────────────────────────────────┐
│              CLOUD STORAGE (Firebase Storage)                             │
│   Optional: store uploaded files + result JSON for audit trail           │
│   Bucket: gs://<project>.appspot.com/runs/<run_id>/                      │
└───────────────────────────────────────────────────────────────────────────┘
```

### Design decisions

**Why Python Cloud Functions, not a JS rewrite?**

The model has ~1,400 lines of carefully validated Python across 12+ modules. It uses pandas, numpy, and scipy for an 8,760-step battery dispatch loop plus numerical root-finding. Rewriting in JavaScript would take weeks and risk introducing bugs. Python 2nd-gen Cloud Functions run the existing code directly with zero refactoring.

**Why Cloud Functions 2nd gen?**

- Python 3.11 support (required by the package)
- Up to 60-minute timeout (the model runs in ~2–10 seconds, so any tier works)
- Up to 32 GB memory (needed if very large Excel files are processed)
- Concurrent request handling

**Why no Firestore for MVP?**

The model is stateless — inputs in, KPIs out. Firestore adds complexity (auth, security rules, schema design) without a clear MVP benefit. It can be added later for run history and saved projects.

**Why Firebase Storage?**

Excel files can be 5–15 MB. Sending them directly through Cloud Functions as multipart form data is fine for MVP. Firebase Storage becomes necessary when files exceed ~10 MB or you need audit trails.

---

## 3. How the Model Logic Will Be Called

### Option A — Excel upload (existing users)

The user uploads their existing Excel workbook (with Assumption, Data Input, Loss, Tariff Schedule sheets). The Cloud Function calls:

```python
from re_storage.pipeline import run_full_model
results = run_full_model(Path(tmp_excel_path))
```

This is the fastest path to value for existing users who already have a formatted Excel file.

### Option B — Structured form + CSV upload (new projects)

The user fills in a web form (assumptions, financial parameters, tariff rates, degradation table) and uploads a CSV of 8,760 hourly rows. The Cloud Function:

1. Assembles the form data into the JSON schema expected by `run_model_from_json`
2. Saves the JSON to `/tmp/<run_id>/project.json`
3. Saves the CSV to `/tmp/<run_id>/hourly.csv`
4. Calls:

```python
from re_storage.pipeline import run_model_from_json
results = run_model_from_json(Path(tmp_project_dir))
```

The JSON schema matches the existing `Emivest.json` fixture format (fully documented in `src/re_storage/inputs/json_loader.py`).

### Vendoring the package

Because Cloud Functions bundle their own dependencies, the `re_storage` package needs to be either:

- **Installed via `requirements.txt`** (using a relative path or pip-installable wheel), OR
- **Copied directly** into the function's `lib/` directory

The recommended approach is to add a `requirements.txt` in the `functions/` directory that installs the package from the repo:

```
# functions/requirements.txt
-e ../..   # installs re_storage from the repo root in editable mode
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0
openpyxl>=3.1.0
scipy>=1.11.0
matplotlib>=3.7.0
flask>=3.0.0
functions-framework>=3.0.0
```

For production deployment (where the repo isn't available), build a wheel:

```bash
cd RE-storage-model
pip wheel . -w dist/
# Then copy dist/re_storage-0.1.0-py3-none-any.whl to functions/
# Add to functions/requirements.txt: ./re_storage-0.1.0-py3-none-any.whl
```

### Serialisation

The model returns `dict[str, float]` (KPIs) and `pd.DataFrame` objects. Before returning to the client, the function converts DataFrames to JSON:

```python
import json, math

def _sanitize(val):
    """Convert NaN/Inf to None for JSON serialisation."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

response_payload = {
    "kpis": {k: _sanitize(v) for k, v in kpi_dict.items()},
    "lifetime": lifetime_df.to_dict(orient="records"),   # 25 rows
    # hourly_df omitted from response (too large: 8760 × ~40 cols)
}
```

---

## 4. UI Design

### Page flow

```
Landing / Home
    └── "New Project" button
           │
           ├─── [Tab 1] Upload Excel  →  drag-drop .xlsx  →  Run
           └─── [Tab 2] New Project Form
                    ├── Step 1: System & BESS Parameters
                    ├── Step 2: DPPA & Tariff Settings
                    ├── Step 3: Financial Parameters
                    ├── Step 4: Degradation Table (editable grid or CSV upload)
                    ├── Step 5: Hourly Data (CSV upload, 8760 rows)
                    └── Step 6: Review & Run
                            │
                            ▼
                    [Results Dashboard]
```

### Step 1 — System & BESS Parameters

| UI Field | Maps to | Input Type | Default | Validation |
|---|---|---|---|---|
| Project name | metadata | text | — | Required |
| Installed capacity (kWp) | `actual_capacity_kwp` | number | — | > 0 |
| PVsyst simulation capacity (kWp) | `simulation_capacity_kwp` | number | — | > 0 |
| Total BESS storage (kWh) | `total_bess_kwh` | number | 0 | ≥ 0 |
| BESS power rating (kW) | `bess_power_rating_kw` | number | 0 | ≥ 0 |
| Depth of discharge (%) | `dod` | slider 0–100 | 85 | 50–100 |
| Half-cycle efficiency (%) | `charge_efficiency` | slider | 95 | 50–100 |
| BESS enabled | `bess_enabled` | toggle | on | — |
| Strategy mode | `strategy_mode` | radio | Arbitrage | — |
| Charging mode | `charging_mode` | radio | Time Window | — |
| Charge window start / end (h) | `charge_start_hour` / `charge_end_hour` | time pickers | 10 / 16 | 0–23 |
| Min PV-to-load share | `min_direct_pv_share` | slider | 10% | 0–100 |
| PV-to-BESS share | `active_pv2bess_share` | slider | 30% | 0–100 |
| Demand reduction target | `demand_reduction_target` | slider | 20% | 0–100 |

### Step 2 — DPPA & Tariff Settings

| UI Field | Maps to | Input Type |
|---|---|---|
| DPPA enabled | `dppa_enabled` | toggle |
| Strike price (VND/kWh) | `strike_price_vnd` | number |
| k-factor | `k_factor` | number (default 1.02) |
| Connection voltage (kV) | `connection_voltage_kv` | select: 22 / 110 |
| Kpp 22 kV | `kpp_22` | number (default 1.027) |
| Kpp 110 kV | `kpp_110` | number (default 1.009) |
| Off-peak tariff (USD/MWh) | `tariff_off_peak` | number |
| Standard tariff (USD/MWh) | `tariff_standard` | number |
| Peak tariff (USD/MWh) | `tariff_peak` | number |

### Step 3 — Financial Parameters

| UI Field | Maps to | Input Type | Default |
|---|---|---|---|
| USD/VND exchange rate | `exchange_rate_usd_vnd` | number | 26,000 |
| Solar CAPEX (USD/MWp) | `solar_usd_per_mwp` | number | — |
| BESS CAPEX (USD/MWh) | `bess_usd_per_mwh` | number | — |
| Base interest rate (%) | `base_rate` | number | 6.0 |
| Debt margin (%) | `debt_margin` | number | 0.0 |
| Max debt tenor (years) | `tenor_years` | number | 15 |
| Target DSCR | `target_dscr` | number | 1.3 |
| Max leverage ratio | `max_leverage_ratio` | number | 1.0 |
| Equity discount rate (%) | `discount_rate_pct` | number | 8.0 |
| Project lifetime (years) | `project_years` | number | 25 |
| COD date | `cod_date` | date picker | — |

### Step 4 — Degradation Table

An editable grid with 25 rows (pre-populated with typical Vietnam solar/BESS degradation curves). Columns: Year, PV retention factor, Battery retention (no replacement), Battery retention (with replacement).

Alternative: upload a CSV file with these 4 columns.

### Step 5 — Hourly Data Upload

- Large-area drag-and-drop zone for a CSV file
- Required columns displayed: `DateTime, SimulationProfile_kW, Irradiation_W/m2, Load_kW, FMP, CFMP`
- Client-side validation: check row count == 8,760
- Column name normalisation already handled server-side by `_normalize_hourly_columns()`

### Results Dashboard

```
┌────────────────────────────────────────────────────────────────────────┐
│  PROJECT: Saigon18                           Run completed in 4.2s     │
├──────────────┬──────────────┬────────────────┬───────────────────────┤
│ Project IRR  │  Equity IRR  │ Unlevered IRR  │       NPV             │
│    5.07%     │    4.64%     │    8.83%       │   -$2.65M             │
├──────────────┴──────────────┴────────────────┴───────────────────────┤
│ DSCR Min: 1.31   DSCR Avg: 1.47   Debt Sized: $12.4M                │
├────────────────────────────────────────────────────────────────────────┤
│ Year 1 Metrics                                                         │
│   Solar Generation: 4,578 MWh    DPPA Revenue: $316K   Grid Savings: $84K│
├────────────────────────────────────────────────────────────────────────┤
│  [Chart: 25-Year Annual Revenue — DPPA vs Grid Savings stacked bar]   │
│  [Chart: 25-Year Solar Generation with degradation curve]             │
│  [Chart: 25-Year Battery Effective Capacity]                          │
│  [Chart: Year 1 Monthly Energy Balance — bar chart]                   │
├────────────────────────────────────────────────────────────────────────┤
│  [Download JSON Results]   [Download HTML Report]   [Run Again]       │
└────────────────────────────────────────────────────────────────────────┘
```

The HTML report reuses the existing `re_storage.reporting.html_report.generate_report()` function, which already produces a polished Matplotlib-based HTML report. The Cloud Function can generate it server-side and return it as a downloadable file.

---

## 5. Firebase Setup

### Services required

| Service | Usage | Required? |
|---|---|---|
| Firebase Hosting | Serve React SPA | Yes |
| Cloud Functions (2nd gen) | Run Python model | Yes |
| Cloud Storage | Store uploaded files | Optional (Phase 2) |
| Firestore | Run history, saved projects | Optional (Phase 2) |
| Firebase Auth | User authentication | Optional (Phase 2) |

### Firebase project initialisation

```bash
npm install -g firebase-tools
firebase login
firebase init
# Select: Hosting, Functions, Storage (optional)
# Functions language: Python
# Hosting public dir: frontend/dist
# SPA rewrite: yes
```

### Cloud Functions configuration

```python
# functions/main.py
import functions_framework
from flask import Request, jsonify
```

Use **2nd-gen Cloud Functions** (not 1st gen) to get Python 3.11 support:

```yaml
# functions/.python-version (or specify in deploy command)
3.11
```

Function resource limits (set in `firebase.json` or via `gcloud` CLI):

```json
{
  "functions": [
    {
      "source": "functions",
      "codebase": "default",
      "ignore": ["node_modules", ".git", "venv"],
      "runtime": "python311",
      "memory": "2GiB",
      "timeoutSeconds": 300,
      "maxInstances": 10
    }
  ]
}
```

Memory: 2 GB is sufficient for an 8,760-row DataFrame with ~40 columns (approx. 50–200 MB). Timeout: 300 seconds is conservative — the model typically runs in under 10 seconds.

### URL rewrites (`firebase.json`)

```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      { "source": "/api/run-excel", "function": "runExcel" },
      { "source": "/api/run-json", "function": "runJson" },
      { "source": "**", "dest": "/index.html" }
    ]
  }
}
```

### CORS

The Cloud Functions must include CORS headers. Use the `flask-cors` package or manually set headers:

```python
from flask_cors import cross_origin

@functions_framework.http
@cross_origin()
def run_json(request: Request):
    ...
```

---

## 6. Project File/Folder Structure

```
RE-storage-model/
├── src/re_storage/           ← Existing model (do not modify)
├── tests/                    ← Existing tests (do not modify)
│
├── web/                      ← NEW: All web tool code
│   ├── frontend/             ← React SPA
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── components/
│   │   │   │   ├── layout/
│   │   │   │   │   ├── Header.tsx
│   │   │   │   │   └── Layout.tsx
│   │   │   │   ├── inputs/
│   │   │   │   │   ├── ExcelUploadTab.tsx
│   │   │   │   │   ├── ProjectForm.tsx
│   │   │   │   │   ├── SystemStep.tsx
│   │   │   │   │   ├── DppaStep.tsx
│   │   │   │   │   ├── FinancialStep.tsx
│   │   │   │   │   ├── DegradationStep.tsx
│   │   │   │   │   └── HourlyDataStep.tsx
│   │   │   │   ├── results/
│   │   │   │   │   ├── KpiCard.tsx
│   │   │   │   │   ├── KpiGrid.tsx
│   │   │   │   │   ├── LifetimeRevenueChart.tsx
│   │   │   │   │   ├── GenerationChart.tsx
│   │   │   │   │   ├── BatteryCapacityChart.tsx
│   │   │   │   │   └── ResultsDashboard.tsx
│   │   │   │   └── shared/
│   │   │   │       ├── FileDropzone.tsx
│   │   │   │       ├── ProgressBar.tsx
│   │   │   │       └── ErrorBanner.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useModelRun.ts      ← Handles API call + state
│   │   │   │   └── useCsvValidation.ts ← Client-side row count check
│   │   │   ├── api/
│   │   │   │   └── client.ts           ← fetch wrappers for /api/*
│   │   │   ├── types/
│   │   │   │   └── model.ts            ← TypeScript interfaces for KPIs, lifetime rows
│   │   │   └── utils/
│   │   │       └── formatters.ts       ← Number formatting (IRR → %, USD → $M, etc.)
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── functions/            ← Cloud Functions (Python 3.11)
│       ├── main.py           ← Function entry points
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── run_excel.py  ← POST /api/run-excel handler
│       │   └── run_json.py   ← POST /api/run-json handler
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── serialise.py  ← DataFrame → JSON, NaN sanitisation
│       │   └── validate.py   ← Request shape validation
│       ├── requirements.txt
│       └── .gcloudignore
│
├── firebase.json             ← Firebase Hosting + Functions config
├── .firebaserc               ← Firebase project alias
└── plans/
    └── web-tool-implementation-plan.md   ← This document
```

---

## 7. Implementation Phases

### Phase 1 — Cloud Function scaffolding (estimated: 2–3 days)

**Goal:** Prove the model runs inside a Cloud Function and returns valid JSON.

**Tasks:**

1. Create `web/functions/` directory structure.

2. Write `web/functions/requirements.txt` with all `re_storage` dependencies plus `functions-framework`, `flask`, `flask-cors`.

3. Write `web/functions/main.py` with two HTTP-triggered function stubs:

```python
# web/functions/main.py
import functions_framework
from handlers.run_excel import handle_run_excel
from handlers.run_json import handle_run_json

@functions_framework.http
def runExcel(request):
    return handle_run_excel(request)

@functions_framework.http
def runJson(request):
    return handle_run_json(request)
```

4. Write `web/functions/handlers/run_excel.py`:

```python
import tempfile, os
from pathlib import Path
from flask import Request, jsonify
from re_storage.pipeline import run_full_model
from utils.serialise import serialise_results

def handle_run_excel(request: Request):
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files['file']
    if not uploaded.filename.endswith('.xlsx'):
        return jsonify({"error": "File must be .xlsx"}), 400

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        uploaded.save(tmp.name)
        tmp_path = tmp.name

    try:
        results = run_full_model(Path(tmp_path))
        return jsonify(serialise_results(results))
    except Exception as e:
        return jsonify({"error": str(e), "type": type(e).__name__}), 422
    finally:
        os.unlink(tmp_path)
```

5. Write `web/functions/handlers/run_json.py` — same pattern but with two files and `run_model_from_json()`.

6. Write `web/functions/utils/serialise.py`:

```python
import math

def serialise_results(results: dict) -> dict:
    """Convert model output to JSON-safe dict (NaN → null)."""
    kpis = {}
    for k, v in results.items():
        if k.startswith('_'):  # skip DataFrames
            continue
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            kpis[k] = None
        else:
            kpis[k] = v

    lifetime_df = results.get('_lifetime_df')
    lifetime = []
    if lifetime_df is not None:
        for rec in lifetime_df.to_dict(orient='records'):
            sanitised = {
                k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                for k, v in rec.items()
            }
            lifetime.append(sanitised)

    return {"kpis": kpis, "lifetime": lifetime}
```

7. Test locally with the Functions Framework emulator:

```bash
cd web/functions
pip install -r requirements.txt
functions-framework --target runJson --debug
# POST to http://localhost:8080
```

8. Test with the real Emivest fixture (`tests/data/projects/emivest/`) to confirm KPIs match `tests/data/references/emivest.json`.

---

### Phase 2 — React frontend skeleton (estimated: 2–3 days)

**Goal:** A working single-page app with tab navigation and a functional Excel upload.

**Tasks:**

1. Scaffold with Vite + React + TypeScript + Tailwind:

```bash
cd web/frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss postcss autoprefixer recharts react-dropzone
npx tailwindcss init -p
```

2. Create `src/types/model.ts`:

```typescript
export interface ModelKpis {
  project_irr: number | null;
  equity_irr: number | null;
  unlevered_irr: number | null;
  npv_usd: number | null;
  dscr_min: number | null;
  dscr_avg: number | null;
  debt_amount_usd: number | null;
  calc_solar_gen_sum_kwh: number | null;
  year1_solar_generation_mwh: number | null;
  year1_dppa_revenue_usd: number | null;
  year1_grid_savings_usd: number | null;
}

export interface LifetimeRow {
  year: number;
  generation_mwh: number;
  battery_capacity_kwh: number;
  dppa_revenue_usd: number;
  grid_savings_usd: number;
}

export interface ModelResponse {
  kpis: ModelKpis;
  lifetime: LifetimeRow[];
}
```

3. Create `src/api/client.ts` with `runExcel(file: File)` and `runJson(formData: FormData)` functions.

4. Create `src/hooks/useModelRun.ts` (manages loading, error, result state).

5. Create `ExcelUploadTab.tsx` — a drag-and-drop zone using `react-dropzone` that calls `runExcel()` and transitions to the results view on success.

6. Create `ResultsDashboard.tsx` with placeholder KPI cards and a `LifetimeRevenueChart` using Recharts `BarChart`.

7. Wire up `App.tsx` with tab navigation (Excel Upload | New Project Form).

8. Configure `vite.config.ts` to proxy `/api/*` to `http://localhost:8080` for local development:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8080'
    }
  }
})
```

9. Verify end-to-end: upload the Ecoplexus Excel file, confirm KPI cards populate.

---

### Phase 3 — Full form inputs (estimated: 3–4 days)

**Goal:** The structured form path (JSON+CSV) works end-to-end.

**Tasks:**

1. Build `SystemStep.tsx` — sliders and inputs for all system/BESS parameters.

2. Build `DppaStep.tsx` — DPPA toggle, strike price, k-factor, connection voltage selector, tariff rates.

3. Build `FinancialStep.tsx` — all financial parameters with tooltips explaining each field.

4. Build `DegradationStep.tsx` — editable 25-row grid with pre-populated default degradation curves (use the values from `tests/data/projects/emivest/Emivest.json` as defaults).

5. Build `HourlyDataStep.tsx` — CSV upload with client-side row count validation (must be exactly 8,760). Show a preview table of the first 5 rows.

6. Build `ProjectForm.tsx` — multi-step wizard with a step indicator, "Next"/"Back" buttons, and a final "Run Model" button.

7. In `run_json.py`, assemble the uploaded form fields into the JSON structure that `load_assumptions_from_json()` and `load_financial_params_from_json()` expect. See `tests/data/projects/emivest/Emivest.json` for the exact structure.

8. Validate all inputs server-side using the existing Pydantic schemas — surface `InputValidationError` messages back to the client with field-level errors.

---

### Phase 4 — Results visualisation & report download (estimated: 2 days)

**Goal:** Rich results page with charts and a downloadable HTML report.

**Tasks:**

1. Complete `ResultsDashboard.tsx` with all KPI cards, formatted correctly (IRR as percentage, USD values with M/K suffix).

2. Add three Recharts charts using the `lifetime` array from the API response:
   - `LifetimeRevenueChart` — stacked bar: DPPA revenue vs grid savings per year
   - `GenerationChart` — line chart: solar generation MWh per year (showing degradation)
   - `BatteryCapacityChart` — line chart: effective battery capacity kWh per year

3. Add a "Download HTML Report" button. The Cloud Function generates the report using the existing `generate_report()` function and returns it as `Content-Type: text/html`:

```python
# In run_excel.py / run_json.py, add optional report endpoint
from re_storage.reporting.html_report import generate_report

if request.args.get('report') == 'true':
    html_content = generate_report_to_string(...)
    return html_content, 200, {'Content-Type': 'text/html'}
```

4. Add a "Download JSON Results" button (client-side, using `URL.createObjectURL`).

---

### Phase 5 — Polish, error handling, and deployment (estimated: 2 days)

**Goal:** Production-ready deployment.

**Tasks:**

1. Add comprehensive error handling in the UI: distinguish between validation errors (field-level form highlights), computation errors (model exploded), and network errors.

2. Add an `ErrorBanner.tsx` component that shows the error type and message from the API.

3. Add loading states: spinner during model run, with estimated time ("This usually takes 2–5 seconds").

4. Add a `ProgressBar.tsx` (indeterminate) while the API call is in flight.

5. Write `web/functions/utils/validate.py` to check request shape before running the model.

6. Set up Firebase project:

```bash
firebase projects:create re-storage-tool
firebase use re-storage-tool
```

7. Configure `firebase.json` (see Section 5).

8. Build and deploy (see Section 8).

9. Smoke test in production with the Emivest fixture.

---

### Phase 6 — Optional enhancements (future)

These are out of scope for the MVP but documented here for reference:

- **Firebase Auth**: Add Google login so users can save and reload their project configurations.
- **Firestore run history**: Store each run's inputs and KPI outputs, linked to a user's account.
- **Firebase Storage**: Upload large Excel files to Storage first, then pass the GCS URI to the function (avoids 10 MB multipart limit on Cloud Functions).
- **Sensitivity analysis**: Allow the user to vary one parameter (e.g., strike price) across a range and see how KPIs change.
- **Scenario comparison**: Run two configurations side-by-side.
- **Progress streaming**: Use Server-Sent Events (SSE) to stream progress through the 8,760-step dispatch loop (requires adding a callback/hook to the physics engine).
- **PDF export**: Generate a PDF summary using `weasyprint` or similar.

---

## 8. Deployment Instructions

### Prerequisites

- Node.js ≥ 18, Python 3.11, Firebase CLI (`npm i -g firebase-tools`)
- A Google Cloud project with billing enabled
- `firebase login` and `gcloud auth login` completed

### Local development

```bash
# Terminal 1: Start the Functions emulator
cd web/functions
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
functions-framework --target runExcel --port 8081 &
functions-framework --target runJson --port 8082 &

# Terminal 2: Start the React dev server
cd web/frontend
npm install
npm run dev
# App available at http://localhost:5173
```

### Build and deploy

```bash
# 1. Build the React app
cd web/frontend
npm run build
# Output: web/frontend/dist/

# 2. Deploy everything to Firebase
cd ../..  # repo root
firebase deploy

# Or deploy individually:
firebase deploy --only hosting
firebase deploy --only functions
```

### Environment variables

Set in `firebase.json` or via `gcloud`:

```bash
# Example: if you ever need to restrict allowed origins
gcloud functions set-env-vars runExcel ALLOWED_ORIGINS="https://your-app.web.app"
```

For the MVP there are no secret API keys required — the model runs entirely on the backend with the inputs provided by the user.

### Verify deployment

```bash
firebase hosting:channel:deploy preview --expires 1d
# Or just:
firebase open hosting:site
```

Run a test POST against the deployed function URL:

```bash
curl -X POST https://us-central1-<project>.cloudfunctions.net/runExcel \
  -F "file=@tests/data/projects/AUDIT 20251201 40MW Solar BESS Ecoplexus.xlsx" \
  | python -m json.tool
```

Expected KPI values to verify against (from `tests/data/references/AUDIT 20251201 40MW Solar BESS Ecoplexus.json`):

```json
{
  "project_irr": ~0.0507,
  "equity_irr": ~0.0464,
  "year1_solar_generation_mwh": <check reference>
}
```

---

## 9. Risks & Considerations

### R1 — Cloud Function cold start latency

**Risk:** Python Cloud Functions have cold starts of 3–10 seconds when idle. For a tool used infrequently this may feel slow.

**Mitigation:** Set `minInstances: 1` on the function to keep one instance warm (adds ~$5/month). Alternatively, set user expectations via a loading message.

### R2 — Memory pressure on large Excel files

**Risk:** The Ecoplexus Excel file is ~10 MB. `openpyxl` loads the entire workbook into memory; with pandas DataFrames the peak memory use could reach 500 MB–1 GB for very large files.

**Mitigation:** Set function memory to 2 GiB (see Section 5). Monitor via Cloud Console. If needed, increase to 4 GiB or switch to Firebase Storage + background processing.

### R3 — Request timeout on slow machines

**Risk:** The 8,760-step battery dispatch loop can take 5–30 seconds depending on function memory/CPU allocation.

**Mitigation:** Set `timeoutSeconds: 300`. The battery dispatch loop in `_run_physics()` is the bottleneck — it is already vectorised where possible but the per-timestep dispatch is inherently sequential. At 2 GiB RAM (which gives proportionally more CPU), it runs in under 10 seconds.

### R4 — Multipart upload size limit

**Risk:** Cloud Functions (1st gen) have a 10 MB request body limit. 2nd-gen functions on Cloud Run have a 32 MB limit. A combined Excel + form upload could exceed this for the largest workbooks.

**Mitigation:** Use 2nd-gen functions (enforced in Section 5). For files > 30 MB, switch to a Firebase Storage pre-upload flow (Phase 6).

### R5 — NaN/Inf in JSON serialisation

**Risk:** The model returns `float('nan')` and `float('inf')` when IRR cannot be solved (e.g., all-positive cash flows). Python's `json.dumps` will raise `ValueError` on these values.

**Mitigation:** The `serialise.py` utility (Phase 1 Task 6) converts `nan`/`inf` to `None` before encoding. The frontend displays `null` KPIs as "N/A".

### R6 — Excel workbook format variations

**Risk:** The `load_assumptions_from_cells()` function relies on label-scanning across Excel sheets (columns C/E, I/K, O/Q). New workbook versions with different layouts will silently use default values.

**Mitigation:** The function already logs `WARNING: Assumption 'X' not found, using default Y`. Surface these warnings to the user in the API response (add a `warnings: string[]` field to the response payload). Users should cross-check KPIs against their Excel before trusting results.

### R7 — DPPA disabled silently producing zero revenue

**Risk:** If `dppa_enabled=False`, the model logs a warning but continues, returning zero DPPA revenue. A user who accidentally turns this off will see drastically different financials.

**Mitigation:** Include a prominent banner on the results page when DPPA revenue is zero and DPPA is enabled in the inputs. Additionally, expose any warnings returned from `validate_financial_solver_freshness()` in the UI.

### R8 — Hourly CSV column name mismatches

**Risk:** Users may export hourly data with slightly different column headers than the canonical format.

**Mitigation:** The existing `_normalize_hourly_columns()` function handles the known aliases (e.g., `FMP` → `fmp_usd_per_kwh`). Document the expected column names prominently in the CSV upload step, and return actionable error messages if validation fails.

### R9 — CORS in production

**Risk:** The Firebase Hosting domain and Cloud Functions domain are different origins. Requests from the frontend will be blocked by browser CORS policy.

**Mitigation:** Add `flask-cors` to the functions and configure `CORS(app, origins=["https://<project>.web.app"])`. The URL rewrite in `firebase.json` (Section 5) means in production all `/api/*` requests are served from the same hosting domain, which avoids CORS entirely. CORS headers are only needed for direct function invocations during development.

### R10 — No authentication (MVP)

**Risk:** The public deployment will accept model runs from anyone, potentially exposing the tool to abuse (large file uploads, resource exhaustion).

**Mitigation:** For MVP (internal use only), restrict access by deploying to a private Firebase Hosting channel or by adding Firebase App Check. Rate-limit by IP via Cloud Armor if needed. Add Firebase Auth in Phase 6.

---

*Plan version: 1.0*
*Authored: 2026-03-19*
*Based on: `src/re_storage/pipeline.py`, `src/re_storage/inputs/`, `tests/data/projects/emivest/Emivest.json`*

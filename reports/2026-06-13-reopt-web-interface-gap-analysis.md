# Gap Analysis: REopt-Style Web Interface Exposing All Model Functions

**Date:** 2026-06-13
**Scope:** Compare the existing `web/` Firebase app against a target of an NREL REopt-like web interface that exposes the full `re_storage` function surface (Excel run, JSON run, scenario comparison, sensitivity, two-component tariff, topology, assessment verdicts, report/workbook export, and run persistence).
**Status:** Draft for Review

---

## Executive Summary

A substantial web tool **already exists** — a Firebase Hosting + 4 Python Cloud Functions backend and a React/TypeScript SPA with a full structured input form, KPI dashboard, seven charts, scenario comparison, and sensitivity analysis. The work is **not greenfield**; it is roughly 60–70% of the way to "expose all functions." The remaining gaps are concentrated in: (1) **assessment/Go-No-Go verdicts** and (2) **report/workbook export**, both fully implemented in the model but unexposed in the UI; (3) the **two-component tariff** and **onsite/offsite topology** paths (recent Sprint 2 & 4 features) that the form hardcodes away; and (4) **persistence/auth/deployment readiness** (the app has never been deployed — `.firebaserc` still points at a placeholder project). There is **one conceptual gap versus REopt itself**: REopt *optimizes* system sizing, whereas `re_storage` only *evaluates* a given configuration — no optimizer function exists to expose. Net: 4 CRITICAL/HIGH gaps, all building on strong existing assets; no module needs to be built from scratch.

---

## Current Capabilities (What We Have)

| Capability | Status | Key Surfaces |
|---|---|---|
| Firebase scaffold (hosting + functions config) | Working | [firebase.json](../firebase.json), [.firebaserc](../.firebaserc), [scripts/prepare_firebase_functions.py](../scripts/prepare_firebase_functions.py) |
| Excel-upload run path | Working | [web/functions/handlers/run_excel.py](../web/functions/handlers/run_excel.py), [ExcelUploadTab.tsx](../web/frontend/src/components/inputs/ExcelUploadTab.tsx) |
| Structured JSON+CSV run path | Working | [run_json.py](../web/functions/handlers/run_json.py), [project_payload.py](../web/functions/handlers/project_payload.py), [ProjectForm.tsx](../web/frontend/src/components/inputs/ProjectForm.tsx) |
| Multi-step input form (system/BESS, DPPA, financial, degradation, hourly CSV) | Working | [SystemStep](../web/frontend/src/components/inputs/SystemStep.tsx), [DppaStep](../web/frontend/src/components/inputs/DppaStep.tsx), [FinancialStep](../web/frontend/src/components/inputs/FinancialStep.tsx), [DegradationStep](../web/frontend/src/components/inputs/DegradationStep.tsx), [HourlyDataStep](../web/frontend/src/components/inputs/HourlyDataStep.tsx) |
| Scenario comparison (PPA options 1–4) | Working | [compare_scenarios.py](../web/functions/handlers/compare_scenarios.py), [scenarios/runner.py](../src/re_storage/scenarios/runner.py), [ScenarioComparisonTable.tsx](../web/frontend/src/components/results/ScenarioComparisonTable.tsx) |
| Sensitivity analysis (sweep one variable) | Working | [run_sensitivity.py](../web/functions/handlers/run_sensitivity.py), [scenarios/sensitivity.py](../src/re_storage/scenarios/sensitivity.py), [SensitivityPanel.tsx](../web/frontend/src/components/results/SensitivityPanel.tsx) |
| KPI dashboard + 7 charts (cashflow, DSCR, lifetime revenue, generation, battery capacity, dispatch week) | Working | [ResultsDashboard.tsx](../web/frontend/src/components/results/ResultsDashboard.tsx), [serialise.py](../web/functions/utils/serialise.py) |
| JSON results download | Working | [ResultsDashboard.tsx:29](../web/frontend/src/components/results/ResultsDashboard.tsx) |
| Web handler test coverage | Working | [tests/unit/test_web_handlers.py](../tests/unit/test_web_handlers.py) (11 tests) |
| Go/No-Go assessment verdicts (`assess_project`) | **Missing in web** (model: mature) | [reporting/assessment.py](../src/re_storage/reporting/assessment.py) |
| HTML report (`generate_report`) | **Missing in web** (model: mature) | [reporting/html_report.py](../src/re_storage/reporting/html_report.py) |
| Branded Excel assessment workbook | **Missing in web** (model: mature) | [reporting/excel_writer.py](../src/re_storage/reporting/excel_writer.py), [scripts/generate_dppa_assessment.py](../scripts/generate_dppa_assessment.py) |
| Two-component tariff mode (Sprint 4) | **Missing in web** (model: mature) | [pipeline.py:964](../src/re_storage/pipeline.py), `run_tariff_mode_comparison` in [sensitivity.py](../src/re_storage/scenarios/sensitivity.py) |
| Onsite/offsite DPPA topology (Sprint 2) | **Missing in web** (model: mature) | `dppa_topology` param in [pipeline.py:976](../src/re_storage/pipeline.py) |
| Run persistence / history / shareable links | Missing | — (no Firestore/Storage wired) |
| Authentication / rate limiting | Missing | — |
| Live production deployment | Missing | `.firebaserc` placeholder, never deployed |
| System-sizing optimization (REopt's core) | Not in model | — (no optimizer function exists) |

---

## Target State

> A deployed, REopt-like web application where a user can configure a Vietnam Solar + BESS project (by Excel upload **or** structured form), run it, and see a full results dashboard — KPIs, lifetime/cashflow/dispatch charts, a **Go/No-Go verdict**, **scenario (PPA option) and tariff-mode comparison**, **sensitivity tornadoes**, and **downloadable HTML report + Excel workbook** — with the option to **save, reload, and share** runs. Every public function in `re_storage` (pipeline, scenarios, sensitivity, settlement variants, assessment, reporting) is reachable through the UI or API.

---

## Gap Analysis

### GAP-01: Assessment (Go/No-Go) verdicts not exposed

**Severity:** HIGH — A REopt-style tool's headline output is a recommendation. The model already computes one; the UI silently drops it.

**Current state:** [reporting/assessment.py](../src/re_storage/reporting/assessment.py) provides `assess_project()`, `AssessmentThresholds`, and `AssessmentVerdict` (IRR/DSCR/NPV pass-fail with an overall verdict). None of the four handlers call it, and [serialise.py](../web/functions/utils/serialise.py) returns only raw KPIs — no verdict field. The dashboard renders numbers with no go/no-go framing.

**What's needed:**
- Call `assess_project()` in the run handlers and add a `verdict` block to the serialised payload (overall + per-metric pass/fail and thresholds).
- Add a verdict banner/card at the top of [ResultsDashboard.tsx](../web/frontend/src/components/results/ResultsDashboard.tsx) (green/amber/red), plus per-metric chips.
- Optionally expose threshold overrides (target DSCR, min IRR) as form inputs feeding `AssessmentThresholds`.

**Existing assets to reuse:**
- `assess_project` / `AssessmentVerdict` / `AssessmentThresholds` — complete and tested (Sprint 3, 10 tests).
- `KpiGrid` / `KpiCard` styling patterns for the new verdict component.

**Effort estimate:** 1 small plan (2 phases): backend wiring + serialise field; frontend verdict component.

---

### GAP-02: Report and workbook export not available (JSON-only download)

**Severity:** HIGH — REopt offers PDF/printable results and data export. Here the model produces a polished HTML report and a branded Excel workbook, but the UI offers only `Download JSON`.

**Current state:** [html_report.py](../src/re_storage/reporting/html_report.py) `generate_report()` and [excel_writer.py](../src/re_storage/reporting/excel_writer.py) (`create_workbook`, `write_*_sheet`, driven by [scripts/generate_dppa_assessment.py](../scripts/generate_dppa_assessment.py)) are mature. No handler emits `text/html` or `.xlsx`. [ResultsDashboard.tsx:29](../web/frontend/src/components/results/ResultsDashboard.tsx) only blobs the JSON.

**What's needed:**
- Add a `runReport`/`exportWorkbook` Cloud Function (or a `?format=html|xlsx` switch on the run handlers) that returns the report with the right `Content-Type` and `Content-Disposition`.
- Add new rewrites in [firebase.json](../firebase.json) and "Download HTML Report" / "Download Excel Workbook" buttons in the dashboard.
- Decide whether to re-run the model or cache `_hourly_df`/`_lifetime_df` from the prior run (they are large and currently discarded after serialisation).

**Existing assets to reuse:**
- `generate_report()` returns a self-contained HTML string with embedded matplotlib PNGs — directly returnable.
- `excel_writer` + `generate_assessment()` already assemble cover/assumptions/comparison/sensitivity/assessment sheets with branding.

**Effort estimate:** 1 plan (2–3 phases): report endpoint, workbook endpoint, frontend buttons + run-context caching.

---

### GAP-03: Two-component tariff path hardcoded off

**Severity:** HIGH — This is the most recent shipped model feature (Sprint 4) and is completely unreachable from the web form.

**Current state:** [project_payload.py:104](../web/functions/handlers/project_payload.py) hardcodes `"tariff_structure": "1-component"` and `Cp_demand: 0.0`. The pipeline supports `tariff_mode`, `cp_demand_vnd_per_kw`, `ca_tariff_rates`, surfaces `demand_charge_savings_usd`, and there is a categorical `run_tariff_mode_comparison()` ([sensitivity.py](../src/re_storage/scenarios/sensitivity.py)) — none of it is wired. `serialise.py` does carry a `demand_charge_savings_usd` column but it is always zero given the hardcode.

**What's needed:**
- Add a tariff-mode selector (1-component / 2-component / both) + `Cp_demand` and Ca-rate inputs to [DppaStep.tsx](../web/frontend/src/components/inputs/DppaStep.tsx) and `formTypes.ts`.
- Thread `tariff_mode` / `cp_demand_vnd_per_kw` through `build_project_payload` and the run/scenario/sensitivity handlers (pipeline params already exist).
- Expose `run_tariff_mode_comparison()` as a comparison view (reuse `ScenarioComparisonTable`), showing the demand-charge-savings delta.

**Existing assets to reuse:**
- Full Sprint 4 pipeline + loader support; `run_tariff_mode_comparison`; `demand_charge_savings_usd` already in the annual serialiser columns.
- `ScenarioComparisonTable` for the mode-delta display.

**Effort estimate:** 1 plan (2 phases): payload/handler threading + form fields; comparison view.

---

### GAP-04: Not deployed; persistence, auth, and run history absent

**Severity:** HIGH — "Have a web interface" implies a reachable, durable app. Today it runs only locally and keeps no state; REopt gives every run a shareable, reloadable URL.

**Current state:** [.firebaserc](../.firebaserc) default is the placeholder `re-storage-tool` (README §132 flags "replace placeholder before first deploy"); no evidence of a real deploy. The plan deliberately deferred Firestore/Storage/Auth to "Phase 6" ([plans/web-tool-implementation-plan.md:822](../plans/web-tool-implementation-plan.md)). No saved-project, run-history, or share-link feature exists; results vanish on refresh.

**What's needed:**
- Provision a real Firebase project, set billing, replace `.firebaserc`, run the documented deploy checklist (README §123), smoke-test with the Emivest/Ecoplexus fixtures.
- (Persistence) Add Firestore for run inputs+KPIs and a `runs/<id>` share route; optionally Storage for uploaded Excel/CSV audit trail.
- (Access control) Decide audience; add Firebase Auth or App Check + a `maxInstances`/rate limit (Risk R10 in the plan).

**Existing assets to reuse:**
- `prepare_firebase_functions.py` vendoring + `predeploy` hook already configured.
- Deploy checklist and resource limits already documented in README and `firebase.json`.

**Effort estimate:** 1 plan (3 phases): (a) first production deploy; (b) Firestore persistence + share links; (c) auth/rate-limit. Phase (a) is small and unblocks everything.

---

### GAP-05: Limited results depth — one-week dispatch sample, no full timeseries export

**Severity:** MEDIUM — REopt lets users inspect and download the full 8,760-hour dispatch; here only the first 168 hours are returned and there is no CSV export of dispatch/annual series.

**Current state:** [serialise.py:45](../web/functions/utils/serialise.py) caps `dispatch_sample` at `24*7` hours from `head()`; the full `_hourly_df` is discarded. [DispatchPreviewChart.tsx](../web/frontend/src/components/results/DispatchPreviewChart.tsx) renders only that week. No average-day or monthly-energy-balance view (the model's `generate_average_day_dispatch` / `generate_monthly_generation_bar` exist but aren't surfaced as data).

**What's needed:**
- Add an endpoint or response field for a selectable date range / representative day, and a "Download dispatch CSV" / "Download annual CSV" action.
- Optionally surface monthly energy-balance and average-day charts (model functions already exist in [reporting/charts.py](../src/re_storage/reporting/charts.py)).

**Existing assets to reuse:**
- `_hourly_df`, `_annual_df`, `_lifetime_df` are already produced by the pipeline; `generate_average_day_dispatch`, `generate_monthly_generation_bar`, `generate_dscr_line_chart` in `reporting/charts.py`.

**Effort estimate:** 1 small plan (2 phases).

---

## Second-Tier Gaps

| Gap | Severity | Summary | Existing Assets |
|---|---|---|---|
| GAP-06: Onsite/offsite topology not in form | MEDIUM | `dppa_topology` param ([pipeline.py:976](../src/re_storage/pipeline.py)) threaded through scenario runner but hardcoded "onsite" in web payload; Sprint 2 feature unreachable | `run_all_scenarios`/sensitivity already accept topology |
| GAP-07: No landing page / example library | MEDIUM | REopt opens with guided examples + docs; app drops straight into a form. Emivest/Ecoplexus fixtures could seed "load example" | [tests/data/projects/](../tests/data) fixtures, defaults in `formTypes.ts` |
| GAP-08: No multi-variable / tornado sensitivity UI | MEDIUM | `run_full_sensitivity` + `plot_tornado_chart` exist ([sensitivity.py](../src/re_storage/scenarios/sensitivity.py)); web exposes only single-variable value sweep | `build_sensitivity_dataframe`, `plot_tornado_chart` |
| GAP-09: Stale built `dist/` committed; no web CI | MEDIUM | [web/frontend/dist/](../web/frontend/dist) is checked in and may drift from source; no lint/build/test gate for `web/` | existing `npm run build`, `test_web_handlers.py` |
| GAP-10: Settlement-variant transparency (bundled/separate/fixed PPA) | LOW | Each PPA option maps to a settlement module ([settlement/](../src/re_storage/settlement)); UI shows option number but no per-option revenue breakdown | `calculate_bundled_revenue`, `calculate_separate_revenue`, `calculate_fixed_ppa_revenue` |
| GAP-11: No unit toggle / currency consistency help | LOW | Dashboard has a currency toggle; inputs mix VND/USD/% with no inline guidance | `formatters.ts`, existing tooltips |
| GAP-12: System-sizing optimization (REopt parity) | LOW (scope note) | REopt *optimizes* PV/BESS sizing for max NPV; `re_storage` only *evaluates*. No optimizer function exists to expose — out of scope for "expose all functions," but note the conceptual divergence | sensitivity sweeps approximate manual optimization |

---

## Recommended Sprint Sequencing

| Priority | Gap | Rationale |
|---|---|---|
| Sprint 1 | GAP-04(a) first production deploy | Unblocks every other gap being testable on a real URL; smallest of the four HIGHs; currently the app exists but is unreachable |
| Sprint 1 | GAP-01 assessment verdicts | Highest user-visible value per unit effort; pure wiring of an already-tested function; defines the REopt-style "recommendation" |
| Sprint 2 | GAP-02 report + workbook export | Depends on a stable run-context/caching decision; high stakeholder value (shareable artifacts) |
| Sprint 2 | GAP-03 two-component tariff | Recent shipped feature should not be dark; small threading effort; pairs naturally with the tariff section of the form |
| Sprint 3 | GAP-04(b/c) persistence + auth | Builds on the Sprint 1 deploy; needed before any external/public audience |
| Sprint 3 | GAP-05 + GAP-06 results depth & topology | Rounds out "all functions" coverage; depends on run-context caching from GAP-02 |
| Backlog | GAP-07…GAP-12 | Polish and REopt-parity UX once core function coverage is complete |

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Run-context caching for report/workbook export | Re-running the model per export doubles latency or requires holding large `_hourly_df` in memory/Storage | M | Decide early in GAP-02: stash run inputs in Firestore and re-run on export, or cache DataFrames to Storage keyed by run id |
| Cloud Function cold start (Python+pandas+scipy) | 3–10s first-run latency feels slow vs REopt | M | `minInstances: 1` (plan Risk R1); show "2–10s" progress copy (already present) |
| Placeholder Firebase project / billing not enabled | First deploy fails or silently uses wrong project | H | GAP-04(a): explicit "provision + replace `.firebaserc` + enable billing" checklist before deploy |
| Stale committed `dist/` deploys outdated UI | Users see old frontend after a deploy that skipped rebuild | M | GAP-09: add CI build step or stop tracking `dist/`; always `npm run build` in predeploy |
| Two-component tariff fixture/voltage edge cases | Wrong Ca-rate tier selected for non-22kV connections | L | Reuse Sprint 4 voltage-tier matching tests; validate `tariff_mode` server-side (already raises `ValueError`) |
| Public abuse without auth | Resource exhaustion / cost from anonymous large uploads | M | GAP-04(c): App Check or Auth + `maxInstances` cap before any public launch |

---

## Suggested Next Step

Review this report, then invoke `/plan` per gap in sequencing order — start with **GAP-04(a) first production deploy** and **GAP-01 assessment verdicts** as the Sprint 1 pair, since both are small, unblock everything else, and deliver the core REopt-style "reachable app with a recommendation." GAP-02 and GAP-03 follow in Sprint 2.

# Active Context — GAP-02: HTML Report and Excel Workbook Export (Web)

**Plan:** `plans/2026-06-13-web-report-workbook-export-plan.md`
**Gap analysis:** `reports/2026-06-13-reopt-web-interface-gap-analysis.md`
**Scope decision (Q-001):** Single-run workbook (Cover + Assumptions + Assessment); full multi-scenario/sensitivity gated behind `?full=true` (deferred — single-run is the MVP).
**Workflow:** TDD per phase → run tests → git commit + push per phase → `model-report-generator`-style final report at end.

## PHASE-01 — Backend: HTML report endpoint ✅
- [x] `web/functions/handlers/run_report.py` `handle_run_report(request)` — accepts JSON (`source=json`, form + `hourly_csv`) or Excel (`source=excel`, `file`)
- [x] Re-runs `run_model_from_json` / `run_full_model` from posted inputs (no caching — stateless)
- [x] Calls `generate_report(project_config, results, reference_kpis=None, lifetime_df, hourly_df)`
- [x] Returns `text/html` + `Content-Disposition: attachment; filename=re-storage-report-<slug>.html`
- [x] `Access-Control-Expose-Headers: Content-Disposition` so frontend can read filename (set on both handler response and `@cross_origin(expose_headers=...)`)
- [x] Registered `runReport` in `web/functions/main.py`
- [x] Tests in `tests/unit/test_web_handlers.py`: 7 new (method, JSON success, JSON missing-csv, Excel success, Excel missing-file, Excel wrong-ext, missing-DataFrames 422) — **23 passed**
- [x] ruff clean (after `--fix` for import ordering); mypy `return-value` warnings match pre-existing pattern in `run_excel.py` (no new regressions)

## PHASE-02 — Backend: Excel workbook endpoint (single-run) ✅
- [x] `web/functions/handlers/export_workbook.py` `handle_export_workbook(request)` — same dual-source pattern as `run_report`
- [x] Reuses `create_workbook` + `write_cover_sheet` + `write_assumptions_sheet` + `write_assessment_sheet` + `save_workbook` (no scenario sweep — single-run scope per Q-001)
- [x] Cover sheet carries `assess_project()` verdict; assumptions sheet filters out KPI keys (mirrors `scripts/generate_dppa_assessment.py::_extract_assumptions`)
- [x] Streams xlsx with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `Content-Disposition: attachment; filename=re-storage-workbook-<slug>-<YYYYMMDD>.xlsx`, and exposes `Content-Disposition` to CORS
- [x] Cleans up temp file in `finally`
- [x] Registered `exportWorkbook` in `main.py` with `@cross_origin(expose_headers=["Content-Disposition"])`
- [x] Added `/api/run-report` and `/api/export-workbook` rewrites to `firebase.json`
- [x] Tests: 6 new (method, JSON success + sheet-name assertions, JSON missing-csv, Excel success, Excel missing-file, Excel wrong-ext) — **29 passed** (loads xlsx with `openpyxl.load_workbook` to assert `Cover`/`Assumptions`/`Assessment` present and no `Comparison`/`Sensitivity`)
- [x] ruff clean

## PHASE-03 — Frontend: download buttons + run-context resend
- [ ] `useModelRun` persists last `FormData` AND last uploaded Excel `File` so exports can resend without re-upload
- [ ] `api/client.ts`: `downloadReport(formData)` + `downloadWorkbook(formData)` — `fetch` → `blob()` → `URL.createObjectURL` → anchor click
- [ ] Both functions support JSON and Excel paths
- [ ] `ResultsDashboard.tsx`: two new buttons next to "Download JSON Results", with loading state
- [ ] `firebase.json`: add `/api/run-report` and `/api/export-workbook` rewrites

## Review / Results
(populated at end of sprint)

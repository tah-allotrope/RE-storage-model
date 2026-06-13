---
title: "Web GAP-02: HTML Report and Excel Workbook Export"
date: "2026-06-13"
status: "draft"
request: "Create a multi-phase plan for GAP-02 (report/workbook export) from reports/2026-06-13-reopt-web-interface-gap-analysis.md"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-06-13-reopt-web-interface-gap-analysis.md"
---

# Plan: Web GAP-02: HTML Report and Excel Workbook Export

## Objective
Let users download the model's polished HTML report and branded Excel assessment workbook from the web UI. Both artifacts are fully implemented in the model but the dashboard currently offers only "Download JSON". This delivers the shareable, client-ready output a REopt-style tool is expected to produce.

## Context Snapshot
- **Current state:** [src/re_storage/reporting/html_report.py](../src/re_storage/reporting/html_report.py) `generate_report()` returns a self-contained HTML string with embedded matplotlib PNGs; [src/re_storage/reporting/excel_writer.py](../src/re_storage/reporting/excel_writer.py) + [scripts/generate_dppa_assessment.py](../scripts/generate_dppa_assessment.py) build a multi-sheet branded workbook. No handler emits `text/html` or `.xlsx`; [ResultsDashboard.tsx:29](../web/frontend/src/components/results/ResultsDashboard.tsx) only blobs JSON.
- **Desired state:** New endpoints return the HTML report and the `.xlsx` workbook with correct `Content-Type`/`Content-Disposition`; the dashboard exposes "Download HTML Report" and "Download Excel Workbook" buttons. A run-context mechanism makes export possible without forcing the user to re-enter inputs.
- **Key repo surfaces:** `generate_report` (html_report.py), `create_workbook`/`write_*_sheet`/`save_workbook` (excel_writer.py), `generate_assessment` (generate_dppa_assessment.py), `main.py` entrypoints, `firebase.json` rewrites, `ResultsDashboard.tsx`, `api/client.ts`.
- **Out of scope:** PDF export, emailing reports, persistence of past reports (touches GAP-04).

## Research Inputs
- [reports/2026-06-13-reopt-web-interface-gap-analysis.md](../reports/2026-06-13-reopt-web-interface-gap-analysis.md) — GAP-02 (HIGH) and Risk "Run-context caching": flags the key decision of re-running vs caching the large `_hourly_df`/`_lifetime_df` discarded after serialisation.

## Assumptions and Constraints
- **CON-001:** Cloud Functions are stateless and `/tmp` is ephemeral; the report/workbook must be generated within a single request from inputs the client re-sends.
- **DEC-001:** Re-run the model inside the export request from the same inputs (rather than caching DataFrames across requests). The model runs in ~2–10s and this avoids any storage dependency, keeping GAP-02 independent of GAP-04.
- **ASM-001:** `generate_report()` needs `results` (incl. `_hourly_df`/`_lifetime_df`), `config`, and an optional `reference`; the export handler reconstructs `results` by re-running `run_model_from_json`/`run_full_model` on the posted inputs.
- **CON-002:** `matplotlib` and `openpyxl` are already in [web/functions/requirements.txt](../web/functions/requirements.txt) (model deps) — verify before relying on them.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | HTML report endpoint | None | `runReport` function + `/api/run-report` rewrite |
| PHASE-02 | Excel workbook endpoint | PHASE-01 | `exportWorkbook` function + `/api/export-workbook` rewrite |
| PHASE-03 | Frontend download buttons + run-context resend | PHASE-01, PHASE-02 | Wired dashboard + `api/client.ts` calls |

## Detailed Phases

### PHASE-01 - HTML report endpoint
**Goal**
A handler re-runs the model from posted inputs and returns `generate_report()` HTML as a downloadable file.

**Tasks**
- [ ] TASK-01-01: Create `web/functions/handlers/run_report.py` with `handle_run_report(request)` that accepts the same multipart form + `hourly_csv` as `run_json` (reuse `build_project_payload`), runs `run_model_from_json`, then calls `generate_report(...)`.
- [ ] TASK-01-02: Decide config/reference inputs for `generate_report` — pass the assembled project payload as `config`; pass `reference={}` (no Excel comparison) when none supplied. Confirm the function tolerates an empty reference (inspect `_render_comparison_table`).
- [ ] TASK-01-03: Return `html, 200, {"Content-Type": "text/html; charset=utf-8", "Content-Disposition": "attachment; filename=re-storage-report.html"}`.
- [ ] TASK-01-04: Add an Excel-path variant or a `source=excel|json` switch so workbook users can also export (reuse `run_full_model`).
- [ ] TASK-01-05: Register `runReport` in [web/functions/main.py](../web/functions/main.py) with `@cross_origin()`.

**Files / Surfaces**
- `web/functions/handlers/run_report.py` (new), `web/functions/main.py`, `web/functions/handlers/project_payload.py` (reuse).

**Dependencies**
- None.

**Exit Criteria**
- [ ] Local `functions-framework --target runReport` returns valid HTML (opens in a browser with charts) for the Emivest fixture.
- [ ] New unit test in `tests/unit/test_web_handlers.py` asserts `Content-Type` is HTML and body contains a known KPI label.

**Phase Risks**
- **RISK-01-01:** `generate_report` may assume a `reference` dict for the comparison table — guard with an empty-dict default and a test.
- **RISK-01-02:** matplotlib in a server context needs the `Agg` backend; confirm `html_report.py` sets it (it builds figures headless) or set `matplotlib.use("Agg")` in the handler.

### PHASE-02 - Excel workbook endpoint
**Goal**
A handler produces the branded `.xlsx` assessment workbook and streams it back.

**Tasks**
- [ ] TASK-02-01: Create `web/functions/handlers/export_workbook.py`. Reuse the orchestration in [scripts/generate_dppa_assessment.py](../scripts/generate_dppa_assessment.py) (`generate_assessment`) or call `create_workbook` + `write_cover_sheet`/`write_assumptions_sheet`/`write_comparison_sheet`/`write_sensitivity_sheet`/`write_assessment_sheet` directly.
- [ ] TASK-02-02: Save to a `/tmp` path via `save_workbook`, read bytes, return with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and an attachment filename; `os.unlink` the temp file in a `finally`.
- [ ] TASK-02-03: Decide workbook scope — minimum viable is cover + assumptions + assessment for a single run; comparison/sensitivity sheets require running `run_all_scenarios`/sensitivity (heavier). Default to single-run sheets; gate comparison sheets behind a `?full=true` flag.
- [ ] TASK-02-04: Register `exportWorkbook` in `main.py`.

**Files / Surfaces**
- `web/functions/handlers/export_workbook.py` (new), `web/functions/main.py`, `src/re_storage/reporting/excel_writer.py` (reuse), `scripts/generate_dppa_assessment.py` (reference for assembly).

**Dependencies**
- PHASE-01 (shares the re-run-from-payload pattern).

**Exit Criteria**
- [ ] Local run downloads an `.xlsx` that opens in Excel/LibreOffice with populated cover + assessment sheets.
- [ ] Unit test asserts the response is a non-empty xlsx (zip magic bytes `PK`).

**Phase Risks**
- **RISK-02-01:** `generate_assessment` may expect on-disk fixtures or a scenario sweep — trace its inputs and feed it the in-request results instead of file paths; budget time for this adaptation.
- **RISK-02-02:** Workbook with full comparison sheets multiplies runtime (4 PPA options × topologies). Keep the default single-run to stay within the 300s timeout.

### PHASE-03 - Frontend download buttons + input resend
**Goal**
Dashboard buttons trigger the export endpoints, resending the inputs from the most recent run.

**Tasks**
- [ ] TASK-03-01: Persist the last submitted `FormData` (form fields + hourly CSV) in `useModelRun` so exports can resend it without re-upload.
- [ ] TASK-03-02: Add `downloadReport(formData)` and `downloadWorkbook(formData)` to [web/frontend/src/api/client.ts](../web/frontend/src/api/client.ts) using `fetch` → `blob()` → `URL.createObjectURL` → anchor download.
- [ ] TASK-03-03: Add "Download HTML Report" and "Download Excel Workbook" buttons beside the existing JSON button in [ResultsDashboard.tsx](../web/frontend/src/components/results/ResultsDashboard.tsx), with loading state (exports re-run the model).
- [ ] TASK-03-04: For the Excel-upload path, store the uploaded workbook and POST it to the `source=excel` export variant.
- [ ] TASK-03-05: Add the two rewrites (`/api/run-report`, `/api/export-workbook`) to [firebase.json](../firebase.json).

**Files / Surfaces**
- `web/frontend/src/hooks/useModelRun.ts`, `web/frontend/src/api/client.ts`, `ResultsDashboard.tsx`, `firebase.json`.

**Dependencies**
- PHASE-01, PHASE-02.

**Exit Criteria**
- [ ] `npm run build` succeeds; manual download of both artifacts works end-to-end via the Vite proxy.
- [ ] Buttons show a spinner and disable while the export request is in flight.

**Phase Risks**
- **RISK-03-01:** Re-uploading the 8,760-row CSV on every export adds latency — acceptable for MVP; note as a candidate for GAP-04 caching later.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_web_handlers.py -v` — report returns HTML, workbook returns xlsx magic bytes.
- **MANUAL-001:** Local end-to-end: run form → download report (renders with charts) and workbook (opens with sheets).
- **OBS-001:** Log export runtime; confirm < 300s timeout headroom even with `?full=true`.

## Risks and Alternatives
- **RISK-001:** Double compute (run + export re-run) — accepted trade-off to keep GAP-02 storage-free; revisit with Firestore/Storage caching in GAP-04.
- **ALT-001:** Cache `_hourly_df`/`_lifetime_df` to Firebase Storage keyed by run id and export from cache. Rejected for now: couples GAP-02 to GAP-04 infrastructure not yet provisioned.

## Grill Me
1. **Q-001:** Should the Excel workbook export default to a single-run summary, or the full multi-scenario/sensitivity workbook?
   - **Recommended default:** Single-run (cover + assumptions + assessment); offer full via `?full=true`.
   - **Why this matters:** Full workbook runs 4 PPA options × topologies (+sensitivity), multiplying runtime and timeout risk.
   - **If answered differently:** Make the export call `run_all_scenarios`/sensitivity and raise the function memory/timeout; add progress UX.

## Suggested Next Step
Answer Q-001, then build PHASE-01 (HTML report) first since it has no scenario-sweep complexity and validates the re-run-from-payload pattern reused by PHASE-02.

---
title: "Web GAP-01: Expose Go/No-Go Assessment Verdicts"
date: "2026-06-13"
status: "draft"
request: "Create a multi-phase plan for GAP-01 (assessment verdicts) from reports/2026-06-13-reopt-web-interface-gap-analysis.md"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-06-13-reopt-web-interface-gap-analysis.md"
---

# Plan: Web GAP-01: Expose Go/No-Go Assessment Verdicts

## Objective
Surface the model's existing Go/No-Go recommendation in the web UI. `assess_project()` already produces a `GO / CAUTION / NO-GO` verdict with per-metric PASS/MARGINAL/FAIL status, but the four Cloud Function handlers never call it and the dashboard shows only raw numbers. This is the single highest value-per-effort REopt-parity gap: it turns a number dump into a recommendation.

## Context Snapshot
- **Current state:** [src/re_storage/reporting/assessment.py](../src/re_storage/reporting/assessment.py) is mature (Sprint 3, 10 tests). [web/functions/utils/serialise.py](../web/functions/utils/serialise.py) returns `kpis/lifetime/annual/cashflow/dscr_series/dispatch_sample` — no verdict. [web/frontend/src/components/results/ResultsDashboard.tsx](../web/frontend/src/components/results/ResultsDashboard.tsx) renders KPI cards + charts with no go/no-go framing.
- **Desired state:** Every run response (`/api/run-json`, `/api/run-excel`) includes a `verdict` block; the dashboard shows a prominent GO/CAUTION/NO-GO banner plus per-metric chips (Equity IRR, Min DSCR, NPV, Simple Payback) and the `details` explanations. Threshold overrides are optionally settable from the form.
- **Key repo surfaces:** `assess_project`, `AssessmentThresholds`, `AssessmentVerdict` (assessment.py); `serialise_results` (serialise.py); `handle_run_json`/`handle_run_excel` (web/functions/handlers); `ResultsDashboard.tsx`, `model.ts`, `KpiGrid.tsx`/`KpiCard.tsx`.
- **Out of scope:** Report/workbook export (GAP-02), tariff-mode (GAP-03), persistence/deploy (GAP-04). Verdicts for the scenario-comparison and sensitivity sub-views are a stretch task, not core.

## Research Inputs
- [reports/2026-06-13-reopt-web-interface-gap-analysis.md](../reports/2026-06-13-reopt-web-interface-gap-analysis.md) — GAP-01 (HIGH). Confirms `assess_project` is unexposed and recommends a verdict banner reusing KpiGrid/KpiCard patterns; sequenced as the Sprint 1 value driver.

## Assumptions and Constraints
- **ASM-001:** `simple_payback_years` is present in the KPI dict (confirmed: [pipeline.py:926](../src/re_storage/pipeline.py)), so `assess_project` has every input it needs with no model change.
- **CON-001:** `AssessmentVerdict` is a dataclass; it must be converted to a plain dict before `jsonify` in the handlers.
- **DEC-001:** Verdict is computed server-side (the thresholds and banding logic already live in Python); the frontend only renders.
- **ASM-002:** Default thresholds (`equity_irr_hurdle=0.12`, `dscr_covenant=1.2`, `max_payback_years=15`, `npv_floor_usd=0`) are acceptable defaults; user overrides are optional (PHASE-03).

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Compute + serialise verdict in handlers | None | `verdict` field in run responses; handler tests |
| PHASE-02 | Render verdict banner + metric chips in dashboard | PHASE-01 | `VerdictBanner.tsx`, `model.ts` types, wired dashboard |
| PHASE-03 | Optional threshold overrides from the form | PHASE-01 | Threshold inputs → `AssessmentThresholds` |

## Detailed Phases

### PHASE-01 - Backend: compute and serialise the verdict
**Goal**
Both run handlers return a JSON-safe `verdict` object derived from `assess_project()`.

**Tasks**
- [ ] TASK-01-01: Add a `serialise_verdict(verdict: AssessmentVerdict) -> dict` helper (or extend `serialise_results`) in [web/functions/utils/serialise.py](../web/functions/utils/serialise.py) producing `{overall, equity_irr_status, dscr_status, npv_status, payback_status, details}`.
- [ ] TASK-01-02: In `serialise_results`, after building `kpis`, call `assess_project(kpis)` and add `"verdict"` to the returned payload. Accept an optional `thresholds: AssessmentThresholds | None` argument for PHASE-03.
- [ ] TASK-01-03: Confirm `handle_run_json` ([run_json.py:54](../web/functions/handlers/run_json.py)) and `handle_run_excel` flow through `serialise_results` so both inherit the verdict automatically.
- [ ] TASK-01-04: Guard against missing payback (NaN) — `assess_project` already handles NaN → FAIL; add a unit assertion that a run with `simple_payback_years=None` yields `payback_status="FAIL"` not a crash.

**Files / Surfaces**
- `web/functions/utils/serialise.py` — add verdict computation + serialisation.
- `web/functions/handlers/run_json.py`, `web/functions/handlers/run_excel.py` — verify they return `serialise_results(...)` unchanged.
- `tests/unit/test_web_handlers.py` — extend with verdict assertions.

**Dependencies**
- None.

**Exit Criteria**
- [ ] `pytest tests/unit/test_web_handlers.py -v` passes with ≥2 new tests asserting `verdict.overall` and one per-metric status.
- [ ] A local `functions-framework` run of `/api/run-json` against the Emivest fixture returns a populated `verdict`.

**Phase Risks**
- **RISK-01-01:** `AssessmentVerdict.details` strings embed `%`/`$` — safe for JSON, but assert they round-trip through `jsonify` without escaping issues.

### PHASE-02 - Frontend: verdict banner and metric chips
**Goal**
The dashboard leads with a color-coded verdict and per-metric pass/fail chips.

**Tasks**
- [ ] TASK-02-01: Extend [web/frontend/src/types/model.ts](../web/frontend/src/types/model.ts) with a `Verdict` interface and add `verdict: Verdict` to `ModelResponse`.
- [ ] TASK-02-02: Create `web/frontend/src/components/results/VerdictBanner.tsx` — large GO/CAUTION/NO-GO pill (green/amber/red) plus four status chips and the `details` list (collapsible).
- [ ] TASK-02-03: Render `VerdictBanner` at the top of [ResultsDashboard.tsx](../web/frontend/src/components/results/ResultsDashboard.tsx), above `KpiGrid`.
- [ ] TASK-02-04: Add verdict color tokens to [web/frontend/src/styles.css](../web/frontend/src/styles.css) consistent with existing `status-pill` styling.

**Files / Surfaces**
- `web/frontend/src/types/model.ts`, `web/frontend/src/components/results/VerdictBanner.tsx`, `ResultsDashboard.tsx`, `styles.css`.

**Dependencies**
- PHASE-01 (response must carry `verdict`).

**Exit Criteria**
- [ ] `npm run build` in `web/frontend` succeeds with no type errors.
- [ ] Manual run shows the banner switching color across a GO and a NO-GO fixture.

**Phase Risks**
- **RISK-02-01:** Older cached API responses lack `verdict`; render defensively (`verdict?` optional) so the dashboard never crashes on a missing field.

### PHASE-03 - Optional threshold overrides
**Goal**
Let users tune hurdle rates and see the verdict recompute.

**Tasks**
- [ ] TASK-03-01: Add `equity_irr_hurdle`, `dscr_covenant`, `max_payback_years`, `npv_floor_usd` inputs to [FinancialStep.tsx](../web/frontend/src/components/inputs/FinancialStep.tsx) + `formTypes.ts` defaults.
- [ ] TASK-03-02: Read these form fields in the handlers, build an `AssessmentThresholds`, and pass to `serialise_results(..., thresholds=...)`.
- [ ] TASK-03-03: Document that thresholds affect the verdict only, not the KPIs.

**Files / Surfaces**
- `web/frontend/src/components/inputs/FinancialStep.tsx`, `formTypes.ts`, `web/functions/handlers/run_json.py`, `run_excel.py`, `serialise.py`.

**Dependencies**
- PHASE-01.

**Exit Criteria**
- [ ] Changing `dscr_covenant` from 1.2 to 1.5 flips a borderline run from GO to CAUTION in a manual test.

**Phase Risks**
- **RISK-03-01:** Scope creep — keep these four fields collapsed under an "Advanced: assessment thresholds" section to avoid cluttering the form.

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_web_handlers.py -v` — verdict present and per-metric statuses correct for Emivest fixture.
- **MANUAL-001:** Local `functions-framework` + `npm run dev`; run the structured form and confirm banner + chips render and match the KPI values.
- **OBS-001:** None required (stateless compute).

## Risks and Alternatives
- **RISK-001:** Verdict semantics drift from the Excel workbook's own verdict logic — mitigate by reusing `assess_project` verbatim (same function the Excel assessment uses).
- **ALT-001:** Compute the verdict client-side in TypeScript. Rejected: duplicates tested Python banding logic and risks divergence.

## Grill Me
1. **Q-001:** Should threshold overrides (PHASE-03) ship in this plan, or stay defaults-only for Sprint 1?
   - **Recommended default:** Ship PHASE-01 + PHASE-02 now; defer PHASE-03 to a fast-follow.
   - **Why this matters:** Determines Sprint 1 scope and form complexity.
   - **If answered differently:** Include PHASE-03 fields in the same PR and extend handler tests for threshold parsing.

## Suggested Next Step
Answer Q-001, then implement PHASE-01 (TDD against `test_web_handlers.py`) before touching the frontend.

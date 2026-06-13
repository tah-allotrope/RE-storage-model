# Active Context — GAP-01: Expose Go/No-Go Assessment Verdicts (Web)

**Plan:** `plans/2026-06-13-web-assessment-verdicts-plan.md`
**Gap analysis:** `reports/2026-06-13-reopt-web-interface-gap-analysis.md`
**Scope decision (Q-001):** Sprint 1 = PHASE-01 + PHASE-02 with fixed default hurdles. PHASE-03 (user-adjustable thresholds) DEFERRED.
**Workflow:** TDD per phase → run tests → `/report` → git commit + push per phase → `/report final` at end.

## PHASE-01 — Backend: compute + serialise verdict ✅
- [x] `serialise_verdict(AssessmentVerdict) -> dict` helper in `web/functions/utils/serialise.py`
- [x] `serialise_results(results, thresholds=None)` computes `assess_project(kpis, thresholds)` and adds a `verdict` block to the payload
- [x] Both run paths inherit it: `handle_run_json` + `handle_run_excel` already route through `serialise_results`
- [x] Missing payback (None) degrades to FAIL, no crash (covered by test)
- [x] Threshold-override seam preserved for deferred PHASE-03
- [x] Tests: 5 new in `tests/unit/test_web_handlers.py` (GO, NO-GO, missing-payback, threshold override, run-excel carries verdict) — **16 passed**
- [x] ruff + black clean on changed files
- [ ] `/report` phase
- [ ] Commit + push

## PHASE-02 — Frontend: verdict banner + metric chips ✅
- [x] `Verdict` / `VerdictStatus` / `VerdictOverall` types + optional `verdict` on `ModelResponse` (`web/frontend/src/types/model.ts`)
- [x] `VerdictBanner.tsx` — GO/CAUTION/NO-GO headline + 4 status chips + collapsible details; renders `null` when `verdict` absent (defensive)
- [x] Rendered at top of `ResultsDashboard.tsx`, above `KpiGrid`
- [x] Verdict color tokens + chip styles in `styles.css` (light-theme green/amber/red)
- [x] `npm run build` clean — `tsc -b` no type errors (only pre-existing chunk-size warning)
- [x] `dist/` confirmed gitignored (regenerated at deploy) — no stale-build commit
- [ ] `/report` phase + commit + push

## PHASE-03 — Threshold overrides — DEFERRED (not in Sprint 1)

## Review / Results

**GAP-01 Sprint 1 complete — PHASE-01 + PHASE-02 shipped.**
- **PHASE-01:** `verdict` block in every run response via `serialise_results`; reuses `assess_project`; 5 TDD tests; web suite 11 → 16 passing.
- **PHASE-02:** `VerdictBanner` renders the GO/CAUTION/NO-GO recommendation + per-metric chips at the top of the dashboard; defensive against verdict-less responses; build green.
- **Verification:** backend `pytest tests/unit/test_web_handlers.py` 16 passed; frontend `npm run build` clean.
- **Deferred:** PHASE-03 user-adjustable thresholds (seam preserved via `serialise_results(..., thresholds=...)`).
- **Recommended manual check before deploy:** run form locally and confirm the banner switches color across a GO and a NO-GO fixture.

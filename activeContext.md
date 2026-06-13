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

## PHASE-02 — Frontend: verdict banner + metric chips
- [ ] `Verdict` interface + `verdict` on `ModelResponse` in `web/frontend/src/types/model.ts`
- [ ] `VerdictBanner.tsx` (GO/CAUTION/NO-GO pill + 4 status chips + collapsible details)
- [ ] Render at top of `ResultsDashboard.tsx`
- [ ] Verdict color tokens in `styles.css`
- [ ] `npm run build` clean
- [ ] `/report` phase + commit + push

## PHASE-03 — Threshold overrides — DEFERRED (not in Sprint 1)

## Review / Results
_To be filled after PHASE-02 + final report._

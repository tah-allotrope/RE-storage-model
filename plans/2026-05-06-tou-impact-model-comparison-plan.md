---
title: "Vietnam TOU Impact Model Comparison — File G vs File C"
date: "2026-05-06"
status: "draft"
request: "Compare logic and accuracy of two TOU Impact sheets (File G and File C) against Decision 963 regulatory source of truth, determine a winner, multi-phase."
plan_type: "multi-phase"
research_inputs:
  - "2026-04-25_vietnam-tou-rooftop-ppa.md"
---

# Plan: Vietnam TOU Impact Model Comparison — File G vs File C

## Objective

Systematically compare two independently-built TOU Impact analysis sheets within the same PV+BESS financial model to determine which is more accurate, complete, and aligned with Vietnam's Decision 963/QĐ-BCT tariff changes. The winner becomes the canonical impact analysis sheet for PPA pricing decisions and investor presentations.

## Context Snapshot

- **Current state:** Two `.xlsm` files (`-G` and `-C` variants) share an identical base model (14 sheets, same Assumptions, same base Equity IRR 8.9%). Each has a different `TOU Impact` sheet — G is compact (36 rows, revaluation-only approach), C is comprehensive (108 rows, 8-section analytical approach with base/worst cases and downstream KPI impacts). The `Cal.` sheet in both uses the **old** TOU windows (Peak = 09:30–11:30 + 17:00–20:00 Mon–Sat).
- **Password**: Saigon18 for sheets unprotect
- **Desired state:** A scored comparison report identifying which file's TOU Impact logic is correct on each dimension (regulatory alignment, solar impact math, BESS impact math, lifetime projections, financial KPI propagation), with a clear winner recommendation and a list of errors/gaps to fix in both.
- **Key repo surfaces:**
  - `20260501 PV BESS Model V02-No VBA -G.xlsm` → `TOU Impact` sheet (36 rows, array-formula-driven hourly revaluation)
  - `20260501 PV BESS Model V02-No VBA -C.xlsm` → `TOU Impact` sheet (108 rows, 8-section analytical breakdown)
  - `2026-04-25_vietnam-tou-rooftop-ppa.md` → Regulatory source of truth for TOU windows and tariff multipliers
  - Both files: `Cal.` sheet (8,760-row hourly dispatch model with TimePeriodFlag in column E), `Measures` sheet (TOU energy breakdowns), `Assumption` sheet (tariff rates, PPA discounts, BESS parameters), `Output` sheet (IRR, NPV), `Financial` sheet (20-year cashflows)
- **Out of scope:** Re-running the BESS dispatch engine, modifying the Cal. sheet formulas, building a new consolidated model, or updating the base model for Decision 963 compliance (that is downstream work after this comparison).

## Research Inputs

- `2026-04-25_vietnam-tou-rooftop-ppa.md` — Provides the regulatory ground truth: (a) new TOU windows (Peak 17:30–22:30 Mon–Sat only; Off-Peak 00:00–06:00 all days; Normal = remainder; Sundays peak-exempt), (b) tariff rates from Decision 14/2025 (Normal ~1,275, Peak ~2,182, Off-Peak ~859 VND/kWh at 22kV industrial), (c) directional impact: solar-only PPAs lose ~20–35% of offtaker-side value, BESS arbitrage revenue drops ~50% from 2-cycle→1-cycle, (d) key uncertainty: whether Decision 14 multipliers are remapped or revised for new windows.

## Assumptions and Constraints

- **ASM-001:** Both files use the same underlying hourly load/generation profiles from Cal. (8,760 hours, year 2024 timestamps). The base dispatch is identical; only the TOU Impact overlay differs.
- **ASM-002:** Tariff rates used are 22kV industrial: Normal = 1,275 VND/kWh, Peak = 2,182 VND/kWh, Off-Peak = 859 VND/kWh (confirmed in both files and consistent with DFDL's Decision 14/2025 summary).
- **ASM-003:** The old TOU windows in the Cal. sheet (col E) follow the pre-963 regime: Peak = 09:30–11:30 + 17:00–20:00 Mon–Sat; Off-Peak = 22:00–04:00; Sundays peak-exempt. Verified from Cal. data (10:00 = P, 12:00 = N, 17:00 = P on weekdays; all N on Sundays).
- **CON-001:** openpyxl reads computed values (data_only=True) but cannot execute Excel's array formulas. File G uses array formulas (SUMPRODUCT-style) for its revaluation — we can read the cached results but not re-derive them from scratch in Python without reimplementing the logic.
- **CON-002:** Neither file has actually modified the Cal. sheet dispatch for the new TOU. Both are "what-if" overlays on top of the old dispatch. This means BESS dispatch timing hasn't been re-optimized for the new peak window — a structural limitation of both approaches.
- **DEC-001:** FX rate = 26,000 VND/USD (confirmed in both files). PV discount from Assumption!Q33, BESS discount from Assumption!Q34.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Verify regulatory alignment of TOU windows | None | Window-mapping accuracy table for G and C |
| PHASE-02 | Validate solar revenue impact math | PHASE-01 | Cell-level arithmetic audit of solar impact in both files |
| PHASE-03 | Validate BESS revenue impact math | PHASE-01, PHASE-02 | BESS methodology comparison and error identification |
| PHASE-04 | Audit lifetime projections and financial KPI propagation | PHASE-02, PHASE-03 | 20-year projection validation, NPV/IRR check |
| PHASE-05 | Score, declare winner, produce comparison report | PHASE-01–04 | Final scored comparison report with recommendations |

## Detailed Phases

### PHASE-01 — Regulatory TOU Window Verification

**Goal**
Confirm that each file's definition of old and new TOU windows matches Decision 963/QĐ-BCT and the prior regime. This is the foundation — if either file maps the wrong hours to Peak/Normal/Off-Peak, all downstream numbers are wrong.

**Tasks**
- [ ] TASK-01-01: Extract the old and new TOU window definitions from File G's TOU Impact rows 23–26 (Tariff Bands Applied section) and File C's Section 1 (rows 3–10). Compare each against the research brief's confirmed windows: OLD Peak = Mon–Sat 09:30–11:30 + 17:00–20:00; NEW Peak = Mon–Sat 17:30–22:30; OLD Off-Peak = Mon–Sat 22:00–04:00; NEW Off-Peak = all days 00:00–06:00.
- [ ] TASK-01-02: Verify Cal. sheet column E (TimePeriodFlag) mapping against the OLD TOU windows by sampling 24 hours from a weekday and a Sunday. Confirm: hours 0–3 = O, 4–9 = N, 10–11 = P, 12–16 = N, 17–19 = P, 20–21 = N, 22–23 = O (weekday). Sunday: all hours N except 22–23 = O.
- [ ] TASK-01-03: Check whether File G's array formulas implement the NEW TOU mapping correctly — extract the formula text from cells B7 and C7 (old vs new solar revenue) and verify the hour-boundary logic. Similarly check File C's stated methodology in Section 7 (Cal. sheet E2 formula update guidance: "NEW Off = (m<360), NEW Peak = (wd<=6)*(m>=1050)*(m<1350)") for correctness.
- [ ] TASK-01-04: Flag any discrepancies: does either file handle the 30-minute boundaries correctly (17:30, 22:30 vs integer-hour model), Sunday exemptions, or the off-peak window shift?

**Files / Surfaces**
- `TOU Impact` sheet in both files — window definition rows
- `Cal.` sheet column E — TimePeriodFlag values
- `2026-04-25_vietnam-tou-rooftop-ppa.md` — regulatory source of truth

**Dependencies**
- None

**Exit Criteria**
- [ ] Table produced showing each file's old/new window mapping vs the regulatory truth
- [ ] Any hour-boundary or day-of-week errors identified and documented
- [ ] Clear pass/fail for each file on window accuracy

**Phase Risks**
- **RISK-01-01:** The Cal. sheet uses hourly resolution (integer hours) but Decision 963 specifies 17:30 and 22:30 boundaries. If neither file addresses the half-hour granularity, both may have a systematic error on the 17:00–18:00 and 22:00–23:00 transition hours. Mitigation: check how each file handles hours 17 and 22 specifically.

### PHASE-02 — Solar Revenue Impact Validation

**Goal**
Verify the solar (PV) revenue impact calculations in both files against first-principles arithmetic using Measures sheet data and tariff rates.

**Tasks**
- [ ] TASK-02-01: Independent calculation of solar impact. From Measures sheet: Direct PV at Peak = 639,534 kWh/yr, Direct PV at Normal = 2,486,099 kWh/yr. Under new TOU, ALL of the 639,534 kWh at old Peak rate reclassifies to Normal. Revenue loss = 639,534 × (2,182 − 1,275) / 26,000 = 639,534 × 907 / 26,000 = **$22,310.42/yr**. Compare this against G ($22,312) and C ($22,310).
- [ ] TASK-02-02: Trace File G's solar figure. G reports $175,586 (old) vs $153,274 (new) = -$22,313 delta. The old figure should equal: (2,486,099 × 1,275 + 639,534 × 2,182 + 0 × 859) / 26,000. Verify this arithmetic matches $175,586.
- [ ] TASK-02-03: Trace File C's solar figure. C reports the impact as $22,310 from the rate-differential method (639,534 × 907 / 26,000). Verify C's stated "PV-to-Load saving (OLD Peak → now Normal)" value of $53,672 (old) is consistent: 639,534 × 2,182 / 26,000 = $53,637. If $53,672 differs, check whether C is using a slightly different volume or rate.
- [ ] TASK-02-04: Check whether either file accounts for solar generation in the NEW off-peak window (00:00–06:00). G shows 0.16 MWh moving to off-peak; C appears to treat this as zero. Confirm the materiality (negligible: <0.01% of generation).
- [ ] TASK-02-05: Verify the "post-Apr 22" partial-year adjustment in File G ($15,881 impact) — this appears to scale the annual impact by the fraction of the year after April 22 (254/365 = 0.696). Check if this is methodologically correct and if File C includes this adjustment.

**Files / Surfaces**
- Both `TOU Impact` sheets — solar impact rows
- `Measures` sheet rows 43–45 — Direct PV Consumption Breakdown (Standard/Peak/Off-Peak kWh)
- `Assumption` sheet — tariff rates, PPA discount (Q33)

**Dependencies**
- PHASE-01 (window mapping must be validated before trusting volume splits)

**Exit Criteria**
- [ ] Independent solar impact figure computed and compared against both files
- [ ] Any rounding discrepancy explained (likely due to hourly-profile revaluation vs aggregate rate-differential)
- [ ] File C's intermediate figures ($53,672 PV at old Peak) verified or flagged
- [ ] Partial-year treatment compared between files

**Phase Risks**
- **RISK-02-01:** File G's array formulas re-scan 8,760 hourly rows which may capture minor generation during the 17:00–17:30 transition differently than File C's aggregate approach. This could explain the $2 rounding difference but is immaterial. Mitigation: document but don't over-investigate.

### PHASE-03 — BESS Revenue Impact Validation

**Goal**
This is the critical divergence between the two files. File G reports BESS impact as **+$101** (trivial revaluation), while File C reports **-$4,591** (base) to **-$11,046** (worst). Determine which treatment is logically correct given the regulatory change.

**Tasks**
- [ ] TASK-03-01: Understand File G's BESS methodology. G explicitly states it "revalues existing Cal. discharge/charge; does not rerun dispatch." This means G takes the existing BESS dispatch profile (when the BESS charges/discharges each hour), holds it fixed, and only changes which tariff rate applies to each hour. Result: old BESS peak discharge = 329 MWh, new BESS peak discharge = 332 MWh — a slight increase because some evening discharge hours (20:00–22:00) that were Normal under old TOU become Peak under new TOU. Net impact = +$101.
- [ ] TASK-03-02: Understand File C's BESS methodology. C takes a structural approach: the old peak window had 5 hours (2+3), and the morning block (09:30–11:30) comprised 40% of peak hours. C assumes 40% of all BESS peak discharge (329,037 × 40% = 131,615 kWh) was attributable to the morning peak block. Under new TOU: Base Case = this 131,615 kWh gets reclassified from Peak to Normal rate (loss of $4,591); Worst Case = this 131,615 kWh is eliminated entirely (BESS reserves SoC for evening, loss of $11,046).
- [ ] TASK-03-03: Determine which approach is more defensible. Key question: does the existing BESS dispatch actually discharge during morning peak hours (09:30–11:30)? Extract from Cal. sheet: sum of BESS discharge (col W) during hours flagged as Peak AND occurring between 09:00–12:00 vs hours flagged as Peak AND occurring between 17:00–20:00. This reveals whether the BESS was actually dispatching in the morning window or only in the evening.
- [ ] TASK-03-04: Cross-check with BESS strategy settings. From Assumption: Strategy mode = 2 (PeakShaving), End Of Day Discharge start hour = 18:00, Demand Reduction Target = 20%. The "End Of Day Discharge" at 18:00 suggests the BESS was primarily dispatching in the evening peak (17:00–20:00), NOT the morning peak. If the BESS doesn't actually discharge in the morning, then File C's 40% attribution is wrong — and File G's revaluation approach is more accurate for current-dispatch economics.
- [ ] TASK-03-05: Evaluate the theoretical arbitrage sensitivity. File G shows a separate "2-cycle→1-cycle" sensitivity: old gross spread $59,966 → new $29,983 (-50%). File C embeds the cycle-count impact implicitly in its base/worst cases. Verify G's arbitrage calculation: max theoretical = BESS capacity × 2 cycles/day × 365 days × (peak rate − off-peak rate) / FX. Compare against G's $59,966 figure.
- [ ] TASK-03-06: Assess File C's "BESS discharge — afternoon/evening peak" figure of $19,661 for 197,422 kWh. Verify: 197,422 × 2,182 / 26,000 = $16,564. If C reports $19,661, check if this includes a capacity-payment component or uses a different rate.

**Files / Surfaces**
- Both `TOU Impact` sheets — BESS impact rows
- `Cal.` sheet columns E (TimePeriodFlag), V (DischargePower_kW), W (DischargeEnergy_kWh), AM (Hours) — to verify actual dispatch timing
- `Measures` sheet rows 53–55 — BESS to Load Breakdown (Standard/Peak/Off-Peak kWh)
- `Assumption` sheet rows 35–60 — BESS strategy parameters

**Dependencies**
- PHASE-01 (window mapping), PHASE-02 (solar methodology established as baseline for comparison)

**Exit Criteria**
- [ ] Actual BESS morning-peak vs evening-peak discharge volumes extracted from Cal. hourly data
- [ ] Determination of whether File G's revaluation or File C's 40% attribution is correct
- [ ] File C's intermediate BESS figures verified or flagged as errors
- [ ] Arbitrage sensitivity in File G independently verified
- [ ] Clear winner on BESS methodology accuracy

**Phase Risks**
- **RISK-03-01:** Both approaches may be partially wrong. File G ignores the behavioral question (would the BESS dispatch differently under new TOU?), while File C assumes a 40% morning split that may not match actual dispatch. The truth may require re-running the dispatch model. Mitigation: flag this as a limitation of both overlay approaches and recommend re-dispatch as a follow-up.
- **RISK-03-02:** openpyxl may not read array formula results correctly in all cases. Mitigation: cross-check G's cached values against manual calculation.

### PHASE-04 — Lifetime Projections and Financial KPI Propagation

**Goal**
Validate the 20-year and NPV projections that only File C provides, and assess whether File G's omission of downstream KPIs is a material gap.

**Tasks**
- [ ] TASK-04-01: Verify File C's 20-year escalation. C applies 5% p.a. escalation to Y1 impacts. Year 2 solar impact should be $22,310 × 1.05 = $23,426. Year 20 = $22,310 × 1.05^19 = $56,376. Check C's stated Y2 ($23,426) and Y20 ($56,376) match.
- [ ] TASK-04-02: Verify File C's 20-year nominal total. Sum of geometric series: $22,310 × (1.05^20 − 1) / (1.05 − 1) = $22,310 × 33.066 = $737,704 (solar). C reports $737,704. Verify BESS base total: $4,591 × 33.066 = $151,806. C reports $151,806.
- [ ] TASK-04-03: Verify File C's NPV calculation. C uses a 9.3% discount rate (stated as "project IRR" — check if this is appropriate as a discount rate). Growing annuity NPV = $22,310 × [1 − (1.05/1.093)^20] / (0.093 − 0.05) = $22,310 × 12.838 = $286,337. C reports $286,342 (close, rounding differences acceptable).
- [ ] TASK-04-04: Evaluate File C's financial KPI impact estimates (Section 8). C claims Equity IRR drops from 8.91% to 5.67% (base) / 4.84% (worst). These are stated as estimates, not recalculated from the Financial sheet. Check whether C explains its methodology for the IRR estimate or whether these are approximate.
- [ ] TASK-04-05: Assess File G's gap. G provides only Y1 revenue impact and a partial-year adjustment. No lifetime projection, no NPV, no IRR impact. Determine whether this is a material omission for PPA decision-making (it is — investors need lifetime and NPV impacts).

**Files / Surfaces**
- File C `TOU Impact` Sections 5–8
- File G `TOU Impact` (confirm no lifetime rows exist)
- Both files: `Output` sheet (baseline IRR = 8.9%), `Financial` sheet (20-year cashflows)
- `Assumption` sheet — price escalation rate, project lifetime, target IRR

**Dependencies**
- PHASE-02 and PHASE-03 (Y1 impact figures must be validated before projecting them over 20 years)

**Exit Criteria**
- [ ] File C's 20-year escalation and NPV independently verified
- [ ] File C's IRR impact methodology assessed (exact vs approximate)
- [ ] File G's omission of lifetime/NPV analysis flagged and materiality assessed
- [ ] Clear winner on completeness of financial analysis

**Phase Risks**
- **RISK-04-01:** File C uses project IRR (9.3%) as the NPV discount rate, but the standard approach for equity NPV is to discount at cost of equity or target IRR (10% per Assumption). If the wrong discount rate is used, NPV figures are off. Mitigation: recalculate NPV at both 9.3% and 10% and note the difference.

### PHASE-05 — Scoring, Winner Declaration, and Comparison Report

**Goal**
Produce a structured comparison report scoring both files across all dimensions, declare a winner, and list specific corrections needed for each file.

**Tasks**
- [ ] TASK-05-01: Build a scoring matrix with dimensions: (1) Regulatory TOU window accuracy, (2) Solar impact methodology and arithmetic, (3) BESS impact methodology and arithmetic, (4) Scenario analysis (base/worst), (5) Lifetime projection, (6) NPV/IRR propagation, (7) Model update guidance, (8) Presentation clarity and auditability, (9) Half-hour boundary handling, (10) Partial-year adjustment.
- [ ] TASK-05-02: Score each file on each dimension (0 = missing/wrong, 1 = partially correct, 2 = fully correct). Compute weighted totals (weight BESS methodology and regulatory accuracy highest).
- [ ] TASK-05-03: Write an error list for each file — specific cells or claims that are incorrect, with the correct value and reasoning.
- [ ] TASK-05-04: Write a "best of both" recommendation — what the ideal TOU Impact sheet would look like, combining the strengths of G (hourly-profile array formulas, quality checks) and C (scenario analysis, lifetime projections, KPI impacts, model update guidance).
- [ ] TASK-05-05: Produce the final comparison report as a markdown file in the `plans/` directory.

**Files / Surfaces**
- All findings from PHASE-01 through PHASE-04
- Output: `plans/tou-impact-comparison-report.md`

**Dependencies**
- PHASE-01 through PHASE-04 (all validation phases must be complete)

**Exit Criteria**
- [ ] Scoring matrix complete with per-dimension scores for both files
- [ ] Winner declared with clear justification
- [ ] Error list produced for both files
- [ ] "Best of both" recommendation written
- [ ] Comparison report saved to `plans/tou-impact-comparison-report.md`

**Phase Risks**
- **RISK-05-01:** If both files have significant errors, the "winner" may still need substantial corrections. Mitigation: frame the winner as "closer to correct" rather than "production-ready" and include required fixes.

## Verification Strategy

- **TEST-001:** Independent solar impact arithmetic: 639,534 × (2,182 − 1,275) / 26,000 = $22,310.42. Both files should match within $5.
- **TEST-002:** Extract actual BESS discharge-by-hour from Cal. sheet using Python — sum DischargeEnergy_kWh for hours where TimePeriodFlag = 'P' AND hour ∈ {10, 11} (morning peak proxy) vs hour ∈ {17, 18, 19} (evening peak). This determines whether File C's 40% morning attribution is accurate.
- **TEST-003:** Verify File C's 20-year geometric series: sum = Y1 × (1.05^20 − 1) / 0.05. Solar total should be ~$737,700. BESS base total should be ~$151,800.
- **TEST-004:** Verify File C's NPV using growing annuity formula at 9.3% and at 10% discount rate. Compare against C's stated figures.
- **MANUAL-001:** Open both files in Excel and trace File G's array formulas to verify they reference the correct Cal. columns and implement the new TOU hour-boundary logic.
- **MANUAL-002:** Cross-check File C's Section 7 "Required Model Updates" against the actual Cal. sheet formula structure to confirm the suggested Cal.!E2 update is syntactically and logically correct.

## Risks and Alternatives

- **RISK-001:** Neither file re-runs the BESS dispatch optimizer for the new TOU windows. Both are overlay analyses. The "true" BESS impact requires updating Cal.!E (TimePeriodFlag) and re-solving the dispatch, which changes charge/discharge timing. Both files are approximations. Mitigation: acknowledge this limitation in the report and recommend a Phase 6 (out of scope here) for re-dispatch modeling.
- **RISK-002:** The model uses hourly timesteps but Decision 963 specifies 17:30 and 22:30 boundaries. The hours 17:00–18:00 and 22:00–23:00 are partially Peak/partially Normal under the new regime. Neither file can handle sub-hourly resolution without model restructuring. Mitigation: quantify the error introduced by integer-hour approximation (likely <1% of revenue impact).
- **ALT-001:** Instead of comparing the two overlay sheets, we could rebuild the Cal. sheet with new TOU windows and re-run the full model. This was not chosen because: (a) the user wants to compare the two analysts' approaches, not bypass them; (b) the VBA-free model may not have a working dispatch solver; (c) re-dispatch is Phase 6 work.

## Grill Me

1. **Q-001:** Should the comparison report evaluate both files against the "current dispatch only" (no behavioral change) or should it also judge whether each file correctly anticipates how the BESS *would* be dispatched differently under the new TOU? (user agree with default)
   - **Recommended default:** Evaluate against current dispatch (what the model says) AND flag behavioral-change awareness as a bonus criterion. Don't penalize for not re-dispatching, but credit files that acknowledge the limitation.
   - **Why this matters:** File G explicitly holds dispatch fixed; File C assumes 40% morning reallocation (a quasi-behavioral change). The "right" answer depends on whether this is a quick-impact assessment or a full re-optimization study.
   - **If answered differently:** If pure re-optimization accuracy is the standard, both files fail and the comparison becomes "which is less wrong" rather than "which is right."

2. **Q-002:** What discount rate should be used for the NPV verification — the project IRR (9.3% as File C uses), the target equity IRR (10% from Assumption), or the weighted average cost of capital? (user agree with default)
   - **Recommended default:** Verify at both 9.3% and 10%; flag File C's choice as non-standard but defensible.
   - **Why this matters:** NPV figures change by ~8% between 9.3% and 10% discount rates. If the report is going to investors, using the wrong rate undermines credibility.
   - **If answered differently:** If a specific hurdle rate is mandated by the fund, use that instead and note it in the report.

3. **Q-003:** Should the partial-year adjustment (Apr 22 → Dec 31, ~254 days) be treated as essential or optional for the comparison? File G includes it; File C appears to report full-year impacts only. (user agree with default)
   - **Recommended default:** Credit File G for including it but don't heavily penalize File C — the full-year figure is what matters for go-forward PPA structuring, while partial-year matters only for 2026 P&L forecasting.
   - **Why this matters:** For near-term cash management vs long-term PPA pricing, the relevant metric differs.
   - **If answered differently:** If 2026 budget impact is the primary use case, partial-year becomes a mandatory criterion and File G gains significant points.

## Suggested Next Step

Eexecute PHASE-01 and PHASE-02 in parallel (both are independent data extraction tasks). PHASE-03 is the critical phase that will likely determine the winner — it requires PHASE-01 results and a Python extraction of BESS discharge timing from the Cal. sheet.

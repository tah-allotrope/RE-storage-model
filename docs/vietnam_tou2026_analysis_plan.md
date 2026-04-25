# Vietnam TOU Tariff 2026 — Revenue Impact Analysis Plan

**Objective:** Quantify the revenue impact of Vietnam's new TOU tariff (effective April 22, 2026) across all
modelled cases in this repo (`Emivest` and `Ecoplexus 40MW`), covering both C&I Solar and BESS revenue streams.

---

## Tariff Change Summary

| Attribute | Old (≤ April 21, 2026) | New (≥ April 22, 2026) |
|---|---|---|
| **Off-Peak (Mon–Sat)** | 22:00–04:00 | 00:00–06:00 |
| **Normal (Mon–Sat)** | 04:00–09:30, 11:30–17:00, 20:00–22:00 | 06:00–17:30, 22:30–24:00 |
| **Peak (Mon–Sat)** | 09:30–11:30 **and** 17:00–20:00 (2 blocks, 5 hrs) | 17:30–22:30 (1 block, 5 hrs) |
| **Sunday** | Normal: 04:00–22:00 / Off-Peak: 22:00–04:00 | Normal: 06:00–24:00 / Off-Peak: 00:00–06:00 |
| **BESS cycles/day** | 2 (morning off-peak charge → morning peak; afternoon off-peak charge → evening peak) | 1 (midnight off-peak charge → evening peak) |

**Key revenue implications:**
- Solar generation (06:00–17:30) now falls **entirely within Normal hours** — the old morning peak window
  (09:30–11:30) no longer overlaps with solar output.
- BESS peak discharge window shifts later and consolidates: 17:30–22:30 instead of two windows.
- BESS is limited to **1 charge-discharge cycle per day**, cutting potential cycling revenue roughly in half.
- Off-peak charging window shifts 2 hours later (midnight start vs. 22:00 start), reducing grid interaction
  during late evening Normal hours.

---

## Phase 1 — Tariff Codification

**Goal:** Formally encode the new schedule in all input formats used by the model, without touching any case results.

### 1.1 Define the new `TimePeriod` hour mapping

- Locate `load_tariff_schedule()` in `src/re_storage/inputs/loaders.py:600+` and the equivalent in
  `json_loader.py:200+`.
- Create a **side-by-side mapping table** (hours 0–23) for old vs. new classification, for both weekday
  and Sunday.
- Document the mapping in a new file `docs/tariff_schedules/vietnam_tou_2026.md` for auditability.

### 1.2 Create new config variants for each input format

| Case | Input Format | Action |
|---|---|---|
| Emivest | JSON | Copy `Emivest.json` → `Emivest_TOU2026.json`; update `tariff_schedule` hour array |
| Ecoplexus 40MW | Excel | Duplicate `Tariff Schedule` sheet → `Tariff Schedule 2026`; remap hours |

### 1.3 Add a `tariff_version` field to assumption schemas

- Add an optional `tariff_version: str` field (e.g. `"2024"` vs `"2026"`) to the JSON schema and the
  `Assumptions` Pydantic model.
- This lets scenario runners tag outputs clearly and avoids silent config drift.

---

## Phase 2 — BESS Dispatch Logic Audit

**Goal:** Confirm whether the battery dispatch engine correctly handles the new 1-cycle-per-day constraint
and the shifted peak window before running any comparisons.

### 2.1 Review current dispatch strategy

- Read `src/re_storage/physics/` battery dispatch module.
- Identify where charge/discharge decisions are made relative to `TimePeriod`.
- Check if the model currently hard-codes 2-cycle behaviour (e.g. two separate charge windows per day)
  or derives it dynamically from the tariff schedule.

### 2.2 Assess cycle-count constraint

- The new regulation explicitly permits **only 1 charge-discharge cycle per day**.
- Determine if the dispatcher already respects this naturally (because there is now only 1 off-peak window
  before 1 peak window), or if an explicit daily cycle cap needs to be enforced.
- If needed, add a `max_cycles_per_day: int` parameter to `BatteryParams` and enforce it in the dispatch loop.

### 2.3 Validate dispatch with unit test

- Write a focused pytest in `tests/unit/` that runs the battery dispatcher against 24 hours of synthetic
  load using the new schedule and asserts:
  - Charge only occurs in 00:00–06:00.
  - Discharge only occurs in 17:30–22:30.
  - Total cycle count ≤ 1.

---

## Phase 3 — Baseline Snapshot (Old Tariff)

**Goal:** Capture a clean, reproducible baseline of all KPIs under the current tariff before any changes,
so the delta is unambiguous.

### 3.1 Run full model for each case on `main` (old tariff)

```bash
# Emivest
python -m re_storage.pipeline \
  --input tests/data/projects/emivest/Emivest.json \
  --output results/baseline/emivest_tou2024.json

# Ecoplexus
python -m re_storage.pipeline \
  --input "tests/data/projects/AUDIT 20251201 40MW Solar & BESS Ecoplexus.xlsx" \
  --output results/baseline/ecoplexus_tou2024.json
```

### 3.2 Record KPIs to freeze as baseline

Capture the following for **Year 1** and **lifetime (25-year)**:

| KPI | Unit |
|---|---|
| Solar generation | MWh |
| Energy dispatched during Peak hours | MWh |
| Energy dispatched during Normal hours | MWh |
| BESS cycles per day (average) | cycles |
| Annual revenue (all PPA modes) | USD |
| Grid savings | USD |
| EBITDA | USD |
| Project IRR | % |
| Equity IRR | % |
| NPV | USD |
| Min DSCR | x |

### 3.3 Commit baseline results

- Save outputs under `results/baseline/` and commit to branch `claude/vietnam-tou-tariff-analysis-uKc41`.

---

## Phase 4 — New Tariff Scenario Runs

**Goal:** Run identical cases with the 2026 TOU schedule and capture the same KPI set.

### 4.1 Emivest — all PPA modes

Run all four settlement options against `Emivest_TOU2026.json`:

- `ppa_option=1` Bundled Discount
- `ppa_option=2` Separate PV + BESS Discount
- `ppa_option=3` DPPA with CfD
- `ppa_option=4` Fixed PPA

Save outputs to `results/new_tariff/emivest_tou2026_option{1..4}.json`.

### 4.2 Ecoplexus 40MW

- Run with the updated `Tariff Schedule 2026` sheet active.
- Save to `results/new_tariff/ecoplexus_tou2026.json`.

### 4.3 Sensitivity: BESS cycle cap on/off

Run a paired sub-scenario for each case:

- **Scenario A:** New tariff schedule only (dispatch optimizer free).
- **Scenario B:** New tariff schedule + explicit `max_cycles_per_day=1` constraint.

This isolates how much of the revenue change is due to the shifted peak window vs. the cycle restriction.

---

## Phase 5 — Delta Analysis

**Goal:** Produce a clear, quantified comparison of revenue and IRR impact.

### 5.1 Build comparison table

For each case and PPA mode, compute:

```
Δ Revenue (USD)  = New − Old
Δ Revenue (%)    = (New − Old) / Old × 100
Δ IRR (pp)       = New IRR − Old IRR
Δ NPV (USD)      = New − Old
```

### 5.2 Decompose the revenue delta

Break the total revenue change into attributable drivers:

| Driver | Mechanism |
|---|---|
| **Loss of morning peak uplift** | Solar kWh that used to earn Peak rate (09:30–11:30) now earns Normal rate |
| **BESS cycle reduction** | Fewer kWh dispatched at Peak rate due to 1-cycle cap |
| **Shifted peak window (timing)** | BESS now discharges 17:30–22:30 instead of 17:00–20:00; net duration same but coincidence with load changes |
| **Off-peak rate changes** | Off-peak window shift (22:00→04:00 to 00:00→06:00) changes grid charge savings |

### 5.3 Produce hourly average-day visualisation

- Plot average weekday energy dispatch under old vs. new tariff (stacked area: solar direct, BESS discharge,
  grid import).
- Overlay the period bands (colour-coded: green=off-peak, yellow=normal, red=peak).
- Save as `results/figures/avg_day_dispatch_comparison.png`.

---

## Phase 6 — Reporting

**Goal:** Deliver a concise, decision-ready summary document.

### 6.1 Write impact summary in `results/vietnam_tou2026_impact_report.md`

Structure:
1. Executive summary (3–5 bullet points with headline numbers)
2. Tariff change description (the table from this plan's header)
3. Per-case results table (Phase 5.1 output)
4. Revenue decomposition by driver (Phase 5.2)
5. Average-day dispatch chart (Phase 5.3)
6. Recommended mitigations (e.g. adjust PPA discount rates, optimise BESS dispatch for evening-only peak)

### 6.2 Update regression reference files

- If the new tariff becomes the production assumption, update `tests/data/references/emivest.json` and the
  Ecoplexus reference JSON with the new KPIs.
- Gate behind a `--tariff-version` flag in the regression test runner so both old and new references can
  coexist during the transition period.

### 6.3 Commit and push final outputs

```bash
git add results/ tests/data/references/ src/ docs/
git commit -m "feat: Vietnam TOU 2026 tariff impact analysis"
git push -u origin claude/vietnam-tou-tariff-analysis-uKc41
```

---

## Dependency Map

```
Phase 1 (Codify tariff)
    └─► Phase 2 (Audit dispatch logic)
            └─► Phase 3 (Baseline snapshot)   ──┐
            └─► Phase 4 (New tariff runs)      ──┤
                                                  ▼
                                          Phase 5 (Delta analysis)
                                                  │
                                                  ▼
                                          Phase 6 (Reporting)
```

---

## Estimated Effort

| Phase | Effort | Notes |
|---|---|---|
| 1 — Codify | 2–3 hrs | Config edits + schema update |
| 2 — Dispatch audit | 3–4 hrs | Code read + possible fix + unit test |
| 3 — Baseline | 1 hr | Script run + commit |
| 4 — New tariff runs | 1–2 hrs | Config swap + script run |
| 5 — Delta analysis | 3–4 hrs | Python analysis script + chart |
| 6 — Reporting | 2 hrs | Markdown write-up + reference updates |
| **Total** | **~12–16 hrs** | |

---

> The most implementation-risk sits in **Phase 2** — whether the battery dispatch engine naturally handles
> the single-cycle regime or requires a code change. That should be validated before any scenario runs to
> avoid comparing apples to oranges.

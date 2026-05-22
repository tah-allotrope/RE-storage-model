# Research Brief: Vietnam TOU Tariff Change Impact on RE-Storage-Model

**Date:** 2026-05-07
**Modes run:** domain, codebase
**Depth:** standard
**Invocation context:** Assess the implications of recent electricity time-of-use (TOU) tariff changes in Vietnam on this repo and the Excel file being worked on in parallel.

---

## Synthesis

The repo already encodes the most impactful recent change — **Decision 963/QĐ-BCT (22 Apr 2026)** — which restructures Vietnam's TOU windows from a split morning+evening peak to a single evening block (17:30–22:30). The codebase's hour mapping in `docs/vietnam_tou_2026.md`, the Emivest TOU2026 JSON fixture, and the Ecoplexus Excel "Tariff Schedule 2026" sheet all correctly reflect this change. The tariff *rates* match Decision 1279/QĐ-BCT (effective 10 May 2025) at the 22 kV manufacturing tier. The model's TOU 2026 analysis shows +3.06 pp IRR, +24.3% Y1 revenue, and a shift from 2 BESS cycles/day to 1 — all consistent with the regulatory intent and independent analysis.

Two regulatory developments are **not yet modeled** and could materially affect project economics: (1) the **two-component tariff pilot** (Decree 146/2025/NĐ-CP), launching Phase 3 actual billing in July 2026 for ~7,000 large industrial customers at 22 kV+, which introduces a capacity charge (Cp ~235,414 VND/kW/month at 22 kV) and lowers energy charges by ~30–38%; and (2) **Circular 62/2025/TT-BCT**, Vietnam's first BESS-specific two-part tariff (capacity + energy), which offers a 10–15% price premium for storage-equipped RE projects meeting minimum thresholds (≥10% storage-to-plant ratio, 2-hr duration). The repo's `retail_tariff_matrix` in the Emivest fixture already encodes the two-component pilot rates, but the pipeline does not yet route through a two-component settlement path or model BESS-specific capacity payments.

[NOTE] Decision 963's TOU windows are formally issued but MOIT is still researching amendments to link them to billing cycles; it is uncertain whether current EVN invoices already reflect the new windows. The Excel workbook should flag this implementation-timing risk in its assumptions.

---

## Domain

### Discovery

The regulatory landscape governing Vietnam's TOU tariffs sits across six recent instruments:

| Instrument | Date | Subject |
|---|---|---|
| Electricity Law 61/2024/QH15 | 30 Nov 2024 | Multi-component tariff mandate (Art. 50) |
| Decision 07/2025/QĐ-TTg | 31 Mar 2025 | Average retail price band: VND 1,826–2,444/kWh |
| Decision 14/2025/QĐ-TTg | 29 May 2025 | Retail tariff structure as % of average price |
| Decision 1279/QĐ-BCT | 9 May 2025 | Current rates (4.8% increase, avg VND 2,204/kWh) |
| Decree 146/2025/NĐ-CP | 2025 | Two-component tariff framework |
| Circular 62/2025/TT-BCT | 26 Jan 2026 | BESS-specific two-part tariff |
| **Decision 963/QĐ-BCT** | **22 Apr 2026** | **New TOU time windows** |

Sources: [EVN tariff page](https://en.evn.com.vn/d6/news/RETAIL-ELECTRICITY-TARIFF-9-28-252.aspx), [Norton Rose Fulbright](https://www.nortonrosefulbright.com/en/knowledge/publications/9f5d6ce8/), [DFDL](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/), [VietnamNet](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html), [Thuvienphapluat](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Quyet-dinh-963-QD-BCT-2026-khung-gio-cao-diem-thap-diem-cua-he-thong-dien-quoc-gia-703327.aspx).

### Verification

- **Decision 963 TOU windows** confirmed via MOIT official announcement and Thuvienphapluat legal database. The old schedule (morning peak 09:30–11:30, evening 17:00–20:00) is replaced by a single evening block (17:30–22:30). Total peak/off-peak hours preserved at 5/6 hrs respectively. **High confidence.**
- **Decision 1279 rate levels** confirmed via EVN's English-language tariff page. Manufacturing 22 kV: Normal 1,833 / Peak 3,398 / Off-Peak 1,190 VND/kWh. Peak:off-peak ratio = 2.86x. **High confidence.**
- **Two-component pilot rates** (Cp and Ca by voltage) sourced from VietnamNet and Norton Rose Fulbright. Exact Ca values by individual voltage level have minor variation across sources (off-peak range 843–904 VND/kWh). The repo's encoded values (Cp=235,414, Ca_normal=1,275, Ca_peak=2,182, Ca_offpeak=859 at 22 kV) fall within published ranges. **Medium confidence** — official gazette table not found in English.
- **Circular 62 BESS tariff details** (specific VND rates) not found in English-language sources. The 10–15% premium figure comes from industry analysis (Energy-Storage.News, Vietnam Briefing), not regulatory text. **Low confidence** on exact rate values.
- **Decision 963 billing implementation** — MOIT is researching amendments to couple the new windows to billing. It is unclear whether May 2026 invoices use old or new windows. **Flagged as uncertainty.**

### Comparison

**Old TOU (pre-22 Apr 2026) vs. New TOU (Decision 963):**

| Attribute | Old | New |
|---|---|---|
| Peak blocks | 2 (09:30–11:30, 17:00–20:00) | 1 (17:30–22:30) |
| Morning peak overlap with solar | Yes (high-value hours) | None |
| BESS cycles/day feasible | 2 (morning + evening) | 1 (evening only) |
| Off-peak window | 22:00–04:00 | 00:00–06:00 |
| Sunday | No peak, normal 04:00–22:00 | No peak, normal 06:00–24:00 |
| Rationale | Legacy load profile | Solar/wind surplus makes daytime cheap; evening = true system stress |

**Single-component vs. Two-component (Decree 146 pilot):**

| Attribute | Single-component | Two-component |
|---|---|---|
| Demand charge | None | Cp ~235,414 VND/kW/month (22 kV) |
| Energy rates | Higher (1,833/3,398/1,190) | ~30–38% lower (1,275/2,182/859) |
| Demand charge share of bill | 0% | ~29–35% |
| BESS arbitrage value | Driven by energy spread | Lower energy spread; BESS also reduces demand charge |
| Scope | All customers | Pilot: ~7,000 mfg at 22 kV+, ≥200 MWh/month |
| Timeline | Current | Phase 3 billing starts Jul 2026 |

### Synthesis

The TOU window restructuring is the dominant near-term change for solar+BESS economics. It eliminates the morning peak premium that rooftop solar previously captured (~10–12% revenue loss for solar-only projects per DFDL analysis) but creates a more valuable evening peak for BESS discharge. For combined solar+BESS projects like Ecoplexus, the net effect is positive (+24% Y1 revenue in the model) because the consolidated evening peak is deeper and BESS can capture the full spread with a single well-timed cycle.

The two-component tariff pilot is the next structural change to watch. If the Ecoplexus offtaker is in the pilot scope (22 kV+, ≥200 MWh/month), the DPPA settlement math changes: lower energy arbitrage but BESS gains demand-charge reduction value. This is not yet modeled.

### Confidence
**Medium-High** — TOU window change is well-documented; rate levels are confirmed; two-component pilot timing is firm but exact scope uncertain; BESS-specific tariff details are sparse.

---

## Codebase

### Discovery

The repo is a Python financial simulation engine for Vietnam solar+BESS projects. Key TOU-related files:

| File | Role |
|---|---|
| `docs/vietnam_tou_2026.md` | Canonical hour-by-hour TOU 2026 mapping (JSON format) |
| `docs/2026-04-25_vietnam-tou-rooftop-ppa.md` | Research brief on tariff implications for rooftop PPAs |
| `src/re_storage/core/types.py` | `TimePeriod` enum (OFF_PEAK, STANDARD, PEAK) |
| `src/re_storage/inputs/json_loader.py` | `load_tariff_schedule_from_json()` — parses weekday hour→period mapping |
| `src/re_storage/inputs/loaders.py` | Excel tariff loading from "Assumption" sheet |
| `src/re_storage/settlement/dppa.py` | DPPA/CfD settlement (CfD payoff against spot FMP) |
| `src/re_storage/settlement/revenue.py` | Revenue dispatcher across 4 PPA modes |
| `src/re_storage/physics/battery.py` | BESS dispatch (arbitrage + peak-shaving modes) |
| `scripts/run_vietnam_tou2026_analysis.py` | Master TOU 2024 vs 2026 comparison runner |
| `scripts/add_ecoplexus_tou2026_sheet.py` | Adds "Tariff Schedule 2026" sheet to Excel workbook |
| `tests/unit/test_tou2026_tariff.py` | 27 passing tests for TOU 2026 schedule encoding |
| `results/baseline/ecoplexus_tou2024.json` | Baseline KPIs (IRR 6.26%, NPV $6.01M) |
| `results/new_tariff/ecoplexus_tou2026.json` | New tariff KPIs (IRR 9.31%, NPV $17.81M) |
| `data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx` | Audited Excel model (TOU 2024 baseline + TOU 2026 sheet) |

### Verification

- **TOU 2026 hour mapping** in `docs/vietnam_tou_2026.md`: Off-peak {0–5}, Standard {6–17,23}, Peak {18–22}. This uses whole-hour rounding (09:30→hour 10, 17:30→hour 18, 22:30→hour 23) which matches the convention documented in the file. **Correct per Decision 963.**
- **Tariff rates** in `Emivest_TOU2026.json`: Normal 1,833, Peak 3,398, Off-Peak 1,190 VND/kWh at 22 kV. **Matches Decision 1279 exactly.**
- **Two-component values** in the fixture's `retail_tariff_matrix`: Cp=235,414, Ca values 1,275/2,182/859. **Consistent with published pilot ranges** (medium confidence).
- **TOU 2026 analysis results**: IRR +3.06 pp, revenue +24.3%, BESS cycles reduced from 2→1. **Consistent with domain analysis.**
- **Test coverage**: 27 unit tests pass for TOU 2026 tariff encoding, dispatch, and comparison math.

### Comparison

**What is modeled vs. what is not:**

| Capability | Status |
|---|---|
| TOU 2024 hour mapping | ✅ Modeled |
| TOU 2026 hour mapping (Decision 963) | ✅ Modeled |
| Decision 1279 rate levels (single-component) | ✅ Modeled |
| DPPA/CfD settlement | ✅ Modeled |
| Bundled/Separate/Fixed PPA modes | ✅ Modeled |
| Two-component tariff settlement (Decree 146) | ❌ Not modeled (rates stored but no settlement path) |
| BESS capacity payment (Circular 62) | ❌ Not modeled |
| Demand charge reduction by BESS | ⚠️ `demand_charge.py` exists but not integrated with two-component rates |
| Decision 963 billing implementation risk | ❌ Not flagged in assumptions |
| Seasonal TOU pricing | ❌ Not adopted by Vietnam; no action needed |

### Synthesis

The codebase is well-aligned with the most impactful regulatory change (Decision 963 TOU windows). The tariff schedule is parameterized and switching between TOU 2024 and 2026 is handled cleanly via JSON config or Excel sheet selection. Three gaps warrant attention:

1. **Two-component tariff path**: The `retail_tariff_matrix` in fixtures already stores Cp and two-component Ca values, but no settlement module routes through capacity+energy pricing. With Phase 3 billing starting July 2026, this is the next modeling priority for large C&I projects.

2. **BESS capacity payment**: Circular 62's BESS-specific tariff (capacity + energy) could add a new revenue stream for storage projects. The exact rates need sourcing from Vietnamese-language regulatory text.

3. **Excel workbook parallel**: The Ecoplexus Excel model has the TOU 2026 sheet but should flag the Decision 963 billing-implementation timing uncertainty in its assumptions tab. The `plans/2026-05-04-claude-for-excel-tou-analysis-plan.md` covers the Excel comparison workflow but doesn't mention the two-component pilot.

### Confidence
**High** on codebase accuracy for what is currently modeled. **Medium** on gap prioritization — depends on whether target offtakers fall within the two-component pilot scope.

---

## Sources

- [EVN Retail Electricity Tariff (Decision 1279/QĐ-BCT)](https://en.evn.com.vn/d6/news/RETAIL-ELECTRICITY-TARIFF-9-28-252.aspx) — Primary rate source; official EVN English page
- [EVN Time-of-Use Charge](https://en.evn.com.vn/d6/news/TIME-OF-USE-ELECTRICITY-CHARGE-9-28-264.aspx) — TOU structure reference
- [Thuvienphapluat: Decision 963/QĐ-BCT](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Quyet-dinh-963-QD-BCT-2026-khung-gio-cao-diem-thap-diem-cua-he-thong-dien-quoc-gia-703327.aspx) — Legal database; authoritative TOU window text
- [MOIT: New Peak/Off-Peak Regulations](https://moit.gov.vn/tin-tuc/quy-dinh-moi-ve-gio-cao-diem-thap-diem-cua-he-thong-dien-quoc-gia.html) — Ministry announcement
- [VietnamNet: Vietnam Adjusts Power Peak Hours](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html) — English coverage of Decision 963 rationale
- [VietnamNet: EVN Trials Two-Part Pricing](https://vietnamnet.vn/en/evn-trials-two-part-electricity-pricing-lowest-rate-set-at-vnd843-per-kwh-2452431.html) — Two-component pilot details
- [Norton Rose Fulbright: Two-Component Tariff](https://www.nortonrosefulbright.com/en/knowledge/publications/9f5d6ce8/) — Legal analysis; capacity charge structure
- [DFDL: Vietnam 2025 Retail Electricity Rates](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/) — Rate analysis with RE implications
- [Energy-Storage.News: Vietnam BESS Revenue Framework](https://www.energy-storage.news/vietnams-bess-breakthrough-a-turning-point-for-energy-storage-across-asean/) — BESS tariff (Circular 62) coverage
- [Vietnam Briefing: Solar FiTs & Storage](https://www.vietnam-briefing.com/news/vietnams-solar-feed-in-tariffs-incentivizing-energy-storage.html/) — Storage premium analysis
- [Arcus Energy: Vietnam Business Tariff](https://arcusenergyasia.com/resources/tariffs/business) — Business/commercial rate tables
- [EVN Pilot Two-Component Tariff](https://en.evn.com.vn/d/en-US/news/Pilot-implementation-of-two-component-retail-electricity-tariff-from-October-2025-60-142-501015) — Official pilot timeline
- [Allens: Resolutions 70 and 328](https://www.allens.com.au/insights-news/insights/2025/10/) — Broader electricity market reform context

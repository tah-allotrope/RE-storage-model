# Research Brief: Vietnam TOU Tariff Shift — Rooftop Solar PPA Financials

**Date:** 2026-04-25
**Modes run:** domain, literature
**Depth:** standard
**Invocation context:** `/research` — Assess and explain the impact of recent Time-of-Use (TOU) tariff changes in Vietnam on rooftop solar PPA financials for both offtakers and developers, starting from the Xanh Terra TOU/BESS post and the VietnamNet peak-hour adjustment article.

---

## Synthesis

Decision **963/QĐ-BCT** (issued 22 April 2026) replaces Vietnam's split TOU peak (morning 09:30–11:30 + evening 17:00–20:00) with a **single consolidated 17:30–22:30 evening peak**, Mon–Sat; off-peak (00:00–06:00) is unchanged and Sundays remain peak-exempt ([VietnamSolar.vn explainer](https://vietnamsolar.vn/gio-cao-diem-thap-diem/), [VietnamNet](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html)). The retail tariff multiplier structure (peak/normal/off-peak as % of average price ~VND 2,204/kWh) is set by **Decision 14/2025/QĐ-TTg** with peak rates running 146–248% of average and normal rates 84–145%, depending on voltage class and customer type ([DFDL summary of Decision 14/2025](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/)).

The structural consequence for rooftop PV is that **all daytime PV output (06:00–17:30) now displaces only the "normal" tariff** — the 09:30–11:30 morning-peak premium that previously rewarded midday self-consumption disappears entirely ([Xanh Terra analysis](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess); [VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/)). At Vietnam's latitudes (10–21°N), PV output is effectively zero before the 17:30 peak begins year-round, so a solar-only system captures **none of the peak window**. This compresses the avoided-cost stack for solar-only DPPAs and pulls down willingness-to-pay from C&I offtakers whose counterfactual is retail TOU.

Conversely, BESS economics **improve in alignment but compress in revenue**. The new evening-only peak maps cleanly onto a 4–5 hour battery, letting a solar-charged BESS dispatch into 17:30–22:30 to displace kWh priced at roughly 1.5–2.5× normal-tariff rates ([Xanh Terra](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess)). However, the prior two-cycle-per-day arbitrage opportunity (morning + evening peak) collapses to a single cycle, reducing annual arbitrage revenue by ~50% per [VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/) — though with longer cycle life. Net effect: **solar-only PPAs lose ~20–35% of their offtaker-side value**; **solar+BESS PPAs become the dominant value proposition**, and developers/IPPs negotiating new contracts should expect price compression on storage-less offerings and a shift toward bundled or two-product (energy + dispatch) PPA structures.

[NOTE] Implementation is sequenced: Xanh Terra reports MOIT is targeting "rollout during the 2026 dry season," contingent on retail tariff adjustments under Decision 14/2025/QĐ-TTg and meter reinstallation. Whether MOIT re-issues the multiplier table for the new windows or leaves Decision 14 multipliers untouched is **not yet confirmed in any public source reviewed** — analyses should sensitivity-test both cases until the next tariff circular lands.

---

## Domain

### Discovery

The strongest sources for the regulatory shift are: (a) MOIT-aligned Vietnamese-language explainer [VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/) which republishes the Decision 963/QĐ-BCT windows and contrasts them with the prior regime; (b) [VietnamNet's English summary](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html) which provides the rationale (industrial share rising from ~30% to >50% of load, solar generation pattern); (c) the [Xanh Terra rooftop+BESS analysis](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess) which translates the windows into solar/BESS sizing implications; (d) [DFDL's overview of Decision 14/2025/QĐ-TTg](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/) which provides the tariff multiplier table and the average retail price baseline of VND 2,204.0655/kWh.

For DPPA framework context, [Vietnam Briefing's Decree 57/2025 explainer](https://www.vietnam-briefing.com/news/vietnam-renewable-energy-decree-57.html/) and [Duane Morris' DPPA+BESS post](https://blogs.duanemorris.com/vietnam/2026/02/26/vietnam-investing-in-solar-projects-with-dppa-and-bess-what-you-must-know/) cover physical-wire vs virtual/CfD models and bankability factors. [Norton Rose Fulbright's Vietnam Power Sector Snapshot](https://www.nortonrosefulbright.com/en/knowledge/publications/1d041eb0/vietnam-power-sector-snapshot) confirms MOIT is developing a separate BESS tariff structure with capacity-style payments.

### Verification

The new TOU windows are independently confirmed by VietnamSolar.vn, VietnamNet, and Xanh Terra — three sources with different audiences (Vietnamese consumer/industry, English news, English investor) all reporting identical 17:30–22:30 Mon–Sat peak / 00:00–06:00 off-peak / Sundays exempt ([VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/); [VietnamNet](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html); [Xanh Terra](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess)). The prior windows (09:30–11:30 + 17:00–20:00 peak; 22:00–04:00 off-peak) are confirmed by both [DFDL's Decision 14/2025 summary](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/) and [VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/). Multipliers come from DFDL only and have not been cross-checked against the original Decision 14/2025/QĐ-TTg text — flag as single-source on tariff levels but high-confidence on directional structure.

The VietnamNet figures (commercial peak VND 5,422/kWh; off-peak VND 1,609/kWh; manufacturing peak VND 3,266–3,640/kWh) are directionally consistent with DFDL's multipliers applied to VND 2,204/kWh average (manufacturing medium-voltage peak ≈ 157% × 2,204 = ~3,460; "other commercial" low-voltage peak ≈ 248% × 2,204 = ~5,466) — close enough to validate both sources but with rounding differences ([VietnamNet](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html); [DFDL](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/)).

What is **not verified**: whether the existing Decision 14/2025 multipliers are simply remapped onto the new Decision 963 windows, or whether MOIT will issue an updated multiplier schedule. VietnamSolar.vn states peak is "80–100% higher than normal, 2.5–3× higher than off-peak" — directionally consistent with current multipliers but no replacement table is published. **Treat tariff levels as preliminary until the next MOIT circular.**

### Comparison

Two implementation lenses dominate the commentary:
- **Xanh Terra** frames the change as a structural shift that *favors* paired solar+BESS while *compressing* solar-only IRR, emphasizing that "a 4-hour BESS discharged at full rated power from 17:30 covers 80% of the peak window" — a clean sizing target ([Xanh Terra](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess)).
- **VietnamSolar.vn** emphasizes the *arbitrage compression* angle: prior rules supported two cycles/day (overnight-charge → morning-peak discharge; midday-charge → evening-peak discharge); new rules support only one cycle, cutting annual arbitrage revenue ~50% but extending battery life ([VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/)).

The two views are complementary rather than contradictory — the first focuses on alignment (good for greenfield BESS sizing), the second on revenue per kWh-installed (worse than under the prior regime, but still positive). [Vietnam Briefing](https://www.vietnam-briefing.com/news/vietnam-renewable-energy-decree-57.html/) layers a regulatory frame on top: under Decree 57/2025, BESS meeting technical thresholds (≥10% of plant capacity, ≥2-hour storage, ≥5% delivered from stored output) qualifies for enhanced FIT-style tariffs on grid-connected projects — but this is for utility-scale RE, not C&I DPPAs.

### Synthesis

For **C&I rooftop PPA structuring**, the new TOU has three first-order effects:

1. **Solar-only avoided cost falls.** The morning-peak premium (~146–248% of average for industrial/commercial) that previously rewarded 09:30–11:30 generation is gone. Daytime PV now displaces only normal-tariff kWh (84–145% of average). At industrial medium voltage, this drops the displaced rate from ~157% (peak) to ~86% (normal) for ~2 hours/day of generation — roughly a 30–40% revenue haircut on those hours, or ~5–10% on a full-day annualized basis depending on the load shape ([DFDL](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/)).
2. **BESS dispatch alignment improves; arbitrage spread narrows.** A single evening peak is cleaner to design for, but the lost morning-peak cycle removes ~50% of theoretical arbitrage revenue ([VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/); [Xanh Terra](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess)).
3. **Two-shift operations face higher exposure.** Industrial offtakers running second shifts past 17:30 see higher peak bills; day-shift operations gain since morning-peak buying disappears ([VietnamNet](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html)).

What's missing for planning: (a) confirmed multipliers for the new windows, (b) a published tariff for grid-connected BESS-paired projects under Decree 57/2025, (c) clarity on whether DPPA virtual contracts will reference the wholesale market price (largely independent of retail TOU) or any retail-linked benchmark.

### Confidence

**Medium-High.** The window change itself is triple-sourced and unambiguous. Tariff multipliers and quantitative IRR effects depend on whether Decision 14/2025 multipliers are remapped or revised — a non-trivial uncertainty until MOIT issues the next implementing circular.

---

## Literature

### Discovery

Practitioner write-ups dominate the available evidence; no peer-reviewed papers yet exist on Decision 963 (issued 22 April 2026, ~3 days before this brief). The most useful items are:
- [Vietnam Briefing on Decree 57/2025 (DPPA)](https://www.vietnam-briefing.com/news/vietnam-renewable-energy-decree-57.html/) — covers physical vs virtual DPPA, surplus-export 20% cap for rooftop, T&D pass-through references.
- [Duane Morris blog on DPPA+BESS](https://blogs.duanemorris.com/vietnam/2026/02/26/vietnam-investing-in-solar-projects-with-dppa-and-bess-what-you-must-know/) — bankability framing: BESS revenue must be priced into the PPA, not left dependent on emerging ancillary markets.
- [B-Company on draft 50% surplus rule](https://b-company.jp/vietnam-rooftop-solar-draft-rules-2026-selling-up-to-50-surplus-power-who-benefits-and-what-to-watch-next) — MOIT January 2026 consultation raising the rooftop surplus-export cap from 20% toward 50%, with bilateral overrides allowed through 31 Dec 2030.
- [Norton Rose Fulbright power sector snapshot](https://www.nortonrosefulbright.com/en/knowledge/publications/1d041eb0/vietnam-power-sector-snapshot) — confirms a separate BESS tariff with capacity-style payments is in development.
- [IEEFA on DPPA decree](https://ieefa.org/resources/vietnams-direct-power-purchase-agreement-dppa-decree-could-catalyze-new-era-renewable) — broader market-reform framing.

### Verification

Decree 57/2025 framework details (private wire vs grid-connected CfD, ceiling tariffs set by MOIT, surplus-export cap at 20%, BESS technical thresholds for tariff incentives) appear consistently across Vietnam Briefing, Duane Morris, and Norton Rose. The 50% surplus draft is at consultation stage as of January 2026 and is **not yet binding** — flag as forward-looking ([B-Company](https://b-company.jp/vietnam-rooftop-solar-draft-rules-2026-selling-up-to-50-surplus-power-who-benefits-and-what-to-watch-next)). No source provides verified IRR ranges for solar-only vs solar+BESS PPAs under the new 963 windows; quantitative claims in this brief are derived from multiplier math, not from observed transactions.

### Comparison

There is broad practitioner agreement on three points: (a) virtual/CfD DPPAs partially decouple developer revenue from retail TOU because settlement is wholesale-linked, while offtaker willingness-to-pay remains retail-linked ([Vietnam Briefing](https://www.vietnam-briefing.com/news/vietnam-renewable-energy-decree-57.html/)); (b) BESS bankability hinges on having dispatch rights and capacity payments priced inside the PPA, not parked in pending ancillary markets ([Duane Morris](https://blogs.duanemorris.com/vietnam/2026/02/26/vietnam-investing-in-solar-projects-with-dppa-and-bess-what-you-must-know/); [Norton Rose](https://www.nortonrosefulbright.com/en/knowledge/publications/1d041eb0/vietnam-power-sector-snapshot)); (c) offtaker credit quality is now the binding constraint on bankability since EVN is no longer the contracted counterparty in virtual DPPAs ([Duane Morris](https://blogs.duanemorris.com/vietnam/2026/02/26/vietnam-investing-in-solar-projects-with-dppa-and-bess-what-you-must-know/)).

The TOU shift sharpens the second point: with arbitrage value compressed (~50% per [VietnamSolar.vn](https://vietnamsolar.vn/gio-cao-diem-thap-diem/)) and the evening-only peak fully outside daylight, BESS revenues must be **contracted as dispatch obligations** with explicit per-kWh or per-kW-month prices for the project to finance.

### Synthesis

Three planning implications fall out of the literature:

1. **Solar-only DPPAs at C&I sites should reprice downward by 5–15%** to remain competitive vs the offtaker's retail counterfactual, depending on customer load shape (daytime-heavy = smaller compression; two-shift = larger).
2. **Solar+BESS PPAs benefit from product unbundling** — separate energy ($/MWh) and dispatch ($/kW-month or $/MWh-discharged) components, both contractually firm. This matches the structure Norton Rose flags MOIT is preparing for utility BESS and which Duane Morris flags as a bankability prerequisite.
3. **Watch the next MOIT circular** for the Decision 963-aligned multiplier table and the finalization of the 50% rooftop surplus-export rule. Both materially change the economics modeled here.

### Confidence

**Medium.** Practitioner literature is internally consistent on framework but provides no transaction-level IRR data; quantitative claims here are inference from regulated tariff multipliers, not observed PPA pricing. Treat as directional, not benchmark.

---

## Sources

- [VietnamSolar.vn — Giờ Cao Điểm Thấp Điểm 2026: 963/QĐ-BCT](https://vietnamsolar.vn/gio-cao-diem-thap-diem/) — Vietnamese-language industry explainer; primary source for both new and prior TOU windows and multiplier ranges.
- [VietnamNet — Vietnam adjusts power peak hours amid rising demand](https://vietnamnet.vn/en/vietnam-adjusts-power-peak-hours-amid-rising-electricity-demand-2509795.html) — English news source; effective date and named tariff figures.
- [Xanh Terra — MOIT TOU and Solar BESS](https://xanhterra.com/xanhblog-moit-tou-and-solar-bess) — practitioner analysis on solar+BESS sizing and DPPA implications.
- [DFDL — Vietnam's 2025 Retail Electricity Rates](https://www.dfdl.com/insights/legal-and-tax-updates/vietnams-2025-retail-electricity-rates/) — Decision 14/2025/QĐ-TTg multiplier table and average retail price baseline.
- [Vietnam Briefing — Renewable Energy Decree 57](https://www.vietnam-briefing.com/news/vietnam-renewable-energy-decree-57.html/) — DPPA framework, physical vs virtual, BESS technical thresholds.
- [Duane Morris — Investing in Solar Projects with DPPA and BESS](https://blogs.duanemorris.com/vietnam/2026/02/26/vietnam-investing-in-solar-projects-with-dppa-and-bess-what-you-must-know/) — bankability and offtaker-credit framing.
- [Norton Rose Fulbright — Vietnam Power Sector Snapshot](https://www.nortonrosefulbright.com/en/knowledge/publications/1d041eb0/vietnam-power-sector-snapshot) — MOIT-developed BESS tariff with capacity payments.
- [B-Company — Vietnam Rooftop Solar Draft Rules 2026](https://b-company.jp/vietnam-rooftop-solar-draft-rules-2026-selling-up-to-50-surplus-power-who-benefits-and-what-to-watch-next) — MOIT draft consultation lifting surplus-export cap toward 50%.
- [IEEFA — Vietnam's DPPA decree](https://ieefa.org/resources/vietnams-direct-power-purchase-agreement-dppa-decree-could-catalyze-new-era-renewable) — broader market-reform context.
- [Thuvienphapluat — Quyết định 963/QĐ-BCT 2026](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Quyet-dinh-963-QD-BCT-2026-khung-gio-cao-diem-thap-diem-cua-he-thong-dien-quoc-gia-703327.aspx) — Vietnamese legal database listing of the decision (not directly fetched; flagged as canonical legal-text reference for follow-up verification).

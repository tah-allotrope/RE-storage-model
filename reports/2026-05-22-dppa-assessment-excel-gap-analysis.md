# Gap Analysis: Onsite & Offsite DPPA Assessment Excel Workbook

**Date:** 2026-05-22
**Scope:** Create a new Excel file from the current repo state that delivers both onsite and offsite DPPA assessment outputs for a client, covering all 4 PPA options, financial KPIs, dispatch profiles, sensitivity analysis, and a structured comparison between onsite and offsite configurations.
**Status:** Draft for Review

---

## Executive Summary

The Python `re_storage` engine has strong coverage of the physics/dispatch layer (solar, BESS, energy balance) and all 4 PPA revenue settlement paths (Bundled, Separate PV+BESS, DPPA CfD, Fixed EVN PPA). Financial modelling — OPEX, taxes, debt, waterfall, IRR/NPV/DSCR — is implemented and functional via both Excel-loader and JSON-loader pipelines. Scenario comparison (`run_all_scenarios`) and sensitivity sweeps (`run_sensitivity`) are operational. **However, the repo has no Excel-generation capability** — all outputs are JSON, HTML, or PPTX. Creating a client-facing DPPA assessment workbook requires: (1) an Excel writer/formatter layer, (2) explicit onsite vs offsite configuration logic, (3) an assessment summary sheet combining both configurations, and (4) client-ready formatting with Allotrope branding. There are **3 CRITICAL gaps**, **3 HIGH gaps**, and **3 MEDIUM gaps**.

---

## Current Capabilities (What We Have)

| Capability | Status | Key Surfaces |
|---|---|---|
| Solar PV generation simulation | Mature | `src/re_storage/physics/solar.py` |
| BESS dispatch (arbitrage, peak-shave, TOU) | Mature | `src/re_storage/physics/battery.py` |
| Energy balance (direct PV, surplus, grid load) | Mature | `src/re_storage/physics/balance.py` |
| DPPA CfD settlement (Option 3) | Mature | `src/re_storage/settlement/dppa.py` |
| Bundled Discount PPA (Option 1) | Working | `src/re_storage/settlement/bundled.py` |
| Separate PV+BESS PPA (Option 2) | Working | `src/re_storage/settlement/separate.py` |
| Fixed EVN PPA (Option 4) | Working | `src/re_storage/settlement/fixed_ppa.py` |
| Grid savings calculation | Mature | `src/re_storage/settlement/grid.py` |
| Demand charge savings | Working | `src/re_storage/settlement/demand_charge.py` |
| OPEX schedule (O&M, insurance, land, mgmt) | Working | `src/re_storage/financial/opex.py` |
| Tax schedule (CIT holiday, tiered rates) | Working | `src/re_storage/financial/taxes.py` |
| MRA (Maintenance Reserve Account) | Working | `src/re_storage/financial/mra.py` |
| Debt sizing (DSCR-constrained) | Working | `src/re_storage/financial/debt.py` |
| Cash flow waterfall | Working | `src/re_storage/financial/waterfall.py` |
| IRR/NPV/DSCR metrics (XIRR/XNPV) | Mature | `src/re_storage/financial/metrics.py` |
| Lifetime projection with degradation | Working | `src/re_storage/aggregation/lifetime.py` |
| Scenario comparison (all 4 PPA options) | Working | `src/re_storage/scenarios/runner.py` |
| Sensitivity analysis | Working | `src/re_storage/scenarios/sensitivity.py` |
| JSON input pipeline | Working | `src/re_storage/inputs/json_loader.py` |
| Excel input pipeline | Working | `src/re_storage/inputs/loaders.py` |
| HTML report generation | Working | `src/re_storage/reporting/html_report.py` |
| TOU 2024 & 2026 tariff codification | Working | `src/re_storage/inputs/loaders.py`, JSON fixtures |
| Baseline & new-tariff scenario JSON outputs | Working | `results/baseline/`, `results/new_tariff/` |
| Excel output generation | Missing | — |
| Onsite vs offsite DPPA configuration split | Missing | — |
| Client-facing assessment formatting | Missing | — |

---

## Target State

> A single, polished Excel workbook (`.xlsx`) that a client can open and review, containing:
>
> 1. **Cover / Summary** sheet with project metadata, key assumptions, and go/no-go recommendation
> 2. **Onsite DPPA Assessment** sheet with KPIs, annual proforma, and dispatch profile for an onsite (behind-the-meter) solar+BESS configuration
> 3. **Offsite DPPA Assessment** sheet with equivalent KPIs for an offsite (front-of-meter / virtual PPA) configuration
> 4. **Comparison** sheet showing side-by-side onsite vs offsite results across all 4 PPA options
> 5. **Sensitivity Analysis** sheet with tornado charts or data tables for key variables
> 6. **Assumptions & Methodology** sheet documenting all inputs
> 7. Professional formatting: Allotrope branding, number formatting, conditional formatting for KPI thresholds, print-ready layout

---

## Gap Analysis

### GAP-01: No Excel Output Writer

**Severity:** CRITICAL — Blocks the entire target deliverable

**Current state:** All model outputs are emitted as Python dicts/DataFrames serialized to JSON (`results/*.json`), HTML reports (`reports/*.html`), or PPTX presentations (`results/*.pptx`). The `src/re_storage/reporting/html_report.py` module generates HTML only. There is no code anywhere in the repo that writes `.xlsx` files.

**What's needed:**
- An Excel writer module that takes pipeline KPI dicts and DataFrames and writes formatted `.xlsx` sheets using `openpyxl`
- Sheet-level formatting: merged header cells, number formats, column widths, conditional formatting
- Chart embedding for dispatch profiles, revenue stacks, DSCR series
- A script entrypoint (e.g., `scripts/generate_dppa_assessment.py`) that orchestrates pipeline runs and feeds results into the writer

**Existing assets to reuse:**
- `src/re_storage/reporting/html_report.py` — has KPI formatting logic, chart generation with matplotlib, tolerance definitions; the data-extraction patterns can be reused
- `src/re_storage/scenarios/runner.py` — `run_all_scenarios()` already produces the multi-option KPI comparison dict needed for the comparison sheet
- `src/re_storage/scenarios/sensitivity.py` — `run_sensitivity()` already produces swept results needed for the sensitivity sheet
- `results/baseline/*.json` and `results/new_tariff/*.json` — contain proven output schemas showing exactly which KPIs the pipeline returns

**Effort estimate:** 1 multi-phase plan (2–3 phases). Core writer is medium complexity; formatting/branding is the long tail.

---

### GAP-02: No Onsite vs Offsite Configuration Logic

**Severity:** CRITICAL — Without this, only one DPPA mode can be assessed per run

**Current state:** The pipeline treats all runs as a single configuration. The `ppa_option` field (1–4) selects the revenue settlement method, but there is no concept of "onsite" (behind-the-meter, load-following, direct wire) vs "offsite" (virtual PPA, grid-injected, CfD-only) as distinct assessment configurations. The DPPA module (`settlement/dppa.py`) always applies the same `k_factor`, `kpp`, and load-matching logic regardless of physical topology.

**What's needed:**
- Define what distinguishes onsite from offsite in the assessment context:
  - **Onsite:** direct PV consumption, BESS behind the meter, grid savings from load offset, demand charge reduction; PPA options 1 (Bundled) and 2 (Separate) are the natural revenue structures
  - **Offsite:** all generation injected to grid, CfD settlement against FMP, no direct load offset or grid savings; PPA option 3 (DPPA CfD) and option 4 (Fixed EVN) are the natural revenue structures
- A configuration parameter (e.g., `dppa_topology: "onsite" | "offsite"`) that adjusts:
  - Which revenue streams are active (grid savings yes/no, demand charge savings yes/no)
  - How `net_gen_for_dppa_kwh` is computed (net of self-consumption vs gross generation)
  - Which PPA options are meaningful to compare in each topology
- This may be achievable without new settlement code — the existing modules already cover all 4 options; the gap is in orchestrating which combination of revenue streams to include per topology

**Existing assets to reuse:**
- `src/re_storage/pipeline.py` — `_run_settlement()` already dispatches by `ppa_option`; the topology layer would wrap this with revenue-stream inclusion/exclusion logic
- `src/re_storage/settlement/grid.py` — grid savings are already computed separately and can be zeroed for offsite
- `src/re_storage/settlement/demand_charge.py` — demand charge savings already return 0 when `cp_demand_vnd_per_kw <= 0`; offsite can simply pass 0
- `activeContext.md` ISSUE-5 DPPA FS Study notes — documents the onsite/offsite distinction from the REopt.jl study (Scenario 3: virtual DPPA)

**Effort estimate:** 1 plan phase. Mostly orchestration, not new settlement math.

---

### GAP-03: No Assessment Summary / Go-No-Go Logic

**Severity:** HIGH — Significantly degrades client value without a synthesized recommendation

**Current state:** The pipeline returns raw KPI dicts. The HTML report shows KPIs with tolerance comparisons against Excel references, but there is no logic that interprets KPIs in a client-facing assessment context (e.g., "Project IRR exceeds hurdle rate → GO", "Min DSCR below covenant → NO-GO"). The web frontend has a placeholder `<GoNoGoIndicator>` mentioned in `activeContext.md` ISSUE-4 outstanding items but it is not implemented.

**What's needed:**
- A function that takes KPIs + hurdle/covenant thresholds and returns a structured assessment verdict:
  - Equity IRR vs target IRR → GO / CAUTION / NO-GO
  - Min DSCR vs covenant (e.g., 1.2x or 1.3x) → PASS / FAIL
  - NPV sign → positive = value-creating
  - Payback period vs project life → acceptable / excessive
- Assessment text generation for the Excel summary sheet
- Conditional formatting rules for the Excel writer (green/amber/red cells)

**Existing assets to reuse:**
- `src/re_storage/financial/metrics.py` — already computes all required KPIs
- `src/re_storage/reporting/html_report.py` — has `KPI_TOLERANCES` dict and formatting helpers
- `activeContext.md` ISSUE-5 DPPA FS Study — documents typical hurdle rates from the REopt.jl study (15% equity hurdle, 1.53x DSCR)

**Effort estimate:** Small — a single utility function + Excel formatting rules.

---

### GAP-04: No Annual Proforma Table Export

**Severity:** HIGH — Clients expect a year-by-year financial table in assessment workbooks

**Current state:** The pipeline returns `_annual_df` (when the financial stage runs) and `_lifetime_df`, but these are internal DataFrames stripped from JSON serialization. The web serializer (`web/functions/utils/serialise.py`) extracts `annual`, `cashflow`, and `dscr_series` arrays from `_annual_df`, but only for JSON API responses — there is no path to write these as formatted Excel rows.

**What's needed:**
- Extract the annual proforma (revenue, OPEX lines, EBITDA, depreciation, taxes, net income, CFADS, debt service, DSCR, equity cashflow) for each year 1–25
- Write as a formatted Excel table with totals row, number formatting, and alternating row shading
- Include both pre-tax and post-tax views

**Existing assets to reuse:**
- `src/re_storage/financial/waterfall.py` — `build_cash_flow_waterfall()` returns a DataFrame with all proforma columns
- `src/re_storage/financial/opex.py` — `build_opex_schedule()` returns itemized OPEX
- `web/functions/utils/serialise.py` — `serialise_results()` already extracts annual/cashflow/dscr data from pipeline outputs; the extraction logic can be reused for Excel writing

**Effort estimate:** Medium — data is available, formatting is the work.

---

### GAP-05: No Dispatch Profile Visualization in Excel

**Severity:** HIGH — Dispatch charts are a key assessment artifact for technical due diligence

**Current state:** The pipeline produces hourly dispatch data (`_hourly_df` with SoC, charge, discharge, solar gen, load, grid load columns), but this is stripped from all outputs. The web frontend has a `DispatchPreviewChart` that shows a 1-week sample, and `results/figures/avg_day_dispatch_comparison.png` exists as a matplotlib PNG. Neither can be embedded in Excel.

**What's needed:**
- Extract representative dispatch days (e.g., average weekday, average weekend, peak day, min-solar day) from hourly data
- Create Excel charts (line or area) showing the stacked dispatch profile
- Alternatively, embed matplotlib-generated charts as images in the Excel workbook

**Existing assets to reuse:**
- `scripts/run_vietnam_tou2026_analysis.py` — already generates `avg_day_dispatch_comparison.png` with matplotlib; the chart-generation code can be adapted
- `src/re_storage/reporting/html_report.py` — `_to_base64_png()` generates inline matplotlib charts; the same figures can be saved and inserted into Excel via `openpyxl.drawing.image`
- `web/functions/utils/serialise.py` — extracts `dispatch_sample` (first 168 hours) from pipeline results

**Effort estimate:** Medium — chart generation exists, Excel embedding is the new work.

---

### GAP-06: No Payback Period or Cash-on-Cash Yield Metric

**Severity:** MEDIUM — Limits completeness of assessment KPI set

**Current state:** `src/re_storage/financial/metrics.py` implements IRR, NPV, and DSCR. Payback period and cash-on-cash yield are not computed. `activeContext.md` ISSUE-4 outstanding items explicitly notes: "Add payback period and cash-on-cash yield to `financial/metrics.py`."

**What's needed:**
- Simple payback = Total CAPEX / Year 1 EBITDA
- Discounted payback = first year where cumulative discounted FCFE turns positive
- Cash-on-cash yield = Year 1 FCFE / equity invested

**Existing assets to reuse:**
- `src/re_storage/financial/metrics.py` — add functions alongside existing metric implementations
- `src/re_storage/financial/waterfall.py` — provides the cashflow series needed for payback calculation

**Effort estimate:** Small — straightforward metric additions.

---

### GAP-07: No Two-Component Tariff Settlement Path

**Severity:** MEDIUM — Limits applicability for clients whose offtakers are in the Decree 146 pilot (22 kV+, ≥200 MWh/month)

**Current state:** The research brief (`research/2026-05-07_vietnam-tou-tariff-impact.md`) documents the two-component tariff pilot (capacity charge Cp + lower energy charges Ca) and notes the Emivest JSON fixture already encodes `retail_tariff_matrix` with the pilot rates. However, the pipeline does not route through a two-component settlement path. The `demand_charge.py` module returns 0 for 1-component tariff projects. For onsite DPPA assessment, the two-component tariff could materially change the economics (lower energy arbitrage, but BESS gains demand-charge reduction value).

**What's needed:**
- A tariff-mode flag (`tariff_mode: "1-component" | "2-component"`) in the pipeline
- When 2-component: apply Cp demand charges to baseline and post-RE peaks, compute energy at Ca rates instead of standard rates
- Update grid savings to include both energy savings and demand charge savings

**Existing assets to reuse:**
- `src/re_storage/settlement/demand_charge.py` — already has the demand charge savings formula; just needs non-zero Cp input
- `src/re_storage/settlement/grid.py` — energy expense calculation already uses `tariff_rates` dict; swapping in Ca rates is a parameter change
- Research brief `research/2026-05-07_vietnam-tou-tariff-impact.md` — documents the exact Cp and Ca values by voltage level

**Effort estimate:** 1 plan phase. Settlement math exists; wiring and testing are the work.

---

### GAP-08: No Client Branding / Formatting Templates

**Severity:** MEDIUM — Assessment workbooks without professional formatting undermine client confidence

**Current state:** The PPTX generation (`results/make_presentation_v2.js`) follows Allotrope-style branding (Calibri Light/Calibri typography, green title rule, confidentiality footer). No equivalent formatting specification exists for Excel output.

**What's needed:**
- Excel style definitions: header fonts, color palette, number formats, border styles
- Cover sheet template with logo placeholder, project name, date, confidentiality notice
- Consistent currency formatting (USD with commas, VND with dots)
- Print area settings for each sheet
- Conditional formatting for KPI thresholds (green = meet hurdle, amber = marginal, red = fail)

**Existing assets to reuse:**
- `results/make_presentation_v2.js` — contains Allotrope color codes and typography specifications that can inform the Excel style palette
- The existing Excel input files (`data/AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx`) — their formatting can be referenced for output styling conventions

**Effort estimate:** Small-Medium — mostly `openpyxl` styling code, no model logic.

---

## Second-Tier Gaps

| Gap | Severity | Summary | Existing Assets |
|---|---|---|---|
| GAP-09 | LOW | No wind generation source support (limits offsite assessment to solar-only) | `physics/solar.py` pattern can be extended; REopt study comparison in `activeContext.md` documents wind parameters |
| GAP-10 | LOW | No factory-side NPV (only developer NPV is computed) | `financial/metrics.py` has NPV; factory NPV needs separate cashflow construction from offtaker perspective |
| GAP-11 | LOW | No viability frontier heatmap (PPA price × interest rate → equity IRR) | `scenarios/sensitivity.py` can sweep 2 variables; needs a 2D grid runner and chart generator |
| GAP-12 | LOW | Excel financial parity not fully converged for Ecoplexus workbook | `activeContext.md` ISSUE-5 documents remaining deltas; not a blocker for new assessment workbook since the Python model can be treated as the source of truth for new projects |

---

## Recommended Sprint Sequencing

| Priority | Gap | Rationale |
|---|---|---|
| Sprint 1 | GAP-01 (Excel writer) | Foundation — nothing else ships without the ability to write `.xlsx` |
| Sprint 1 | GAP-06 (Payback/CoC metrics) | Quick win — adds 2–3 functions to existing metrics module; needed for Sprint 2 sheets |
| Sprint 2 | GAP-02 (Onsite vs offsite config) | Core differentiator — the assessment needs both modes |
| Sprint 2 | GAP-04 (Annual proforma export) | High client value — year-by-year table is expected in any financial assessment |
| Sprint 3 | GAP-03 (Go/No-Go logic) | Synthesizes Sprint 2 outputs into a client recommendation |
| Sprint 3 | GAP-05 (Dispatch charts in Excel) | Visual due diligence artifact |
| Sprint 3 | GAP-08 (Branding/formatting) | Polish — applied across all sheets at the end |
| Sprint 4 | GAP-07 (Two-component tariff) | Extends applicability but not required for initial delivery |

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| `openpyxl` chart API limitations | Excel charts may not match matplotlib quality; embedded images may not resize cleanly | M | Use `openpyxl` native charts for simple bar/line; fall back to embedded PNG for complex dispatch profiles |
| Onsite/offsite boundary definition mismatch with client expectations | Assessment may not match the client's specific DPPA contract structure | H | Clarify with client: is "onsite" = physical behind-the-meter, or = synthetic net-metering? Document assumptions in Methodology sheet |
| Financial KPI accuracy for Ecoplexus-scale projects | Known parity gaps in `activeContext.md` ISSUE-5 (NPV sign mismatch, debt sizing delta) could affect assessment credibility | M | Use Emivest-calibrated JSON path for the assessment (closer to parity); flag known limitations in Methodology sheet |
| Client-specific inputs not yet in repo | Assessment requires project-specific assumptions (site capacity, load profile, tariff tier, CAPEX quotes) | H | Create a client input template (JSON or simple Excel) that the script reads; provide defaults from Emivest/Ecoplexus fixtures |
| TOU 2026 implementation timing uncertainty | Decision 963 TOU windows are issued but billing implementation timeline is uncertain | M | Include both TOU 2024 and TOU 2026 scenarios in the assessment; flag regulatory uncertainty in Methodology sheet |

---

## Suggested Next Step

1. Clarify with the client which project parameters to use (site capacity, load profile, voltage tier, CAPEX).
2. Review this report, then invoke `/plan` for GAP-01 (Excel writer module) as the first implementation target.
3. In parallel, add the payback/cash-on-cash metrics (GAP-06) as a quick standalone task.
4. Once the writer is functional, invoke `/plan` for GAP-02 (onsite vs offsite orchestration) and GAP-04 (annual proforma export).

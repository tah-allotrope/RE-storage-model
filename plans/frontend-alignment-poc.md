# Frontend Alignment Plan: RE-Storage-Model Web App

**Reference POC:** [PV-webapp-vibed](https://deepwiki.com/tah-allotrope/PV-webapp-vibed)
**Date:** 2026-03-23
**Status:** Draft

---

## 1. Context & Gap Analysis

### What the POC Does Well
The AI Studio POC (`PV-webapp-vibed`) establishes a clean, functional pattern:
- React 19 + Vite 6 + TypeScript + Tailwind CSS 4
- Two-column responsive layout (inputs left, outputs right)
- Leaflet `MapSelector` for geographic coordinate capture
- `useMemo`-based financial engine (25-year NPV simulation)
- Recharts `LineChart` for cumulative cash flow visualization
- KPI cards with `Intl.NumberFormat` (VND localization)
- Vietnam solar yield bands by latitude (South/Central/North)

### What the RE-Storage-Model Needs Beyond the POC

| Dimension | POC | RE-Storage-Model Target |
|-----------|-----|-------------------------|
| Asset type | Residential rooftop solar | 40 MW commercial Solar + BESS |
| Battery dispatch | None | Arbitrage / Peak Shaving modes, SoC tracking |
| Revenue streams | Grid savings only | Grid savings + DPPA/CfD settlement |
| Financial structure | Simple NPV/payback | IRR, DSCR, debt sizing, MRA waterfall |
| Inputs | ~5 parameters | ~30 named-range parameters |
| Computation | In-browser `useMemo` | Python backend API (re_storage engine) |
| Output horizon | 25-year cash flow chart | 25-year + annual breakdown + hourly dispatch preview |

---

## 2. Proposed Tech Stack

Adopt the POC stack unchanged, adding a backend client layer:

```
React 19 + TypeScript
Vite 6
Tailwind CSS 4
Recharts          — financial charts (cash flow, DSCR, SoC profile)
Leaflet / react-leaflet — site location selector
Lucide-react      — icons
Zod               — input validation schemas (already in repo .opencode deps)
fetch / React Query (TanStack) — async calls to Python API
```

The Python backend (`re_storage`) already exists. The web app calls it via HTTP (Firebase Functions or local FastAPI dev server).

---

## 3. Component Architecture

```
src/
  components/
    layout/
      AppShell.tsx          # Two-panel responsive shell (mirrors POC layout)
      Sidebar.tsx           # Left panel: input accordion sections
      ResultsPane.tsx       # Right panel: KPI grid + chart tabs
    inputs/
      MapSelector.tsx       # Lifted from POC; extend with Vietnam province lookup
      SystemParams.tsx      # Solar capacity, BESS capacity/power, COD date
      BatteryDispatch.tsx   # Strategy mode (Arbitrage/Peak Shaving), charge windows
      DPPAParams.tsx        # Strike price, k-factor, Kpp, DPPA toggle
      FinancialParams.tsx   # Debt %, interest rate, tenor, DSCR covenant, MRA %
    outputs/
      KPICard.tsx           # Reuse POC pattern; support USD + VND toggle
      CashFlowChart.tsx     # Recharts LineChart: project/equity/unlevered IRR series
      DSCRChart.tsx         # Bar chart: annual DSCR vs. covenant floor
      RevenueStackChart.tsx # Stacked bar: grid savings vs. DPPA revenue by year
      DispatchPreview.tsx   # Optional: 24h SoC + dispatch profile (sample week)
    common/
      InputSlider.tsx       # Numeric slider with unit label
      ToggleSwitch.tsx      # Boolean flags (BESS enabled, DPPA active)
      SectionAccordion.tsx  # Collapsible input groups
  hooks/
    useSimulation.ts        # Wraps API call; returns { results, isLoading, error }
    useInputValidation.ts   # Zod schema validation for all parameters
  types/
    simulation.ts           # TypeScript types mirroring Python SimulationResult
    inputs.ts               # InputParams type with all ~30 named ranges
  api/
    client.ts               # fetch wrapper targeting /api/simulate endpoint
```

---

## 4. Data Flow

```
User Input (React state)
        |
        v
useInputValidation (Zod) --> validation errors shown inline
        |
        v
[Run Simulation button]
        |
        v
useSimulation hook
  --> POST /api/simulate { params }
        |
        v
Python re_storage engine
  (physics -> settlement -> aggregation -> financial)
        |
        v
SimulationResult JSON
  {
    kpis: { project_irr, equity_irr, unlevered_irr, npv, payback_years, dscr_min },
    annual: [ { year, revenue, opex, ebitda, debt_service, dscr, cf_equity } x25 ],
    lifetime: { solar_mwh_by_year, bess_mwh_by_year },
    dispatch_sample: { hourly_soc, hourly_pv, hourly_load } // 1 week sample
  }
        |
        v
ResultsPane renders KPICards + Charts
```

---

## 5. Input Panel: Parameter Groups

Mirror the model's `Assumption` sheet structure as accordion sections:

### Section 1 — Site & System
- [ ] Map selector (lat/lng from Leaflet, same as POC)
- [ ] Solar capacity (kWp) — slider + text input
- [ ] BESS capacity (kWh) + power (kW) — conditional on BESS toggle
- [ ] COD date

### Section 2 — Battery Dispatch
- [ ] Strategy mode: Arbitrage | Peak Shaving (radio)
- [ ] PV-to-BESS mode: Time Window | Pre-charge Target (conditional)
- [ ] Charge window start/end hours
- [ ] PV divert share (%)
- [ ] Demand reduction target (% for peak shaving mode)

### Section 3 — DPPA / Revenue
- [ ] DPPA toggle (enable/disable)
- [ ] Strike price (VND/kWh)
- [ ] k-factor, Kpp, PCL, CDPPAdv (collapsible advanced)

### Section 4 — Financial Structure
- [ ] Debt/equity ratio (%)
- [ ] Interest rate (%)
- [ ] Loan tenor (years)
- [ ] DSCR covenant floor
- [ ] MRA contribution (% of CFADS)
- [ ] Discount rate (% for NPV)

### Section 5 — Cost Assumptions
- [ ] CapEx ($/kWp)
- [ ] O&M (% of CapEx/yr)
- [ ] Battery replacement cycle (years)
- [ ] Exchange rate (USD/VND)

---

## 6. Output Panel: KPI Cards + Chart Tabs

### KPI Row (top of results pane)
| Card | Value | Source |
|------|-------|--------|
| Project IRR | % | `kpis.project_irr` |
| Equity IRR | % | `kpis.equity_irr` |
| NPV | USD / VND | `kpis.npv` |
| Payback | years | `kpis.payback_years` |
| Min DSCR | x | `kpis.dscr_min` |
| Unlevered IRR | % | `kpis.unlevered_irr` |

### Chart Tabs
1. **Cash Flow** — Cumulative cash flow (project + equity) with break-even reference line (mirrors POC LineChart)
2. **DSCR** — Annual DSCR bar chart with covenant floor line
3. **Revenue Stack** — Stacked bar: DPPA revenue vs. grid savings vs. demand savings per year
4. **Generation** — Solar MWh + BESS MWh by year (with degradation visible)
5. **Dispatch Preview** *(optional v2)* — 7-day hourly SoC + PV + load area chart

---

## 7. Implementation Phases

### Phase 1 — Scaffold & Static Shell
- [ ] `npm create vite@latest web -- --template react-ts` inside `RE-storage-model/web/`
- [ ] Install: `tailwindcss`, `recharts`, `leaflet`, `react-leaflet`, `lucide-react`, `@tanstack/react-query`, `zod`
- [ ] Port `AppShell`, `Sidebar`, `ResultsPane` layout from POC two-column pattern
- [ ] Port `MapSelector` from POC (Leaflet CDN icon fix included)
- [ ] Wire `KPICard` and `CashFlowChart` with hardcoded mock data to validate layout

### Phase 2 — Input Forms
- [ ] Define `InputParams` TypeScript type covering all ~30 parameters
- [ ] Define Zod validation schema in `useInputValidation`
- [ ] Build `SystemParams`, `BatteryDispatch`, `DPPAParams`, `FinancialParams`, `CostParams` form sections
- [ ] Implement accordion collapse/expand with `SectionAccordion`
- [ ] Real-time validation feedback (red border + message on invalid fields)

### Phase 3 — API Integration
- [ ] Expose Python `re_storage` engine via FastAPI (`/api/simulate` POST endpoint) for local dev
- [ ] Define `SimulationResult` response TypeScript type
- [ ] Implement `api/client.ts` and `useSimulation` hook with loading/error states
- [ ] Replace mock data with live API results

### Phase 4 — Full Chart Suite
- [ ] `DSCRChart` (bar + covenant line)
- [ ] `RevenueStackChart` (stacked bar, DPPA vs grid savings)
- [ ] `GenerationChart` (dual line: solar + BESS MWh with degradation curve)
- [ ] Currency toggle (USD / VND) on all monetary KPIs

### Phase 5 — Polish & Deploy
- [ ] Scenario comparison: save up to 3 input sets, overlay results on charts
- [ ] Export: download results as CSV or PDF summary
- [ ] Mobile responsive audit (single-column stacked layout below md breakpoint)
- [ ] Deploy to Firebase Hosting alongside existing Firebase Functions backend

---

## 8. Key Decisions to Confirm

1. **API surface**: Should the frontend call a new FastAPI server, or use the existing Firebase Functions setup in `web/functions/`? The `.venv` under `web/functions/` suggests Firebase Functions is already scaffolded — preference to use that.

2. **Computation location**: For large parameter sweeps, keep full 8760-hour simulation server-side. For quick sensitivity sliders (discount rate, CapEx), consider a lightweight in-browser approximation (like the POC) so UI feels instant.

3. **DPPA toggle UX**: When DPPA is disabled, hide Section 3 entirely or gray it out? Graying out (disabled inputs) is safer to avoid surprising users who forget to re-enable it.

4. **Currency display**: Default to VND (project is Vietnam-based) with a toggle to USD. Use `Intl.NumberFormat` as the POC does.

5. **Dispatch preview scope**: Full 8760-row hourly data is large. Recommend the API return only a configurable sample week (e.g., peak-week or first-week-of-each-season) for the dispatch chart.

---

## 9. Files to Create

```
RE-storage-model/
  web/
    index.html
    vite.config.ts
    tsconfig.json
    package.json
    src/
      main.tsx
      App.tsx
      index.css
      components/  (see Section 3)
      hooks/
      types/
      api/
  plans/
    frontend-alignment-poc.md   <-- this file
```

---

## 10. Out of Scope (for this phase)

- Authentication / multi-user project saving
- Excel export (replaces the current .xlsx model)
- Real-time PVsyst data import
- Automated DSCR GoalSeek (the Python engine handles this server-side)

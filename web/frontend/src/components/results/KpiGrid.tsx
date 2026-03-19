import type { ModelKpis } from "../../types/model";
import { formatNumber, formatPercent, formatUsd } from "../../utils/formatters";
import { KpiCard } from "./KpiCard";

interface KpiGridProps {
  kpis: ModelKpis;
}

export function KpiGrid({ kpis }: KpiGridProps): JSX.Element {
  return (
    <section className="kpi-grid">
      <KpiCard label="Project IRR" value={formatPercent(kpis.project_irr)} />
      <KpiCard label="Equity IRR" value={formatPercent(kpis.equity_irr)} />
      <KpiCard label="Unlevered IRR" value={formatPercent(kpis.unlevered_irr)} />
      <KpiCard label="NPV" value={formatUsd(kpis.npv_usd)} />
      <KpiCard label="DSCR Min" value={formatNumber(kpis.dscr_min, 3)} />
      <KpiCard label="DSCR Avg" value={formatNumber(kpis.dscr_avg, 3)} />
      <KpiCard label="Debt Sized" value={formatUsd(kpis.debt_amount_usd)} />
      <KpiCard label="Year 1 Solar (MWh)" value={formatNumber(kpis.year1_solar_generation_mwh, 2)} />
      <KpiCard label="Year 1 DPPA Revenue" value={formatUsd(kpis.year1_dppa_revenue_usd)} />
      <KpiCard label="Year 1 Grid Savings" value={formatUsd(kpis.year1_grid_savings_usd)} />
    </section>
  );
}

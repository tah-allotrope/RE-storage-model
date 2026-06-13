import type { ModelKpis } from "../../types/model";
import { formatCurrency, formatNumber, formatPercent, type CurrencyCode } from "../../utils/formatters";
import { KpiCard } from "./KpiCard";

interface KpiGridProps {
  kpis: ModelKpis;
  currency: CurrencyCode;
  exchangeRate: number;
}

export function KpiGrid({ kpis, currency, exchangeRate }: KpiGridProps): JSX.Element {
  const isTwoComponent = kpis.tariff_mode === "2-component";
  return (
    <section className="kpi-grid">
      <KpiCard label="Project IRR" value={formatPercent(kpis.project_irr)} />
      <KpiCard label="Equity IRR" value={formatPercent(kpis.equity_irr)} />
      <KpiCard label="Unlevered IRR" value={formatPercent(kpis.unlevered_irr)} />
      <KpiCard label={`NPV (${currency})`} value={formatCurrency(kpis.npv_usd, currency, exchangeRate)} />
      <KpiCard label="DSCR Min" value={formatNumber(kpis.dscr_min, 3)} />
      <KpiCard label="DSCR Avg" value={formatNumber(kpis.dscr_avg, 3)} />
      <KpiCard label={`Debt Sized (${currency})`} value={formatCurrency(kpis.debt_amount_usd, currency, exchangeRate)} />
      <KpiCard label="Year 1 Solar (MWh)" value={formatNumber(kpis.year1_solar_generation_mwh, 2)} />
      <KpiCard label={`Year 1 DPPA (${currency})`} value={formatCurrency(kpis.year1_dppa_revenue_usd, currency, exchangeRate)} />
      <KpiCard label={`Year 1 Grid Savings (${currency})`} value={formatCurrency(kpis.year1_grid_savings_usd, currency, exchangeRate)} />
      {isTwoComponent ? (
        <KpiCard
          label={`Year 1 Demand Charge Savings (${currency})`}
          value={formatCurrency(kpis.demand_charge_savings_usd ?? null, currency, exchangeRate)}
        />
      ) : null}
    </section>
  );
}

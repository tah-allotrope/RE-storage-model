import { useMemo, useState } from "react";

import type { ModelResponse } from "../../types/model";
import { currencyLabel, type CurrencyCode, formatCurrency, formatNumber } from "../../utils/formatters";
import { BatteryCapacityChart } from "./BatteryCapacityChart";
import { CashFlowChart } from "./CashFlowChart";
import { DispatchPreviewChart } from "./DispatchPreviewChart";
import { DscrChart } from "./DscrChart";
import { GenerationChart } from "./GenerationChart";
import { KpiGrid } from "./KpiGrid";
import { LifetimeRevenueChart } from "./LifetimeRevenueChart";

interface ResultsDashboardProps {
  result: ModelResponse;
}

function downloadJson(result: ModelResponse): void {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "re-storage-results.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ResultsDashboard({ result }: ResultsDashboardProps): JSX.Element {
  const [currency, setCurrency] = useState<CurrencyCode>("USD");
  const exchangeRate = 26000;

  const firstAnnualRow = result.annual[0] ?? null;
  const dispatchHours = result.dispatch_sample.length;

  const overviewStats = useMemo(
    () => [
      {
        label: `Year 1 EBITDA (${currencyLabel(currency)})`,
        value: formatCurrency(firstAnnualRow?.ebitda_usd ?? null, currency, exchangeRate),
      },
      {
        label: `Year 1 CFADS (${currencyLabel(currency)})`,
        value: formatCurrency(firstAnnualRow?.cfads_usd ?? null, currency, exchangeRate),
      },
      {
        label: "Dispatch Sample",
        value: dispatchHours > 0 ? `${dispatchHours} hrs` : "Unavailable",
      },
      {
        label: "DSCR Points",
        value: formatNumber(result.dscr_series.filter((row) => row.dscr !== null).length, 0),
      },
    ],
    [currency, dispatchHours, firstAnnualRow?.cfads_usd, firstAnnualRow?.ebitda_usd, result.dscr_series],
  );

  return (
    <section className="results-shell results-dashboard">
      <div className="results-heading">
        <div>
          <p className="workspace-kicker">Run Complete</p>
          <h3>Results dashboard</h3>
        </div>
        <div className="currency-toggle-group" role="group" aria-label="Currency toggle">
          <button
            type="button"
            className={currency === "USD" ? "currency-toggle currency-toggle-active" : "currency-toggle"}
            onClick={() => setCurrency("USD")}
          >
            USD
          </button>
          <button
            type="button"
            className={currency === "VND" ? "currency-toggle currency-toggle-active" : "currency-toggle"}
            onClick={() => setCurrency("VND")}
          >
            VND
          </button>
        </div>
      </div>

      <KpiGrid kpis={result.kpis} currency={currency} exchangeRate={exchangeRate} />

      <section className="data-highlights-grid">
        {overviewStats.map((stat) => (
          <div key={stat.label} className="data-highlight-card">
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
          </div>
        ))}
      </section>

      <div className="charts-grid">
        <CashFlowChart rows={result.cashflow} currency={currency} exchangeRate={exchangeRate} />
        <DscrChart rows={result.dscr_series} covenantFloor={1.3} />
        <LifetimeRevenueChart rows={result.annual} currency={currency} exchangeRate={exchangeRate} />
        <GenerationChart rows={result.lifetime} />
        <BatteryCapacityChart rows={result.lifetime} />
      </div>

      <DispatchPreviewChart rows={result.dispatch_sample} />

      <div className="results-actions">
        <button className="secondary-button" type="button" onClick={() => downloadJson(result)}>
          Download JSON Results
        </button>
      </div>
    </section>
  );
}

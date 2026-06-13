import type { CurrencyCode } from "../../utils/formatters";
import { formatCurrency, formatPercent } from "../../utils/formatters";
import type { TariffModeComparisonResponse, TariffModeKpis } from "../../types/model";

interface TariffModeComparisonProps {
  comparison: TariffModeComparisonResponse;
  currency: CurrencyCode;
  exchangeRate: number;
}

interface Row {
  label: string;
  format: (value: number | null | undefined) => string;
  key: keyof TariffModeKpis;
}

function buildRows(currency: CurrencyCode, exchangeRate: number): Row[] {
  const money = (value: number | null | undefined): string =>
    formatCurrency(value ?? null, currency, exchangeRate);
  return [
    { label: "Project IRR", key: "project_irr", format: (value) => formatPercent(value ?? null) },
    { label: "Equity IRR", key: "equity_irr", format: (value) => formatPercent(value ?? null) },
    { label: `NPV (${currency})`, key: "npv_usd", format: money },
    { label: `Year 1 Grid Savings (${currency})`, key: "year1_grid_savings_usd", format: money },
    {
      label: `Year 1 Demand Charge Savings (${currency})`,
      key: "demand_charge_savings_usd",
      format: money,
    },
  ];
}

function renderCell(row: Row, kpis: TariffModeKpis | undefined): string {
  if (!kpis) {
    return "-";
  }
  if (kpis.error) {
    return `error: ${kpis.error}`;
  }
  const value = kpis[row.key] as number | null | undefined;
  return row.format(value);
}

export function TariffModeComparison({
  comparison,
  currency,
  exchangeRate,
}: TariffModeComparisonProps): JSX.Element {
  const oneComponent = comparison["1-component"];
  const twoComponent = comparison["2-component"];
  const delta = comparison.delta;
  const rows = buildRows(currency, exchangeRate);

  return (
    <section className="chart-card chart-card-wide analysis-card">
      <div className="analysis-card-header">
        <div>
          <h3>Tariff Mode Comparison</h3>
          <p className="panel-description">
            One-component (energy only) vs two-component (Ca energy + Cp demand charge under Decree
            146/2025). The delta column is 2-component minus 1-component for each headline KPI -
            negative grid-savings + positive demand-charge-savings is the expected trade-off.
          </p>
        </div>
      </div>

      <div className="table-shell">
        <table className="analysis-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>1-component</th>
              <th>2-component</th>
              <th>Delta (2C - 1C)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key as string}>
                <td>
                  <strong>{row.label}</strong>
                </td>
                <td>{renderCell(row, oneComponent)}</td>
                <td>{renderCell(row, twoComponent)}</td>
                <td>{renderCell(row, delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

import type { ScenarioComparisonResponse } from "../../types/model";
import {
  formatCurrency,
  formatPercent,
  type CurrencyCode,
} from "../../utils/formatters";

interface ScenarioComparisonTableProps {
  comparison: ScenarioComparisonResponse | null;
  currency: CurrencyCode;
  exchangeRate: number;
}

const OPTION_ORDER = ["1", "2", "3", "4"];

export function ScenarioComparisonTable({
  comparison,
  currency,
  exchangeRate,
}: ScenarioComparisonTableProps): JSX.Element {
  const rows = OPTION_ORDER.map((option) => comparison?.scenarios[option]).filter(
    (row): row is NonNullable<typeof row> => row !== undefined,
  );

  return (
    <section className="chart-card chart-card-wide analysis-card">
      <div className="analysis-card-header">
        <div>
          <h3>Scenario Comparison</h3>
          <p className="panel-description">
            Compare all four PPA paths against the same structured-form input set.
          </p>
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="panel-description">Run scenario comparison to populate the side-by-side option table.</p>
      ) : (
        <div className="table-shell">
          <table className="analysis-table">
            <thead>
              <tr>
                <th>Option</th>
                <th>Project IRR</th>
                <th>Equity IRR</th>
                <th>NPV</th>
                <th>Year 1 Revenue</th>
                <th>Year 1 Grid Savings</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.ppa_option ?? row.ppa_label ?? "unknown"}>
                  <td>
                    <strong>{row.ppa_label ?? `Option ${row.ppa_option ?? "?"}`}</strong>
                  </td>
                  <td>{formatPercent(row.project_irr ?? null)}</td>
                  <td>{formatPercent(row.equity_irr ?? null)}</td>
                  <td>{formatCurrency(row.npv_usd ?? null, currency, exchangeRate)}</td>
                  <td>{formatCurrency(row.year1_dppa_revenue_usd ?? null, currency, exchangeRate)}</td>
                  <td>{formatCurrency(row.year1_grid_savings_usd ?? null, currency, exchangeRate)}</td>
                  <td>{row.error ?? "OK"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

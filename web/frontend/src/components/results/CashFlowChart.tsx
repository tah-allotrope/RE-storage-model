import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CashflowRow } from "../../types/model";
import {
  convertCurrency,
  currencyLabel,
  formatCurrency,
  formatCurrencyAxis,
  type CurrencyCode,
} from "../../utils/formatters";

interface CashFlowChartProps {
  rows: CashflowRow[];
  currency: CurrencyCode;
  exchangeRate: number;
}

export function CashFlowChart({ rows, currency, exchangeRate }: CashFlowChartProps): JSX.Element {
  let cumulativeProject = 0;
  let cumulativeEquity = 0;

  const chartRows = rows.map((row) => {
    const projectDelta = (row.ebitda_usd ?? 0) - (row.capex_usd ?? 0);
    const equityDelta = row.free_cash_flow_to_equity_usd ?? 0;

    cumulativeProject += projectDelta;
    cumulativeEquity += equityDelta;

    return {
      year: row.year,
      cumulative_project_display: convertCurrency(cumulativeProject, currency, exchangeRate),
      cumulative_equity_display: convertCurrency(cumulativeEquity, currency, exchangeRate),
    };
  });

  function formatTooltipValue(value: string | number | Array<string | number> | null): string {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value !== "number") {
      return String(value ?? "N/A");
    }

    return formatCurrency(value, currency);
  }

  return (
    <section className="chart-card">
      <h3>Cash Flow ({currencyLabel(currency)})</h3>
      {chartRows.length === 0 ? (
        <p className="panel-description">No annual cash-flow rows are available for this run.</p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis tickFormatter={(value: number) => formatCurrencyAxis(value, currency)} />
            <Tooltip formatter={formatTooltipValue} />
            <Legend />
            <Line type="monotone" dataKey="cumulative_project_display" stroke="#144b59" strokeWidth={2} dot={false} name="Cumulative Project" />
            <Line type="monotone" dataKey="cumulative_equity_display" stroke="#bc6c25" strokeWidth={2} dot={false} name="Cumulative Equity" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}

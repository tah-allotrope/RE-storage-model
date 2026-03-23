import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnnualRow } from "../../types/model";
import {
  convertCurrency,
  currencyLabel,
  formatCurrency,
  formatCurrencyAxis,
  type CurrencyCode,
} from "../../utils/formatters";

interface LifetimeRevenueChartProps {
  rows: AnnualRow[];
  currency: CurrencyCode;
  exchangeRate: number;
}

export function LifetimeRevenueChart({ rows, currency, exchangeRate }: LifetimeRevenueChartProps): JSX.Element {
  const chartRows = rows.map((row) => ({
    ...row,
    dppa_revenue_display: convertCurrency(row.dppa_revenue_usd, currency, exchangeRate),
    grid_savings_display: convertCurrency(row.grid_savings_usd, currency, exchangeRate),
    demand_charge_display: convertCurrency(row.demand_charge_savings_usd, currency, exchangeRate),
  }));

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
      <h3>Revenue Stack ({currencyLabel(currency)})</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartRows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis tickFormatter={(value: number) => formatCurrencyAxis(value, currency)} />
          <Tooltip formatter={formatTooltipValue} />
          <Legend />
          <Bar dataKey="dppa_revenue_display" stackId="a" fill="#1f7a8c" name="DPPA" />
          <Bar dataKey="grid_savings_display" stackId="a" fill="#bfdbf7" name="Grid Savings" />
          <Bar dataKey="demand_charge_display" stackId="a" fill="#bc6c25" name="Demand Savings" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

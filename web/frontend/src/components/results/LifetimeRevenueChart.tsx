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

import type { LifetimeRow } from "../../types/model";

interface LifetimeRevenueChartProps {
  rows: LifetimeRow[];
}

export function LifetimeRevenueChart({ rows }: LifetimeRevenueChartProps): JSX.Element {
  return (
    <section className="chart-card">
      <h3>25-Year Annual Revenue</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="dppa_revenue_usd" stackId="a" fill="#1f7a8c" name="DPPA" />
          <Bar dataKey="grid_savings_usd" stackId="a" fill="#bfdbf7" name="Grid Savings" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

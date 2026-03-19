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

import type { LifetimeRow } from "../../types/model";

interface GenerationChartProps {
  rows: LifetimeRow[];
}

export function GenerationChart({ rows }: GenerationChartProps): JSX.Element {
  return (
    <section className="chart-card">
      <h3>25-Year Solar Generation</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="generation_mwh"
            stroke="#204b57"
            strokeWidth={2}
            dot={false}
            name="Generation (MWh)"
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

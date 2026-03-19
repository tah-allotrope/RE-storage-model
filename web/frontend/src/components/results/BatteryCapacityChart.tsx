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

interface BatteryCapacityChartProps {
  rows: LifetimeRow[];
}

export function BatteryCapacityChart({ rows }: BatteryCapacityChartProps): JSX.Element {
  return (
    <section className="chart-card">
      <h3>25-Year Battery Capacity</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="battery_capacity_kwh"
            stroke="#bc6c25"
            strokeWidth={2}
            dot={false}
            name="Battery Capacity (kWh)"
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

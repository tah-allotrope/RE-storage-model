import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DispatchSampleRow } from "../../types/model";
import { formatNumber } from "../../utils/formatters";

interface DispatchPreviewChartProps {
  rows: DispatchSampleRow[];
}

function shortLabel(value: string | null): string {
  if (value === null) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
}

export function DispatchPreviewChart({ rows }: DispatchPreviewChartProps): JSX.Element {
  const chartRows = rows.map((row) => ({
    ...row,
    label: shortLabel(row.datetime),
  }));

  function formatTooltipValue(value: string | number | Array<string | number> | null): string {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value !== "number") {
      return String(value ?? "N/A");
    }

    return formatNumber(value, 2);
  }

  return (
    <section className="chart-card chart-card-wide">
      <h3>Dispatch Preview (First Week)</h3>
      {chartRows.length === 0 ? (
        <p className="panel-description">No dispatch sample is available for this run.</p>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" minTickGap={36} />
            <YAxis tickFormatter={(value: number) => formatNumber(value, 0)} />
            <Tooltip formatter={formatTooltipValue} />
            <Legend />
            <Area type="monotone" dataKey="soc_kwh" stroke="#bc6c25" fill="#f4d4b7" name="SoC (kWh)" />
            <Line type="monotone" dataKey="solar_gen_kw" stroke="#1f7a8c" dot={false} name="Solar (kW)" />
            <Line type="monotone" dataKey="load_kw" stroke="#144b59" dot={false} name="Load (kW)" />
            <Line type="monotone" dataKey="discharged_kw" stroke="#9f2f2f" dot={false} name="Discharge (kW)" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}

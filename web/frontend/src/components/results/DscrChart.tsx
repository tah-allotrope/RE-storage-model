import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DscrRow } from "../../types/model";
import { formatNumber } from "../../utils/formatters";

interface DscrChartProps {
  rows: DscrRow[];
  covenantFloor: number | null;
}

export function DscrChart({ rows, covenantFloor }: DscrChartProps): JSX.Element {
  const chartRows = rows
    .filter((row) => row.dscr !== null)
    .map((row) => ({
      ...row,
      covenant_floor: covenantFloor,
    }));

  function formatTooltipValue(value: string | number | Array<string | number> | null): string {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value !== "number") {
      return String(value ?? "N/A");
    }

    return formatNumber(value, 3);
  }

  return (
    <section className="chart-card">
      <h3>Annual DSCR</h3>
      {chartRows.length === 0 ? (
        <p className="panel-description">No DSCR series is available for this run.</p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis tickFormatter={(value: number) => formatNumber(value, 2)} />
            <Tooltip formatter={formatTooltipValue} />
            <Legend />
            <Bar dataKey="dscr" fill="#1f7a8c" name="DSCR" />
            {covenantFloor !== null ? <Line type="monotone" dataKey="covenant_floor" stroke="#9f2f2f" dot={false} name="Covenant Floor" /> : null}
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}

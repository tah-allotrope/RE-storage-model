import { useMemo } from "react";

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

import type { SensitivityResponse } from "../../types/model";
import {
  formatCurrency,
  formatCurrencyAxis,
  formatNumber,
  formatPercent,
  type CurrencyCode,
} from "../../utils/formatters";

interface SensitivityPanelProps {
  sensitivity: SensitivityResponse | null;
  selectedVariable: string;
  currency: CurrencyCode;
  exchangeRate: number;
  isRunning: boolean;
  onChangeVariable: (value: string) => void;
  onRun: () => void;
  disabled: boolean;
}

const VARIABLE_OPTIONS = [
  { value: "strike_price_vnd", label: "Strike price" },
  { value: "bundled_discount_pct", label: "Bundled discount" },
  { value: "pv_discount_pct", label: "PV discount" },
  { value: "bess_discount_pct", label: "BESS discount" },
  { value: "fixed_ppa_price_usd_per_mwh", label: "Fixed PPA price" },
  { value: "interest_rate_pct", label: "Interest rate" },
  { value: "max_leverage_ratio", label: "Max leverage" },
  { value: "revenue_escalation_pct", label: "Revenue escalation" },
  { value: "opex_escalation_pct", label: "OPEX escalation" },
  { value: "fmp_descent_pct", label: "FMP descent" },
  { value: "pv_capex_usd_per_mwp", label: "Solar CAPEX" },
  { value: "bess_capex_usd_per_mwh", label: "BESS CAPEX" },
];

export function SensitivityPanel({
  sensitivity,
  selectedVariable,
  currency,
  exchangeRate,
  isRunning,
  onChangeVariable,
  onRun,
  disabled,
}: SensitivityPanelProps): JSX.Element {
  const chartRows = useMemo(
    () =>
      Object.entries(sensitivity?.results ?? {})
        .map(([paramValue, result]) => ({
          paramValue: Number(paramValue),
          project_irr: result.project_irr ?? null,
          equity_irr: result.equity_irr ?? null,
          npv_display: result.npv_usd ?? null,
        }))
        .sort((left, right) => left.paramValue - right.paramValue),
    [sensitivity],
  );

  function formatTooltipValue(value: string | number | Array<string | number> | null, name: string): string {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value !== "number") {
      return String(value ?? "N/A");
    }

    if (name.includes("NPV")) {
      return formatCurrency(value, currency, exchangeRate);
    }
    return formatPercent(value);
  }

  return (
    <section className="chart-card chart-card-wide analysis-card">
      <div className="analysis-card-header analysis-card-header-stack">
        <div>
          <h3>Sensitivity Analysis</h3>
          <p className="panel-description">
            Sweep one structured-form variable across a preset range and compare the IRR/NPV response.
          </p>
        </div>

        <div className="analysis-controls">
          <label>
            Variable
            <select value={selectedVariable} onChange={(event) => onChangeVariable(event.target.value)}>
              {VARIABLE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="secondary-button" onClick={onRun} disabled={disabled || isRunning}>
            {isRunning ? "Running..." : "Run Sensitivity"}
          </button>
        </div>
      </div>

      {chartRows.length === 0 ? (
        <p className="panel-description">Run a sensitivity sweep after a structured-form model run to populate this chart.</p>
      ) : (
        <>
          <div className="analysis-summary-grid">
            <div className="analysis-summary-card">
              <span>Variable</span>
              <strong>{sensitivity?.variable ?? selectedVariable}</strong>
            </div>
            <div className="analysis-summary-card">
              <span>Low IRR</span>
              <strong>{formatPercent(chartRows[0]?.project_irr ?? null)}</strong>
            </div>
            <div className="analysis-summary-card">
              <span>High IRR</span>
              <strong>{formatPercent(chartRows[chartRows.length - 1]?.project_irr ?? null)}</strong>
            </div>
            <div className="analysis-summary-card">
              <span>NPV Range</span>
              <strong>
                {formatCurrency(
                  (chartRows[chartRows.length - 1]?.npv_display ?? 0) - (chartRows[0]?.npv_display ?? 0),
                  currency,
                  exchangeRate,
                )}
              </strong>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="paramValue" tickFormatter={(value: number) => formatNumber(value, 2)} />
              <YAxis yAxisId="irr" orientation="left" tickFormatter={(value: number) => formatPercent(value)} />
              <YAxis
                yAxisId="npv"
                orientation="right"
                tickFormatter={(value: number) => formatCurrencyAxis(value, currency, exchangeRate)}
              />
              <Tooltip formatter={formatTooltipValue} labelFormatter={(value) => `Value: ${formatNumber(Number(value), 2)}`} />
              <Legend />
              <Line yAxisId="irr" type="monotone" dataKey="project_irr" stroke="#144b59" strokeWidth={2} dot />
              <Line yAxisId="irr" type="monotone" dataKey="equity_irr" stroke="#bc6c25" strokeWidth={2} dot />
              <Line yAxisId="npv" type="monotone" dataKey="npv_display" stroke="#1f7a8c" strokeWidth={2} dot={false} name="NPV" />
            </LineChart>
          </ResponsiveContainer>
        </>
      )}
    </section>
  );
}

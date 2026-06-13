import { useState } from "react";

import type { Verdict, VerdictOverall, VerdictStatus } from "../../types/model";

const OVERALL_CLASS: Record<VerdictOverall, string> = {
  GO: "verdict-go",
  CAUTION: "verdict-caution",
  "NO-GO": "verdict-nogo",
};

const STATUS_CLASS: Record<VerdictStatus, string> = {
  PASS: "verdict-chip-pass",
  MARGINAL: "verdict-chip-marginal",
  FAIL: "verdict-chip-fail",
};

type MetricKey = "equity_irr_status" | "dscr_status" | "npv_status" | "payback_status";

const METRICS: { key: MetricKey; label: string }[] = [
  { key: "equity_irr_status", label: "Equity IRR" },
  { key: "dscr_status", label: "Min DSCR" },
  { key: "npv_status", label: "NPV" },
  { key: "payback_status", label: "Payback" },
];

interface VerdictBannerProps {
  verdict?: Verdict | null;
}

export function VerdictBanner({ verdict }: VerdictBannerProps): JSX.Element | null {
  const [showDetails, setShowDetails] = useState(false);

  // Defensive: older responses (pre-GAP-01) carry no verdict.
  if (!verdict) {
    return null;
  }

  return (
    <section className={`verdict-banner ${OVERALL_CLASS[verdict.overall] ?? ""}`} aria-live="polite">
      <div className="verdict-headline">
        <div className="verdict-overall-block">
          <p className="workspace-kicker">Go / No-Go Assessment</p>
          <strong className="verdict-overall">{verdict.overall}</strong>
        </div>
        <div className="verdict-chips" role="list">
          {METRICS.map((metric) => {
            const status = verdict[metric.key];
            return (
              <span
                key={metric.key}
                role="listitem"
                className={`verdict-chip ${STATUS_CLASS[status] ?? ""}`}
              >
                {metric.label}: {status}
              </span>
            );
          })}
        </div>
      </div>

      {verdict.details.length > 0 ? (
        <div className="verdict-details">
          <button
            type="button"
            className="verdict-details-toggle"
            aria-expanded={showDetails}
            onClick={() => setShowDetails((open) => !open)}
          >
            {showDetails ? "Hide assessment detail" : "Show assessment detail"}
          </button>
          {showDetails ? (
            <ul>
              {verdict.details.map((detail) => (
                <li key={detail}>{detail}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

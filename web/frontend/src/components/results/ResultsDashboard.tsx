import type { ModelResponse } from "../../types/model";
import { BatteryCapacityChart } from "./BatteryCapacityChart";
import { GenerationChart } from "./GenerationChart";
import { KpiGrid } from "./KpiGrid";
import { LifetimeRevenueChart } from "./LifetimeRevenueChart";

interface ResultsDashboardProps {
  result: ModelResponse;
}

function downloadJson(result: ModelResponse): void {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "re-storage-results.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ResultsDashboard({ result }: ResultsDashboardProps): JSX.Element {
  return (
    <section className="results-shell">
      <h2>Results Dashboard</h2>
      <KpiGrid kpis={result.kpis} />
      <div className="charts-grid">
        <LifetimeRevenueChart rows={result.lifetime} />
        <GenerationChart rows={result.lifetime} />
        <BatteryCapacityChart rows={result.lifetime} />
      </div>
      <div className="results-actions">
        <button className="secondary-button" type="button" onClick={() => downloadJson(result)}>
          Download JSON Results
        </button>
      </div>
    </section>
  );
}

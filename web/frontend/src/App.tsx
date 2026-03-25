import { useState } from "react";

import { ExcelUploadTab } from "./components/inputs/ExcelUploadTab";
import { ProjectForm } from "./components/inputs/ProjectForm";
import { Layout } from "./components/layout/Layout";
import { ResultsDashboard } from "./components/results/ResultsDashboard";
import { ErrorBanner } from "./components/shared/ErrorBanner";
import { ProgressBar } from "./components/shared/ProgressBar";
import { useModelRun } from "./hooks/useModelRun";

type ActiveTab = "excel" | "form";

export default function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<ActiveTab>("excel");
  const {
    isRunning,
    error,
    result,
    scenarioComparison,
    sensitivity,
    lastStructuredRunReady,
    runWithExcel,
    runWithJson,
    runScenarioComparison,
    runSensitivityAnalysis,
  } = useModelRun();

  return (
    <Layout subtitle="Configure a model run on the left and review live outputs on the right.">
      <div className="workspace-shell">
        <section className="workspace-panel workspace-panel-inputs">
          <div className="workspace-header">
            <div>
              <p className="workspace-kicker">Input Workspace</p>
              <h2>Choose a run path</h2>
              <p className="workspace-copy">
                Keep the existing Excel shortcut for workbook users, or use the structured form for JSON + CSV runs.
              </p>
            </div>
          </div>

          <section className="tabs-row" role="tablist" aria-label="Input mode">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "excel"}
              className={activeTab === "excel" ? "tab-button tab-active" : "tab-button"}
              onClick={() => setActiveTab("excel")}
            >
              Upload Excel
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "form"}
              className={activeTab === "form" ? "tab-button tab-active" : "tab-button"}
              onClick={() => setActiveTab("form")}
            >
              Structured Form
            </button>
          </section>

          <div className="mode-summary">
            <div>
              <span className="mode-summary-label">Active mode</span>
              <strong>{activeTab === "excel" ? "Workbook upload" : "JSON + CSV form"}</strong>
            </div>
            <span className={result ? "status-pill status-pill-ready" : "status-pill"}>
              {result ? "Results loaded" : "Awaiting run"}
            </span>
          </div>

          {activeTab === "excel" ? (
            <ExcelUploadTab onRun={runWithExcel} isRunning={isRunning} />
          ) : (
            <ProjectForm isRunning={isRunning} onRun={runWithJson} />
          )}
        </section>

        <section className="workspace-panel workspace-panel-results">
          <div className="workspace-header workspace-header-results">
            <div>
              <p className="workspace-kicker">Results Workspace</p>
              <h2>Simulation outputs</h2>
              <p className="workspace-copy">
                KPI cards and charts update from the live backend response after each run.
              </p>
            </div>
          </div>

          {error ? <ErrorBanner message={error} /> : null}
          {isRunning ? <ProgressBar label="This usually takes 2-10 seconds." /> : null}

          {result ? (
            <ResultsDashboard
              result={result}
              scenarioComparison={scenarioComparison}
              sensitivity={sensitivity}
              canRunAnalysis={lastStructuredRunReady}
              isRunningAnalysis={isRunning}
              onRunScenarioComparison={runScenarioComparison}
              onRunSensitivity={runSensitivityAnalysis}
            />
          ) : (
            <section className="results-shell results-empty-state">
              <p className="workspace-kicker">Ready When You Are</p>
              <h3>No results yet</h3>
              <p className="panel-description">
                Start a run from the left panel to populate KPI cards, revenue charts, and generation views here.
              </p>
              <div className="empty-state-grid">
                <div className="empty-state-card">
                  <strong>Excel path</strong>
                  <span>Upload a workbook to run the existing spreadsheet-compatible flow.</span>
                </div>
                <div className="empty-state-card">
                  <strong>Structured path</strong>
                  <span>Use the form and hourly CSV to drive the JSON model endpoint.</span>
                </div>
              </div>
            </section>
          )}
        </section>
      </div>
    </Layout>
  );
}

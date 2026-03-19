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
  const { isRunning, error, result, runWithExcel, runWithJson } = useModelRun();

  return (
    <Layout subtitle="Run Excel uploads or structured JSON+CSV projects in-browser.">
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
          New Project Form
        </button>
      </section>

      {error ? <ErrorBanner message={error} /> : null}
      {isRunning ? <ProgressBar label="This usually takes 2-10 seconds." /> : null}

      {activeTab === "excel" ? (
        <ExcelUploadTab onRun={runWithExcel} isRunning={isRunning} />
      ) : (
        <ProjectForm isRunning={isRunning} onRun={runWithJson} />
      )}

      {result ? <ResultsDashboard result={result} /> : null}
    </Layout>
  );
}

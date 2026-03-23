import { useCallback, useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { DegradationStep } from "./DegradationStep";
import { DppaStep } from "./DppaStep";
import { FinancialStep } from "./FinancialStep";
import { HourlyDataStep } from "./HourlyDataStep";
import type { FieldErrors } from "./formValidation";
import { validateProjectForm } from "./formValidation";
import { defaultFormValues, type ProjectFormValues } from "./formTypes";
import { SystemStep } from "./SystemStep";

type SectionKey = "system" | "dppa" | "financial" | "degradation" | "hourly" | "review";

interface ProjectFormProps {
  isRunning: boolean;
  onRun: (formData: FormData) => Promise<void>;
}

interface CsvValidationSnapshot {
  rowCount: number;
  error: string | null;
  previewRows: string[];
}

interface SectionDefinition {
  key: SectionKey;
  title: string;
  description: string;
  fields: Array<keyof ProjectFormValues | "hourly_csv">;
}

const SECTIONS: SectionDefinition[] = [
  {
    key: "system",
    title: "Site & system",
    description: "Core PV and BESS operating assumptions.",
    fields: [
      "project_name",
      "actual_capacity_kwp",
      "simulation_capacity_kwp",
      "total_bess_kwh",
      "bess_power_rating_kw",
      "dod",
      "half_cycle_efficiency",
      "bess_enabled",
      "strategy_mode",
      "charging_mode",
      "charge_start_hour",
      "charge_end_hour",
      "min_direct_pv_share",
      "active_pv2bess_share",
      "precharge_target_soc_kwh",
      "precharge_target_hour",
    ],
  },
  {
    key: "dppa",
    title: "DPPA & tariff",
    description: "DPPA toggles, strike price, and tariff assumptions.",
    fields: [
      "dppa_enabled",
      "strike_price_vnd",
      "k_factor",
      "connection_voltage_kv",
      "kpp_22",
      "kpp_110",
      "tariff_off_peak",
      "tariff_standard",
      "tariff_peak",
    ],
  },
  {
    key: "financial",
    title: "Financial structure",
    description: "Foreign exchange, CAPEX, debt, and tenor assumptions.",
    fields: [
      "exchange_rate_usd_vnd",
      "solar_usd_per_mwp",
      "bess_usd_per_mwh",
      "base_rate",
      "debt_margin",
      "tenor_years",
      "target_dscr",
      "project_years",
      "financial_close_serial",
      "cod_excel_serial",
    ],
  },
  {
    key: "degradation",
    title: "Degradation",
    description: "Optional override for annual PV and BESS retention curves.",
    fields: ["degradation_json"],
  },
  {
    key: "hourly",
    title: "Hourly CSV",
    description: "Required 8760-row profile upload for the JSON model path.",
    fields: ["hourly_csv"],
  },
  {
    key: "review",
    title: "Review & run",
    description: "Check the key assumptions and run the model.",
    fields: [],
  },
];

function toFormData(values: ProjectFormValues, hourlyCsv: File): FormData {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => {
    if (value.trim() !== "") {
      form.append(key, value);
    }
  });
  form.append("hourly_csv", hourlyCsv);
  return form;
}

function sectionErrorCount(section: SectionDefinition, errors: FieldErrors): number {
  return section.fields.reduce((count, field) => count + (errors[field] ? 1 : 0), 0);
}

export function ProjectForm({ isRunning, onRun }: ProjectFormProps): JSX.Element {
  const [values, setValues] = useState<ProjectFormValues>(defaultFormValues);
  const [hourlyCsv, setHourlyCsv] = useState<File | null>(null);
  const [activeSection, setActiveSection] = useState<SectionKey>("system");
  const [showValidation, setShowValidation] = useState(false);
  const [csvState, setCsvState] = useState<CsvValidationSnapshot>({ rowCount: 0, error: null, previewRows: [] });

  const errors = useMemo(
    () =>
      validateProjectForm(values, {
        hasHourlyCsv: hourlyCsv !== null,
        csvError: csvState.error,
      }),
    [csvState.error, hourlyCsv, values],
  );

  const visibleErrors = showValidation ? errors : {};
  const totalErrorCount = Object.keys(errors).length;
  const canSubmit = totalErrorCount === 0 && hourlyCsv !== null && !isRunning;

  const reviewRows = useMemo(
    () => [
      ["Project", values.project_name || "(unnamed)"],
      ["Capacity (kWp)", values.actual_capacity_kwp],
      ["BESS enabled", values.bess_enabled === "true" ? "Yes" : "No"],
      ["DPPA enabled", values.dppa_enabled === "true" ? "Yes" : "No"],
      ["Project years", values.project_years],
      ["Hourly CSV", hourlyCsv?.name ?? "Not uploaded"],
    ],
    [hourlyCsv?.name, values.actual_capacity_kwp, values.bess_enabled, values.dppa_enabled, values.project_name, values.project_years],
  );

  const handleCsvValidationChange = useCallback((snapshot: CsvValidationSnapshot) => {
    setCsvState((current) => {
      if (
        current.rowCount === snapshot.rowCount &&
        current.error === snapshot.error &&
        current.previewRows.join("\n") === snapshot.previewRows.join("\n")
      ) {
        return current;
      }

      return snapshot;
    });
  }, []);

  function handleInputChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement>): void {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  function handleTextAreaChange(event: ChangeEvent<HTMLTextAreaElement>): void {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function submitRun(): Promise<void> {
    setShowValidation(true);

    if (hourlyCsv === null || Object.keys(errors).length > 0) {
      const firstInvalidSection = SECTIONS.find((section) => sectionErrorCount(section, errors) > 0);
      if (firstInvalidSection !== undefined) {
        setActiveSection(firstInvalidSection.key);
      }
      return;
    }

    await onRun(toFormData(values, hourlyCsv));
  }

  return (
    <section className="panel panel-input-surface grouped-form-shell">
      <div className="grouped-form-header">
        <div>
          <h3>Structured project form</h3>
          <p className="panel-description">
            Work section-by-section, validate inputs inline, and submit the same `FormData` contract used by the current JSON endpoint.
          </p>
        </div>
        <div className="status-pill-group">
          <span className="status-pill">{SECTIONS.length} sections</span>
          <span className={totalErrorCount > 0 && showValidation ? "status-pill status-pill-warning" : "status-pill"}>
            {showValidation && totalErrorCount > 0 ? `${totalErrorCount} issues to fix` : "Validation ready"}
          </span>
        </div>
      </div>

      <div className="grouped-form-layout">
        <aside className="section-nav" aria-label="Structured form sections">
          {SECTIONS.map((section) => {
            const errorCount = sectionErrorCount(section, errors);
            const isActive = activeSection === section.key;

            return (
              <button
                key={section.key}
                type="button"
                className={isActive ? "section-nav-item section-nav-item-active" : "section-nav-item"}
                onClick={() => setActiveSection(section.key)}
              >
                <span className="section-nav-title">{section.title}</span>
                <span className="section-nav-meta">
                  {showValidation && errorCount > 0 ? `${errorCount} issue${errorCount === 1 ? "" : "s"}` : section.description}
                </span>
              </button>
            );
          })}
        </aside>

        <div className="section-stack">
          {SECTIONS.map((section) => {
            const expanded = activeSection === section.key;
            const errorCount = sectionErrorCount(section, errors);

            return (
              <section key={section.key} className="section-card">
                <button
                  type="button"
                  className="section-card-header"
                  onClick={() => setActiveSection(section.key)}
                  aria-expanded={expanded}
                >
                  <div>
                    <h4>{section.title}</h4>
                    <p>{section.description}</p>
                  </div>
                  <div className="section-card-badges">
                    {showValidation && errorCount > 0 ? <span className="section-badge section-badge-error">{errorCount} issue{errorCount === 1 ? "" : "s"}</span> : null}
                    <span className="section-badge">{expanded ? "Open" : "Closed"}</span>
                  </div>
                </button>

                {expanded ? (
                  <div className="section-card-body">
                    {section.key === "system" ? <SystemStep values={values} onChange={handleInputChange} errors={visibleErrors} /> : null}
                    {section.key === "dppa" ? <DppaStep values={values} onChange={handleInputChange} errors={visibleErrors} /> : null}
                    {section.key === "financial" ? <FinancialStep values={values} onChange={handleInputChange} errors={visibleErrors} /> : null}
                    {section.key === "degradation" ? (
                      <DegradationStep values={values} onChange={handleTextAreaChange} errors={visibleErrors} />
                    ) : null}
                    {section.key === "hourly" ? (
                      <HourlyDataStep
                        file={hourlyCsv}
                        setFile={setHourlyCsv}
                        validationError={visibleErrors.hourly_csv}
                        onValidationChange={handleCsvValidationChange}
                      />
                    ) : null}
                    {section.key === "review" ? (
                      <div className="review-panel">
                        <div className="review-grid">
                          {reviewRows.map(([label, value]) => (
                            <div key={label} className="review-row">
                              <span>{label}</span>
                              <strong>{value}</strong>
                            </div>
                          ))}
                        </div>

                        {showValidation && totalErrorCount > 0 ? (
                          <div className="review-alert">
                            <strong>Fix the highlighted inputs before running the model.</strong>
                            <p className="panel-description">Use the section list to jump back to the fields with validation messages.</p>
                          </div>
                        ) : null}

                        <div className="panel-row">
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setShowValidation(true)}
                            disabled={isRunning}
                          >
                            Validate Inputs
                          </button>
                          <button type="button" className="primary-button" onClick={() => void submitRun()} disabled={!canSubmit}>
                            {isRunning ? "Running..." : "Run Model"}
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </section>
            );
          })}
        </div>
      </div>
    </section>
  );
}

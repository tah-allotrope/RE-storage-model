import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { DegradationStep } from "./DegradationStep";
import { DppaStep } from "./DppaStep";
import { FinancialStep } from "./FinancialStep";
import { HourlyDataStep } from "./HourlyDataStep";
import { SystemStep } from "./SystemStep";
import { defaultFormValues, type ProjectFormValues } from "./formTypes";

interface ProjectFormProps {
  isRunning: boolean;
  onRun: (formData: FormData) => Promise<void>;
}

type StepKey = "system" | "dppa" | "financial" | "degradation" | "hourly" | "review";

const STEPS: StepKey[] = ["system", "dppa", "financial", "degradation", "hourly", "review"];

function stepTitle(step: StepKey): string {
  switch (step) {
    case "system":
      return "System & BESS";
    case "dppa":
      return "DPPA & Tariff";
    case "financial":
      return "Financial";
    case "degradation":
      return "Degradation";
    case "hourly":
      return "Hourly CSV";
    case "review":
      return "Review & Run";
    default:
      return "Step";
  }
}

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

export function ProjectForm({ isRunning, onRun }: ProjectFormProps): JSX.Element {
  const [values, setValues] = useState<ProjectFormValues>(defaultFormValues);
  const [hourlyCsv, setHourlyCsv] = useState<File | null>(null);
  const [stepIndex, setStepIndex] = useState(0);

  const currentStep = STEPS[stepIndex];

  function handleInputChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement>): void {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  function handleTextAreaChange(event: ChangeEvent<HTMLTextAreaElement>): void {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  function nextStep(): void {
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  function previousStep(): void {
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  async function submitRun(): Promise<void> {
    if (hourlyCsv === null) {
      return;
    }
    await onRun(toFormData(values, hourlyCsv));
  }

  const reviewRows = useMemo(
    () => [
      ["Project", values.project_name || "(unnamed)"],
      ["Capacity (kWp)", values.actual_capacity_kwp],
      ["BESS (kWh)", values.total_bess_kwh],
      ["DPPA enabled", values.dppa_enabled],
      ["Project years", values.project_years],
      ["Hourly CSV", hourlyCsv?.name ?? "Not uploaded"],
    ],
    [hourlyCsv?.name, values.actual_capacity_kwp, values.dppa_enabled, values.project_name, values.project_years, values.total_bess_kwh],
  );

  return (
    <section className="panel">
      <h2>New Project Form</h2>
      <p className="panel-description">Step {stepIndex + 1} of {STEPS.length}: {stepTitle(currentStep)}</p>

      {currentStep === "system" ? <SystemStep values={values} onChange={handleInputChange} /> : null}
      {currentStep === "dppa" ? <DppaStep values={values} onChange={handleInputChange} /> : null}
      {currentStep === "financial" ? <FinancialStep values={values} onChange={handleInputChange} /> : null}
      {currentStep === "degradation" ? (
        <DegradationStep values={values} onChange={handleTextAreaChange} />
      ) : null}
      {currentStep === "hourly" ? <HourlyDataStep file={hourlyCsv} setFile={setHourlyCsv} /> : null}
      {currentStep === "review" ? (
        <div className="review-grid">
          {reviewRows.map(([label, value]) => (
            <div key={label} className="review-row">
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      ) : null}

      <div className="panel-row">
        <button type="button" className="secondary-button" onClick={previousStep} disabled={stepIndex === 0 || isRunning}>
          Back
        </button>
        {currentStep !== "review" ? (
          <button type="button" className="primary-button" onClick={nextStep} disabled={isRunning}>
            Next
          </button>
        ) : (
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              void submitRun();
            }}
            disabled={isRunning || hourlyCsv === null}
          >
            {isRunning ? "Running..." : "Run Model"}
          </button>
        )}
      </div>
    </section>
  );
}

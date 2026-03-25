import { useCallback, useState } from "react";

import { compareScenarios, runExcel, runJson, runSensitivity } from "../api/client";
import type {
  ModelResponse,
  ScenarioComparisonResponse,
  SensitivityResponse,
} from "../types/model";

const SENSITIVITY_PRESETS: Record<string, number[]> = {
  strike_price_vnd: [1600, 1700, 1800, 1900, 2000],
  bundled_discount_pct: [0.05, 0.1, 0.15, 0.2, 0.25],
  pv_discount_pct: [0.02, 0.04, 0.05, 0.06, 0.08],
  bess_discount_pct: [0.02, 0.04, 0.05, 0.06, 0.08],
  fixed_ppa_price_usd_per_mwh: [55, 65, 70, 75, 85],
  interest_rate_pct: [0.05, 0.06, 0.065, 0.075, 0.085],
  max_leverage_ratio: [0.5, 0.6, 0.7, 0.75, 0.8],
  revenue_escalation_pct: [0.02, 0.035, 0.05, 0.065, 0.08],
  opex_escalation_pct: [0.02, 0.03, 0.04, 0.05, 0.06],
  fmp_descent_pct: [-0.08, -0.06, -0.05, -0.04, -0.02],
  pv_capex_usd_per_mwp: [600000, 700000, 750000, 800000, 900000],
  bess_capex_usd_per_mwh: [160000, 180000, 200000, 220000, 240000],
};

function cloneFormData(formData: FormData): FormData {
  const copy = new FormData();
  formData.forEach((value, key) => {
    copy.append(key, value);
  });
  return copy;
}

function buildSensitivityFormData(baseFormData: FormData, variable: string): FormData {
  const formData = cloneFormData(baseFormData);
  formData.set("sensitivity_variable", variable);
  formData.set(
    "sensitivity_values",
    JSON.stringify(SENSITIVITY_PRESETS[variable] ?? [0.8, 0.9, 1.0, 1.1, 1.2]),
  );
  return formData;
}

interface UseModelRunResult {
  isRunning: boolean;
  error: string | null;
  result: ModelResponse | null;
  scenarioComparison: ScenarioComparisonResponse | null;
  sensitivity: SensitivityResponse | null;
  lastStructuredRunReady: boolean;
  runWithExcel: (file: File) => Promise<void>;
  runWithJson: (formData: FormData) => Promise<void>;
  runScenarioComparison: () => Promise<void>;
  runSensitivityAnalysis: (variable: string) => Promise<void>;
  clearError: () => void;
}

export function useModelRun(): UseModelRunResult {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModelResponse | null>(null);
  const [scenarioComparison, setScenarioComparison] = useState<ScenarioComparisonResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);
  const [lastStructuredRunFormData, setLastStructuredRunFormData] = useState<FormData | null>(null);

  const runWithExcel = useCallback(async (file: File) => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await runExcel(file);
      setResult(response);
      setScenarioComparison(null);
      setSensitivity(null);
      setLastStructuredRunFormData(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown run error";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const runWithJson = useCallback(async (formData: FormData) => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await runJson(formData);
      setResult(response);
      setScenarioComparison(null);
      setSensitivity(null);
      setLastStructuredRunFormData(cloneFormData(formData));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown run error";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const runScenarioComparison = useCallback(async () => {
    if (lastStructuredRunFormData === null) {
      setError("Run the structured form once before requesting scenario comparison.");
      return;
    }

    setIsRunning(true);
    setError(null);
    try {
      const response = await compareScenarios(cloneFormData(lastStructuredRunFormData));
      setScenarioComparison(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown scenario comparison error";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }, [lastStructuredRunFormData]);

  const runSensitivityAnalysis = useCallback(
    async (variable: string) => {
      if (lastStructuredRunFormData === null) {
        setError("Run the structured form once before requesting sensitivity analysis.");
        return;
      }

      setIsRunning(true);
      setError(null);
      try {
        const response = await runSensitivity(buildSensitivityFormData(lastStructuredRunFormData, variable));
        setSensitivity(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown sensitivity error";
        setError(message);
      } finally {
        setIsRunning(false);
      }
    },
    [lastStructuredRunFormData],
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    isRunning,
    error,
    result,
    scenarioComparison,
    sensitivity,
    lastStructuredRunReady: lastStructuredRunFormData !== null,
    runWithExcel,
    runWithJson,
    runScenarioComparison,
    runSensitivityAnalysis,
    clearError,
  };
}

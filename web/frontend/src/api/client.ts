import type {
  ModelResponse,
  ScenarioComparisonResponse,
  SensitivityResponse,
} from "../types/model";

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    const error = payload as { error?: string };
    throw new Error(error.error ?? "Model run failed");
  }
  return payload as T;
}

export async function runExcel(file: File): Promise<ModelResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/run-excel", {
    method: "POST",
    body: formData,
  });

  return parseResponse<ModelResponse>(response);
}

export async function runJson(formData: FormData): Promise<ModelResponse> {
  const response = await fetch("/api/run-json", {
    method: "POST",
    body: formData,
  });

  return parseResponse<ModelResponse>(response);
}

export async function compareScenarios(formData: FormData): Promise<ScenarioComparisonResponse> {
  const response = await fetch("/api/compare-scenarios", {
    method: "POST",
    body: formData,
  });

  return parseResponse<ScenarioComparisonResponse>(response);
}

export async function runSensitivity(formData: FormData): Promise<SensitivityResponse> {
  const response = await fetch("/api/run-sensitivity", {
    method: "POST",
    body: formData,
  });

  return parseResponse<SensitivityResponse>(response);
}

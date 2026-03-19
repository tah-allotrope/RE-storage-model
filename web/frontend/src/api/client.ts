import type { ModelResponse } from "../types/model";

async function parseResponse(response: Response): Promise<ModelResponse> {
  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    const error = payload as { error?: string };
    throw new Error(error.error ?? "Model run failed");
  }
  return payload as ModelResponse;
}

export async function runExcel(file: File): Promise<ModelResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/run-excel", {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}

export async function runJson(formData: FormData): Promise<ModelResponse> {
  const response = await fetch("/api/run-json", {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}

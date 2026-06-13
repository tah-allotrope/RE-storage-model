import type {
  ModelResponse,
  ScenarioComparisonResponse,
  SensitivityResponse,
  TariffModeComparisonResponse,
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

export async function compareTariffModes(
  formData: FormData,
): Promise<TariffModeComparisonResponse> {
  const response = await fetch("/api/compare-tariff-modes", {
    method: "POST",
    body: formData,
  });

  return parseResponse<TariffModeComparisonResponse>(response);
}

export interface DownloadResult {
  blob: Blob;
  filename: string;
}

function parseContentDispositionFilename(header: string | null): string | null {
  if (header === null) {
    return null;
  }
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header);
  return match ? decodeURIComponent(match[1].trim()) : null;
}

async function postForDownload(
  url: string,
  formData: FormData,
  fallbackFilename: string,
): Promise<DownloadResult> {
  const response = await fetch(url, { method: "POST", body: formData });
  if (!response.ok) {
    let message = `Download failed (${response.status})`;
    try {
      const payload = (await response.json()) as { error?: string };
      if (payload.error) {
        message = payload.error;
      }
    } catch {
      // Body wasn't JSON - keep the status-code message.
    }
    throw new Error(message);
  }

  const filename =
    parseContentDispositionFilename(response.headers.get("Content-Disposition")) ??
    fallbackFilename;
  const blob = await response.blob();
  return { blob, filename };
}

export async function downloadReport(formData: FormData): Promise<DownloadResult> {
  return postForDownload("/api/run-report", formData, "re-storage-report.html");
}

export async function downloadWorkbook(formData: FormData): Promise<DownloadResult> {
  return postForDownload("/api/export-workbook", formData, "re-storage-workbook.xlsx");
}

export function triggerBrowserDownload({ blob, filename }: DownloadResult): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

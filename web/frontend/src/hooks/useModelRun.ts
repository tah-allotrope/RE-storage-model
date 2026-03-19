import { useCallback, useState } from "react";

import { runExcel, runJson } from "../api/client";
import type { ModelResponse } from "../types/model";

interface UseModelRunResult {
  isRunning: boolean;
  error: string | null;
  result: ModelResponse | null;
  runWithExcel: (file: File) => Promise<void>;
  runWithJson: (formData: FormData) => Promise<void>;
  clearError: () => void;
}

export function useModelRun(): UseModelRunResult {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModelResponse | null>(null);

  const runWithExcel = useCallback(async (file: File) => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await runExcel(file);
      setResult(response);
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
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown run error";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    isRunning,
    error,
    result,
    runWithExcel,
    runWithJson,
    clearError,
  };
}

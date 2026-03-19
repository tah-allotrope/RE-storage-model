import { useCallback, useState } from "react";

interface CsvValidationResult {
  rowCount: number;
  error: string | null;
  previewRows: string[];
  validateCsv: (file: File) => Promise<boolean>;
}

export function useCsvValidation(): CsvValidationResult {
  const [rowCount, setRowCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewRows, setPreviewRows] = useState<string[]>([]);

  const validateCsv = useCallback(async (file: File): Promise<boolean> => {
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
    if (lines.length < 2) {
      setError("CSV must include a header and at least one data row.");
      setRowCount(0);
      setPreviewRows([]);
      return false;
    }

    const dataRows = lines.length - 1;
    setRowCount(dataRows);
    setPreviewRows(lines.slice(0, 6));

    if (dataRows !== 8760) {
      setError(`Expected 8760 data rows, got ${dataRows}.`);
      return false;
    }

    setError(null);
    return true;
  }, []);

  return { rowCount, error, previewRows, validateCsv };
}

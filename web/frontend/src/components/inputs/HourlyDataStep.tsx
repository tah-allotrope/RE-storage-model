import { useEffect, useState } from "react";

import { useCsvValidation } from "../../hooks/useCsvValidation";
import { FileDropzone } from "../shared/FileDropzone";

interface CsvValidationSnapshot {
  rowCount: number;
  error: string | null;
  previewRows: string[];
}

interface HourlyDataStepProps {
  file: File | null;
  setFile: (file: File | null) => void;
  validationError?: string;
  onValidationChange: (snapshot: CsvValidationSnapshot) => void;
}

export function HourlyDataStep({ file, setFile, validationError, onValidationChange }: HourlyDataStepProps): JSX.Element {
  const { rowCount, error, previewRows, validateCsv } = useCsvValidation();
  const [isChecking, setIsChecking] = useState(false);

  async function handleFile(nextFile: File): Promise<void> {
    setIsChecking(true);
    const ok = await validateCsv(nextFile);
    setFile(ok ? nextFile : null);
    setIsChecking(false);
  }

  const effectiveError = error ?? validationError ?? null;

  useEffect(() => {
    onValidationChange({ rowCount, error, previewRows });
  }, [error, onValidationChange, previewRows, rowCount]);

  return (
    <section>
      <FileDropzone
        label="Drop hourly CSV (8760 rows)"
        accept={{ "text/csv": [".csv"] }}
        onFile={(next) => {
          void handleFile(next);
        }}
      />
      <p className="form-note">Required columns: DateTime, SimulationProfile_kW, Irradiation_W/m2, Load_kW, FMP, CFMP.</p>
      <p className="form-note">Rows detected: {rowCount}</p>
      {isChecking ? <p className="form-note">Validating CSV...</p> : null}
      {effectiveError ? <p className="form-error">{effectiveError}</p> : null}
      {file ? <p className="form-note">Selected file: {file.name}</p> : null}
      {previewRows.length > 0 ? (
        <pre className="preview-box">{previewRows.join("\n")}</pre>
      ) : null}
    </section>
  );
}

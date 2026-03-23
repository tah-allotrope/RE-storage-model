import { useState } from "react";

import { FileDropzone } from "../shared/FileDropzone";

interface ExcelUploadTabProps {
  onRun: (file: File) => Promise<void>;
  isRunning: boolean;
}

export function ExcelUploadTab({ onRun, isRunning }: ExcelUploadTabProps): JSX.Element {
  const [file, setFile] = useState<File | null>(null);

  async function handleRun(): Promise<void> {
    if (file === null) {
      return;
    }
    await onRun(file);
  }

  return (
    <section className="panel panel-input-surface">
      <h3>Upload Excel workbook</h3>
      <p className="panel-description">
        Upload a model workbook with Assumption, Data Input, Loss, and Tariff Schedule sheets.
      </p>
      <FileDropzone
        label="Drop .xlsx file here"
        accept={{
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
        }}
        onFile={setFile}
      />
      <div className="panel-row">
        <span>{file ? `Selected: ${file.name}` : "No file selected"}</span>
        <button type="button" className="primary-button" onClick={handleRun} disabled={file === null || isRunning}>
          {isRunning ? "Running..." : "Run Model"}
        </button>
      </div>
    </section>
  );
}

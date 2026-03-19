import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface FileDropzoneProps {
  label: string;
  accept: Record<string, string[]>;
  onFile: (file: File) => void;
}

export function FileDropzone({ label, accept, onFile }: FileDropzoneProps): JSX.Element {
  const handleDrop = useCallback(
    (files: File[]) => {
      if (files.length > 0) {
        onFile(files[0]);
      }
    },
    [onFile],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    maxFiles: 1,
    onDrop: handleDrop,
  });

  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? "dropzone-active" : ""}`}>
      <input {...getInputProps()} />
      <p>{label}</p>
      <p className="dropzone-hint">Drag and drop or click to browse</p>
    </div>
  );
}

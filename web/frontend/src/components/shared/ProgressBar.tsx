interface ProgressBarProps {
  label?: string;
}

export function ProgressBar({ label = "Running model..." }: ProgressBarProps): JSX.Element {
  return (
    <div className="progress-shell" role="status" aria-live="polite">
      <div className="progress-label">{label}</div>
      <div className="progress-track">
        <div className="progress-indeterminate" />
      </div>
    </div>
  );
}

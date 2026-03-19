export function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function formatUsd(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) {
    return `${value < 0 ? "-" : ""}$${(absolute / 1_000_000).toFixed(2)}M`;
  }
  if (absolute >= 1_000) {
    return `${value < 0 ? "-" : ""}$${(absolute / 1_000).toFixed(1)}K`;
  }
  return `${value < 0 ? "-" : ""}$${absolute.toFixed(2)}`;
}

export function formatNumber(value: number | null, digits = 2): string {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export type CurrencyCode = "USD" | "VND";

const DEFAULT_USD_VND_RATE = 26000;

export function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function convertCurrency(
  value: number | null,
  currency: CurrencyCode,
  exchangeRate = DEFAULT_USD_VND_RATE,
): number | null {
  if (value === null || Number.isNaN(value)) {
    return null;
  }

  if (currency === "VND") {
    return value * exchangeRate;
  }

  return value;
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

export function formatVnd(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  const absolute = Math.abs(value);
  if (absolute >= 1_000_000_000) {
    return `${value < 0 ? "-" : ""}${(absolute / 1_000_000_000).toFixed(2)}B VND`;
  }
  if (absolute >= 1_000_000) {
    return `${value < 0 ? "-" : ""}${(absolute / 1_000_000).toFixed(1)}M VND`;
  }
  return `${value < 0 ? "-" : ""}${absolute.toFixed(0)} VND`;
}

export function formatCurrency(
  value: number | null,
  currency: CurrencyCode,
  exchangeRate = DEFAULT_USD_VND_RATE,
): string {
  const converted = convertCurrency(value, currency, exchangeRate);
  return currency === "VND" ? formatVnd(converted) : formatUsd(converted);
}

export function formatCurrencyAxis(
  value: number | null,
  currency: CurrencyCode,
  exchangeRate = DEFAULT_USD_VND_RATE,
): string {
  const converted = convertCurrency(value, currency, exchangeRate);
  if (converted === null) {
    return "N/A";
  }

  if (currency === "VND") {
    const absolute = Math.abs(converted);
    if (absolute >= 1_000_000_000) {
      return `${(converted / 1_000_000_000).toFixed(1)}B`;
    }
    if (absolute >= 1_000_000) {
      return `${(converted / 1_000_000).toFixed(1)}M`;
    }
    return converted.toFixed(0);
  }

  return formatUsd(converted);
}

export function currencyLabel(currency: CurrencyCode): string {
  return currency === "VND" ? "VND" : "USD";
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

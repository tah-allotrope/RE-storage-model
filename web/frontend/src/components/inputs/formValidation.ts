import type { ProjectFormValues } from "./formTypes";

export type FormFieldName = keyof ProjectFormValues | "hourly_csv";

export type FieldErrors = Partial<Record<FormFieldName, string>>;

interface ValidationContext {
  hasHourlyCsv: boolean;
  csvError: string | null;
}

function asNumber(value: string): number | null {
  if (value.trim() === "") {
    return null;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return null;
  }

  return parsed;
}

function validatePositive(errors: FieldErrors, field: FormFieldName, label: string, value: string): void {
  const parsed = asNumber(value);

  if (parsed === null || parsed <= 0) {
    errors[field] = `${label} must be greater than 0.`;
  }
}

function validateNonNegative(errors: FieldErrors, field: FormFieldName, label: string, value: string): void {
  const parsed = asNumber(value);

  if (parsed === null || parsed < 0) {
    errors[field] = `${label} cannot be negative.`;
  }
}

function validateHour(errors: FieldErrors, field: FormFieldName, label: string, value: string): void {
  const parsed = asNumber(value);

  if (parsed === null || parsed < 0 || parsed > 23) {
    errors[field] = `${label} must be between 0 and 23.`;
  }
}

function validateRatio(errors: FieldErrors, field: FormFieldName, label: string, value: string): void {
  const parsed = asNumber(value);

  if (parsed === null || parsed < 0 || parsed > 1) {
    errors[field] = `${label} must be between 0 and 1.`;
  }
}

export function validateProjectForm(
  values: ProjectFormValues,
  context: ValidationContext,
): FieldErrors {
  const errors: FieldErrors = {};
  const bessEnabled = values.bess_enabled === "true";
  const dppaEnabled = values.dppa_enabled === "true";

  validatePositive(errors, "actual_capacity_kwp", "Installed capacity", values.actual_capacity_kwp);
  validatePositive(errors, "simulation_capacity_kwp", "Simulation capacity", values.simulation_capacity_kwp);

  if (bessEnabled) {
    validatePositive(errors, "total_bess_kwh", "BESS storage", values.total_bess_kwh);
    validatePositive(errors, "bess_power_rating_kw", "BESS power rating", values.bess_power_rating_kw);
    validateRatio(errors, "dod", "Depth of discharge", values.dod);
    validateRatio(errors, "half_cycle_efficiency", "Half-cycle efficiency", values.half_cycle_efficiency);
    validateRatio(errors, "min_direct_pv_share", "Min PV direct-to-load share", values.min_direct_pv_share);
    validateRatio(errors, "active_pv2bess_share", "Active PV-to-BESS share", values.active_pv2bess_share);
    validateNonNegative(errors, "precharge_target_soc_kwh", "Precharge target SoC", values.precharge_target_soc_kwh);
    validateHour(errors, "precharge_target_hour", "Precharge target hour", values.precharge_target_hour);
    validateHour(errors, "charge_start_hour", "Charge start hour", values.charge_start_hour);
    validateHour(errors, "charge_end_hour", "Charge end hour", values.charge_end_hour);

    const startHour = asNumber(values.charge_start_hour);
    const endHour = asNumber(values.charge_end_hour);
    if (startHour !== null && endHour !== null && endHour < startHour) {
      errors.charge_end_hour = "Charge end hour must be later than or equal to the start hour.";
    }
  }

  if (dppaEnabled) {
    validatePositive(errors, "strike_price_vnd", "Strike price", values.strike_price_vnd);
    validatePositive(errors, "k_factor", "k-factor", values.k_factor);
    validatePositive(errors, "kpp_22", "Kpp 22kV", values.kpp_22);
    validatePositive(errors, "kpp_110", "Kpp 110kV", values.kpp_110);
  }

  validateNonNegative(errors, "tariff_off_peak", "Off-peak tariff", values.tariff_off_peak);
  validateNonNegative(errors, "tariff_standard", "Standard tariff", values.tariff_standard);
  validateNonNegative(errors, "tariff_peak", "Peak tariff", values.tariff_peak);

  validatePositive(errors, "exchange_rate_usd_vnd", "USD/VND exchange rate", values.exchange_rate_usd_vnd);
  validateNonNegative(errors, "solar_usd_per_mwp", "Solar CAPEX", values.solar_usd_per_mwp);
  validateNonNegative(errors, "base_rate", "Base interest rate", values.base_rate);
  validateNonNegative(errors, "debt_margin", "Debt margin", values.debt_margin);
  validatePositive(errors, "tenor_years", "Debt tenor", values.tenor_years);
  validatePositive(errors, "target_dscr", "Target DSCR", values.target_dscr);
  validatePositive(errors, "project_years", "Project years", values.project_years);
  validatePositive(errors, "financial_close_serial", "Financial close serial", values.financial_close_serial);
  validatePositive(errors, "cod_excel_serial", "COD serial", values.cod_excel_serial);

  if (bessEnabled) {
    validateNonNegative(errors, "bess_usd_per_mwh", "BESS CAPEX", values.bess_usd_per_mwh);
  }

  if (values.degradation_json.trim() !== "") {
    try {
      const parsed = JSON.parse(values.degradation_json) as unknown;
      if (!Array.isArray(parsed)) {
        errors.degradation_json = "Degradation JSON must be an array of yearly rows.";
      }
    } catch {
      errors.degradation_json = "Degradation JSON must be valid JSON.";
    }
  }

  if (!context.hasHourlyCsv) {
    errors.hourly_csv = "Upload an hourly CSV before running the model.";
  } else if (context.csvError !== null) {
    errors.hourly_csv = context.csvError;
  }

  return errors;
}

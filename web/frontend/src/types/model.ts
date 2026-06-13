export interface ModelKpis {
  project_irr: number | null;
  equity_irr: number | null;
  unlevered_irr: number | null;
  npv_usd: number | null;
  dscr_min: number | null;
  dscr_avg: number | null;
  debt_amount_usd: number | null;
  calc_solar_gen_sum_kwh: number | null;
  year1_solar_generation_mwh: number | null;
  year1_dppa_revenue_usd: number | null;
  year1_grid_savings_usd: number | null;
  // Sprint 4 / GAP-03: surfaces when the run was configured for
  // tariff_mode="2-component". Optional so older responses still type-check.
  demand_charge_savings_usd?: number | null;
  tariff_mode?: string | null;
}

export interface ScenarioKpis extends Partial<ModelKpis> {
  ppa_option?: number;
  ppa_label?: string;
  error?: string;
}

export interface LifetimeRow {
  year: number;
  generation_mwh: number;
  battery_capacity_kwh: number;
  dppa_revenue_usd: number;
  grid_savings_usd: number;
}

export interface AnnualRow {
  year: number;
  dppa_revenue_usd: number | null;
  grid_savings_usd: number | null;
  demand_charge_savings_usd: number | null;
  total_revenue_usd: number | null;
  total_opex_usd: number | null;
  ebitda_usd: number | null;
  total_debt_service_usd: number | null;
  cfads_usd: number | null;
  taxes_usd: number | null;
  mra_contribution_usd: number | null;
  free_cash_flow_to_equity_usd: number | null;
  capex_usd: number | null;
  dscr: number | null;
}

export interface CashflowRow {
  year: number;
  ebitda_usd: number | null;
  cfads_usd: number | null;
  free_cash_flow_to_equity_usd: number | null;
  capex_usd: number | null;
}

export interface DscrRow {
  year: number;
  dscr: number | null;
  total_debt_service_usd: number | null;
  cfads_usd: number | null;
}

export interface DispatchSampleRow {
  datetime: string | null;
  soc_kwh: number | null;
  solar_gen_kw: number | null;
  load_kw: number | null;
  direct_pv_consumption_kw?: number | null;
  pv_charged_kw?: number | null;
  grid_charged_kw?: number | null;
  discharged_kw: number | null;
  grid_load_after_re_kw?: number | null;
}

export type VerdictStatus = "PASS" | "MARGINAL" | "FAIL";
export type VerdictOverall = "GO" | "CAUTION" | "NO-GO";

export interface Verdict {
  overall: VerdictOverall;
  equity_irr_status: VerdictStatus;
  dscr_status: VerdictStatus;
  npv_status: VerdictStatus;
  payback_status: VerdictStatus;
  details: string[];
}

export interface ModelResponse {
  kpis: ModelKpis;
  // Optional so the dashboard renders defensively against older responses
  // produced before the assessment-verdict backend (GAP-01 PHASE-01).
  verdict?: Verdict;
  lifetime: LifetimeRow[];
  annual: AnnualRow[];
  cashflow: CashflowRow[];
  dscr_series: DscrRow[];
  dispatch_sample: DispatchSampleRow[];
}

export interface ApiErrorResponse {
  error: string;
  type?: string;
}

export interface ScenarioComparisonResponse {
  scenarios: Record<string, ScenarioKpis>;
}

export interface SensitivityPointResponse extends Partial<ModelKpis> {
  sensitivity_variable?: string;
  sensitivity_value?: number;
  error?: string;
}

export interface SensitivityResponse {
  variable: string;
  results: Record<string, SensitivityPointResponse>;
}

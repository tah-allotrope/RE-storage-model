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
}

export interface LifetimeRow {
  year: number;
  generation_mwh: number;
  battery_capacity_kwh: number;
  dppa_revenue_usd: number;
  grid_savings_usd: number;
}

export interface ModelResponse {
  kpis: ModelKpis;
  lifetime: LifetimeRow[];
}

export interface ApiErrorResponse {
  error: string;
  type?: string;
}

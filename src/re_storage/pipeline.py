"""
End-to-end model pipeline entrypoint.

Wires together all simulation layers (inputs → physics → settlement →
aggregation → financial → metrics) and returns a flat KPI dictionary
suitable for regression testing against Excel reference outputs.

Usage:
    from re_storage.pipeline import run_full_model
    results = run_full_model(Path("project.xlsx"))

Reference: model_architecture.md §1.3 (Simplified Data Pipeline)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from re_storage.aggregation.annual import calculate_year1_totals
from re_storage.aggregation.lifetime import build_lifetime_projection
from re_storage.aggregation.monthly import aggregate_hourly_to_monthly
from re_storage.core.types import (
    ChargingMode,
    GridChargeMode,
    StrategyMode,
    TimePeriod,
)
from re_storage.financial.debt import size_debt_for_dscr
from re_storage.financial.metrics import (
    calculate_dscr_series,
    calculate_equity_irr,
    calculate_npv,
    calculate_project_irr,
)
from re_storage.financial.waterfall import build_cash_flow_waterfall
from re_storage.inputs.json_loader import (
    load_assumptions_from_json,
    load_degradation_from_json,
    load_financial_params_from_json,
    load_hourly_data_from_csv,
    load_tariff_rates_from_json,
)
from re_storage.inputs.loaders import (
    load_assumptions_from_cells,
    load_degradation_table,
    load_financial_params_from_cells,
    load_hourly_data,
    load_tariff_rates_from_cells,
    load_tariff_schedule,
)
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.physics.battery import BatteryConfig, dispatch_single_timestep
from re_storage.physics.solar import (
    calculate_direct_pv_consumption_vectorized,
    calculate_surplus_generation_vectorized,
    scale_generation,
)
from re_storage.settlement.dppa import calculate_dppa_revenue
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_grid_savings,
    calculate_re_expense,
)
from re_storage.validation.checks import validate_financial_solver_freshness

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: classify hours into tariff periods using schedule
# ---------------------------------------------------------------------------


def _classify_time_periods(
    datetimes: pd.Series,
    schedule: dict[TimePeriod, list[int]],
) -> pd.Series:
    """
    Map each datetime to its TimePeriod using the tariff schedule.

    Why: The Excel Calc sheet uses TimePeriodFlag (Col E) to classify
    each hour. This function replicates that mapping from the loaded
    tariff schedule.
    """
    hour_to_period: dict[int, TimePeriod] = {}
    for period, hours in schedule.items():
        for h in hours:
            hour_to_period[h] = period

    # Default to STANDARD for any unclassified hours
    hours = pd.to_datetime(datetimes).dt.hour
    periods = hours.map(hour_to_period).fillna(TimePeriod.STANDARD)
    return periods


def _build_battery_config(assumptions: SystemAssumptions) -> BatteryConfig:
    """
    Construct BatteryConfig from SystemAssumptions.

    Why: The pipeline needs to translate the flat Pydantic schema into
    the frozen dataclass expected by the physics engine.
    """
    return BatteryConfig(
        usable_capacity_kwh=assumptions.usable_bess_capacity_kwh,
        power_rating_kw=assumptions.bess_power_rating_kw,
        charge_efficiency=assumptions.charge_efficiency,
        discharge_efficiency=assumptions.discharge_efficiency,
        strategy_mode=StrategyMode(assumptions.strategy_mode),
        charging_mode=ChargingMode(assumptions.charging_mode),
        charge_start_hour=assumptions.charge_start_hour,
        charge_end_hour=assumptions.charge_end_hour,
        precharge_target_hour=assumptions.precharge_target_hour,
        precharge_target_soc_kwh=assumptions.precharge_target_soc_kwh,
        min_direct_pv_share=assumptions.min_direct_pv_share,
        active_pv2bess_share=assumptions.active_pv2bess_share,
        demand_target_kw=0.0,  # Computed per-month from demand_reduction_target
        grid_charge_mode=GridChargeMode.DISABLED,
        grid_charge_capacity_kw=0.0,
    )


# ---------------------------------------------------------------------------
# Stage A: Physics Engine (hourly dispatch simulation)
# ---------------------------------------------------------------------------


def _run_physics(
    hourly_data: pd.DataFrame,
    assumptions: SystemAssumptions,
    tariff_schedule: dict[TimePeriod, list[int]],
) -> pd.DataFrame:
    """
    Run the hourly physics simulation: solar scaling, battery dispatch,
    energy balance columns.

    Why: This replicates the Calc sheet — the core 8760-row physics engine
    that produces SoC, charge/discharge power, and net grid load columns.

    Returns a new DataFrame (does not mutate hourly_data).
    """
    result = hourly_data.copy()

    # A.1 Solar generation scaling
    scale_factor = assumptions.scale_factor
    solar_gen_kw = scale_generation(
        result["simulation_profile_kw"].to_numpy(),
        scale_factor=scale_factor,
    )
    result["solar_gen_kw"] = solar_gen_kw

    # Classify time periods
    time_periods = _classify_time_periods(result["datetime"], tariff_schedule)
    result["time_period"] = time_periods

    # A.2-A.4 Battery dispatch (iterative, timestep-by-timestep)
    battery_config = _build_battery_config(assumptions)

    n_hours = len(result)
    soc_kwh = np.zeros(n_hours)
    pv_charged_kw = np.zeros(n_hours)
    grid_charged_kw = np.zeros(n_hours)
    discharged_kw = np.zeros(n_hours)

    previous_soc = 0.0  # Start with empty battery

    datetimes = pd.to_datetime(result["datetime"])
    hours = datetimes.dt.hour.to_numpy()
    weekdays = datetimes.dt.dayofweek.to_numpy()  # 6 = Sunday
    load_kw_arr = result["load_kw"].to_numpy(dtype=float)
    is_peak_arr = (time_periods == TimePeriod.PEAK).to_numpy()

    if assumptions.bess_enabled and assumptions.usable_bess_capacity_kwh > 0:
        for i in range(n_hours):
            state = dispatch_single_timestep(
                solar_gen_kw=float(solar_gen_kw[i]),
                load_kw=float(load_kw_arr[i]),
                previous_soc_kwh=previous_soc,
                hour=int(hours[i]),
                config=battery_config,
                is_peak_period=bool(is_peak_arr[i]),
                is_sunday=(int(weekdays[i]) == 6),
                step_hours=1.0,
                timestep=i,
            )
            soc_kwh[i] = state.soc_kwh
            pv_charged_kw[i] = state.pv_charged_kw
            grid_charged_kw[i] = state.grid_charged_kw
            discharged_kw[i] = state.discharged_kw
            previous_soc = state.soc_kwh

    result["soc_kwh"] = soc_kwh
    result["pv_charged_kw"] = pv_charged_kw
    result["grid_charged_kw"] = grid_charged_kw
    result["discharged_kw"] = discharged_kw

    # Derived columns
    direct_pv_kw = calculate_direct_pv_consumption_vectorized(
        solar_gen_kw,
        load_kw_arr,
        pv_charged_kw,
    )
    result["direct_pv_consumption_kw"] = direct_pv_kw

    surplus_kw = calculate_surplus_generation_vectorized(
        solar_gen_kw,
        direct_pv_kw,
        pv_charged_kw,
    )
    result["surplus_kw"] = surplus_kw

    # Grid load after solar only
    grid_load_after_solar_kw = np.maximum(load_kw_arr - direct_pv_kw, 0.0)
    result["grid_load_after_solar_kw"] = grid_load_after_solar_kw

    # Grid load after solar + BESS (discharge reduces grid import)
    grid_load_after_re_kw = np.maximum(
        grid_load_after_solar_kw - discharged_kw,
        0.0,
    )
    result["grid_load_after_re_kw"] = grid_load_after_re_kw

    # Net generation available for DPPA = surplus after direct + BESS charging
    result["net_gen_for_dppa_kwh"] = surplus_kw

    # Load in kWh (for hourly step = 1h, kW == kWh)
    result["load_kwh"] = load_kw_arr

    return result


# ---------------------------------------------------------------------------
# Stage B: Settlement (DPPA + Grid expenses)
# ---------------------------------------------------------------------------


def _run_settlement(
    hourly_data: pd.DataFrame,
    assumptions: SystemAssumptions,
    tariff_rates: dict[TimePeriod, float],
) -> pd.DataFrame:
    """
    Calculate DPPA revenue and grid expenses for each hour.

    Why: This replicates the DPPA sheet and the grid expense columns
    from the Calc sheet (Cols AC, AD, AE).

    Returns a new DataFrame (does not mutate hourly_data).
    """
    result = hourly_data.copy()

    # Grid expenses
    bau_expense = calculate_bau_expense(
        result["load_kwh"],
        result["time_period"],
        tariff_rates,
    )
    re_expense = calculate_re_expense(
        result["grid_load_after_re_kw"],
        result["time_period"],
        tariff_rates,
    )
    result["bau_expense_usd"] = bau_expense
    result["re_expense_usd"] = re_expense
    result["grid_savings_usd"] = calculate_grid_savings(bau_expense, re_expense)

    # DPPA revenue
    dppa_result = calculate_dppa_revenue(result, assumptions)

    return dppa_result


# ---------------------------------------------------------------------------
# Stage C: Aggregation (hourly → monthly → annual → lifetime)
# ---------------------------------------------------------------------------


def _run_aggregation(
    hourly_data: pd.DataFrame,
    dppa_hourly: pd.DataFrame,
    assumptions: SystemAssumptions,
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> dict[str, Any]:
    """
    Aggregate hourly results into monthly, Year 1, and lifetime projections.

    Why: This replicates the Helper → Measures → Lifetime sheet chain.

    Returns dict with 'monthly', 'year1', and 'lifetime' DataFrames.
    """
    monthly = aggregate_hourly_to_monthly(
        hourly_data,
        demand_reduction_target_ratio=assumptions.demand_reduction_target,
    )

    year1 = calculate_year1_totals(
        monthly,
        hourly_data,
        dppa_hourly,
        scale_factor=assumptions.scale_factor,
        solar_gen_column="solar_gen_kw",
    )

    lifetime = build_lifetime_projection(
        year1,
        degradation_table,
        initial_capacity_kwh=assumptions.usable_bess_capacity_kwh,
        project_years=project_years,
    )

    return {"monthly": monthly, "year1": year1, "lifetime": lifetime}


# ---------------------------------------------------------------------------
# Stage D: Financial (waterfall → debt → metrics)
# ---------------------------------------------------------------------------


def _build_placeholder_opex(project_years: int) -> pd.DataFrame:
    """
    Build placeholder opex schedule when detailed opex inputs are unavailable.

    Why: The current input loaders don't yet parse the Other Input sheet
    for detailed O&M/insurance/land-lease line items. This provides zero
    placeholders so the waterfall can still run. As we add loaders for
    Other Input, these will be replaced with real values.
    """
    years = list(range(1, project_years + 1))
    return pd.DataFrame(
        {
            "year": years,
            "o_and_m_usd": 0.0,
            "insurance_usd": 0.0,
            "land_lease_usd": 0.0,
            "management_fees_usd": 0.0,
            "grid_connection_usd": 0.0,
            "taxes_usd": 0.0,
            "mra_contribution_usd": 0.0,
        }
    )


def _run_financial(
    lifetime: pd.DataFrame,
    project_years: int = 25,
    interest_rate_pct: float = 6.0,
    tenor_years: int = 15,
    target_dscr: float = 1.3,
    initial_capex_usd: float = 0.0,
    discount_rate_pct: float = 8.0,
    cod_date: str = "2027-01-01",
) -> dict[str, float]:
    """
    Run financial waterfall and calculate return metrics.

    Why: This replicates the Financial sheet — building revenue → EBITDA →
    debt service → equity cash flows and computing IRR/NPV/DSCR.

    Returns a flat dict of financial KPIs.
    """
    years = list(range(1, project_years + 1))

    # Revenue schedule from lifetime projection
    revenue = pd.DataFrame(
        {
            "year": years,
            "dppa_revenue_usd": lifetime["dppa_revenue_usd"].values,
            "grid_savings_usd": lifetime["grid_savings_usd"].values,
            "demand_charge_savings_usd": 0.0,  # Placeholder until demand charges added
        }
    )

    opex = _build_placeholder_opex(project_years)

    # Calculate EBITDA for debt sizing
    total_revenue = (
        revenue["dppa_revenue_usd"]
        + revenue["grid_savings_usd"]
        + revenue["demand_charge_savings_usd"]
    )
    total_opex = (
        opex["o_and_m_usd"]
        + opex["insurance_usd"]
        + opex["land_lease_usd"]
        + opex["management_fees_usd"]
        + opex["grid_connection_usd"]
    )
    ebitda = total_revenue - total_opex
    ebitda_series = pd.Series(ebitda.values, index=pd.Index(years, name="year"))

    # Debt sizing
    try:
        debt_amount_usd, debt_schedule = size_debt_for_dscr(
            ebitda_series=ebitda_series,
            interest_rate_pct=interest_rate_pct,
            tenor_years=tenor_years,
            target_dscr=target_dscr,
            initial_guess_usd=initial_capex_usd * 0.7 if initial_capex_usd > 0 else 1e6,
        )
    except Exception as exc:
        logger.warning("Debt sizing failed: %s — using zero debt", exc)
        debt_amount_usd = 0.0
        debt_schedule = pd.DataFrame(
            {
                "year": years,
                "interest_usd": 0.0,
                "principal_usd": 0.0,
                "total_debt_service_usd": 0.0,
            }
        ).set_index("year", drop=False)

    # Pad debt schedule to cover full project lifetime
    full_debt = pd.DataFrame(
        {
            "year": years,
            "interest_usd": 0.0,
            "principal_usd": 0.0,
            "total_debt_service_usd": 0.0,
        }
    ).set_index("year", drop=False)

    for col in ["interest_usd", "principal_usd", "total_debt_service_usd"]:
        overlap = full_debt.index.intersection(debt_schedule.index)
        if len(overlap) > 0:
            full_debt.loc[overlap, col] = debt_schedule.loc[overlap, col].values

    # Build waterfall
    waterfall = build_cash_flow_waterfall(
        lifetime_revenue=revenue,
        lifetime_opex=opex,
        debt_schedule=full_debt,
        capex={"initial_capex_usd": initial_capex_usd},
    )

    # Build date series for XIRR/XNPV
    cod = pd.Timestamp(cod_date)
    dates = pd.Series(
        [cod + pd.DateOffset(years=int(y)) for y in waterfall.index],
        index=waterfall.index,
    )

    # Project IRR: capex (negative) + EBITDA
    project_cf = waterfall["ebitda_usd"].copy()
    project_cf.iloc[0] = -initial_capex_usd  # Year 0 = capex outflow

    # Equity IRR: capex - debt + free cash flow to equity
    equity_cf = waterfall["free_cash_flow_to_equity_usd"].copy()
    equity_cf.iloc[0] = -(initial_capex_usd - debt_amount_usd)  # Equity portion

    # Unlevered IRR: EBITDA without debt (same as project_cf)
    unlevered_cf = project_cf.copy()

    results: dict[str, float] = {}

    try:
        results["project_irr"] = calculate_project_irr(project_cf, dates)
    except Exception as exc:
        logger.warning("Project IRR calculation failed: %s", exc)
        results["project_irr"] = float("nan")

    try:
        results["equity_irr"] = calculate_equity_irr(equity_cf, dates)
    except Exception as exc:
        logger.warning("Equity IRR calculation failed: %s", exc)
        results["equity_irr"] = float("nan")

    try:
        results["unlevered_irr"] = calculate_project_irr(unlevered_cf, dates)
    except Exception as exc:
        logger.warning("Unlevered IRR calculation failed: %s", exc)
        results["unlevered_irr"] = float("nan")

    try:
        results["npv_usd"] = calculate_npv(unlevered_cf, dates, discount_rate_pct)
    except Exception as exc:
        logger.warning("NPV calculation failed: %s", exc)
        results["npv_usd"] = float("nan")

    # DSCR
    debt_service_years = full_debt.loc[full_debt["total_debt_service_usd"] > 0]
    if len(debt_service_years) > 0:
        dscr_series = calculate_dscr_series(
            ebitda_series.loc[debt_service_years.index],
            debt_service_years["total_debt_service_usd"],
        )
        results["dscr_min"] = float(dscr_series.min())
        results["dscr_avg"] = float(dscr_series.mean())
    else:
        results["dscr_min"] = float("nan")
        results["dscr_avg"] = float("nan")

    results["debt_amount_usd"] = debt_amount_usd

    return results


# ===========================================================================
# PUBLIC API
# ===========================================================================


def run_full_model(
    excel_path: Path,
    project_years: int = 25,
    interest_rate_pct: float = 6.0,
    tenor_years: int = 15,
    target_dscr: float = 1.3,
    initial_capex_usd: float = 0.0,
    discount_rate_pct: float = 8.0,
    cod_date: str = "2027-01-01",
    tariff_rates: dict[TimePeriod, float] | None = None,
) -> dict[str, float]:
    """
    Run the full RE-Storage simulation pipeline on an Excel input file.

    This is the main entrypoint that the regression test suite calls.
    It loads inputs, runs physics, settlement, aggregation, and financial
    layers, and returns a flat dict of KPIs matching the reference JSON
    format produced by scripts/extract_excel_kpis.py.

    Args:
        excel_path: Path to Excel input file with Assumption, Data Input,
            Loss, and Tariff Schedule sheets.
        project_years: Project lifetime in years (default 25).
        interest_rate_pct: Annual interest rate (%) for debt sizing.
        tenor_years: Debt tenor in years.
        target_dscr: Minimum DSCR covenant for debt sizing.
        initial_capex_usd: Total initial capital expenditure (USD).
        discount_rate_pct: Discount rate for NPV calculation (%).
        cod_date: Commercial operation date (ISO format string).
        tariff_rates: Optional tariff rates override. If None, uses
            default rates {OFF_PEAK: 0.05, STANDARD: 0.10, PEAK: 0.20}.

    Returns:
        Flat dict with KPI keys matching the JSON reference format:
        - project_irr, equity_irr, unlevered_irr, npv_usd
        - dscr_min, dscr_avg, debt_amount_usd
        - calc_solar_gen_sum_kwh, calc_soc_min_kwh, calc_soc_max_kwh
        - year1_solar_generation_mwh, year1_dppa_revenue_usd, year1_grid_savings_usd

    Raises:
        InputValidationError: If Excel inputs are invalid.
        EnergyBalanceError: If physics simulation violates energy balance.
        SoCBoundsError: If battery SoC goes out of bounds.
    """
    excel_path = Path(excel_path)
    logger.info("Running full model on %s", excel_path.name)

    financial_params = load_financial_params_from_cells(excel_path)
    project_years_effective = int(financial_params["project_years"])
    interest_rate_effective = float(financial_params["interest_rate_pct"])
    tenor_years_effective = int(financial_params["tenor_years"])
    target_dscr_effective = float(financial_params["target_dscr"])
    initial_capex_effective = float(financial_params["initial_capex_usd"])
    discount_rate_effective = float(financial_params["discount_rate_pct"])
    cod_date_effective = str(financial_params["cod_date"])

    # --- Workbook-level diagnostics ---
    freshness_warnings = validate_financial_solver_freshness(str(excel_path))
    for warning in freshness_warnings:
        logger.warning("%s", warning)

    # --- Load inputs ---
    assumptions = load_assumptions_from_cells(excel_path)
    hourly_data = load_hourly_data(excel_path)
    degradation_table = load_degradation_table(
        excel_path,
        project_years=project_years_effective,
    )

    try:
        schedule = load_tariff_schedule(excel_path)
    except Exception as exc:
        logger.warning("Tariff schedule load failed: %s — using defaults", exc)
        schedule = {
            TimePeriod.OFF_PEAK: list(range(0, 7)),
            TimePeriod.STANDARD: list(range(7, 17)),
            TimePeriod.PEAK: list(range(17, 24)),
        }

    if tariff_rates is None:
        tariff_rates = load_tariff_rates_from_cells(excel_path)

    # --- Stage A: Physics ---
    hourly_result = _run_physics(hourly_data, assumptions, schedule)

    # --- Stage B: Settlement ---
    settlement_result = _run_settlement(hourly_result, assumptions, tariff_rates)

    # --- Stage C: Aggregation ---
    agg = _run_aggregation(
        settlement_result,
        settlement_result,  # dppa columns are already in the same DF
        assumptions,
        degradation_table,
        project_years=project_years_effective,
    )

    # --- Stage D: Financial ---
    financial_kpis = _run_financial(
        lifetime=agg["lifetime"],
        project_years=project_years_effective,
        interest_rate_pct=interest_rate_effective,
        tenor_years=tenor_years_effective,
        target_dscr=target_dscr_effective,
        initial_capex_usd=initial_capex_effective,
        discount_rate_pct=discount_rate_effective,
        cod_date=cod_date_effective,
    )

    # --- Assemble KPI dict ---
    results: dict[str, float] = {}

    # Financial KPIs
    results.update(financial_kpis)

    # Physics intermediate KPIs
    results["calc_solar_gen_sum_kwh"] = float(hourly_result["solar_gen_kw"].sum())
    soc_series = hourly_result["soc_kwh"]
    results["calc_soc_min_kwh"] = float(soc_series.min())
    results["calc_soc_max_kwh"] = float(soc_series.max())

    # Aggregation intermediate KPIs
    year1 = agg["year1"]
    results["year1_solar_generation_mwh"] = float(year1.loc[1, "total_solar_generation_mwh"])
    results["year1_dppa_revenue_usd"] = float(year1.loc[1, "total_dppa_revenue_usd"])
    results["year1_grid_savings_usd"] = float(year1.loc[1, "total_grid_savings_usd"])

    logger.info(
        "Model complete — Project IRR: %.4f, Equity IRR: %.4f, NPV: %.0f",
        results.get("project_irr", float("nan")),
        results.get("equity_irr", float("nan")),
        results.get("npv_usd", float("nan")),
    )

    return results


def run_model_from_json(
    project_dir: Path,
    tariff_rates: dict[TimePeriod, float] | None = None,
) -> dict[str, Any]:
    """
    Run the full RE-Storage pipeline using JSON+CSV project inputs.

    Returns the same scalar KPI keys as run_full_model, plus report-friendly
    DataFrames under underscore-prefixed keys: _hourly_df and _lifetime_df.
    """
    project_dir = Path(project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        raise ValueError(f"project_dir must be an existing directory: {project_dir}")

    json_files = sorted(project_dir.glob("*.json"))
    csv_files = sorted(project_dir.glob("*.csv"))

    if len(json_files) != 1:
        raise ValueError(
            f"Expected exactly one JSON file in {project_dir}, found {len(json_files)}"
        )
    if len(csv_files) != 1:
        raise ValueError(f"Expected exactly one CSV file in {project_dir}, found {len(csv_files)}")

    json_path = json_files[0]
    csv_path = csv_files[0]
    logger.info("Running JSON model on %s", project_dir)

    assumptions = load_assumptions_from_json(json_path)
    hourly_data = load_hourly_data_from_csv(csv_path)
    financial_params = load_financial_params_from_json(json_path)
    project_years = int(financial_params["project_years"])
    degradation_table = load_degradation_from_json(json_path, project_years=project_years)

    schedule = {
        TimePeriod.OFF_PEAK: list(range(0, 7)),
        TimePeriod.STANDARD: list(range(7, 17)),
        TimePeriod.PEAK: list(range(17, 24)),
    }

    if tariff_rates is None:
        tariff_rates = load_tariff_rates_from_json(json_path)

    exchange_rate_usd_vnd = float(financial_params["exchange_rate_usd_vnd"])
    if exchange_rate_usd_vnd <= 0:
        raise ValueError("exchange_rate_usd_vnd must be positive")

    hourly_data = hourly_data.copy()
    hourly_data["fmp_usd_per_kwh"] = hourly_data["fmp_usd_per_kwh"] / exchange_rate_usd_vnd
    hourly_data["cfmp_usd_per_kwh"] = hourly_data["cfmp_usd_per_kwh"] / exchange_rate_usd_vnd

    hourly_result = _run_physics(hourly_data, assumptions, schedule)
    settlement_result = _run_settlement(hourly_result, assumptions, tariff_rates)
    agg = _run_aggregation(
        settlement_result,
        settlement_result,
        assumptions.model_copy(update={"actual_capacity_kwp": assumptions.simulation_capacity_kwp}),
        degradation_table,
        project_years=project_years,
    )

    financial_kpis = _run_financial(
        lifetime=agg["lifetime"],
        project_years=project_years,
        interest_rate_pct=float(financial_params["interest_rate_pct"]),
        tenor_years=int(financial_params["tenor_years"]),
        target_dscr=float(financial_params["target_dscr"]),
        initial_capex_usd=float(financial_params["initial_capex_usd"]),
        discount_rate_pct=float(financial_params["discount_rate_pct"]),
        cod_date=str(financial_params["cod_date"]),
    )

    results: dict[str, Any] = {}
    results.update(financial_kpis)

    results["calc_solar_gen_sum_kwh"] = float(hourly_result["solar_gen_kw"].sum())
    soc_series = hourly_result["soc_kwh"]
    results["calc_soc_min_kwh"] = float(soc_series.min())
    results["calc_soc_max_kwh"] = float(soc_series.max())

    year1 = agg["year1"]
    results["year1_solar_generation_mwh"] = float(year1.loc[1, "total_solar_generation_mwh"])
    results["year1_dppa_revenue_usd"] = float(year1.loc[1, "total_dppa_revenue_usd"])
    results["year1_grid_savings_usd"] = float(year1.loc[1, "total_grid_savings_usd"])

    results["_hourly_df"] = settlement_result
    results["_lifetime_df"] = agg["lifetime"]

    return results

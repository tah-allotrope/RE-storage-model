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
from re_storage.financial.debt import calculate_amortization_schedule, size_debt_for_dscr
from re_storage.financial.metrics import (
    calculate_cash_on_cash_yield,
    calculate_discounted_payback,
    calculate_dscr_series,
    calculate_equity_irr,
    calculate_npv,
    calculate_project_irr,
    calculate_simple_payback,
)
from re_storage.financial.mra import build_mra_schedule
from re_storage.financial.opex import build_opex_schedule
from re_storage.financial.taxes import (
    build_combined_depreciation_schedule,
    build_tax_rate_schedule,
    calculate_depreciation_schedule,
    calculate_levered_taxes,
    calculate_unlevered_taxes,
)
from re_storage.financial.waterfall import build_cash_flow_waterfall
from re_storage.inputs.json_loader import (
    load_assumptions_from_json,
    load_degradation_from_json,
    load_financial_params_from_json,
    load_hourly_data_from_csv,
    load_tariff_rates_from_json,
    load_tariff_schedule_from_json,
)
from re_storage.inputs.loaders import (
    load_assumptions_from_cells,
    load_degradation_table,
    load_financial_params_from_cells,
    load_hourly_data,
    load_tariff_rates_from_cells,
    load_tariff_schedule,
    load_tariff_schedule_from_calc,
)
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.physics.battery import BatteryConfig, dispatch_single_timestep
from re_storage.physics.solar import (
    calculate_direct_pv_consumption_vectorized,
    calculate_surplus_generation_vectorized,
    scale_generation,
)
from re_storage.settlement.bundled import calculate_bundled_revenue
from re_storage.settlement.demand_charge import calculate_annual_demand_savings
from re_storage.settlement.dppa import calculate_dppa_revenue
from re_storage.settlement.fixed_ppa import calculate_fixed_ppa_revenue
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_grid_savings,
    calculate_re_expense,
)
from re_storage.settlement.separate import calculate_separate_revenue
from re_storage.validation.checks import validate_financial_solver_freshness

logger = logging.getLogger(__name__)

#: Accepted values for the two-component tariff mode (Sprint 4).
VALID_TARIFF_MODES = {"1-component", "2-component"}


def _validate_tariff_mode(tariff_mode: str) -> None:
    """Raise ValueError when *tariff_mode* is not a recognised mode."""
    if tariff_mode not in VALID_TARIFF_MODES:
        raise ValueError(
            f"tariff_mode must be one of {sorted(VALID_TARIFF_MODES)}, got {tariff_mode!r}"
        )


_ASSUMPTION_OVERRIDE_KEYS = set(SystemAssumptions.model_fields)
_FINANCIAL_OVERRIDE_KEYS = {
    "asset_management_usd",
    "asset_management_usd_per_mwp",
    "base_rate_floating",
    "bess_capex_usd",
    "bess_capex_usd_per_mwh",
    "bess_capacity_mwh",
    "bess_depreciation_tenor_years",
    "bess_discount_pct",
    "bess_mra_pct",
    "bess_mwh",
    "bop_capex_usd",
    "bundled_discount_pct",
    "cod_date",
    "cpi",
    "debt_margin_pct",
    "discount_rate_pct",
    "exchange_rate_usd_vnd",
    "first_discount_rate",
    "first_discount_years",
    "fixed_ppa_price_usd_per_mwh",
    "fixed_ppa_curtailment_pct",
    "fixed_ppa_tx_loss_pct",
    "fmp_change_rate",
    "fmp_descent_pct",
    "initial_capex_usd",
    "installed_pv_mwp",
    "insurance_bess_pct_capex",
    "insurance_pct_capex",
    "insurance_solar_pct_capex",
    "interest_rate_pct",
    "land_capex_usd",
    "land_lease_pct_revenue",
    "land_lease_usd",
    "land_lease_usd_per_mwp",
    "max_leverage_ratio",
    "om_bess_usd_per_mwh",
    "om_solar_usd_per_mwp",
    "opex_escalation_pct",
    "other_opex_usd_per_mwp",
    "ppa_option",
    "project_years",
    "pv_capex_usd_per_mwp",
    "pv_depreciation_tenor_years",
    "pv_discount_pct",
    "pv_mra_pct",
    "revenue_escalation_pct",
    "second_discount_rate",
    "second_discount_years",
    "solar_capex_usd",
    "solar_capacity_mwp",
    "strike_price_vnd",
    "target_dscr",
    "tax_holiday_years",
    "tax_rate",
    "tariff_schedule_sheet",
    "tenor_years",
    "mra_buildup_schedule",
}


def _coerce_project_percent_to_ratio(value: Any) -> float:
    """Convert percentage-like overrides to a 0-1 ratio when needed."""
    numeric_value = float(value)
    if abs(numeric_value) > 1.0:
        return numeric_value / 100.0
    return numeric_value


def _normalize_base_params(
    base_params: dict[str, Any] | None,
    fallback_financial_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map scenario override keys onto the pipeline's internal parameter names."""
    if not base_params:
        return {}

    params = dict(base_params)
    fallback = fallback_financial_params or {}

    exchange_rate_usd_vnd = params.get(
        "exchange_rate_usd_vnd", fallback.get("exchange_rate_usd_vnd")
    )
    if "strike_price_vnd" in params and exchange_rate_usd_vnd is not None:
        params["strike_price_usd_per_kwh"] = float(params["strike_price_vnd"]) / float(
            exchange_rate_usd_vnd
        )

    installed_pv_mwp = params.get(
        "installed_pv_mwp",
        params.get(
            "solar_capacity_mwp",
            fallback.get("installed_pv_mwp", fallback.get("solar_capacity_mwp")),
        ),
    )
    if "installed_pv_mwp" in params or "solar_capacity_mwp" in params:
        if installed_pv_mwp is not None:
            installed_pv_mwp_value = float(installed_pv_mwp)
            params["installed_pv_mwp"] = installed_pv_mwp_value
            params.setdefault("solar_capacity_mwp", installed_pv_mwp_value)
            params["actual_capacity_kwp"] = installed_pv_mwp_value * 1000.0

    bess_mwh = params.get(
        "bess_mwh",
        params.get(
            "bess_capacity_mwh",
            fallback.get("bess_mwh", fallback.get("bess_capacity_mwh")),
        ),
    )
    if "bess_mwh" in params or "bess_capacity_mwh" in params:
        if bess_mwh is not None:
            bess_mwh_value = float(bess_mwh)
            params["bess_mwh"] = bess_mwh_value
            params.setdefault("bess_capacity_mwh", bess_mwh_value)
            params["usable_bess_capacity_kwh"] = bess_mwh_value * 1000.0

    solar_unit_capex = params.get("pv_capex_usd_per_mwp")
    if solar_unit_capex is not None and installed_pv_mwp is not None:
        params["solar_capex_usd"] = float(solar_unit_capex) * float(installed_pv_mwp)

    bess_unit_capex = params.get("bess_capex_usd_per_mwh")
    if bess_unit_capex is not None and bess_mwh is not None:
        params["bess_capex_usd"] = float(bess_unit_capex) * float(bess_mwh)

    for key in (
        "bundled_discount_pct",
        "pv_discount_pct",
        "bess_discount_pct",
        "opex_escalation_pct",
        "revenue_escalation_pct",
        "fmp_descent_pct",
        "tax_rate",
        "first_discount_rate",
        "second_discount_rate",
        "max_leverage_ratio",
        "bess_mra_pct",
        "pv_mra_pct",
    ):
        if key in params:
            params[key] = _coerce_project_percent_to_ratio(params[key])

    return params


def _split_pipeline_overrides(
    base_params: dict[str, Any] | None,
    fallback_financial_params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split caller overrides into assumption fields and financial fields."""
    normalized = _normalize_base_params(base_params, fallback_financial_params)
    assumption_updates = {
        key: value for key, value in normalized.items() if key in _ASSUMPTION_OVERRIDE_KEYS
    }
    financial_updates = {
        key: value
        for key, value in normalized.items()
        if key in _FINANCIAL_OVERRIDE_KEYS or key in _ASSUMPTION_OVERRIDE_KEYS
    }
    return assumption_updates, financial_updates


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
        when_needed=assumptions.when_needed,
        after_sunset=assumptions.after_sunset,
        optimize_mode=assumptions.optimize_mode,
        peak_mode=assumptions.peak_mode,
        max_cycles_per_day=assumptions.max_cycles_per_day,
    )


def _normalize_hourly_price_columns_to_usd(
    hourly_data: pd.DataFrame,
    exchange_rate_usd_vnd: float,
) -> pd.DataFrame:
    """
    Convert workbook hourly market prices from VND to USD when needed.

    Why: Real Excel workbooks store FMP/CFMP in VND-scale values (e.g. 1377),
    while settlement logic expects USD/kWh like the strike-price assumption.
    """
    if exchange_rate_usd_vnd <= 0:
        raise ValueError("exchange_rate_usd_vnd must be positive")

    result = hourly_data.copy()
    for column in ("fmp_usd_per_kwh", "cfmp_usd_per_kwh"):
        if column not in result.columns:
            continue
        numeric_series = pd.Series(
            pd.to_numeric(result[column], errors="coerce"), index=result.index
        )
        if bool(numeric_series.notna().any()) and float(numeric_series.abs().max()) > 10.0:
            result[column] = numeric_series / exchange_rate_usd_vnd
    return result


def _build_dppa_net_generation(hourly_data: pd.DataFrame) -> pd.Series:
    """
    Build the Calc!AB-equivalent DPPA generation signal.

    Why: The workbook feeds DPPA from net generation after battery charging,
    then adds battery discharge back in; using surplus-only understates revenue.
    """
    net_generation = (
        hourly_data["solar_gen_kw"] - hourly_data["pv_charged_kw"] + hourly_data["discharged_kw"]
    )
    return net_generation.clip(lower=0.0)


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
    cycles_used_today = 0
    previous_discharge_active = False
    previous_day_key: tuple[int, int, int] | None = None

    datetimes = pd.to_datetime(result["datetime"])
    hours = datetimes.dt.hour.to_numpy()
    weekdays = datetimes.dt.dayofweek.to_numpy()  # 6 = Sunday
    load_kw_arr = result["load_kw"].to_numpy(dtype=float)
    is_peak_arr = (time_periods == TimePeriod.PEAK).to_numpy()

    if assumptions.bess_enabled and assumptions.usable_bess_capacity_kwh > 0:
        for i in range(n_hours):
            day_key = (
                int(datetimes.iloc[i].year),
                int(datetimes.iloc[i].month),
                int(datetimes.iloc[i].day),
            )
            if previous_day_key != day_key:
                cycles_used_today = 0
                previous_discharge_active = False
                previous_day_key = day_key

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
                cycles_used_today=cycles_used_today,
                previous_discharge_active=previous_discharge_active,
            )
            soc_kwh[i] = state.soc_kwh
            pv_charged_kw[i] = state.pv_charged_kw
            grid_charged_kw[i] = state.grid_charged_kw
            discharged_kw[i] = state.discharged_kw
            previous_soc = state.soc_kwh
            discharge_active = state.discharged_kw > 0
            if discharge_active and not previous_discharge_active:
                cycles_used_today += 1
            previous_discharge_active = discharge_active

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

    # Net generation available for DPPA follows the workbook's Calc!AB logic.
    result["net_gen_for_dppa_kwh"] = _build_dppa_net_generation(result)

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
    dppa_topology: str = "onsite",
) -> pd.DataFrame:
    """
    Calculate PPA revenue and grid expenses for each hour.

    Dispatches to the correct settlement module based on assumptions.ppa_option:
        1 = Bundled Discount  (settlement/bundled.py)
        2 = Separate PV+BESS  (settlement/separate.py)
        3 = DPPA CfD          (settlement/dppa.py)  ← default
        4 = Fixed EVN PPA     (settlement/fixed_ppa.py)

    Why: This replicates the DPPA sheet and the grid expense columns
    from the Calc sheet (Cols AC, AD, AE).

    Returns a new DataFrame (does not mutate hourly_data).
    """
    result = hourly_data.copy()

    # Grid expenses (same for all PPA options — these are the savings vs BAU)
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

    # Apply topology masking for offsite projects
    if dppa_topology == "offsite":
        result["grid_savings_usd"] = 0.0

    ppa_option = getattr(assumptions, "ppa_option", 3)

    if ppa_option == 1:
        # Option 1: Bundled Discount
        result["dppa_revenue_usd"] = calculate_bundled_revenue(
            direct_pv_kw=result["direct_pv_consumption_kw"],
            discharged_kw=result["discharged_kw"],
            time_period=result["time_period"],
            tariff_rates=tariff_rates,
            discount_pct=assumptions.bundled_discount_pct,
        )
    elif ppa_option == 2:
        # Option 2: Separate PV + BESS
        result["dppa_revenue_usd"] = calculate_separate_revenue(
            direct_pv_kw=result["direct_pv_consumption_kw"],
            discharged_kw=result["discharged_kw"],
            time_period=result["time_period"],
            tariff_rates=tariff_rates,
            pv_discount_pct=assumptions.pv_discount_pct,
            bess_discount_pct=assumptions.bess_discount_pct,
        )
    elif ppa_option == 4:
        # Option 4: Fixed EVN PPA
        result["dppa_revenue_usd"] = calculate_fixed_ppa_revenue(
            solar_gen_kw=result["solar_gen_kw"],
            fixed_price_usd_per_mwh=assumptions.fixed_ppa_price_usd_per_mwh,
            curtailment_pct=assumptions.fixed_ppa_curtailment_pct,
            tx_loss_pct=assumptions.fixed_ppa_tx_loss_pct,
        )
    else:
        # Option 3 (default): DPPA CfD
        result = calculate_dppa_revenue(result, assumptions)

    if "total_dppa_revenue_usd" not in result.columns and "dppa_revenue_usd" in result.columns:
        result["total_dppa_revenue_usd"] = result["dppa_revenue_usd"]
    if "dppa_revenue_usd" not in result.columns and "total_dppa_revenue_usd" in result.columns:
        result["dppa_revenue_usd"] = result["total_dppa_revenue_usd"]

    return result


# ---------------------------------------------------------------------------
# Stage C: Aggregation (hourly → monthly → annual → lifetime)
# ---------------------------------------------------------------------------


def _run_aggregation(
    hourly_data: pd.DataFrame,
    dppa_hourly: pd.DataFrame,
    assumptions: SystemAssumptions,
    degradation_table: pd.DataFrame,
    project_years: int = 25,
    revenue_escalation_pct: float = 0.0,
    fmp_descent_pct: float = 0.0,
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
        revenue_escalation_pct=revenue_escalation_pct,
        fmp_descent_pct=fmp_descent_pct,
    )

    return {"monthly": monthly, "year1": year1, "lifetime": lifetime}


# ---------------------------------------------------------------------------
# Stage D: Financial (waterfall → debt → metrics)
# ---------------------------------------------------------------------------


def _run_financial(
    lifetime: pd.DataFrame,
    project_years: int = 25,
    interest_rate_pct: float = 6.0,
    tenor_years: int = 15,
    target_dscr: float = 1.3,
    initial_capex_usd: float = 0.0,
    discount_rate_pct: float = 8.0,
    cod_date: str = "2027-01-01",
    max_leverage_ratio: float = 1.0,
    # OPEX parameters
    solar_capacity_mwp: float = 0.0,
    bess_capacity_mwh: float = 0.0,
    om_solar_usd_per_mwp: float = 8_000.0,
    om_bess_usd_per_mwh: float = 5_000.0,
    insurance_pct_capex: float = 0.005,
    other_opex_usd_per_mwp: float = 0.0,
    asset_management_usd_per_mwp: float = 0.0,
    land_lease_pct_revenue: float = 0.0,
    asset_management_usd: float = 15_000.0,
    land_lease_usd: float = 20_000.0,
    cpi: float = 0.04,
    # Tax parameters
    tax_rate: float = 0.20,
    tax_holiday_years: int = 4,
    first_discount_years: int = 5,
    first_discount_rate: float = 0.10,
    second_discount_years: int = 0,
    second_discount_rate: float = 0.0,
    pv_depreciation_tenor_years: int = 20,
    bess_depreciation_tenor_years: int = 10,
    # MRA parameters
    bess_capex_usd: float = 0.0,
    pv_capex_usd: float = 0.0,
    bess_mra_pct: float = 0.60,
    pv_mra_pct: float = 0.10,
    mra_buildup_schedule: dict[int, float] | None = None,
    # Demand charge savings (annual, already converted to USD)
    demand_charge_savings_usd_yr1: float = 0.0,
) -> dict[str, Any]:
    """
    Run financial waterfall and calculate return metrics.

    Why: This replicates the Financial sheet — building revenue → EBITDA →
    debt service → equity cash flows and computing IRR/NPV/DSCR.

    Returns a flat dict of financial KPIs.
    """
    years = list(range(1, project_years + 1))
    year_index = pd.RangeIndex(1, project_years + 1)

    lifetime_aligned = lifetime.set_index("year", drop=False).reindex(year_index)
    if bool(lifetime_aligned[["dppa_revenue_usd", "grid_savings_usd"]].isna().to_numpy().sum()):
        raise ValueError("lifetime projection must cover every project year for financial runs")

    demand_charge_savings = pd.Series(
        demand_charge_savings_usd_yr1,
        index=year_index,
        dtype=float,
        name="demand_charge_savings_usd",
    )

    # Revenue schedule from lifetime projection
    revenue = pd.DataFrame(
        {
            "year": year_index,
            "dppa_revenue_usd": lifetime_aligned["dppa_revenue_usd"].to_numpy(),
            "grid_savings_usd": lifetime_aligned["grid_savings_usd"].to_numpy(),
            "demand_charge_savings_usd": demand_charge_savings.to_numpy(),
        }
    ).set_index("year", drop=False)

    # Calculate revenue before OPEX so revenue-linked land lease can use it.
    total_revenue = (
        revenue["dppa_revenue_usd"]
        + revenue["grid_savings_usd"]
        + revenue["demand_charge_savings_usd"]
    )

    # Build real OPEX schedule
    opex = build_opex_schedule(
        solar_capacity_mwp=solar_capacity_mwp,
        bess_capacity_mwh=bess_capacity_mwh,
        total_capex_usd=initial_capex_usd,
        project_years=project_years,
        cpi=cpi,
        om_solar_usd_per_mwp=om_solar_usd_per_mwp,
        om_bess_usd_per_mwh=om_bess_usd_per_mwh,
        insurance_pct_capex=insurance_pct_capex,
        other_opex_usd_per_mwp=other_opex_usd_per_mwp,
        asset_management_usd_per_mwp=asset_management_usd_per_mwp,
        land_lease_pct_revenue=land_lease_pct_revenue,
        annual_revenue_usd=total_revenue,
        asset_management_usd=asset_management_usd,
        land_lease_usd=land_lease_usd,
    )

    total_opex_excluding_mra = (
        opex["o_and_m_usd"]
        + opex["insurance_usd"]
        + opex["land_lease_usd"]
        + opex["management_fees_usd"]
        + opex["grid_connection_usd"]
    )

    # --- Taxes ---
    tax_rates = build_tax_rate_schedule(
        project_years=project_years,
        tax_rate=tax_rate,
        holiday_years=tax_holiday_years,
        first_discount_years=first_discount_years,
        first_discount_rate=first_discount_rate,
        second_discount_years=second_discount_years,
        second_discount_rate=second_discount_rate,
    )

    # --- MRA ---
    mra_series = build_mra_schedule(
        bess_capex_usd=bess_capex_usd,
        pv_capex_usd=pv_capex_usd,
        bess_mra_pct=bess_mra_pct,
        pv_mra_pct=pv_mra_pct,
        buildup_schedule=mra_buildup_schedule,
        project_years=project_years,
    )

    total_opex = total_opex_excluding_mra + mra_series
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
        if initial_capex_usd > 0:
            debt_cap_usd = max(initial_capex_usd * max_leverage_ratio, 0.0)
            if debt_amount_usd > debt_cap_usd:
                debt_amount_usd = debt_cap_usd
                if debt_amount_usd > 0:
                    debt_schedule = calculate_amortization_schedule(
                        debt_amount_usd=debt_amount_usd,
                        interest_rate_pct=interest_rate_pct,
                        tenor_years=tenor_years,
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

    # Use separate tenors for PV (20yr) and BESS (10yr) per Vietnam tax rules
    depreciation = build_combined_depreciation_schedule(
        pv_capex_usd=pv_capex_usd,
        bess_capex_usd=bess_capex_usd,
        pv_tenor_years=pv_depreciation_tenor_years,
        bess_tenor_years=bess_depreciation_tenor_years,
        project_years=project_years,
    )
    levered_taxes_raw = calculate_levered_taxes(
        ebitda=ebitda_series,
        depreciation=depreciation,
        debt_interest=full_debt["interest_usd"].set_axis(year_index),
        tax_rates=tax_rates,
    )
    levered_taxes = -levered_taxes_raw
    unlevered_taxes_raw = calculate_unlevered_taxes(
        ebitda=ebitda_series,
        depreciation=depreciation,
        tax_rates=tax_rates,
    )
    unlevered_taxes = -unlevered_taxes_raw

    # Inject levered taxes and MRA into the opex DataFrame for waterfall
    opex_with_tax = opex.copy()
    opex_with_tax["taxes_usd"] = levered_taxes.values
    opex_with_tax["mra_contribution_usd"] = mra_series.values

    # Build waterfall
    waterfall = build_cash_flow_waterfall(
        lifetime_revenue=revenue,
        lifetime_opex=opex_with_tax,
        debt_schedule=full_debt,
        capex={"initial_capex_usd": initial_capex_usd},
    )

    # Build date series for XIRR/XNPV
    cod = pd.Timestamp(cod_date)
    dates = pd.Series(
        [cod + pd.DateOffset(years=int(y)) for y in waterfall.index],
        index=waterfall.index,
    )

    # after_tax_project_cf mirrors Financial!134 = pre-tax FCF + signed unlevered tax row.
    after_tax_project_cf = waterfall["ebitda_usd"].copy()
    after_tax_project_cf.iloc[0] = -initial_capex_usd
    after_tax_project_cf.loc[year_index] += unlevered_taxes.values

    # project_irr = workbook G123 = unlevered pre-tax FCF.
    project_cf = waterfall["ebitda_usd"].copy()
    project_cf.iloc[0] = -initial_capex_usd  # Year 0 = full capex outflow

    # equity_irr = workbook G136 = unlevered after-tax FCF.
    equity_cf = after_tax_project_cf  # already has year 0 = -capex

    # unlevered_irr = workbook G189 = levered equity IRR on FCFE.
    # npv_usd = workbook G193 = XNPV on the same FCFE series.
    unlevered_cf = waterfall["free_cash_flow_to_equity_usd"].copy()
    unlevered_cf.iloc[0] = -(initial_capex_usd - debt_amount_usd)  # equity contribution at year 0

    results: dict[str, Any] = {}
    results["year1_opex_usd"] = float(
        opex_with_tax["o_and_m_usd"].iloc[0]
        + opex_with_tax["insurance_usd"].iloc[0]
        + opex_with_tax["land_lease_usd"].iloc[0]
        + opex_with_tax["management_fees_usd"].iloc[0]
        + opex_with_tax["mra_contribution_usd"].iloc[0]
    )
    results["year1_ebitda_usd"] = float(ebitda_series.iloc[0])

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
        results["after_tax_project_irr"] = calculate_project_irr(after_tax_project_cf, dates)
    except Exception as exc:
        logger.warning("After-tax project IRR calculation failed: %s", exc)
        results["after_tax_project_irr"] = float("nan")

    try:
        results["npv_usd"] = calculate_npv(unlevered_cf, dates, discount_rate_pct)
    except Exception as exc:
        logger.warning("NPV calculation failed: %s", exc)
        results["npv_usd"] = float("nan")

    try:
        results["after_tax_npv_usd"] = calculate_npv(after_tax_project_cf, dates, discount_rate_pct)
    except Exception as exc:
        logger.warning("After-tax NPV calculation failed: %s", exc)
        results["after_tax_npv_usd"] = float("nan")

    # DSCR
    debt_service_years = full_debt.loc[full_debt["total_debt_service_usd"] > 0]
    if len(debt_service_years) > 0:
        dscr_series = calculate_dscr_series(
            (ebitda_series + levered_taxes).loc[debt_service_years.index],
            debt_service_years["total_debt_service_usd"],
        )
        results["dscr_min"] = float(dscr_series.min())
        results["dscr_avg"] = float(dscr_series.mean())
    else:
        results["dscr_min"] = float("nan")
        results["dscr_avg"] = float("nan")
        dscr_series = pd.Series(dtype=float)

    results["debt_amount_usd"] = debt_amount_usd

    # Payback metrics
    results["simple_payback_years"] = calculate_simple_payback(
        total_capex_usd=initial_capex_usd,
        year1_ebitda_usd=results["year1_ebitda_usd"],
    )

    try:
        results["discounted_payback_year"] = calculate_discounted_payback(
            cashflows=project_cf,
            dates=dates,
            discount_rate_pct=discount_rate_pct,
        )
    except Exception as exc:
        logger.warning("Discounted payback calculation failed: %s", exc)
        results["discounted_payback_year"] = None

    equity_invested = initial_capex_usd - debt_amount_usd
    year1_fcfe = float(waterfall["free_cash_flow_to_equity_usd"].iloc[0]) if len(waterfall) > 0 else 0.0
    results["cash_on_cash_yield"] = calculate_cash_on_cash_yield(
        year1_fcfe_usd=year1_fcfe,
        equity_invested_usd=equity_invested,
    )

    annual = waterfall.loc[year_index].copy()
    annual["dppa_revenue_usd"] = revenue["dppa_revenue_usd"].values
    annual["grid_savings_usd"] = revenue["grid_savings_usd"].values
    annual["demand_charge_savings_usd"] = revenue["demand_charge_savings_usd"].values
    annual["dscr"] = dscr_series.reindex(year_index).astype(float)

    results["_annual_df"] = annual.reset_index(drop=True)

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
    ppa_option: int | None = None,
    base_params: dict[str, Any] | None = None,
    dppa_topology: str = "onsite",
    tariff_mode: str = "1-component",
    cp_demand_vnd_per_kw: float | None = None,
    ca_tariff_rates: dict[TimePeriod, float] | None = None,
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
    if dppa_topology not in {"onsite", "offsite"}:
        raise ValueError(f"dppa_topology must be 'onsite' or 'offsite', got {dppa_topology!r}")
    _validate_tariff_mode(tariff_mode)

    excel_path = Path(excel_path)
    logger.info(
        "Running full model on %s (topology: %s, tariff: %s)",
        excel_path.name,
        dppa_topology,
        tariff_mode,
    )

    financial_params = load_financial_params_from_cells(excel_path)
    assumption_updates, financial_updates = _split_pipeline_overrides(base_params, financial_params)
    financial_params.update(financial_updates)
    project_years_effective = int(financial_params["project_years"])
    interest_rate_effective = float(financial_params["interest_rate_pct"])
    tenor_years_effective = int(financial_params["tenor_years"])
    target_dscr_effective = float(financial_params["target_dscr"])
    initial_capex_effective = float(financial_params["initial_capex_usd"])
    discount_rate_effective = float(financial_params["discount_rate_pct"])
    cod_date_effective = str(financial_params["cod_date"])
    exchange_rate_effective = float(financial_params["exchange_rate_usd_vnd"])
    max_leverage_effective = float(financial_params["max_leverage_ratio"])
    # Default 5% DPPA escalation, -5% FMP descent (Financial!H16, H18)
    revenue_escalation_effective = float(
        financial_params.get(
            "revenue_escalation_pct", financial_params.get("dppa_escalation_rate", 0.05)
        )
    )
    fmp_descent_effective = float(
        financial_params.get("fmp_descent_pct", financial_params.get("fmp_change_rate", -0.05))
    )
    ppa_option_effective = (
        ppa_option if ppa_option is not None else int(financial_params.get("ppa_option", 3))
    )

    # --- Workbook-level diagnostics ---
    freshness_warnings = validate_financial_solver_freshness(str(excel_path))
    for warning in freshness_warnings:
        logger.warning("%s", warning)

    # --- Load inputs ---
    assumptions = load_assumptions_from_cells(excel_path)
    # Override ppa_option if specified at call site or from loader
    assumptions = assumptions.model_copy(
        update={
            "ppa_option": ppa_option_effective,
            "bundled_discount_pct": float(financial_params.get("bundled_discount_pct", 0.15)),
            "pv_discount_pct": float(financial_params.get("pv_discount_pct", 0.05)),
            "bess_discount_pct": float(financial_params.get("bess_discount_pct", 0.05)),
            "fixed_ppa_price_usd_per_mwh": float(
                financial_params.get("fixed_ppa_price_usd_per_mwh", 70.0)
            ),
            **assumption_updates,
        }
    )
    hourly_data = _normalize_hourly_price_columns_to_usd(
        load_hourly_data(excel_path),
        exchange_rate_effective,
    )
    degradation_table = load_degradation_table(
        excel_path,
        project_years=project_years_effective,
    )

    try:
        schedule = load_tariff_schedule(
            excel_path,
            sheet_name=str(financial_params.get("tariff_schedule_sheet", "Tariff Schedule")),
        )
    except Exception:
        try:
            schedule = load_tariff_schedule_from_calc(excel_path)
        except Exception as exc2:
            logger.warning("Tariff schedule load failed: %s — using defaults", exc2)
            schedule = {
                TimePeriod.OFF_PEAK: list(range(0, 7)),
                TimePeriod.STANDARD: list(range(7, 17)),
                TimePeriod.PEAK: list(range(17, 24)),
            }

    if tariff_rates is None:
        tariff_rates = load_tariff_rates_from_cells(excel_path)

    # For 2-component tariff, settle energy on the lower Ca rates when supplied.
    effective_tariff_rates = (
        ca_tariff_rates
        if tariff_mode == "2-component" and ca_tariff_rates
        else tariff_rates
    )

    # --- Stage A: Physics ---
    hourly_result = _run_physics(hourly_data, assumptions, schedule)

    # --- Stage B: Settlement ---
    settlement_result = _run_settlement(
        hourly_result, assumptions, effective_tariff_rates, dppa_topology
    )

    # --- Stage C: Aggregation ---
    agg = _run_aggregation(
        settlement_result,
        settlement_result,  # dppa columns are already in the same DF
        assumptions,
        degradation_table,
        project_years=project_years_effective,
        revenue_escalation_pct=revenue_escalation_effective,
        fmp_descent_pct=fmp_descent_effective,
    )

    # Demand charge savings — use capacity tariff from Excel if available.
    # For 2-component (energy+capacity) EVN tariff, the capacity component is
    # in USD/MW/year (Financial!H32). Convert to VND/kW for the shared helper:
    #   cp_vnd_per_kw = (USD/MW/year × FX) / (kW/MW) = USD/kW/year × FX
    # Demand-charge savings are a two-component-tariff feature: under a single
    # energy rate there is no capacity charge to reduce, so Cp stays zero.
    if tariff_mode == "2-component":
        if cp_demand_vnd_per_kw is not None:
            cp_demand_effective = float(cp_demand_vnd_per_kw)
        else:
            capacity_demand_rate_usd_per_mw = float(
                financial_params.get("capacity_demand_rate_usd_per_mw", 0.0)
            )
            cp_demand_effective = (
                capacity_demand_rate_usd_per_mw / 1000.0 * exchange_rate_effective
                if capacity_demand_rate_usd_per_mw > 0 and exchange_rate_effective > 0
                else float(financial_params.get("cp_demand_vnd_per_kw", 0.0))
            )
    else:
        cp_demand_effective = 0.0

    demand_savings_yr1 = calculate_annual_demand_savings(
        monthly_data=agg["monthly"],
        cp_demand_vnd_per_kw=cp_demand_effective,
        exchange_rate_usd_vnd=exchange_rate_effective,
    )

    # Topology masking for offsite: zero out demand charge savings
    if dppa_topology == "offsite":
        demand_savings_yr1 = 0.0

    # Grid savings = factory's utility bill reduction. For all PPA structures, the project only
    # receives its PPA cash flows (dppa_revenue_usd). Grid savings accrue to the off-taker.
    lifetime_for_financial = agg["lifetime"].copy()
    lifetime_for_financial["grid_savings_usd"] = 0.0

    # --- Stage D: Financial ---
    financial_kpis = _run_financial(
        lifetime=lifetime_for_financial,
        project_years=project_years_effective,
        interest_rate_pct=interest_rate_effective,
        tenor_years=tenor_years_effective,
        target_dscr=target_dscr_effective,
        initial_capex_usd=initial_capex_effective,
        discount_rate_pct=discount_rate_effective,
        cod_date=cod_date_effective,
        max_leverage_ratio=max_leverage_effective,
        solar_capacity_mwp=float(
            financial_params.get(
                "solar_capacity_mwp", financial_params.get("installed_pv_mwp", 0.0)
            )
        ),
        bess_capacity_mwh=float(
            financial_params.get("bess_capacity_mwh", financial_params.get("bess_mwh", 0.0))
        ),
        om_solar_usd_per_mwp=float(financial_params.get("om_solar_usd_per_mwp", 8_000.0)),
        om_bess_usd_per_mwh=float(financial_params.get("om_bess_usd_per_mwh", 5_000.0)),
        insurance_pct_capex=float(
            financial_params.get(
                "insurance_pct_capex",
                financial_params.get("insurance_solar_pct_capex", 0.0025)
                + financial_params.get("insurance_bess_pct_capex", 0.0025),
            )
        ),
        asset_management_usd=float(financial_params.get("asset_management_usd", 15_000.0)),
        land_lease_usd=float(financial_params.get("land_lease_usd", 20_000.0)),
        cpi=float(financial_params.get("cpi", financial_params.get("opex_escalation_pct", 0.04))),
        tax_rate=float(financial_params.get("tax_rate", 0.20)),
        tax_holiday_years=int(financial_params.get("tax_holiday_years", 4)),
        first_discount_years=int(financial_params.get("first_discount_years", 5)),
        first_discount_rate=float(financial_params.get("first_discount_rate", 0.10)),
        second_discount_years=int(financial_params.get("second_discount_years", 0)),
        second_discount_rate=float(financial_params.get("second_discount_rate", 0.0)),
        pv_depreciation_tenor_years=int(financial_params.get("pv_depreciation_tenor_years", 20)),
        bess_depreciation_tenor_years=int(
            financial_params.get("bess_depreciation_tenor_years", 10)
        ),
        bess_capex_usd=float(financial_params.get("bess_capex_usd", 0.0)),
        pv_capex_usd=float(financial_params.get("solar_capex_usd", 0.0)),
        bess_mra_pct=float(financial_params.get("bess_mra_pct", 0.60)),
        pv_mra_pct=float(financial_params.get("pv_mra_pct", 0.10)),
        mra_buildup_schedule=financial_params.get("mra_buildup_schedule"),
        demand_charge_savings_usd_yr1=demand_savings_yr1,
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
    year1_grid_savings = float(year1.loc[1, "total_grid_savings_usd"])
    results["year1_grid_savings_usd"] = year1_grid_savings if dppa_topology == "onsite" else 0.0

    # Record topology and tariff mode
    results["dppa_topology"] = dppa_topology
    results["tariff_mode"] = tariff_mode
    results["demand_charge_savings_usd"] = float(demand_savings_yr1)

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
    ppa_option: int | None = None,
    base_params: dict[str, Any] | None = None,
    dppa_topology: str = "onsite",
    tariff_mode: str = "1-component",
    cp_demand_vnd_per_kw: float | None = None,
    ca_tariff_rates: dict[TimePeriod, float] | None = None,
) -> dict[str, Any]:
    """
    Run the full RE-Storage pipeline using JSON+CSV project inputs.

    Returns the same scalar KPI keys as run_full_model, plus report-friendly
    DataFrames under underscore-prefixed keys: _hourly_df and _lifetime_df.

    When ``tariff_mode == "2-component"`` the energy settlement uses
    ``ca_tariff_rates`` (lower Ca rates) when supplied, and the capacity charge
    ``cp_demand_vnd_per_kw`` activates demand-charge savings.  Both fall back to
    the project JSON's ``retail_tariff_matrix`` values when not passed explicitly.
    """
    if dppa_topology not in {"onsite", "offsite"}:
        raise ValueError(f"dppa_topology must be 'onsite' or 'offsite', got {dppa_topology!r}")
    _validate_tariff_mode(tariff_mode)

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
    assumption_updates, financial_updates = _split_pipeline_overrides(base_params, financial_params)
    financial_params.update(financial_updates)
    project_years = int(financial_params["project_years"])
    degradation_table = load_degradation_from_json(json_path, project_years=project_years)

    # Load tariff schedule from JSON if present; fall back to TOU2024 default.
    # The default below reflects the pre-April-2026 Vietnamese EVN TOU schedule
    # (morning peak 10–11, afternoon peak 17–19) used before TOU2026 took effect.
    schedule = load_tariff_schedule_from_json(json_path) or {
        TimePeriod.OFF_PEAK: [0, 1, 2, 3, 22, 23],
        TimePeriod.STANDARD: [4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 20, 21],
        TimePeriod.PEAK: [10, 11, 17, 18, 19],
    }

    if tariff_rates is None:
        tariff_rates = load_tariff_rates_from_json(json_path)

    exchange_rate_usd_vnd = float(financial_params["exchange_rate_usd_vnd"])
    if exchange_rate_usd_vnd <= 0:
        raise ValueError("exchange_rate_usd_vnd must be positive")

    hourly_data = _normalize_hourly_price_columns_to_usd(hourly_data, exchange_rate_usd_vnd)

    ppa_option_effective = (
        ppa_option
        if ppa_option is not None
        else int(financial_params.get("ppa_option", assumptions.ppa_option))
    )
    assumptions = assumptions.model_copy(
        update={
            "actual_capacity_kwp": assumption_updates.get(
                "actual_capacity_kwp",
                float(
                    financial_params.get(
                        "installed_pv_mwp", assumptions.actual_capacity_kwp / 1000.0
                    )
                )
                * 1000.0,
            ),
            "ppa_option": ppa_option_effective,
            "bundled_discount_pct": float(financial_params.get("bundled_discount_pct", 0.15)),
            "pv_discount_pct": float(financial_params.get("pv_discount_pct", 0.05)),
            "bess_discount_pct": float(financial_params.get("bess_discount_pct", 0.05)),
            "fixed_ppa_price_usd_per_mwh": float(
                financial_params.get("fixed_ppa_price_usd_per_mwh", 70.0)
            ),
            "fixed_ppa_curtailment_pct": float(
                financial_params.get("fixed_ppa_curtailment_pct", 0.0)
            ),
            "fixed_ppa_tx_loss_pct": float(financial_params.get("fixed_ppa_tx_loss_pct", 0.0)),
            **assumption_updates,
        }
    )

    # For 2-component tariff, settle energy on the lower Ca rates when supplied.
    effective_tariff_rates = (
        ca_tariff_rates
        if tariff_mode == "2-component" and ca_tariff_rates
        else tariff_rates
    )

    hourly_result = _run_physics(hourly_data, assumptions, schedule)
    settlement_result = _run_settlement(
        hourly_result, assumptions, effective_tariff_rates, dppa_topology
    )
    rev_esc = float(
        financial_params.get(
            "revenue_escalation_pct", financial_params.get("dppa_escalation_rate", 0.05)
        )
    )
    fmp_desc = float(
        financial_params.get("fmp_descent_pct", financial_params.get("fmp_change_rate", -0.05))
    )
    agg = _run_aggregation(
        settlement_result,
        settlement_result,
        assumptions,
        degradation_table,
        project_years=project_years,
        revenue_escalation_pct=rev_esc,
        fmp_descent_pct=fmp_desc,
    )

    initial_capex_usd = float(financial_params["initial_capex_usd"])

    # Compute demand-charge savings for JSON path. These are a two-component
    # tariff feature; under a single energy rate Cp stays zero.
    exchange_rate_usd_vnd = float(financial_params.get("exchange_rate_usd_vnd", 25_000.0))
    if tariff_mode == "2-component":
        cp_demand_effective = (
            float(cp_demand_vnd_per_kw)
            if cp_demand_vnd_per_kw is not None
            else float(financial_params.get("cp_demand_vnd_per_kw", 0.0))
        )
    else:
        cp_demand_effective = 0.0
    demand_savings_yr1 = 0.0
    if cp_demand_effective > 0 and exchange_rate_usd_vnd > 0:
        demand_savings_yr1 = calculate_annual_demand_savings(
            monthly_data=agg["monthly"],
            cp_demand_vnd_per_kw=cp_demand_effective,
            exchange_rate_usd_vnd=exchange_rate_usd_vnd,
        )
    # Topology masking for offsite
    if dppa_topology == "offsite":
        demand_savings_yr1 = 0.0

    financial_kpis = _run_financial(
        lifetime=agg["lifetime"],
        project_years=project_years,
        interest_rate_pct=float(financial_params["interest_rate_pct"]),
        tenor_years=int(financial_params["tenor_years"]),
        target_dscr=float(financial_params["target_dscr"]),
        initial_capex_usd=initial_capex_usd,
        discount_rate_pct=float(financial_params["discount_rate_pct"]),
        cod_date=str(financial_params["cod_date"]),
        max_leverage_ratio=float(financial_params.get("max_leverage_ratio", 1.0)),
        solar_capacity_mwp=float(
            financial_params.get(
                "solar_capacity_mwp", financial_params.get("installed_pv_mwp", 0.0)
            )
        ),
        bess_capacity_mwh=float(
            financial_params.get("bess_capacity_mwh", financial_params.get("bess_mwh", 0.0))
        ),
        om_solar_usd_per_mwp=float(financial_params.get("om_solar_usd_per_mwp", 8_000.0)),
        om_bess_usd_per_mwh=float(financial_params.get("om_bess_usd_per_mwh", 5_000.0)),
        insurance_pct_capex=float(
            financial_params.get(
                "insurance_pct_capex",
                float(financial_params.get("insurance_solar_pct_capex", 0.0025))
                + float(financial_params.get("insurance_bess_pct_capex", 0.0025)),
            )
        ),
        other_opex_usd_per_mwp=float(financial_params.get("other_opex_usd_per_mwp", 0.0)),
        asset_management_usd_per_mwp=float(
            financial_params.get("asset_management_usd_per_mwp", 0.0)
        ),
        land_lease_pct_revenue=float(financial_params.get("land_lease_pct_revenue", 0.0)),
        asset_management_usd=float(financial_params.get("asset_management_usd", 15_000.0)),
        land_lease_usd=float(financial_params.get("land_lease_usd", 20_000.0)),
        cpi=float(financial_params.get("cpi", financial_params.get("opex_escalation_pct", 0.04))),
        tax_rate=float(financial_params.get("tax_rate", 0.20)),
        tax_holiday_years=int(financial_params.get("tax_holiday_years", 4)),
        first_discount_years=int(financial_params.get("first_discount_years", 5)),
        first_discount_rate=float(financial_params.get("first_discount_rate", 0.10)),
        second_discount_years=int(financial_params.get("second_discount_years", 0)),
        second_discount_rate=float(financial_params.get("second_discount_rate", 0.0)),
        pv_depreciation_tenor_years=int(financial_params.get("pv_depreciation_tenor_years", 20)),
        bess_depreciation_tenor_years=int(
            financial_params.get("bess_depreciation_tenor_years", 10)
        ),
        bess_capex_usd=float(financial_params.get("bess_capex_usd", 0.0)),
        pv_capex_usd=float(financial_params.get("solar_capex_usd", 0.0)),
        bess_mra_pct=float(financial_params.get("bess_mra_pct", 0.60)),
        pv_mra_pct=float(financial_params.get("pv_mra_pct", 0.10)),
        mra_buildup_schedule=financial_params.get("mra_buildup_schedule"),
        demand_charge_savings_usd_yr1=demand_savings_yr1,
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
    year1_grid_savings = float(year1.loc[1, "total_grid_savings_usd"])
    results["year1_grid_savings_usd"] = year1_grid_savings if dppa_topology == "onsite" else 0.0

    # Record topology and tariff mode
    results["dppa_topology"] = dppa_topology
    results["tariff_mode"] = tariff_mode
    results["demand_charge_savings_usd"] = float(demand_savings_yr1)

    annual_df = financial_kpis.get("_annual_df")
    if isinstance(annual_df, pd.DataFrame):
        results["_annual_df"] = annual_df

    results["_hourly_df"] = settlement_result
    results["_lifetime_df"] = agg["lifetime"]

    return results

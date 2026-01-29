"""
Annual aggregation utilities.

Converts monthly summaries and hourly results into Year 1 totals that
feed the lifetime and financial layers.
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import AnnualTimeSeries, HourlyTimeSeries, MonthlyTimeSeries


def _require_columns(data: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(data.columns)
    if missing:
        raise InputValidationError(
            f"Missing required columns in {label}: {sorted(missing)}"
        )


def calculate_total_solar_generation_mwh(
    hourly_data: HourlyTimeSeries,
    solar_gen_column: str = "solar_gen_kw",
    scale_factor: float = 1.0,
) -> float:
    """
    Calculate total solar generation for Year 1 in MWh.

    Args:
        hourly_data: Hourly data containing solar generation (kW).
        solar_gen_column: Column name for solar generation (kW).
        scale_factor: Scaling factor from simulation to actual capacity.

    Returns:
        Total solar generation (MWh).

    Raises:
        InputValidationError: If inputs are invalid or negative.
    """
    _require_columns(hourly_data, {solar_gen_column}, "hourly_data")

    if scale_factor <= 0:
        raise InputValidationError(
            "scale_factor must be positive.", field="scale_factor", value=scale_factor
        )

    solar_gen_kw = hourly_data[solar_gen_column]
    if (solar_gen_kw < 0).any():
        raise InputValidationError("solar_gen_kw contains negative values.")

    total_kwh = float(solar_gen_kw.sum() * scale_factor)
    return total_kwh / 1000.0


def calculate_total_dppa_revenue_usd(
    dppa_hourly: HourlyTimeSeries,
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> float:
    """
    Calculate total DPPA revenue for Year 1.

    Args:
        dppa_hourly: Hourly DPPA output with revenue column.
        total_dppa_column: Column name for total DPPA revenue (USD).

    Returns:
        Total DPPA revenue (USD).

    Raises:
        InputValidationError: If required columns are missing.
    """
    _require_columns(dppa_hourly, {total_dppa_column}, "dppa_hourly")
    return float(dppa_hourly[total_dppa_column].sum())


def calculate_year1_totals(
    monthly_data: MonthlyTimeSeries,
    hourly_data: HourlyTimeSeries,
    dppa_hourly: HourlyTimeSeries,
    scale_factor: float,
    solar_gen_column: str = "solar_gen_kw",
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> AnnualTimeSeries:
    """
    Build Year 1 totals from monthly and hourly inputs.

    Args:
        monthly_data: Monthly aggregated results.
        hourly_data: Hourly simulation results.
        dppa_hourly: Hourly DPPA results.
        scale_factor: Scaling factor from simulation to actual capacity.
        solar_gen_column: Column name for solar generation (kW).
        total_dppa_column: Column name for total DPPA revenue (USD).

    Returns:
        AnnualTimeSeries with Year 1 totals (index=year).

    Raises:
        InputValidationError: If required columns are missing or invalid.
    """
    _require_columns(
        monthly_data,
        {
            "baseline_peak_kw",
            "demand_target_kw",
            "grid_savings_usd",
            "peak_demand_after_solar_kw",
            "peak_demand_after_re_kw",
        },
        "monthly_data",
    )

    total_solar_generation_mwh = calculate_total_solar_generation_mwh(
        hourly_data, solar_gen_column=solar_gen_column, scale_factor=scale_factor
    )
    total_dppa_revenue_usd = calculate_total_dppa_revenue_usd(
        dppa_hourly, total_dppa_column=total_dppa_column
    )
    total_grid_savings_usd = float(monthly_data["grid_savings_usd"].sum())

    result = pd.DataFrame(
        {
            "year": [1],
            "total_solar_generation_mwh": [total_solar_generation_mwh],
            "total_dppa_revenue_usd": [total_dppa_revenue_usd],
            "total_grid_savings_usd": [total_grid_savings_usd],
            "baseline_peak_kw": [float(monthly_data["baseline_peak_kw"].max())],
            "demand_target_kw": [float(monthly_data["demand_target_kw"].max())],
            "peak_demand_after_solar_kw": [
                float(monthly_data["peak_demand_after_solar_kw"].max())
            ],
            "peak_demand_after_re_kw": [
                float(monthly_data["peak_demand_after_re_kw"].max())
            ],
        }
    )

    return result.set_index("year", drop=False)

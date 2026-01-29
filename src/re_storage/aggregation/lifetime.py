"""
Lifetime projection utilities.

Projects Year 1 metrics across the project lifetime using degradation
factors from the Loss table.
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.exceptions import DegradationTableError, InputValidationError
from re_storage.core.types import AnnualTimeSeries


def _validate_degradation_table(
    degradation_table: pd.DataFrame,
    project_years: int,
) -> None:
    required = {"year", "pv_factor", "battery_factor_with_replacement"}
    missing = required - set(degradation_table.columns)
    if missing:
        raise InputValidationError(
            f"Missing required degradation columns: {sorted(missing)}"
        )

    if (degradation_table["pv_factor"] <= 0).any() or (
        degradation_table["pv_factor"] > 1
    ).any():
        raise InputValidationError("pv_factor must be within (0, 1].")

    if (degradation_table["battery_factor_with_replacement"] <= 0).any() or (
        degradation_table["battery_factor_with_replacement"] > 1
    ).any():
        raise InputValidationError("battery_factor_with_replacement must be within (0, 1].")

    years = set(degradation_table["year"])
    missing_years = [year for year in range(1, project_years + 1) if year not in years]
    if missing_years:
        raise DegradationTableError(
            "Degradation table does not cover all project years.",
            missing_years=missing_years,
        )


def project_lifetime_generation_mwh(
    year1_generation_mwh: float,
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> pd.Series:
    """
    Project solar generation across project lifetime with degradation.

    Args:
        year1_generation_mwh: Year 1 generation (MWh).
        degradation_table: DataFrame with year and pv_factor columns.
        project_years: Number of years in the projection.

    Returns:
        Series of generation (MWh) indexed by year.

    Raises:
        DegradationTableError: If coverage is incomplete.
        InputValidationError: If inputs are invalid.
    """
    if year1_generation_mwh < 0:
        raise InputValidationError("year1_generation_mwh cannot be negative.")

    _validate_degradation_table(degradation_table, project_years)

    factors = degradation_table.set_index("year")["pv_factor"].reindex(
        range(1, project_years + 1)
    )
    if factors.isna().any():
        raise DegradationTableError("Degradation table has missing pv_factor years.")

    return pd.Series(
        [year1_generation_mwh * factors.loc[year] for year in factors.index],
        index=factors.index,
        name="generation_mwh",
    )


def project_battery_capacity_kwh(
    initial_capacity_kwh: float,
    degradation_table: pd.DataFrame,
    replacement_cycle: int = 11,
    project_years: int = 25,
) -> pd.Series:
    """
    Project battery capacity with replacement factors from the Loss table.

    Args:
        initial_capacity_kwh: Starting usable capacity (kWh).
        degradation_table: DataFrame with battery_factor_with_replacement.
        replacement_cycle: Replacement cadence (unused; documented for parity).
        project_years: Number of years in the projection.

    Returns:
        Series of effective capacity (kWh) indexed by year.

    Raises:
        DegradationTableError: If coverage is incomplete.
        InputValidationError: If inputs are invalid.
    """
    if initial_capacity_kwh <= 0:
        raise InputValidationError("initial_capacity_kwh must be positive.")
    if replacement_cycle <= 0:
        raise InputValidationError("replacement_cycle must be positive.")

    _validate_degradation_table(degradation_table, project_years)

    factors = degradation_table.set_index("year")["battery_factor_with_replacement"].reindex(
        range(1, project_years + 1)
    )
    if factors.isna().any():
        raise DegradationTableError(
            "Degradation table has missing battery_factor_with_replacement years."
        )

    return pd.Series(
        [initial_capacity_kwh * factors.loc[year] for year in factors.index],
        index=factors.index,
        name="battery_capacity_kwh",
    )


def build_lifetime_projection(
    year1_totals: AnnualTimeSeries,
    degradation_table: pd.DataFrame,
    initial_capacity_kwh: float,
    project_years: int = 25,
    replacement_cycle: int = 11,
) -> AnnualTimeSeries:
    """
    Build lifetime projection from Year 1 totals and degradation factors.

    Args:
        year1_totals: AnnualTimeSeries with Year 1 totals.
        degradation_table: Loss table with degradation factors.
        initial_capacity_kwh: Initial battery capacity (kWh).
        project_years: Projection length in years.
        replacement_cycle: Battery replacement cadence.

    Returns:
        AnnualTimeSeries indexed by year with unit-suffixed columns.

    Raises:
        InputValidationError: If required inputs are missing.
    """
    required = {
        "total_solar_generation_mwh",
        "total_dppa_revenue_usd",
        "total_grid_savings_usd",
    }
    missing = required - set(year1_totals.columns)
    if missing:
        raise InputValidationError(
            f"Missing required year1_totals columns: {sorted(missing)}"
        )
    if 1 not in year1_totals.index:
        raise InputValidationError("year1_totals must include year=1 index.")

    year1_generation_mwh = float(year1_totals.loc[1, "total_solar_generation_mwh"])
    year1_dppa_revenue_usd = float(year1_totals.loc[1, "total_dppa_revenue_usd"])
    year1_grid_savings_usd = float(year1_totals.loc[1, "total_grid_savings_usd"])

    generation_mwh = project_lifetime_generation_mwh(
        year1_generation_mwh,
        degradation_table,
        project_years=project_years,
    )
    battery_capacity_kwh = project_battery_capacity_kwh(
        initial_capacity_kwh,
        degradation_table,
        replacement_cycle=replacement_cycle,
        project_years=project_years,
    )

    if year1_generation_mwh > 0:
        pv_factors = generation_mwh / year1_generation_mwh
    else:
        pv_factors = pd.Series(0.0, index=generation_mwh.index)

    dppa_revenue_usd = year1_dppa_revenue_usd * pv_factors
    grid_savings_usd = year1_grid_savings_usd * pv_factors

    result = pd.DataFrame(
        {
            "year": generation_mwh.index,
            "generation_mwh": generation_mwh.values,
            "battery_capacity_kwh": battery_capacity_kwh.values,
            "dppa_revenue_usd": dppa_revenue_usd.values,
            "grid_savings_usd": grid_savings_usd.values,
        }
    )

    return result.set_index("year", drop=False)

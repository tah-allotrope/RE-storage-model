"""
Grid expense and savings calculations.

This module calculates business-as-usual (BAU) grid costs, grid costs after
renewables, and savings due to solar + BESS.
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import TimePeriod


def calculate_energy_expense(
    energy_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series:
    """
    Calculate grid energy expense based on tariff period.

    Args:
        energy_kwh: Energy consumption (kWh) per timestep.
        time_period: TimePeriod for each timestep.
        tariff_rates_usd_per_kwh: Tariff rate per TimePeriod.

    Returns:
        Series of energy expense (USD).

    Raises:
        InputValidationError: If energy is negative or tariff rates missing.
    """
    if (energy_kwh < 0).any():
        raise InputValidationError("Cannot calculate expense with negative energy values.")

    missing_rates = {period for period in time_period.unique() if period not in tariff_rates_usd_per_kwh}
    if missing_rates:
        raise InputValidationError(
            f"Missing tariff rate for periods: {sorted(missing_rates)}"
        )

    rates = time_period.map(tariff_rates_usd_per_kwh)
    if rates.isna().any():
        raise InputValidationError("Time period contains invalid values.")

    return energy_kwh * rates


def calculate_bau_expense(
    load_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series:
    """
    Calculate business-as-usual grid expense.
    """
    return calculate_energy_expense(load_kwh, time_period, tariff_rates_usd_per_kwh)


def calculate_re_expense(
    grid_load_after_re_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series:
    """
    Calculate grid expense after renewables.
    """
    return calculate_energy_expense(grid_load_after_re_kwh, time_period, tariff_rates_usd_per_kwh)


def calculate_demand_charges(
    peak_demand_kw: float,
    demand_charge_rate_usd_per_kw: float,
) -> float:
    """
    Calculate demand charges from peak demand.

    Args:
        peak_demand_kw: Peak demand (kW).
        demand_charge_rate_usd_per_kw: Demand charge rate ($/kW).

    Returns:
        Demand charges (USD).

    Raises:
        InputValidationError: If inputs are negative.
    """
    if peak_demand_kw < 0:
        raise InputValidationError(f"peak_demand_kw cannot be negative: {peak_demand_kw}")
    if demand_charge_rate_usd_per_kw < 0:
        raise InputValidationError(
            f"demand_charge_rate_usd_per_kw cannot be negative: {demand_charge_rate_usd_per_kw}"
        )

    return peak_demand_kw * demand_charge_rate_usd_per_kw


def calculate_grid_savings(bau_expense_usd: pd.Series, re_expense_usd: pd.Series) -> pd.Series:
    """
    Calculate grid savings as BAU expense minus RE expense.
    """
    return bau_expense_usd - re_expense_usd

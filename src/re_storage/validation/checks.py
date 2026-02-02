"""
Cross-cutting validation checks for the RE-Storage model.

These helpers aggregate physics, settlement, and financial validations into
warnings so users can review issues without losing the full audit trail.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from re_storage.core.exceptions import EnergyBalanceError, InputValidationError, SoCBoundsError
from re_storage.core.types import HourlyTimeSeries, MonthlyTimeSeries
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.physics.balance import (
    validate_energy_balance_vectorized,
    validate_soc_bounds_vectorized,
)


def _require_columns(data: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(data.columns)
    if missing:
        raise InputValidationError(
            f"Missing required columns in {label}: {sorted(missing)}"
        )


def _with_year_index(data: pd.DataFrame, label: str) -> pd.DataFrame:
    _require_columns(data, {"year"}, label)
    result = data.copy()
    return result.set_index("year", drop=False)


def validate_energy_balance_series(
    hourly_results: HourlyTimeSeries,
    solar_gen_column: str = "solar_gen_kwh",
    direct_consumption_column: str = "direct_consumption_kwh",
    charged_column: str = "charged_kwh",
    surplus_column: str = "surplus_kwh",
    tolerance: float = 0.001,
) -> list[str]:
    """
    Validate hourly energy balance and return warnings if violated.

    Args:
        hourly_results: Hourly results containing energy balance columns.
        solar_gen_column: Column name for solar generation (kWh).
        direct_consumption_column: Column name for direct consumption (kWh).
        charged_column: Column name for charged energy (kWh).
        surplus_column: Column name for surplus energy (kWh).
        tolerance: Acceptable imbalance per timestep (kWh).

    Returns:
        List of warning strings. Empty if no violations.

    Raises:
        InputValidationError: If required columns are missing.
    """
    _require_columns(
        hourly_results,
        {solar_gen_column, direct_consumption_column, charged_column, surplus_column},
        "hourly_results",
    )

    try:
        validate_energy_balance_vectorized(
            solar_gen_kwh=hourly_results[solar_gen_column].to_numpy(dtype=float),
            direct_consumption_kwh=hourly_results[direct_consumption_column].to_numpy(
                dtype=float
            ),
            charged_kwh=hourly_results[charged_column].to_numpy(dtype=float),
            surplus_kwh=hourly_results[surplus_column].to_numpy(dtype=float),
            tolerance=tolerance,
        )
    except EnergyBalanceError as exc:
        return [str(exc)]

    return []


def validate_soc_bounds_series(
    hourly_results: HourlyTimeSeries,
    max_capacity_kwh: float,
    soc_column: str = "soc_kwh",
    tolerance: float = 0.001,
) -> list[str]:
    """
    Validate hourly SoC bounds and return warnings if violated.

    Args:
        hourly_results: Hourly results containing SoC column.
        max_capacity_kwh: Usable battery capacity (kWh).
        soc_column: Column name for state of charge (kWh).
        tolerance: Acceptable SoC tolerance (kWh).

    Returns:
        List of warning strings. Empty if no violations.

    Raises:
        InputValidationError: If required columns are missing or inputs invalid.
    """
    _require_columns(hourly_results, {soc_column}, "hourly_results")
    if max_capacity_kwh <= 0:
        raise InputValidationError(
            "max_capacity_kwh must be positive.",
            field="max_capacity_kwh",
            value=max_capacity_kwh,
        )

    try:
        validate_soc_bounds_vectorized(
            soc_kwh=hourly_results[soc_column].to_numpy(dtype=float),
            max_capacity_kwh=max_capacity_kwh,
            tolerance=tolerance,
        )
    except SoCBoundsError as exc:
        return [f"SoC bounds violation: {exc}"]

    return []


def validate_dppa_revenue(
    lifetime_results: pd.DataFrame,
    dppa_enabled: bool,
    revenue_column: str = "dppa_revenue_usd",
) -> list[str]:
    """
    Validate DPPA revenue presence when the module is enabled.

    Args:
        lifetime_results: Lifetime results containing DPPA revenue column.
        dppa_enabled: Whether DPPA is enabled in assumptions.
        revenue_column: Column name for DPPA revenue (USD).

    Returns:
        List of warning strings. Empty if no violations.

    Raises:
        InputValidationError: If required columns are missing.
    """
    _require_columns(lifetime_results, {revenue_column}, "lifetime_results")

    if not dppa_enabled:
        return []

    total_revenue = float(lifetime_results[revenue_column].sum())
    if total_revenue == 0:
        return [
            "DPPA is enabled but total DPPA revenue is $0. Check DPPA inputs and toggles."
        ]

    return []


def validate_degradation_coverage(
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> list[str]:
    """
    Validate degradation table coverage over the full project horizon.

    Args:
        degradation_table: Degradation table with year entries.
        project_years: Expected number of project years.

    Returns:
        List of warning strings. Empty if coverage is complete.

    Raises:
        InputValidationError: If required columns are missing or inputs invalid.
    """
    _require_columns(degradation_table, {"year"}, "degradation_table")
    if project_years <= 0:
        raise InputValidationError(
            "project_years must be positive.", field="project_years", value=project_years
        )

    years = set(int(year) for year in degradation_table["year"].tolist())
    missing_years = [year for year in range(1, project_years + 1) if year not in years]
    if missing_years:
        return [
            "Degradation table missing years: "
            f"{missing_years}. Coverage must include 1..{project_years}."
        ]

    return []


def validate_augmentation_funding(
    lifetime_results: pd.DataFrame,
    augmentation_years: list[int] | None = None,
    augmentation_capex_column: str = "augmentation_capex_usd",
    mra_balance_column: str = "mra_balance_usd",
) -> list[str]:
    """
    Validate that augmentation capex is covered by MRA balances.

    Args:
        lifetime_results: Lifetime results with augmentation and MRA columns.
        augmentation_years: Years in which augmentation is expected.
        augmentation_capex_column: Column name for augmentation capex (USD).
        mra_balance_column: Column name for MRA balance (USD).

    Returns:
        List of warning strings. Empty if MRA covers augmentation.

    Raises:
        InputValidationError: If required columns are missing.
    """
    _require_columns(
        lifetime_results,
        {"year", augmentation_capex_column, mra_balance_column},
        "lifetime_results",
    )

    data = _with_year_index(lifetime_results, "lifetime_results")
    years_to_check: Iterable[int] = augmentation_years or [11, 22]

    warnings: list[str] = []
    for year in years_to_check:
        if year not in data.index:
            continue
        augmentation_capex = float(data.loc[year, augmentation_capex_column])
        mra_balance = float(data.loc[year, mra_balance_column])
        if augmentation_capex > mra_balance:
            warnings.append(
                "Augmentation funding shortfall in year "
                f"{year}: capex ${augmentation_capex:,.0f} exceeds MRA balance "
                f"${mra_balance:,.0f}. Equity top-up required."
            )

    return warnings


def validate_full_model(
    hourly_results: HourlyTimeSeries,
    monthly_results: MonthlyTimeSeries,
    lifetime_results: pd.DataFrame,
    assumptions: SystemAssumptions,
    degradation_table: pd.DataFrame | None = None,
    project_years: int = 25,
    augmentation_years: list[int] | None = None,
) -> list[str]:
    """
    Run all validation checks and return consolidated warnings.

    Args:
        hourly_results: Hourly simulation outputs.
        monthly_results: Monthly aggregated results (reserved for future checks).
        lifetime_results: Lifetime projection data.
        assumptions: System assumptions with toggles and capacity.
        degradation_table: Optional degradation table for coverage checks.
        project_years: Expected project lifetime in years.

    Returns:
        List of warning strings aggregated from all checks.
    """
    _ = monthly_results

    warnings: list[str] = []
    warnings.extend(validate_energy_balance_series(hourly_results))
    warnings.extend(
        validate_soc_bounds_series(
            hourly_results, max_capacity_kwh=assumptions.usable_bess_capacity_kwh
        )
    )
    warnings.extend(
        validate_dppa_revenue(lifetime_results, dppa_enabled=assumptions.dppa_enabled)
    )
    if degradation_table is not None:
        warnings.extend(
            validate_degradation_coverage(degradation_table, project_years=project_years)
        )
    warnings.extend(
        validate_augmentation_funding(lifetime_results, augmentation_years=augmentation_years)
    )

    return warnings

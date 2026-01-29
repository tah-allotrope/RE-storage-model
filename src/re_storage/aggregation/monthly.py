"""
Monthly aggregation utilities.

Rolls hourly simulation outputs into monthly summaries following the
Helper sheet logic in the Excel model.
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import HourlyTimeSeries, MonthlyTimeSeries


def aggregate_hourly_to_monthly(
    hourly_data: HourlyTimeSeries,
    demand_reduction_target_ratio: float,
    datetime_column: str = "datetime",
    load_column: str = "load_kw",
    bau_expense_column: str = "bau_expense_usd",
    re_expense_column: str = "re_expense_usd",
    grid_after_solar_column: str = "grid_load_after_solar_kw",
    grid_after_re_column: str = "grid_load_after_re_kw",
) -> MonthlyTimeSeries:
    """
    Aggregate hourly results into monthly summaries.

    This mirrors the Helper sheet in the Excel model and produces
    unit-suffixed monthly columns for downstream financial logic.

    Args:
        hourly_data: Hourly simulation output data.
        demand_reduction_target_ratio: Target peak reduction ratio (0-1).
        datetime_column: Column with timestamps.
        load_column: Column with site load (kW).
        bau_expense_column: Column with BAU grid expense (USD).
        re_expense_column: Column with RE grid expense (USD).
        grid_after_solar_column: Column with net load after solar (kW).
        grid_after_re_column: Column with net load after solar + BESS (kW).

    Returns:
        MonthlyTimeSeries with unit-suffixed columns.

    Raises:
        InputValidationError: If required columns are missing or inputs invalid.
    """
    if not 0 <= demand_reduction_target_ratio <= 1:
        raise InputValidationError(
            "demand_reduction_target_ratio must be within [0, 1].",
            field="demand_reduction_target_ratio",
            value=demand_reduction_target_ratio,
        )

    required_columns = {
        datetime_column,
        load_column,
        bau_expense_column,
        re_expense_column,
        grid_after_solar_column,
        grid_after_re_column,
    }
    missing = required_columns - set(hourly_data.columns)
    if missing:
        raise InputValidationError(f"Missing required columns: {sorted(missing)}")

    datetime_series = pd.to_datetime(hourly_data[datetime_column], errors="coerce")
    if datetime_series.isna().any():
        raise InputValidationError("datetime_column contains invalid timestamps.")

    month_index = datetime_series.dt.month

    aggregated = hourly_data.groupby(month_index).agg(
        **{
            "baseline_peak_kw": (load_column, "max"),
            "bau_grid_expense_usd": (bau_expense_column, "sum"),
            "re_grid_expense_usd": (re_expense_column, "sum"),
            "peak_demand_after_solar_kw": (grid_after_solar_column, "max"),
            "peak_demand_after_re_kw": (grid_after_re_column, "max"),
        }
    )

    aggregated["demand_target_kw"] = aggregated["baseline_peak_kw"] * (
        1 - demand_reduction_target_ratio
    )
    aggregated["grid_savings_usd"] = (
        aggregated["bau_grid_expense_usd"] - aggregated["re_grid_expense_usd"]
    )

    ordered_columns = [
        "baseline_peak_kw",
        "demand_target_kw",
        "bau_grid_expense_usd",
        "re_grid_expense_usd",
        "grid_savings_usd",
        "peak_demand_after_solar_kw",
        "peak_demand_after_re_kw",
    ]

    return aggregated[ordered_columns]

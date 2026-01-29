"""
Excel/CSV loaders for RE-Storage inputs.

These functions load raw input sheets and apply validation before
passing data to the physics engine.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from re_storage.core.exceptions import DegradationTableError, InputValidationError
from re_storage.core.types import (
    HOURS_PER_LEAP_YEAR,
    HOURS_PER_YEAR,
    HourlyTimeSeries,
    TimePeriod,
)
from re_storage.inputs.schemas import SystemAssumptions


ASSUMPTIONS_SHEET = "Assumption"
DATA_INPUT_SHEET = "Data Input"
LOSS_SHEET = "Loss"
TARIFF_SHEET = "Tariff Schedule"

REQUIRED_HOURLY_COLUMNS = {
    "datetime",
    "simulation_profile_kw",
    "irradiation_wh_m2",
    "load_kw",
    "fmp_usd_per_kwh",
    "cfmp_usd_per_kwh",
}

REQUIRED_DEGRADATION_COLUMNS = {
    "year",
    "pv_factor",
    "battery_factor_no_replacement",
    "battery_factor_with_replacement",
}


def load_assumptions(path: Path) -> SystemAssumptions:
    """
    Load and validate the Assumption sheet.

    Args:
        path: Path to Excel input file.

    Returns:
        SystemAssumptions instance.

    Raises:
        InputValidationError: If sheet is missing or invalid.
    """
    df = _read_sheet(path, ASSUMPTIONS_SHEET)

    if len(df) != 1:
        raise InputValidationError(
            f"Expected exactly 1 row in {ASSUMPTIONS_SHEET}, got {len(df)}."
        )

    missing = _missing_columns(df, SystemAssumptions.model_fields.keys())
    if missing:
        raise InputValidationError(
            f"Missing required assumptions columns: {sorted(missing)}."
        )

    data = df.iloc[0].to_dict()

    try:
        return SystemAssumptions(**data)
    except ValidationError as exc:  # pragma: no cover - Pydantic raises ValidationError
        raise InputValidationError(f"Assumptions validation failed: {exc}") from exc


def load_hourly_data(path: Path) -> HourlyTimeSeries:
    """
    Load and validate the hourly time series data.

    Args:
        path: Path to Excel input file.

    Returns:
        HourlyTimeSeries DataFrame.

    Raises:
        InputValidationError: If row count or required columns are invalid.
    """
    df = _read_sheet(path, DATA_INPUT_SHEET)

    if len(df) not in (HOURS_PER_YEAR, HOURS_PER_LEAP_YEAR):
        raise InputValidationError(
            f"Expected 8760 or 8784 rows, got {len(df)}. "
            "Check for leap year or incomplete data."
        )

    missing = _missing_columns(df, REQUIRED_HOURLY_COLUMNS)
    if missing:
        raise InputValidationError(f"Missing required hourly columns: {sorted(missing)}.")

    for column in ("simulation_profile_kw", "irradiation_wh_m2", "load_kw"):
        if (df[column] < 0).any():
            raise InputValidationError(
                f"Hourly column '{column}' contains negative values."
            )

    return df


def load_degradation_table(path: Path, project_years: int = 25) -> pd.DataFrame:
    """
    Load and validate the degradation (Loss) table.

    Args:
        path: Path to Excel input file.
        project_years: Expected project length in years.

    Returns:
        DataFrame with degradation factors.

    Raises:
        InputValidationError: If columns or values are invalid.
        DegradationTableError: If year coverage is incomplete.
    """
    df = _read_sheet(path, LOSS_SHEET)

    missing = _missing_columns(df, REQUIRED_DEGRADATION_COLUMNS)
    if missing:
        raise InputValidationError(
            f"Missing required degradation columns: {sorted(missing)}."
        )

    invalid_mask = (
        (df["pv_factor"] <= 0)
        | (df["pv_factor"] > 1)
        | (df["battery_factor_no_replacement"] <= 0)
        | (df["battery_factor_no_replacement"] > 1)
        | (df["battery_factor_with_replacement"] <= 0)
        | (df["battery_factor_with_replacement"] > 1)
    )
    if invalid_mask.any():
        raise InputValidationError("Degradation factors out of range (0, 1].")

    years = set(df["year"].astype(int).tolist())
    missing_years = [year for year in range(1, project_years + 1) if year not in years]
    if missing_years:
        raise DegradationTableError(
            f"Missing degradation years: {missing_years}", missing_years=missing_years
        )

    return df


def load_tariff_schedule(path: Path) -> dict[TimePeriod, list[int]]:
    """
    Load tariff schedule defining peak/off-peak hours.

    Args:
        path: Path to Excel input file.

    Returns:
        Mapping from TimePeriod to list of hours.

    Raises:
        InputValidationError: If the schedule contains invalid hours or periods.
    """
    df = _read_sheet(path, TARIFF_SHEET)

    if _missing_columns(df, {"hour", "period"}):
        raise InputValidationError("Tariff schedule must contain 'hour' and 'period'.")

    if (df["hour"] < 0).any() or (df["hour"] > 23).any():
        raise InputValidationError("Invalid hour in tariff schedule (must be 0-23).")

    period_map = {
        "off_peak": TimePeriod.OFF_PEAK,
        "standard": TimePeriod.STANDARD,
        "peak": TimePeriod.PEAK,
    }

    schedule: dict[TimePeriod, list[int]] = {
        TimePeriod.OFF_PEAK: [],
        TimePeriod.STANDARD: [],
        TimePeriod.PEAK: [],
    }

    for _, row in df.iterrows():
        period_key = str(row["period"]).strip().lower()
        if period_key not in period_map:
            raise InputValidationError(
                f"Invalid tariff period '{row['period']}'. Expected off_peak, standard, peak."
            )
        period = period_map[period_key]
        schedule[period].append(int(row["hour"]))

    return schedule


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    """
    Read a sheet from an Excel file with standard error handling.

    Args:
        path: Path to Excel input file.
        sheet_name: Name of sheet to read.

    Returns:
        DataFrame for the sheet.

    Raises:
        InputValidationError: If sheet cannot be loaded.
    """
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except (FileNotFoundError, OSError, ValueError) as exc:  # pragma: no cover - IO errors
        raise InputValidationError(
            f"Failed to read sheet '{sheet_name}' from {path}: {exc}"
        ) from exc


def _missing_columns(df: pd.DataFrame, required: set[str]) -> set[str]:
    """
    Return the set of missing required columns for a DataFrame.
    """
    return set(required) - set(df.columns)

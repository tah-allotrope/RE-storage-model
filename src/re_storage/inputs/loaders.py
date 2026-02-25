"""
Excel/CSV loaders for RE-Storage inputs.

These functions load raw input sheets and apply validation before
passing data to the physics engine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from pydantic import ValidationError

from re_storage.core.exceptions import DegradationTableError, InputValidationError
from re_storage.core.types import (
    HOURS_PER_LEAP_YEAR,
    HOURS_PER_YEAR,
    HourlyTimeSeries,
    TimePeriod,
)
from re_storage.inputs.schemas import SystemAssumptions

logger = logging.getLogger(__name__)

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


def load_assumptions_from_cells(path: Path) -> SystemAssumptions:
    """
    Load assumptions from the real Excel multi-region Assumption sheet.

    The production Assumption sheet has a complex layout with labels and
    values spread across multiple column pairs (C/E, I/K, O/Q). This
    function reads specific cells by label search rather than expecting
    a flat single-row DataFrame.

    Why: The original load_assumptions expects a preprocessed single-row
    sheet. Real Excel files have 67+ rows with section headers, units,
    and multiple data regions. This function bridges that gap.

    Args:
        path: Path to Excel input file.

    Returns:
        SystemAssumptions instance.

    Raises:
        InputValidationError: If the sheet or required values are missing.
    """
    try:
        wb = load_workbook(str(path), data_only=True, read_only=False)
    except (FileNotFoundError, OSError) as exc:
        raise InputValidationError(
            f"Failed to open Excel file {path}: {exc}"
        ) from exc

    if ASSUMPTIONS_SHEET not in wb.sheetnames:
        wb.close()
        raise InputValidationError(
            f"Sheet '{ASSUMPTIONS_SHEET}' not found in {path}."
        )

    ws = wb[ASSUMPTIONS_SHEET]

    # Build label→value indexes for each column pair
    ce_map = _build_label_map(ws, label_col="C", value_col="E")
    ik_map = _build_label_map(ws, label_col="I", value_col="K")
    oq_map = _build_label_map(ws, label_col="O", value_col="Q")

    def _get(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
        """Case-insensitive substring label lookup."""
        key_lower = key.lower()
        for k, v in mapping.items():
            if key_lower in k.lower():
                return v
        return default

    def _get_exact(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
        """Case-insensitive exact label lookup (no substring)."""
        key_lower = key.strip().lower()
        for k, v in mapping.items():
            if k.strip().lower() == key_lower:
                return v
        return default

    def _float(mapping: dict[str, Any], key: str, default: float = 0.0) -> float:
        val = _get(mapping, key)
        if val is None:
            logger.warning("Assumption '%s' not found, using default %.4f", key, default)
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            logger.warning("Assumption '%s' has non-numeric value %r, using default", key, val)
            return default

    def _int_val(mapping: dict[str, Any], key: str, default: int = 0) -> int:
        return int(_float(mapping, key, float(default)))

    def _bool_val(mapping: dict[str, Any], key: str, default: bool = False) -> bool:
        val = _float(mapping, key, 1.0 if default else 0.0)
        return val >= 0.5

    # --- Map real Excel cells to SystemAssumptions fields ---
    # Column C/E: System parameters
    simulation_capacity_kwp = _float(ce_map, "Simulation Capacity")
    actual_capacity_kwp = _float(ce_map, "Actual installation capacity")
    total_bess_kwh = _float(ce_map, "Total BESS Storage Capacity")
    total_bess_kw = _float(ce_map, "Total BESS Power Output")
    dod = _float(ce_map, "DoD", 0.85)
    half_cycle_eff = _float(ce_map, "HalfCycle Efficiency", 0.95)
    strategy_mode = _int_val(ce_map, "Strategy mode", 1)
    bess_enabled = _bool_val(ce_map, "Does BESS System include", True)
    demand_reduction_target = _float(ce_map, "Demand Reduction Target", 0.2)

    # Charging parameters
    # PV2BESS Pre-Charge Mode: 0=Off (use time window), 1=Time Window, 2=Precharge
    pv2bess_mode = _int_val(ce_map, "PV2BESS Pre-Charge Mode", 0)
    if pv2bess_mode == 0:
        # Mode 0 = Off: charge all surplus PV into battery at ANY hour.
        # Excel debug confirms PVActive2BESS_kW=0 and PVCharged = full surplus
        # at hours 8-14 (whenever solar > load). No time window restriction.
        # We set the window to 0-23 to allow charging at any hour.
        charging_mode = 1  # Time window
        charge_start = 0
        charge_end = 23
        min_direct_pv = 1.0  # Load is fully served first; only true surplus charges BESS
        pv2bess_share = 1.0  # All surplus goes to BESS
    elif pv2bess_mode == 1:
        charging_mode = 1
        charge_start = _int_val(ce_map, "Pre-Charge_StartHour", 10)
        charge_end = _int_val(ce_map, "Pre-Charge_EndHour", 16)
        min_direct_pv = _float(ce_map, "Min PV directly to load", 0.1)
        pv2bess_share = _float(ce_map, "Pre-Charge Share of PV", 0.1)
    else:
        charging_mode = 2  # Precharge to target
        charge_start = _int_val(ce_map, "Pre-Charge_StartHour", 10)
        charge_end = _int_val(ce_map, "Pre-Charge_EndHour", 16)
        min_direct_pv = _float(ce_map, "Min PV directly to load", 0.1)
        pv2bess_share = _float(ce_map, "Pre-Charge Share of PV", 0.1)
    precharge_soc = _float(ce_map, "Precharge_TargetSoC_kWh", 0.0)
    precharge_hour = _int_val(ce_map, "Precharge_TargetHour", 17)

    # Column O/Q: DPPA parameters
    # Use exact matching for short/ambiguous labels to avoid false matches.
    # "k" would substring-match "Ca_peak", "Kpp_22kv", etc.
    dppa_enabled = _bool_val(oq_map, "Does model is actived", True)
    strike_price_vnd = _float(oq_map, "Strike Price", 1800.0)
    k_factor_val = _get_exact(oq_map, "k")
    if k_factor_val is None:
        logger.warning("DPPA k-factor not found, using default 1.02")
        k_factor_val = 1.02
    else:
        k_factor_val = float(k_factor_val)
    kpp_22 = _float(oq_map, "Kpp_22kv", 1.027)
    kpp_110 = _float(oq_map, "Kpp_110kv", 1.009)
    connection_voltage = _float(oq_map, "Connection Voltage Level", 22.0)

    # Column I/K: Financial parameters
    exchange_rate = _float(ik_map, "USD/VND", 26000.0)
    if exchange_rate <= 0:
        exchange_rate = 26000.0

    # Derive usable BESS capacity (total × DoD)
    usable_bess_kwh = total_bess_kwh * dod

    # Select Kpp based on connection voltage
    kpp = kpp_110 if connection_voltage >= 100 else kpp_22

    # Convert strike price from VND to USD/kWh
    # Excel stores strike price in VND/kWh; divide by exchange rate for USD/kWh
    strike_price_usd_per_kwh = strike_price_vnd / exchange_rate

    wb.close()

    try:
        return SystemAssumptions(
            simulation_capacity_kwp=simulation_capacity_kwp,
            actual_capacity_kwp=actual_capacity_kwp,
            usable_bess_capacity_kwh=usable_bess_kwh,
            bess_power_rating_kw=total_bess_kw,
            charge_efficiency=half_cycle_eff,
            discharge_efficiency=half_cycle_eff,
            strategy_mode=strategy_mode,
            charging_mode=charging_mode,
            charge_start_hour=charge_start,
            charge_end_hour=charge_end,
            precharge_target_hour=precharge_hour,
            precharge_target_soc_kwh=precharge_soc,
            min_direct_pv_share=min_direct_pv,
            active_pv2bess_share=pv2bess_share,
            demand_reduction_target=demand_reduction_target,
            strike_price_usd_per_kwh=strike_price_usd_per_kwh,
            k_factor=k_factor_val,
            kpp=kpp,
            bess_enabled=bess_enabled,
            dppa_enabled=dppa_enabled,
        )
    except ValidationError as exc:
        raise InputValidationError(
            f"Assumptions validation failed: {exc}"
        ) from exc


def _build_label_map(
    ws: Any,
    label_col: str,
    value_col: str,
    max_row: int | None = None,
) -> dict[str, Any]:
    """
    Build a {label_string: value} dict from a worksheet column pair.

    Why: The Assumption sheet stores parameters as label/value pairs in
    adjacent columns (e.g., C=label, E=value). This function scans all
    rows and returns a lookup dict for downstream field extraction.

    Args:
        ws: openpyxl worksheet.
        label_col: Column letter for labels (e.g., "C").
        value_col: Column letter for values (e.g., "E").
        max_row: Maximum row to scan. Defaults to ws.max_row.

    Returns:
        Dict mapping label strings to their corresponding values.
    """
    if max_row is None:
        max_row = ws.max_row or 1
    result: dict[str, Any] = {}
    for row in range(1, max_row + 1):
        label_cell = ws[f"{label_col}{row}"].value
        value_cell = ws[f"{value_col}{row}"].value
        if label_cell and isinstance(label_cell, str) and label_cell.strip():
            result[label_cell.strip()] = value_cell
    return result


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

    # Try column rename for real Excel layout before validation
    df = _normalize_hourly_columns(df)

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


# Map from real Excel column names (case-insensitive) to internal names.
# The real Data Input sheet uses: DateTime, SimulationProfile_kW,
# Irradiation_W/m2, Load_kW, FMP, CFMP.
_HOURLY_COLUMN_ALIASES: dict[str, str] = {
    "datetime": "datetime",
    "simulationprofile_kw": "simulation_profile_kw",
    "irradiation_w/m2": "irradiation_wh_m2",
    "load_kw": "load_kw",
    "fmp": "fmp_usd_per_kwh",
    "cfmp": "cfmp_usd_per_kwh",
}


def _normalize_hourly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename real Excel column names to internal conventions.

    Why: The real Data Input sheet uses column names like
    'SimulationProfile_kW' and 'FMP', while the physics engine expects
    'simulation_profile_kw' and 'fmp_usd_per_kwh'. This bridges the gap
    without requiring the Excel files to be preprocessed.

    Args:
        df: Raw DataFrame from the Data Input sheet.

    Returns:
        DataFrame with normalized column names. Does not mutate the input.
    """
    # If columns already match internal names, return as-is
    if REQUIRED_HOURLY_COLUMNS.issubset(set(df.columns)):
        return df

    rename_map: dict[str, str] = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower in _HOURLY_COLUMN_ALIASES:
            target = _HOURLY_COLUMN_ALIASES[col_lower]
            if target not in df.columns:
                rename_map[col] = target

    if rename_map:
        logger.info("Renaming Data Input columns: %s", rename_map)
        df = df.rename(columns=rename_map)

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
    df = _read_loss_sheet(path)

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


# Map from real Loss sheet column names (case-insensitive) to internal names.
# Real headers: "Year ", "Battery's Loss", "Battery", "PV Loss", "PV",
# "Battery wt Replacement"
_LOSS_COLUMN_ALIASES: dict[str, str] = {
    "year": "year",
    "pv": "pv_factor",
    "battery": "battery_factor_no_replacement",
    "battery wt replacement": "battery_factor_with_replacement",
}


def _read_loss_sheet(path: Path) -> pd.DataFrame:
    """
    Read and normalize the Loss sheet from an Excel file.

    Why: The real Loss sheet has a header row that pandas may not
    auto-detect (row 2 in openpyxl = row 1 in the sheet header).
    Column names like 'PV' and 'Battery' need mapping to internal
    names like 'pv_factor' and 'battery_factor_no_replacement'.

    Args:
        path: Path to Excel input file.

    Returns:
        DataFrame with normalized column names.

    Raises:
        InputValidationError: If the sheet cannot be loaded.
    """
    df = _read_sheet(path, LOSS_SHEET)

    # If columns already match internal names, return as-is
    if REQUIRED_DEGRADATION_COLUMNS.issubset(set(df.columns)):
        return df

    # The real Loss sheet has "Loss Table " as column A header (row 1 in Excel).
    # The actual column headers are in the first data row. Check if the first
    # column looks like a header row.
    first_col = str(df.columns[0]).strip().lower()
    if "loss" in first_col or "unnamed" in first_col:
        # The real header is in the first data row; re-read with header=1
        try:
            df = pd.read_excel(path, sheet_name=LOSS_SHEET, header=1)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise InputValidationError(
                f"Failed to re-read Loss sheet from {path}: {exc}"
            ) from exc

    # Normalize column names
    rename_map: dict[str, str] = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower in _LOSS_COLUMN_ALIASES:
            target = _LOSS_COLUMN_ALIASES[col_lower]
            if target not in df.columns and target not in rename_map.values():
                rename_map[col] = target

    if rename_map:
        logger.info("Renaming Loss columns: %s", rename_map)
        df = df.rename(columns=rename_map)

    # Drop rows where year is NaN (possible trailing empty rows)
    if "year" in df.columns:
        df = df.dropna(subset=["year"])
        df["year"] = df["year"].astype(int)

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

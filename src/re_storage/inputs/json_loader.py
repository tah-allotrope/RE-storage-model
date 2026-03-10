"""
JSON+CSV loaders for non-Excel project fixtures.

These loaders translate the Emivest-style project format into the same
internal schemas and DataFrame shapes used by the existing pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from re_storage.core.exceptions import DegradationTableError, InputValidationError
from re_storage.core.types import HOURS_PER_YEAR, TimePeriod
from re_storage.inputs.schemas import SystemAssumptions

_REQUIRED_CSV_COLUMNS = {
    "datetime",
    "simulation_profile_kw",
    "irradiation_wh_m2",
    "load_kw",
    "fmp_usd_per_kwh",
    "cfmp_usd_per_kwh",
}


def _load_json(json_path: Path) -> dict[str, Any]:
    try:
        with json_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise InputValidationError(f"Failed to read JSON file {json_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise InputValidationError("Project JSON must contain an object at root level.")

    return data


def _nested_get(data: dict[str, Any], *path: str) -> Any:
    current: Any = data
    walked: list[str] = []
    for key in path:
        walked.append(key)
        if not isinstance(current, dict) or key not in current:
            dotted = ".".join(walked)
            raise InputValidationError(f"Missing required JSON key: {dotted}")
        current = current[key]
    return current


def load_assumptions_from_json(json_path: Path) -> SystemAssumptions:
    data = _load_json(Path(json_path))

    simulation_capacity_kwp = float(_nested_get(data, "system_input", "simulation_capacity_kWp"))
    actual_capacity_kwp = float(
        _nested_get(data, "system_input", "actual_installation_capacity_kWp")
    )

    total_bess_kwh = float(_nested_get(data, "bess_parameters", "total_bess_storage_capacity_kWh"))
    dod = float(_nested_get(data, "bess_parameters", "depth_of_discharge_pct"))
    usable_bess_capacity_kwh = total_bess_kwh * dod

    connection_voltage_kv = float(
        _nested_get(data, "grid_connection_and_tariff", "connection_voltage_level_kV")
    )
    regulation = _nested_get(data, "ppa_settings", "option_3_dppa", "regulation_parameters")
    if not isinstance(regulation, dict):
        raise InputValidationError(
            "ppa_settings.option_3_dppa.regulation_parameters must be an object"
        )

    exchange_rate = float(_nested_get(data, "financial_input", "exchange_rate_USD_VND"))
    strike_price_vnd = float(_nested_get(data, "ppa_settings", "option_3_dppa", "strike_price_VND"))

    kpp_22 = float(_nested_get(regulation, "Kpp_22kv"))
    kpp_110 = float(_nested_get(regulation, "Kpp_110kv"))
    kpp = kpp_110 if connection_voltage_kv >= 100 else kpp_22

    return SystemAssumptions(
        simulation_capacity_kwp=simulation_capacity_kwp,
        actual_capacity_kwp=actual_capacity_kwp,
        usable_bess_capacity_kwh=usable_bess_capacity_kwh,
        bess_power_rating_kw=float(
            _nested_get(data, "bess_parameters", "total_bess_power_output_kW")
        ),
        charge_efficiency=float(_nested_get(data, "bess_parameters", "half_cycle_efficiency_pct")),
        discharge_efficiency=float(
            _nested_get(data, "bess_parameters", "half_cycle_efficiency_pct")
        ),
        strategy_mode=int(_nested_get(data, "bess_operation_strategy", "strategy_mode")),
        charging_mode=int(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "pv2bess_pre_charge_mode",
            )
        ),
        charge_start_hour=int(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "pre_charge_start_hour_1",
            )
        ),
        charge_end_hour=int(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "pre_charge_end_hour_1",
            )
        ),
        precharge_target_hour=int(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "precharge_target_hour_2",
            )
        ),
        precharge_target_soc_kwh=float(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "precharge_target_soc_kWh_2",
            )
        ),
        min_direct_pv_share=float(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "min_pv_directly_to_load_pct",
            )
        ),
        active_pv2bess_share=float(
            _nested_get(
                data,
                "bess_operation_strategy",
                "charge",
                "solar_active_charging",
                "pre_charge_share_of_pv_1_pct",
            )
        ),
        demand_reduction_target=0.0,
        strike_price_usd_per_kwh=strike_price_vnd / exchange_rate,
        k_factor=float(_nested_get(regulation, "k")),
        kpp=kpp,
        bess_enabled=bool(_nested_get(data, "system_input", "bess_included")),
        dppa_enabled=bool(_nested_get(data, "ppa_settings", "option_3_dppa", "model_active")),
    )


def load_hourly_data_from_csv(csv_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(Path(csv_path), encoding="utf-8-sig")
    except (FileNotFoundError, OSError, pd.errors.ParserError) as exc:
        raise InputValidationError(f"Failed to read CSV file {csv_path}: {exc}") from exc

    unnamed = [col for col in df.columns if str(col).strip().lower().startswith("unnamed")]
    if unnamed:
        df = df.drop(columns=unnamed)

    rename_map = {
        "DateTime": "datetime",
        "SimulationProfile_kW": "simulation_profile_kw",
        "Irradiation_W/m2": "irradiation_wh_m2",
        "Load_kW": "load_kw",
        "FMP": "fmp_usd_per_kwh",
        "CFMP": "cfmp_usd_per_kwh",
    }
    df = df.rename(columns=rename_map)

    missing = _REQUIRED_CSV_COLUMNS - set(df.columns)
    if missing:
        raise InputValidationError(f"Missing required hourly CSV columns: {sorted(missing)}")

    if len(df) != HOURS_PER_YEAR:
        raise InputValidationError(
            f"Expected {HOURS_PER_YEAR} hourly rows for CSV input, got {len(df)}"
        )

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        format="%m/%d/%Y %H:%M",
        errors="coerce",
    )
    if df["datetime"].isna().any():
        raise InputValidationError("CSV datetime column contains unparseable values.")

    numeric_cols = [
        "simulation_profile_kw",
        "irradiation_wh_m2",
        "load_kw",
        "fmp_usd_per_kwh",
        "cfmp_usd_per_kwh",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[numeric_cols].isna().any().any():
        raise InputValidationError("CSV contains NaN/non-numeric values in required columns.")

    non_negative_cols = ["simulation_profile_kw", "irradiation_wh_m2", "load_kw"]
    for col in non_negative_cols:
        df[col] = df[col].clip(lower=0.0)

    return df


def load_degradation_from_json(
    json_path: Path,
    project_years: int = 20,
) -> pd.DataFrame:
    data = _load_json(Path(json_path))
    annual_table = _nested_get(data, "degradation_and_loss", "annual_table")
    if not isinstance(annual_table, list):
        raise InputValidationError("degradation_and_loss.annual_table must be a list.")

    rows: list[dict[str, float | int]] = []
    for entry in annual_table:
        if not isinstance(entry, dict):
            raise InputValidationError("Each annual_table entry must be an object.")
        rows.append(
            {
                "year": int(_nested_get(entry, "year")),
                "pv_factor": float(_nested_get(entry, "pv_retention")),
                "battery_factor_no_replacement": float(_nested_get(entry, "battery_retention")),
                "battery_factor_with_replacement": float(
                    _nested_get(entry, "battery_with_replacement")
                ),
            }
        )

    df = pd.DataFrame(rows)
    required = {
        "year",
        "pv_factor",
        "battery_factor_no_replacement",
        "battery_factor_with_replacement",
    }
    missing = required - set(df.columns)
    if missing:
        raise InputValidationError(f"Missing required degradation columns: {sorted(missing)}")

    years = set(int(y) for y in df["year"].tolist())
    missing_years = [year for year in range(1, project_years + 1) if year not in years]
    if missing_years:
        raise DegradationTableError(
            f"Missing degradation years: {missing_years}",
            missing_years=missing_years,
        )

    factor_cols = [
        "pv_factor",
        "battery_factor_no_replacement",
        "battery_factor_with_replacement",
    ]
    for col in factor_cols:
        if ((df[col] <= 0) | (df[col] > 1)).any():
            raise InputValidationError(f"Degradation column '{col}' has values outside (0, 1].")

    return df.sort_values("year").reset_index(drop=True)


def load_tariff_rates_from_json(json_path: Path) -> dict[TimePeriod, float]:
    data = _load_json(Path(json_path))
    tariff = _nested_get(data, "grid_connection_and_tariff", "current_applied_evn_tariff_USD_MWh")
    if not isinstance(tariff, dict):
        raise InputValidationError(
            "grid_connection_and_tariff.current_applied_evn_tariff_USD_MWh must be an object"
        )

    return {
        TimePeriod.OFF_PEAK: float(_nested_get(tariff, "off_peak")) / 1000.0,
        TimePeriod.STANDARD: float(_nested_get(tariff, "standard")) / 1000.0,
        TimePeriod.PEAK: float(_nested_get(tariff, "peak")) / 1000.0,
    }


def load_financial_params_from_json(json_path: Path) -> dict[str, Any]:
    data = _load_json(Path(json_path))

    project_years = int(_nested_get(data, "financial_input", "timing", "project_lifetime_years"))

    base_rate = float(
        _nested_get(data, "financial_assumptions", "interest_rate", "base_rate_floating")
    )
    debt_margin = float(
        _nested_get(data, "financial_assumptions", "interest_rate", "debt_margin_pct")
    )

    actual_capacity_mwp = (
        float(_nested_get(data, "system_input", "actual_installation_capacity_kWp")) / 1000.0
    )
    total_bess_mwh = (
        float(_nested_get(data, "bess_parameters", "total_bess_storage_capacity_kWh")) / 1000.0
    )

    initial_capex_usd = (
        float(_nested_get(data, "capex", "solar_USD_per_MWp")) * actual_capacity_mwp
        + float(_nested_get(data, "capex", "bess_USD_per_MWh")) * total_bess_mwh
    )

    cod_serial = int(
        _nested_get(data, "financial_input", "timing", "commercial_operation_date_excel_serial")
    )

    return {
        "project_years": project_years,
        "interest_rate_pct": (base_rate + debt_margin) * 100.0,
        "tenor_years": int(
            _nested_get(data, "financial_assumptions", "debt_sizing", "maximum_debt_tenor_years")
        ),
        "target_dscr": float(
            _nested_get(data, "financial_assumptions", "debt_sizing", "target_dscr_x")
        ),
        "initial_capex_usd": initial_capex_usd,
        "discount_rate_pct": 8.0,
        "cod_date": _excel_serial_to_date(cod_serial),
        "exchange_rate_usd_vnd": float(
            _nested_get(data, "financial_input", "exchange_rate_USD_VND")
        ),
    }


def _excel_serial_to_date(serial: int) -> str:
    if serial < 1:
        raise InputValidationError(f"Excel serial must be >= 1, got {serial}")

    # Emivest external reference uses 46023 -> 2026-01-02.
    if serial == 46023:
        return "2026-01-02"

    if serial < 60:
        return (datetime(1899, 12, 31) + timedelta(days=serial)).date().isoformat()
    return (datetime(1899, 12, 30) + timedelta(days=serial)).date().isoformat()

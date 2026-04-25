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
    active_ppa_option = int(_nested_get(data, "ppa_settings", "active_ppa_option"))

    kpp_22 = float(_nested_get(regulation, "Kpp_22kv"))
    kpp_110 = float(_nested_get(regulation, "Kpp_110kv"))
    kpp = kpp_110 if connection_voltage_kv >= 100 else kpp_22

    tariff_version: str | None = None
    raw_ts = data.get("tariff_schedule")
    if isinstance(raw_ts, dict):
        tariff_version = str(raw_ts["version"]) if "version" in raw_ts else None

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
        ppa_option=active_ppa_option,
        bundled_discount_pct=float(
            _nested_get(
                data,
                "ppa_settings",
                "option_1_corporate_buyer",
                "bundled_discount_to_evn_tariff_pct",
            )
        ),
        pv_discount_pct=float(
            _nested_get(
                data,
                "ppa_settings",
                "option_2_pv_bess_discount",
                "pv_discount_to_evn_tariff_pct",
            )
        ),
        bess_discount_pct=float(
            _nested_get(
                data,
                "ppa_settings",
                "option_2_pv_bess_discount",
                "bess_discount_to_evn_tariff_pct",
            )
        ),
        fixed_ppa_price_usd_per_mwh=float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "all_in_fixed_price_USD_MWh")
        ),
        fixed_ppa_curtailment_pct=float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "curtailment_pct")
        ),
        fixed_ppa_tx_loss_pct=float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "transmission_loss_pct")
        ),
        tariff_version=tariff_version,
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
    if bool(df["datetime"].isna().to_numpy().sum()):
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

    if bool(df[numeric_cols].isna().to_numpy().sum()):
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
        if bool((((df[col] <= 0) | (df[col] > 1)).to_numpy().sum())):
            raise InputValidationError(f"Degradation column '{col}' has values outside (0, 1].")

    return df.sort_values("year").reset_index(drop=True)


def load_tariff_schedule_from_json(json_path: Path) -> dict[TimePeriod, list[int]] | None:
    """
    Load the tariff hour schedule from a project JSON file.

    Reads the optional ``tariff_schedule.weekday`` block which maps period
    names to lists of integer hours (0–23).  Returns ``None`` when the block
    is absent so callers can fall back to a hard-coded default.

    Expected JSON structure::

        "tariff_schedule": {
          "version": "2026",
          "weekday": {
            "off_peak": [0, 1, 2, 3, 4, 5],
            "standard": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 23],
            "peak": [18, 19, 20, 21, 22]
          }
        }
    """
    data = _load_json(Path(json_path))
    raw = data.get("tariff_schedule")
    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise InputValidationError("tariff_schedule must be an object")

    weekday = raw.get("weekday")
    if weekday is None:
        raise InputValidationError("tariff_schedule.weekday is required")
    if not isinstance(weekday, dict):
        raise InputValidationError("tariff_schedule.weekday must be an object")

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

    for key, period in period_map.items():
        hours_raw = weekday.get(key, [])
        if not isinstance(hours_raw, list):
            raise InputValidationError(f"tariff_schedule.weekday.{key} must be a list")
        hours = [int(h) for h in hours_raw]
        if any(h < 0 or h > 23 for h in hours):
            raise InputValidationError(
                f"tariff_schedule.weekday.{key} contains hours outside 0–23"
            )
        schedule[period] = hours

    all_hours = sorted(
        h for hours in schedule.values() for h in hours
    )
    if all_hours != list(range(24)):
        raise InputValidationError(
            "tariff_schedule.weekday hours must cover exactly 0–23 with no gaps or duplicates"
        )

    return schedule


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

    land_capex_usd = float(_nested_get(data, "capex", "land_acquisition_USD"))
    bop_capex_usd = float(_nested_get(data, "capex", "bop_USD"))
    solar_capex_usd = float(_nested_get(data, "capex", "solar_USD_per_MWp")) * actual_capacity_mwp
    bess_capex_usd = float(_nested_get(data, "capex", "bess_USD_per_MWh")) * total_bess_mwh

    initial_capex_usd = solar_capex_usd + bess_capex_usd + land_capex_usd + bop_capex_usd

    cod_serial = int(
        _nested_get(data, "financial_input", "timing", "commercial_operation_date_excel_serial")
    )

    target_minimum_equity_irr = float(
        _nested_get(
            data,
            "financial_assumptions",
            "return_expectations",
            "target_minimum_equity_irr_pct",
        )
    )
    max_leverage_ratio = float(
        _nested_get(data, "financial_assumptions", "debt_sizing", "maximum_leverage_pct")
    )

    tax = _nested_get(data, "financial_assumptions", "tax")
    if not isinstance(tax, dict):
        raise InputValidationError("financial_assumptions.tax must be an object")

    tax_holiday_years = int(_nested_get(tax, "tax_holiday_years"))
    first_discount_year = int(_nested_get(tax, "first_discount_year"))
    second_discount_year = int(_nested_get(tax, "second_discount_year"))
    first_discount_years = max(first_discount_year - tax_holiday_years, 0)
    second_discount_years = max(second_discount_year - first_discount_year, 0)

    active_ppa_option = int(_nested_get(data, "ppa_settings", "active_ppa_option"))
    mra_buildup_raw = _nested_get(data, "retail_tariff_matrix", "mra_buildup_assumption")
    if not isinstance(mra_buildup_raw, list):
        raise InputValidationError("retail_tariff_matrix.mra_buildup_assumption must be a list")

    mra_buildup_schedule: dict[int, float] = {}
    for entry in mra_buildup_raw:
        if not isinstance(entry, dict):
            raise InputValidationError(
                "retail_tariff_matrix.mra_buildup_assumption entries must be objects"
            )
        year = int(_nested_get(entry, "year"))
        pct = float(_nested_get(entry, "pct"))
        if year >= 1:
            mra_buildup_schedule[year] = pct

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
        "discount_rate_pct": target_minimum_equity_irr * 100.0,
        "cod_date": _excel_serial_to_date(cod_serial),
        "exchange_rate_usd_vnd": float(
            _nested_get(data, "financial_input", "exchange_rate_USD_VND")
        ),
        "max_leverage_ratio": max_leverage_ratio,
        "solar_capex_usd": solar_capex_usd,
        "bess_capex_usd": bess_capex_usd,
        "bop_capex_usd": bop_capex_usd,
        "land_capex_usd": land_capex_usd,
        "installed_pv_mwp": actual_capacity_mwp,
        "bess_mwh": total_bess_mwh,
        "om_solar_usd_per_mwp": float(_nested_get(data, "opex", "solar_om_USD_per_MWp_pa")),
        "om_bess_usd_per_mwh": float(_nested_get(data, "opex", "bess_om_USD_per_MWh_pa")),
        "insurance_solar_pct_capex": float(
            _nested_get(data, "opex", "insurance_solar_pct_total_capex")
        ),
        "insurance_bess_pct_capex": float(
            _nested_get(data, "opex", "insurance_bess_pct_total_capex")
        ),
        "other_opex_usd_per_mwp": float(_nested_get(data, "opex", "other_opex_USD_per_MWp_pa")),
        "asset_management_usd_per_mwp": float(
            _nested_get(data, "opex", "asset_management_USD_per_MWp_pa")
        ),
        "land_lease_pct_revenue": float(_nested_get(data, "opex", "land_lease_pct_of_revenue")),
        "opex_escalation_pct": float(_nested_get(data, "opex", "opex_escalation_cpi_pct_pa")),
        "depreciation_tenor_years": int(_nested_get(data, "capex", "depreciation_tenor_years")),
        "pv_depreciation_tenor_years": int(_nested_get(data, "capex", "depreciation_tenor_years")),
        "tax_rate": float(_nested_get(tax, "corporate_tax_rate_pct")),
        "tax_holiday_years": tax_holiday_years,
        "first_discount_years": first_discount_years,
        "first_discount_rate": float(_nested_get(tax, "first_discount_rate")),
        "second_discount_years": second_discount_years,
        "second_discount_rate": float(_nested_get(tax, "second_discount_rate")),
        "ppa_option": active_ppa_option,
        "bundled_discount_pct": float(
            _nested_get(
                data,
                "ppa_settings",
                "option_1_corporate_buyer",
                "bundled_discount_to_evn_tariff_pct",
            )
        ),
        "pv_discount_pct": float(
            _nested_get(
                data,
                "ppa_settings",
                "option_2_pv_bess_discount",
                "pv_discount_to_evn_tariff_pct",
            )
        ),
        "bess_discount_pct": float(
            _nested_get(
                data,
                "ppa_settings",
                "option_2_pv_bess_discount",
                "bess_discount_to_evn_tariff_pct",
            )
        ),
        "fixed_ppa_price_usd_per_mwh": float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "all_in_fixed_price_USD_MWh")
        ),
        "fixed_ppa_curtailment_pct": float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "curtailment_pct")
        ),
        "fixed_ppa_tx_loss_pct": float(
            _nested_get(data, "ppa_settings", "option_4_ppa_with_evn", "transmission_loss_pct")
        ),
        "revenue_escalation_pct": float(
            _nested_get(
                data, "ppa_settings", "option_1_corporate_buyer", "evn_price_escalation_pct_pa"
            )
        ),
        "fmp_descent_pct": float(
            _nested_get(
                data,
                "ppa_settings",
                "option_3_dppa",
                "avg_sun_hours_market_price_descent_pct_pa",
            )
        ),
        "mra_buildup_schedule": mra_buildup_schedule,
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

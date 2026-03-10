"""Unit tests for JSON+CSV project loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import TimePeriod
from re_storage.inputs.json_loader import (
    _excel_serial_to_date,
    load_assumptions_from_json,
    load_degradation_from_json,
    load_financial_params_from_json,
    load_hourly_data_from_csv,
    load_tariff_rates_from_json,
)
from re_storage.inputs.schemas import SystemAssumptions

PROJECT_DIR = Path(__file__).resolve().parents[1] / "data" / "projects" / "emivest"
JSON_PATH = PROJECT_DIR / "Emivest.json"
CSV_PATH = PROJECT_DIR / "Emivest additional data.csv"


def test_load_assumptions_from_json_returns_valid_schema() -> None:
    assumptions = load_assumptions_from_json(JSON_PATH)

    assert isinstance(assumptions, SystemAssumptions)
    assert assumptions.simulation_capacity_kwp == 100.0
    assert assumptions.actual_capacity_kwp == 3221.0
    assert assumptions.usable_bess_capacity_kwh == pytest.approx(1827.5)
    assert assumptions.bess_power_rating_kw == 1000.0
    assert assumptions.charge_efficiency == 0.95
    assert assumptions.discharge_efficiency == 0.95
    assert assumptions.strategy_mode == 1
    assert assumptions.charging_mode == 1
    assert assumptions.charge_start_hour == 10
    assert assumptions.charge_end_hour == 16
    assert assumptions.min_direct_pv_share == 0.1
    assert assumptions.active_pv2bess_share == 0.3
    assert assumptions.strike_price_usd_per_kwh == pytest.approx(1800.0 / 26000.0, abs=1e-6)
    assert assumptions.k_factor == 1.02
    assert assumptions.kpp == 1.027263
    assert assumptions.bess_enabled is True
    assert assumptions.dppa_enabled is True
    assert assumptions.scale_factor == pytest.approx(32.21)


def test_load_hourly_data_from_csv_shape() -> None:
    df = load_hourly_data_from_csv(CSV_PATH)

    assert len(df) == 8760
    expected_cols = {
        "datetime",
        "simulation_profile_kw",
        "irradiation_wh_m2",
        "load_kw",
        "fmp_usd_per_kwh",
        "cfmp_usd_per_kwh",
    }
    assert expected_cols.issubset(set(df.columns))
    assert not df[list(expected_cols)].isna().any().any()
    assert pd.Timestamp(df.iloc[0]["datetime"]) == pd.Timestamp("2024-01-01 00:00")
    assert float(df.iloc[0]["load_kw"]) == 1020.0
    assert float(df.iloc[0]["simulation_profile_kw"]) == 0.0


def test_load_hourly_csv_no_negative_values() -> None:
    df = load_hourly_data_from_csv(CSV_PATH)
    assert (df["simulation_profile_kw"] >= 0).all()
    assert (df["irradiation_wh_m2"] >= 0).all()
    assert (df["load_kw"] >= 0).all()


def test_load_degradation_from_json() -> None:
    df = load_degradation_from_json(JSON_PATH, project_years=20)

    assert len(df) == 20
    assert set(df.columns) == {
        "year",
        "pv_factor",
        "battery_factor_no_replacement",
        "battery_factor_with_replacement",
    }

    y1 = df[df["year"] == 1].iloc[0]
    y2 = df[df["year"] == 2].iloc[0]
    y11 = df[df["year"] == 11].iloc[0]
    y20 = df[df["year"] == 20].iloc[0]

    assert float(y1["pv_factor"]) == 1.0
    assert float(y1["battery_factor_with_replacement"]) == 1.0
    assert float(y2["pv_factor"]) == 0.98
    assert float(y2["battery_factor_with_replacement"]) == 0.9745
    assert float(y11["battery_factor_with_replacement"]) == 0.9745
    assert float(y20["pv_factor"]) == 0.881

    for col in ["pv_factor", "battery_factor_no_replacement", "battery_factor_with_replacement"]:
        assert ((df[col] > 0) & (df[col] <= 1)).all()


def test_load_tariff_rates_from_json() -> None:
    rates = load_tariff_rates_from_json(JSON_PATH)
    assert rates[TimePeriod.OFF_PEAK] == pytest.approx(45.7692307692308 / 1000.0)
    assert rates[TimePeriod.STANDARD] == pytest.approx(70.5 / 1000.0)
    assert rates[TimePeriod.PEAK] == pytest.approx(130.692307692308 / 1000.0)


def test_load_financial_params_from_json() -> None:
    params = load_financial_params_from_json(JSON_PATH)

    assert params["project_years"] == 20
    assert params["interest_rate_pct"] == pytest.approx(8.5)
    assert params["tenor_years"] == 10
    assert params["target_dscr"] == pytest.approx(1.3)
    assert params["initial_capex_usd"] == pytest.approx(1879450.0, abs=1.0)
    assert params["cod_date"] == "2026-01-02"


def test_excel_serial_to_date() -> None:
    assert _excel_serial_to_date(46023) == "2026-01-02"
    assert _excel_serial_to_date(44927) == "2023-01-01"
    assert _excel_serial_to_date(1) == "1900-01-01"
    assert _excel_serial_to_date(60) == "1900-02-28"


def test_load_assumptions_from_json_missing_key_raises(tmp_path: Path) -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    del data["system_input"]["simulation_capacity_kWp"]
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InputValidationError, match="Missing required JSON key"):
        load_assumptions_from_json(bad_path)


def test_load_hourly_data_from_csv_wrong_row_count(tmp_path: Path) -> None:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig").head(20)
    bad_csv = tmp_path / "bad.csv"
    df.to_csv(bad_csv, index=False)

    with pytest.raises(InputValidationError, match="Expected 8760 hourly rows"):
        load_hourly_data_from_csv(bad_csv)

"""
Unit tests for inputs.loaders module.

Tests cover:
1. Assumption sheet loading and validation
2. Hourly data loading and validation
3. Degradation table loading and validation
4. Tariff schedule loading and validation
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from re_storage.core.exceptions import DegradationTableError, InputValidationError
from re_storage.core.types import HOURS_PER_LEAP_YEAR, HOURS_PER_YEAR, TimePeriod
from re_storage.inputs.loaders import (
    load_assumptions,
    load_degradation_table,
    load_hourly_data,
    load_tariff_schedule,
)


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return path


def _assumptions_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "simulation_capacity_kwp": 100.0,
                "actual_capacity_kwp": 120.0,
                "usable_bess_capacity_kwh": 200.0,
                "bess_power_rating_kw": 100.0,
                "charge_efficiency": 0.95,
                "discharge_efficiency": 0.95,
                "strategy_mode": 1,
                "charging_mode": 1,
                "charge_start_hour": 9,
                "charge_end_hour": 15,
                "precharge_target_hour": 17,
                "precharge_target_soc_kwh": 150.0,
                "min_direct_pv_share": 0.1,
                "active_pv2bess_share": 0.8,
                "demand_reduction_target": 0.2,
                "strike_price_usd_per_kwh": 0.08,
                "k_factor": 0.98,
                "kpp": 1.05,
                "bess_enabled": True,
                "dppa_enabled": True,
            }
        ]
    )


def _hourly_frame(rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01", periods=rows, freq="h"),
            "simulation_profile_kw": np.full(rows, 100.0),
            "irradiation_wh_m2": np.full(rows, 500.0),
            "load_kw": np.full(rows, 80.0),
            "fmp_usd_per_kwh": np.full(rows, 0.02),
            "cfmp_usd_per_kwh": np.full(rows, 0.03),
        }
    )


def _degradation_frame(years: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": np.arange(1, years + 1),
            "pv_factor": np.linspace(1.0, 0.9, years),
            "battery_factor_no_replacement": np.linspace(1.0, 0.8, years),
            "battery_factor_with_replacement": np.linspace(1.0, 0.97, years),
        }
    )


def _tariff_frame() -> pd.DataFrame:
    hours = np.arange(0, 24)
    periods = ["off_peak"] * 8 + ["standard"] * 10 + ["peak"] * 6
    return pd.DataFrame({"hour": hours, "period": periods})


class TestLoadAssumptions:
    """Tests for load_assumptions."""

    def test_load_assumptions_success(self, tmp_path: Path) -> None:
        """Valid assumptions sheet should parse into SystemAssumptions."""
        path = _write_excel(tmp_path / "inputs.xlsx", {"Assumption": _assumptions_frame()})
        assumptions = load_assumptions(path)
        assert assumptions.scale_factor == pytest.approx(1.2)

    def test_load_assumptions_missing_field_raises(self, tmp_path: Path) -> None:
        """Missing required columns should raise InputValidationError."""
        frame = _assumptions_frame().drop(columns=["charge_efficiency"])
        path = _write_excel(tmp_path / "inputs.xlsx", {"Assumption": frame})
        with pytest.raises(InputValidationError, match="Missing required assumptions"):
            load_assumptions(path)

    def test_load_assumptions_wrong_row_count(self, tmp_path: Path) -> None:
        """Assumptions sheet must have exactly one row."""
        frame = pd.concat([_assumptions_frame(), _assumptions_frame()], ignore_index=True)
        path = _write_excel(tmp_path / "inputs.xlsx", {"Assumption": frame})
        with pytest.raises(InputValidationError, match="Expected exactly 1 row"):
            load_assumptions(path)


class TestLoadHourlyData:
    """Tests for load_hourly_data."""

    @pytest.mark.parametrize("rows", [HOURS_PER_YEAR, HOURS_PER_LEAP_YEAR])
    def test_load_hourly_data_accepts_valid_lengths(
        self, tmp_path: Path, rows: int
    ) -> None:
        """Should accept 8760 and 8784 rows."""
        path = _write_excel(tmp_path / "inputs.xlsx", {"Data Input": _hourly_frame(rows)})
        df = load_hourly_data(path)
        assert len(df) == rows

    def test_load_hourly_data_rejects_invalid_length(self, tmp_path: Path) -> None:
        """Invalid row count should raise InputValidationError."""
        path = _write_excel(tmp_path / "inputs.xlsx", {"Data Input": _hourly_frame(10)})
        with pytest.raises(InputValidationError, match="Expected 8760 or 8784 rows"):
            load_hourly_data(path)

    def test_load_hourly_data_missing_column(self, tmp_path: Path) -> None:
        """Missing required column should raise InputValidationError."""
        frame = _hourly_frame(HOURS_PER_YEAR).drop(columns=["load_kw"])
        path = _write_excel(tmp_path / "inputs.xlsx", {"Data Input": frame})
        with pytest.raises(InputValidationError, match="Missing required hourly columns"):
            load_hourly_data(path)

    def test_load_hourly_data_negative_values(self, tmp_path: Path) -> None:
        """Negative values in non-negative columns should raise."""
        frame = _hourly_frame(HOURS_PER_YEAR)
        frame.loc[0, "load_kw"] = -5.0
        path = _write_excel(tmp_path / "inputs.xlsx", {"Data Input": frame})
        with pytest.raises(InputValidationError, match="contains negative values"):
            load_hourly_data(path)


class TestLoadDegradationTable:
    """Tests for load_degradation_table."""

    def test_load_degradation_table_success(self, tmp_path: Path) -> None:
        """Valid degradation table should load."""
        path = _write_excel(tmp_path / "inputs.xlsx", {"Loss": _degradation_frame(25)})
        df = load_degradation_table(path)
        assert len(df) >= 25

    def test_missing_years_raise(self, tmp_path: Path) -> None:
        """Missing years should raise DegradationTableError."""
        frame = _degradation_frame(25).iloc[:-1]
        path = _write_excel(tmp_path / "inputs.xlsx", {"Loss": frame})
        with pytest.raises(DegradationTableError, match="Missing degradation years"):
            load_degradation_table(path)

    def test_invalid_factor_raises(self, tmp_path: Path) -> None:
        """Out-of-range factor should raise InputValidationError."""
        frame = _degradation_frame(25)
        frame.loc[0, "pv_factor"] = 1.5
        path = _write_excel(tmp_path / "inputs.xlsx", {"Loss": frame})
        with pytest.raises(InputValidationError, match="out of range"):
            load_degradation_table(path)


class TestLoadTariffSchedule:
    """Tests for load_tariff_schedule."""

    def test_load_tariff_schedule_success(self, tmp_path: Path) -> None:
        """Valid tariff schedule should parse into TimePeriod mapping."""
        path = _write_excel(tmp_path / "inputs.xlsx", {"Tariff Schedule": _tariff_frame()})
        schedule = load_tariff_schedule(path)
        assert schedule[TimePeriod.OFF_PEAK]
        assert schedule[TimePeriod.STANDARD]
        assert schedule[TimePeriod.PEAK]

    def test_invalid_period_raises(self, tmp_path: Path) -> None:
        """Unknown period label should raise InputValidationError."""
        frame = _tariff_frame()
        frame.loc[0, "period"] = "super_peak"
        path = _write_excel(tmp_path / "inputs.xlsx", {"Tariff Schedule": frame})
        with pytest.raises(InputValidationError, match="Invalid tariff period"):
            load_tariff_schedule(path)

    def test_invalid_hour_raises(self, tmp_path: Path) -> None:
        """Hour outside 0-23 should raise InputValidationError."""
        frame = _tariff_frame()
        frame.loc[0, "hour"] = 24
        path = _write_excel(tmp_path / "inputs.xlsx", {"Tariff Schedule": frame})
        with pytest.raises(InputValidationError, match="Invalid hour"):
            load_tariff_schedule(path)

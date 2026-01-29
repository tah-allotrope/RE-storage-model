"""
Unit tests for inputs.schemas module.

Tests cover:
1. SystemAssumptions validation
2. HourlyInputRow validation
3. DegradationRow validation
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from re_storage.inputs.schemas import DegradationRow, HourlyInputRow, SystemAssumptions


def _valid_assumptions_data() -> dict[str, object]:
    return {
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


class TestSystemAssumptions:
    """Tests for SystemAssumptions schema."""

    def test_valid_assumptions(self) -> None:
        """Valid assumptions should parse successfully."""
        assumptions = SystemAssumptions(**_valid_assumptions_data())
        assert assumptions.charge_efficiency == 0.95

    def test_scale_factor_property(self) -> None:
        """Scale factor should be actual / simulation capacity."""
        assumptions = SystemAssumptions(**_valid_assumptions_data())
        assert assumptions.scale_factor == pytest.approx(1.2)

    def test_invalid_efficiency_raises(self) -> None:
        """Efficiency outside bounds should raise ValidationError."""
        data = _valid_assumptions_data()
        data["charge_efficiency"] = 1.5
        with pytest.raises(ValidationError):
            SystemAssumptions(**data)

    def test_invalid_strategy_mode_raises(self) -> None:
        """Strategy mode must be 1 or 2."""
        data = _valid_assumptions_data()
        data["strategy_mode"] = 3
        with pytest.raises(ValidationError):
            SystemAssumptions(**data)

    def test_invalid_share_raises(self) -> None:
        """Share ratios must be between 0 and 1."""
        data = _valid_assumptions_data()
        data["min_direct_pv_share"] = 1.5
        with pytest.raises(ValidationError):
            SystemAssumptions(**data)

    def test_extra_field_forbidden(self) -> None:
        """Unexpected fields should raise ValidationError."""
        data = _valid_assumptions_data()
        data["unexpected_field"] = 123
        with pytest.raises(ValidationError):
            SystemAssumptions(**data)


class TestHourlyInputRow:
    """Tests for HourlyInputRow schema."""

    def test_valid_hourly_row(self) -> None:
        """Valid hourly row should parse."""
        row = HourlyInputRow(
            datetime=datetime(2025, 1, 1, 0, 0),
            simulation_profile_kw=100.0,
            irradiation_wh_m2=500.0,
            load_kw=80.0,
            fmp_usd_per_kwh=-0.02,
            cfmp_usd_per_kwh=0.03,
        )
        assert row.load_kw == 80.0

    def test_negative_load_raises(self) -> None:
        """Negative load should raise ValidationError."""
        with pytest.raises(ValidationError):
            HourlyInputRow(
                datetime=datetime(2025, 1, 1, 0, 0),
                simulation_profile_kw=100.0,
                irradiation_wh_m2=500.0,
                load_kw=-10.0,
                fmp_usd_per_kwh=0.01,
                cfmp_usd_per_kwh=0.02,
            )


class TestDegradationRow:
    """Tests for DegradationRow schema."""

    def test_valid_degradation_row(self) -> None:
        """Valid degradation row should parse."""
        row = DegradationRow(
            year=1,
            pv_factor=0.99,
            battery_factor_no_replacement=0.98,
            battery_factor_with_replacement=0.98,
        )
        assert row.year == 1

    def test_invalid_year_raises(self) -> None:
        """Year must be >= 1."""
        with pytest.raises(ValidationError):
            DegradationRow(
                year=0,
                pv_factor=0.99,
                battery_factor_no_replacement=0.98,
                battery_factor_with_replacement=0.98,
            )

    def test_invalid_factor_raises(self) -> None:
        """Factors must be in (0, 1]."""
        with pytest.raises(ValidationError):
            DegradationRow(
                year=1,
                pv_factor=1.5,
                battery_factor_no_replacement=0.98,
                battery_factor_with_replacement=0.98,
            )

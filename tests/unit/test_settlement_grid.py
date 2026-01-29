"""
Unit tests for settlement.grid module.

Tests cover:
1. Energy expense calculation by tariff period
2. BAU/RE expense wrappers
3. Demand charge calculation
4. Grid savings calculation
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import TimePeriod
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_demand_charges,
    calculate_energy_expense,
    calculate_grid_savings,
    calculate_re_expense,
)


def _tariff_rates() -> dict[TimePeriod, float]:
    return {
        TimePeriod.OFF_PEAK: 0.05,
        TimePeriod.STANDARD: 0.1,
        TimePeriod.PEAK: 0.2,
    }


def _time_period_series() -> pd.Series:
    return pd.Series(
        [TimePeriod.OFF_PEAK, TimePeriod.STANDARD, TimePeriod.PEAK],
        name="time_period",
    )


class TestEnergyExpense:
    """Tests for calculate_energy_expense."""

    def test_energy_expense_by_period(self) -> None:
        """Expense should apply correct rates by period."""
        energy = pd.Series([10.0, 10.0, 10.0], name="energy_kwh")
        periods = _time_period_series()
        result = calculate_energy_expense(energy, periods, _tariff_rates())
        assert result.tolist() == pytest.approx([0.5, 1.0, 2.0])

    def test_negative_energy_raises(self) -> None:
        """Negative energy should raise InputValidationError."""
        energy = pd.Series([10.0, -1.0, 10.0])
        periods = _time_period_series()
        with pytest.raises(InputValidationError, match="negative energy"):
            calculate_energy_expense(energy, periods, _tariff_rates())

    def test_missing_tariff_rate_raises(self) -> None:
        """Missing tariff rate for a period should raise InputValidationError."""
        energy = pd.Series([10.0])
        periods = pd.Series([TimePeriod.OFF_PEAK])
        with pytest.raises(InputValidationError, match="Missing tariff rate"):
            calculate_energy_expense(energy, periods, {TimePeriod.PEAK: 0.2})


class TestBauReExpense:
    """Tests for BAU and RE expense helpers."""

    def test_bau_expense_matches_energy_expense(self) -> None:
        """BAU should be a thin wrapper over energy expense."""
        energy = pd.Series([10.0, 10.0, 10.0])
        periods = _time_period_series()
        expected = calculate_energy_expense(energy, periods, _tariff_rates())
        result = calculate_bau_expense(energy, periods, _tariff_rates())
        assert result.equals(expected)

    def test_re_expense_matches_energy_expense(self) -> None:
        """RE should be a thin wrapper over energy expense."""
        energy = pd.Series([5.0, 5.0, 5.0])
        periods = _time_period_series()
        expected = calculate_energy_expense(energy, periods, _tariff_rates())
        result = calculate_re_expense(energy, periods, _tariff_rates())
        assert result.equals(expected)


class TestDemandCharges:
    """Tests for demand charge calculation."""

    def test_demand_charges(self) -> None:
        """Demand charges should be peak demand times rate."""
        result = calculate_demand_charges(peak_demand_kw=100.0, demand_charge_rate_usd_per_kw=5.0)
        assert result == pytest.approx(500.0)

    def test_negative_demand_raises(self) -> None:
        """Negative demand should raise InputValidationError."""
        with pytest.raises(InputValidationError, match="negative"):
            calculate_demand_charges(peak_demand_kw=-10.0, demand_charge_rate_usd_per_kw=5.0)


class TestGridSavings:
    """Tests for grid savings calculation."""

    def test_grid_savings(self) -> None:
        """Grid savings should be BAU minus RE expense."""
        bau = pd.Series([10.0, 12.0])
        re = pd.Series([6.0, 8.0])
        result = calculate_grid_savings(bau, re)
        assert result.tolist() == pytest.approx([4.0, 4.0])

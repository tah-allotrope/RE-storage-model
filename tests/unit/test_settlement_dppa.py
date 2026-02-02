"""
Unit tests for settlement.dppa module.

Tests cover:
1. Core DPPA formula functions
2. DPPA revenue aggregation over hourly data
3. DPPA disabled guard behavior
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from re_storage.core.exceptions import InputValidationError
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.settlement.dppa import (
    calculate_cfd_settlement,
    calculate_consumed_re,
    calculate_delivered_re,
    calculate_dppa_revenue,
    calculate_market_revenue,
    calculate_total_dppa_revenue,
)


def _assumptions(dppa_enabled: bool = True) -> SystemAssumptions:
    return SystemAssumptions(
        simulation_capacity_kwp=100.0,
        actual_capacity_kwp=120.0,
        usable_bess_capacity_kwh=200.0,
        bess_power_rating_kw=100.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=1,
        charging_mode=1,
        charge_start_hour=9,
        charge_end_hour=15,
        precharge_target_hour=17,
        precharge_target_soc_kwh=150.0,
        min_direct_pv_share=0.1,
        active_pv2bess_share=0.8,
        demand_reduction_target=0.2,
        strike_price_usd_per_kwh=0.08,
        k_factor=0.98,
        kpp=1.05,
        bess_enabled=True,
        dppa_enabled=dppa_enabled,
    )


class TestDppaFormulas:
    """Tests for core DPPA formula functions."""

    def test_calculate_delivered_re(self) -> None:
        """Delivered RE should apply division by k-factor and kpp."""
        # 100 / (0.98 * 1.05) = 100 / 1.029 = 97.1817...
        result = calculate_delivered_re(net_gen_kwh=100.0, k_factor=0.98, kpp=1.05, delta=1.0)
        assert result == pytest.approx(97.1817, abs=0.0001)

    def test_calculate_consumed_re(self) -> None:
        """Consumed RE should be capped by load."""
        result = calculate_consumed_re(delivered_re_kwh=80.0, load_kwh=100.0)
        assert result == 80.0

    def test_calculate_market_revenue(self) -> None:
        """Market revenue is net generation times spot price."""
        result = calculate_market_revenue(net_gen_kwh=100.0, fmp_usd_per_kwh=0.02)
        assert result == pytest.approx(2.0)

    def test_calculate_cfd_settlement(self) -> None:
        """CfD settlement is consumed RE times (strike - spot)."""
        result = calculate_cfd_settlement(
            consumed_re_kwh=100.0,
            strike_price_usd_per_kwh=0.08,
            spot_price_usd_per_kwh=0.02,
        )
        assert result == pytest.approx(6.0)

    def test_total_dppa_revenue(self) -> None:
        """Total DPPA revenue is market + CfD."""
        result = calculate_total_dppa_revenue(market_revenue_usd=2.0, cfd_settlement_usd=6.0)
        assert result == pytest.approx(8.0)

    def test_negative_energy_raises(self) -> None:
        """Negative energy inputs should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_delivered_re(net_gen_kwh=-1.0, k_factor=0.98, kpp=1.05, delta=1.0)


class TestCalculateDppaRevenue:
    """Tests for calculate_dppa_revenue."""

    def test_dppa_revenue_computation(self) -> None:
        """DPPA revenue should compute expected columns and values."""
        hourly_data = pd.DataFrame(
            {
                "net_gen_for_dppa_kwh": [100.0, 50.0],
                "load_kwh": [80.0, 60.0],
                "fmp_usd_per_kwh": [0.02, 0.03],
            }
        )
        assumptions = _assumptions()

        result = calculate_dppa_revenue(hourly_data, assumptions)

        assert "total_dppa_revenue_usd" in result.columns
        # delivered[0] = 100 / (0.98 * 1.05) = 97.18
        # load[0] = 80 -> consumed[0] = 80
        assert result["consumed_re_kwh"].iloc[0] == pytest.approx(80.0)
        assert result["market_revenue_usd"].iloc[1] == pytest.approx(1.5)

    def test_dppa_revenue_does_not_mutate_input(self) -> None:
        """Input DataFrame should not be mutated."""
        hourly_data = pd.DataFrame(
            {
                "net_gen_for_dppa_kwh": [100.0],
                "load_kwh": [80.0],
                "fmp_usd_per_kwh": [0.02],
            }
        )
        assumptions = _assumptions()
        original_columns = hourly_data.columns.tolist()

        _ = calculate_dppa_revenue(hourly_data, assumptions)

        assert hourly_data.columns.tolist() == original_columns

    def test_dppa_disabled_returns_zeroes(self, caplog: pytest.LogCaptureFixture) -> None:
        """When DPPA is disabled, revenue columns should be zeroed and warned."""
        hourly_data = pd.DataFrame(
            {
                "net_gen_for_dppa_kwh": [100.0],
                "load_kwh": [80.0],
                "fmp_usd_per_kwh": [0.02],
            }
        )
        assumptions = _assumptions(dppa_enabled=False)

        caplog.set_level(logging.WARNING)
        result = calculate_dppa_revenue(hourly_data, assumptions)

        assert (result["total_dppa_revenue_usd"] == 0).all()
        assert "DPPA module is DISABLED" in caplog.text

    def test_missing_columns_raise(self) -> None:
        """Missing required columns should raise InputValidationError."""
        hourly_data = pd.DataFrame({"net_gen_for_dppa_kwh": [100.0]})
        with pytest.raises(InputValidationError, match="Missing required columns"):
            calculate_dppa_revenue(hourly_data, _assumptions())

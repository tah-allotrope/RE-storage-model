"""
Unit tests for settlement.bundled module (Option 1 — Bundled Discount).

Tests cover:
1. Basic revenue calculation against known values.
2. Full discount (100%) gives zero revenue.
3. Zero discount replicates grid savings.
4. Different tariff periods produce different revenues.
5. Zero delivered energy gives zero revenue.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.types import TimePeriod
from re_storage.settlement.bundled import calculate_bundled_revenue

_TARIFF_RATES = {
    TimePeriod.OFF_PEAK: 0.05,
    TimePeriod.STANDARD: 0.10,
    TimePeriod.PEAK: 0.20,
}


def _series(values: list, period: TimePeriod = TimePeriod.STANDARD) -> tuple:
    n = len(values)
    direct_pv = pd.Series(values, dtype=float)
    discharged = pd.Series([0.0] * n, dtype=float)
    time_period = pd.Series([period] * n)
    return direct_pv, discharged, time_period


class TestCalculateBundledRevenue:
    """Tests for calculate_bundled_revenue."""

    def test_basic_calculation(self) -> None:
        # 100 kWh at STANDARD ($0.10/kWh) with 15% discount
        direct_pv, discharged, time_period = _series([100.0])
        revenue = calculate_bundled_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES, discount_pct=0.15
        )
        # 100 × 0.10 × 0.85 = 8.5
        assert revenue.iloc[0] == pytest.approx(8.5)

    def test_full_discount_gives_zero(self) -> None:
        direct_pv, discharged, time_period = _series([500.0])
        revenue = calculate_bundled_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES, discount_pct=1.0
        )
        assert revenue.iloc[0] == pytest.approx(0.0)

    def test_zero_discount_equals_full_tariff_value(self) -> None:
        direct_pv, discharged, time_period = _series([200.0], TimePeriod.PEAK)
        revenue = calculate_bundled_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES, discount_pct=0.0
        )
        assert revenue.iloc[0] == pytest.approx(200.0 * 0.20)

    def test_bess_discharge_adds_to_revenue(self) -> None:
        direct_pv = pd.Series([100.0])
        discharged = pd.Series([50.0])
        time_period = pd.Series([TimePeriod.STANDARD])
        revenue = calculate_bundled_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES, discount_pct=0.0
        )
        assert revenue.iloc[0] == pytest.approx(150.0 * 0.10)

    def test_peak_period_produces_higher_revenue(self) -> None:
        direct_pv_peak = pd.Series([100.0])
        discharged = pd.Series([0.0])
        tp_peak = pd.Series([TimePeriod.PEAK])
        tp_standard = pd.Series([TimePeriod.STANDARD])
        rev_peak = calculate_bundled_revenue(
            direct_pv_peak, discharged, tp_peak, _TARIFF_RATES, discount_pct=0.10
        )
        rev_std = calculate_bundled_revenue(
            direct_pv_peak, discharged, tp_standard, _TARIFF_RATES, discount_pct=0.10
        )
        assert rev_peak.iloc[0] > rev_std.iloc[0]

    def test_zero_delivered_energy_gives_zero(self) -> None:
        direct_pv, discharged, time_period = _series([0.0])
        revenue = calculate_bundled_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES, discount_pct=0.15
        )
        assert revenue.iloc[0] == pytest.approx(0.0)

"""
Unit tests for settlement.separate module (Option 2 — Separate PV+BESS).

Tests cover:
1. Basic revenue calculation against known values.
2. Different discount rates for PV vs BESS components.
3. Zero BESS discharge only charges PV component.
4. Equal discounts match a bundled-equivalent computation.
5. Zero values give zero revenue.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.types import TimePeriod
from re_storage.settlement.separate import calculate_separate_revenue

_TARIFF_RATES = {
    TimePeriod.OFF_PEAK: 0.05,
    TimePeriod.STANDARD: 0.10,
    TimePeriod.PEAK: 0.20,
}


class TestCalculateSeparateRevenue:
    """Tests for calculate_separate_revenue."""

    def test_basic_calculation(self) -> None:
        direct_pv = pd.Series([100.0])
        discharged = pd.Series([50.0])
        time_period = pd.Series([TimePeriod.STANDARD])
        revenue = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
            pv_discount_pct=0.05, bess_discount_pct=0.05,
        )
        # PV: 100 × 0.10 × 0.95 = 9.5
        # BESS: 50 × 0.10 × 0.95 = 4.75
        assert revenue.iloc[0] == pytest.approx(14.25)

    def test_different_discounts_produce_different_revenues_unequal_energy(self) -> None:
        # Different PV and BESS amounts so swapping discounts changes total
        direct_pv = pd.Series([200.0])
        discharged = pd.Series([50.0])
        time_period = pd.Series([TimePeriod.STANDARD])
        revenue_high_pv_disc = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
            pv_discount_pct=0.20, bess_discount_pct=0.05,
        )
        revenue_high_bess_disc = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
            pv_discount_pct=0.05, bess_discount_pct=0.20,
        )
        # pv=200 so high pv discount hurts more than high bess discount
        assert revenue_high_pv_disc.iloc[0] < revenue_high_bess_disc.iloc[0]

    def test_zero_bess_only_pv_component(self) -> None:
        direct_pv = pd.Series([200.0])
        discharged = pd.Series([0.0])
        time_period = pd.Series([TimePeriod.PEAK])
        revenue = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
            pv_discount_pct=0.10, bess_discount_pct=0.50,
        )
        # Only PV matters here: 200 × 0.20 × 0.90 = 36.0
        assert revenue.iloc[0] == pytest.approx(36.0)

    def test_equal_discounts_matches_bundled_formula(self) -> None:
        direct_pv = pd.Series([100.0])
        discharged = pd.Series([50.0])
        time_period = pd.Series([TimePeriod.STANDARD])
        discount = 0.10
        revenue_sep = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
            pv_discount_pct=discount, bess_discount_pct=discount,
        )
        expected = (100.0 + 50.0) * 0.10 * (1.0 - discount)
        assert revenue_sep.iloc[0] == pytest.approx(expected)

    def test_zero_inputs_give_zero_revenue(self) -> None:
        direct_pv = pd.Series([0.0])
        discharged = pd.Series([0.0])
        time_period = pd.Series([TimePeriod.STANDARD])
        revenue = calculate_separate_revenue(
            direct_pv, discharged, time_period, _TARIFF_RATES,
        )
        assert revenue.iloc[0] == pytest.approx(0.0)

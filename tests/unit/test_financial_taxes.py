"""
Unit tests for financial.taxes module.

Tests cover:
1. Tax rate schedule with holiday, discount tiers, and standard rate.
2. Straight-line depreciation schedule.
3. Unlevered tax calculation (EBIT-based).
4. Levered tax calculation (EBT-based after interest).
5. Edge cases: zero CAPEX, full holiday, post-project depreciation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from re_storage.financial.taxes import (
    build_combined_depreciation_schedule,
    build_tax_rate_schedule,
    calculate_depreciation_schedule,
    calculate_levered_taxes,
    calculate_unlevered_taxes,
)


class TestBuildTaxRateSchedule:
    """Tests for build_tax_rate_schedule."""

    def test_default_schedule_structure(self) -> None:
        rates = build_tax_rate_schedule(project_years=25)
        assert len(rates) == 25
        assert rates.index[0] == 1
        assert rates.index[-1] == 25

    def test_holiday_years_are_zero(self) -> None:
        rates = build_tax_rate_schedule(project_years=10, tax_rate=0.20, holiday_years=3)
        assert rates.loc[1] == 0.0
        assert rates.loc[2] == 0.0
        assert rates.loc[3] == 0.0

    def test_first_discount_period(self) -> None:
        # holiday=3, first_discount=4 → years 4–7 at 5%
        rates = build_tax_rate_schedule(
            project_years=15,
            holiday_years=3,
            first_discount_years=4,
            first_discount_rate=0.05,
        )
        for yr in [4, 5, 6, 7]:
            assert rates.loc[yr] == pytest.approx(0.05)

    def test_second_discount_period(self) -> None:
        # holiday=3, first=4, second=2 → years 8–9 at 10%
        rates = build_tax_rate_schedule(
            project_years=15,
            holiday_years=3,
            first_discount_years=4,
            first_discount_rate=0.05,
            second_discount_years=2,
            second_discount_rate=0.10,
        )
        assert rates.loc[8] == pytest.approx(0.10)
        assert rates.loc[9] == pytest.approx(0.10)

    def test_standard_rate_after_all_discounts(self) -> None:
        # holiday=3, first=4, second=2 → years 10+ at 20%
        rates = build_tax_rate_schedule(
            project_years=15,
            tax_rate=0.20,
            holiday_years=3,
            first_discount_years=4,
            second_discount_years=2,
        )
        for yr in range(10, 16):
            assert rates.loc[yr] == pytest.approx(0.20)

    def test_vietnam_incentive_zone_default(self) -> None:
        # Default schedule: 0% yr 1-4, 10% yr 5-9, 20% yr 10+
        rates = build_tax_rate_schedule(project_years=25)
        assert all(rates.loc[y] == 0.0 for y in range(1, 5))
        assert all(rates.loc[y] == pytest.approx(0.10) for y in range(5, 10))
        assert all(rates.loc[y] == pytest.approx(0.20) for y in range(10, 26))

    def test_custom_excel_reference_schedule(self) -> None:
        # Explicit schedule matching older Excel: holiday=5, 8yrs@5%, 2yrs@10%, then 20%
        rates = build_tax_rate_schedule(
            project_years=25,
            tax_rate=0.20,
            holiday_years=5,
            first_discount_years=8,
            first_discount_rate=0.05,
            second_discount_years=2,
            second_discount_rate=0.10,
        )
        assert all(rates.loc[y] == 0.0 for y in range(1, 6))
        assert all(rates.loc[y] == pytest.approx(0.05) for y in range(6, 14))
        assert all(rates.loc[y] == pytest.approx(0.10) for y in [14, 15])
        assert all(rates.loc[y] == pytest.approx(0.20) for y in range(16, 26))


class TestCalculateDepreciationSchedule:
    """Tests for calculate_depreciation_schedule."""

    def test_straight_line_within_tenor(self) -> None:
        dep = calculate_depreciation_schedule(total_capex_usd=20_000.0, tenor_years=20, project_years=25)
        for yr in range(1, 21):
            assert dep.loc[yr] == pytest.approx(1_000.0)

    def test_zero_after_tenor(self) -> None:
        dep = calculate_depreciation_schedule(total_capex_usd=20_000.0, tenor_years=10, project_years=15)
        for yr in range(11, 16):
            assert dep.loc[yr] == 0.0

    def test_total_depreciation_equals_capex(self) -> None:
        dep = calculate_depreciation_schedule(total_capex_usd=50_000_000.0, tenor_years=20, project_years=20)
        assert dep.sum() == pytest.approx(50_000_000.0, rel=1e-9)

    def test_zero_capex_gives_zero_depreciation(self) -> None:
        dep = calculate_depreciation_schedule(total_capex_usd=0.0, tenor_years=20, project_years=5)
        assert (dep == 0.0).all()


class TestCalculateUnleveredTaxes:
    """Tests for calculate_unlevered_taxes."""

    def _series(self, values: list[float]) -> pd.Series:
        return pd.Series(values, index=pd.RangeIndex(1, len(values) + 1))

    def test_basic_tax_computation(self) -> None:
        ebitda = self._series([1_000_000.0])
        dep = self._series([200_000.0])
        rates = self._series([0.20])
        taxes = calculate_unlevered_taxes(ebitda, dep, rates)
        # EBIT = 800,000; Tax = 800,000 × 20% = 160,000
        assert taxes.iloc[0] == pytest.approx(160_000.0)

    def test_tax_holiday_zero_rate(self) -> None:
        ebitda = self._series([500_000.0, 500_000.0])
        dep = self._series([100_000.0, 100_000.0])
        rates = self._series([0.0, 0.20])
        taxes = calculate_unlevered_taxes(ebitda, dep, rates)
        assert taxes.iloc[0] == 0.0
        assert taxes.iloc[1] == pytest.approx(80_000.0)

    def test_negative_ebit_gives_zero_tax(self) -> None:
        ebitda = self._series([100_000.0])
        dep = self._series([200_000.0])  # Depreciation > EBITDA → EBIT < 0
        rates = self._series([0.20])
        taxes = calculate_unlevered_taxes(ebitda, dep, rates)
        assert taxes.iloc[0] == 0.0

    def test_output_index_matches_ebitda(self) -> None:
        ebitda = self._series([1_000_000.0] * 5)
        dep = self._series([200_000.0] * 5)
        rates = self._series([0.20] * 5)
        taxes = calculate_unlevered_taxes(ebitda, dep, rates)
        assert list(taxes.index) == list(ebitda.index)


class TestCalculateLeveredTaxes:
    """Tests for calculate_levered_taxes."""

    def _series(self, values: list[float]) -> pd.Series:
        return pd.Series(values, index=pd.RangeIndex(1, len(values) + 1))

    def test_levered_less_than_unlevered(self) -> None:
        ebitda = self._series([1_000_000.0])
        dep = self._series([200_000.0])
        interest = self._series([100_000.0])
        rates = self._series([0.20])
        unlevered = calculate_unlevered_taxes(ebitda, dep, rates)
        levered = calculate_levered_taxes(ebitda, dep, interest, rates)
        # EBT = EBIT - interest = 800,000 - 100,000 = 700,000
        # Tax = 700,000 × 20% = 140,000 < 160,000 (unlevered)
        assert levered.iloc[0] < unlevered.iloc[0]
        assert levered.iloc[0] == pytest.approx(140_000.0)

    def test_negative_ebt_gives_zero_tax(self) -> None:
        ebitda = self._series([200_000.0])
        dep = self._series([100_000.0])
        interest = self._series([200_000.0])  # Interest > EBIT → EBT < 0
        rates = self._series([0.20])
        taxes = calculate_levered_taxes(ebitda, dep, interest, rates)
        assert taxes.iloc[0] == 0.0


class TestBuildCombinedDepreciationSchedule:
    """Tests for build_combined_depreciation_schedule (PV 20yr + BESS 10yr)."""

    def test_output_length(self) -> None:
        dep = build_combined_depreciation_schedule(
            pv_capex_usd=30_000_000.0,
            bess_capex_usd=13_200_000.0,
            project_years=25,
        )
        assert len(dep) == 25
        assert list(dep.index) == list(range(1, 26))

    def test_pv_and_bess_combined_year1(self) -> None:
        # PV: 30M / 20yr = 1.5M/yr; BESS: 13.2M / 10yr = 1.32M/yr
        # Year 1 = 1.5M + 1.32M = 2.82M
        dep = build_combined_depreciation_schedule(
            pv_capex_usd=30_000_000.0,
            bess_capex_usd=13_200_000.0,
            pv_tenor_years=20,
            bess_tenor_years=10,
            project_years=25,
        )
        expected_yr1 = 30_000_000.0 / 20 + 13_200_000.0 / 10
        assert dep.loc[1] == pytest.approx(expected_yr1)

    def test_bess_depreciation_stops_after_tenor(self) -> None:
        # After year 10, only PV depreciation remains
        dep = build_combined_depreciation_schedule(
            pv_capex_usd=30_000_000.0,
            bess_capex_usd=13_200_000.0,
            pv_tenor_years=20,
            bess_tenor_years=10,
            project_years=25,
        )
        pv_only = 30_000_000.0 / 20
        for yr in range(11, 21):
            assert dep.loc[yr] == pytest.approx(pv_only)

    def test_both_stop_after_longer_tenor(self) -> None:
        dep = build_combined_depreciation_schedule(
            pv_capex_usd=20_000_000.0,
            bess_capex_usd=10_000_000.0,
            pv_tenor_years=20,
            bess_tenor_years=10,
            project_years=25,
        )
        for yr in range(21, 26):
            assert dep.loc[yr] == pytest.approx(0.0)

    def test_zero_capex_gives_zero(self) -> None:
        dep = build_combined_depreciation_schedule(
            pv_capex_usd=0.0,
            bess_capex_usd=0.0,
            project_years=5,
        )
        assert (dep == 0.0).all()

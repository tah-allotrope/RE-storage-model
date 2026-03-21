"""
Unit tests for financial.mra module.

Tests cover:
1. Default build-up schedule: years 1-4 each at 25% of target.
2. Total contributions equal 100% of combined target over years 1-4.
3. Zero capex produces zero contributions.
4. Custom build-up schedules.
5. Years beyond build-up schedule are zero.
"""

from __future__ import annotations

import pytest

from re_storage.financial.mra import build_mra_schedule, _DEFAULT_BUILDUP


class TestBuildMraSchedule:
    """Tests for build_mra_schedule."""

    def test_returns_correct_length(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=30_270_000.0,
            project_years=25,
        )
        assert len(mra) == 25
        assert list(mra.index) == list(range(1, 26))

    def test_default_buildup_years_1_to_4_nonzero(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=30_270_000.0,
            bess_mra_pct=0.60,
            pv_mra_pct=0.10,
        )
        for yr in range(1, 5):
            assert mra.loc[yr] > 0.0

    def test_years_beyond_buildup_are_zero(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=30_270_000.0,
            project_years=10,
        )
        for yr in range(5, 11):
            assert mra.loc[yr] == pytest.approx(0.0)

    def test_default_buildup_equal_per_year(self) -> None:
        """Each of years 1-4 should contribute exactly 25% of total target."""
        bess_capex = 13_200_000.0
        pv_capex = 30_270_000.0
        bess_target = 0.60 * bess_capex
        pv_target = 0.10 * pv_capex
        total_target = bess_target + pv_target
        expected_per_year = total_target * 0.25

        mra = build_mra_schedule(
            bess_capex_usd=bess_capex,
            pv_capex_usd=pv_capex,
            project_years=25,
        )
        for yr in range(1, 5):
            assert mra.loc[yr] == pytest.approx(expected_per_year, rel=1e-9)

    def test_total_contributions_equal_full_target(self) -> None:
        """Sum of years 1-4 should equal 100% of the combined MRA target."""
        bess_capex = 13_200_000.0
        pv_capex = 30_270_000.0
        total_target = 0.60 * bess_capex + 0.10 * pv_capex

        mra = build_mra_schedule(
            bess_capex_usd=bess_capex,
            pv_capex_usd=pv_capex,
            project_years=25,
        )
        assert mra.sum() == pytest.approx(total_target, rel=1e-9)

    def test_bess_mra_ballpark(self) -> None:
        """BESS MRA: 60% of 13.2M = 7.92M, each year ≈ 1.98M for 4 years."""
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=0.0,
            bess_mra_pct=0.60,
            pv_mra_pct=0.0,
            project_years=25,
        )
        expected_per_year = 0.60 * 13_200_000.0 * 0.25
        assert mra.loc[1] == pytest.approx(expected_per_year, rel=1e-9)
        assert mra.sum() == pytest.approx(0.60 * 13_200_000.0, rel=1e-9)

    def test_zero_capex_gives_zero_mra(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=0.0,
            pv_capex_usd=0.0,
            project_years=5,
        )
        assert (mra == 0.0).all()

    def test_custom_buildup_schedule(self) -> None:
        custom = {1: 0.50, 2: 0.50}
        mra = build_mra_schedule(
            bess_capex_usd=10_000.0,
            pv_capex_usd=0.0,
            bess_mra_pct=1.0,
            pv_mra_pct=0.0,
            buildup_schedule=custom,
            project_years=5,
        )
        # target = 1.0 × 10,000 = 10,000
        # year 1 = 50% = 5,000; year 2 = 50% = 5,000; rest = 0
        assert mra.loc[1] == pytest.approx(5_000.0)
        assert mra.loc[2] == pytest.approx(5_000.0)
        assert mra.loc[3] == pytest.approx(0.0)

    def test_default_buildup_constant_is_correct(self) -> None:
        """_DEFAULT_BUILDUP should be {1: 25%, 2: 25%, 3: 25%, 4: 25%}."""
        assert _DEFAULT_BUILDUP == {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
        assert sum(_DEFAULT_BUILDUP.values()) == pytest.approx(1.0)

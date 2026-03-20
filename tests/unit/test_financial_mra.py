"""
Unit tests for financial.mra module.

Tests cover:
1. Default build-up schedule (10/30/30/30 split).
2. Total contributions equal target amount.
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

    def test_default_buildup_years_1_to_3_nonzero(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=30_270_000.0,
            bess_mra_pct=0.60,
            pv_mra_pct=0.10,
        )
        assert mra.loc[1] > 0.0
        assert mra.loc[2] > 0.0
        assert mra.loc[3] > 0.0

    def test_years_beyond_buildup_are_zero(self) -> None:
        mra = build_mra_schedule(
            bess_capex_usd=13_200_000.0,
            pv_capex_usd=30_270_000.0,
            project_years=10,
        )
        for yr in range(4, 11):
            assert mra.loc[yr] == pytest.approx(0.0)

    def test_total_operating_contributions_equal_90_percent_of_target(self) -> None:
        # Default: Year 0 = 10% at FC; Years 1-3 = 90% operational
        bess_capex = 13_200_000.0
        pv_capex = 30_270_000.0
        bess_target = 0.60 * bess_capex
        pv_target = 0.10 * pv_capex
        total_target = bess_target + pv_target
        expected_operating = total_target * (
            _DEFAULT_BUILDUP.get(1, 0.0)
            + _DEFAULT_BUILDUP.get(2, 0.0)
            + _DEFAULT_BUILDUP.get(3, 0.0)
        )
        mra = build_mra_schedule(
            bess_capex_usd=bess_capex,
            pv_capex_usd=pv_capex,
            project_years=25,
        )
        assert mra.sum() == pytest.approx(expected_operating, rel=1e-9)

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

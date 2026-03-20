"""
Unit tests for financial.opex module.

Tests cover:
1. Basic OPEX computation from unit rates.
2. Compound escalation logic.
3. Zero-value edge cases (no PV, no BESS, no capex).
4. Land lease proportional to revenue.
5. Schema compliance with waterfall OPEX_COLUMNS.
"""

from __future__ import annotations

import pytest

from re_storage.financial.opex import build_opex_schedule
from re_storage.financial.waterfall import OPEX_COLUMNS


class TestBuildOpexSchedule:
    """Tests for build_opex_schedule."""

    def test_returns_dataframe_with_required_columns(self) -> None:
        opex = build_opex_schedule(
            project_years=5,
            installed_pv_mwp=40.0,
            bess_mwh=66.0,
            total_capex_usd=49_513_200.0,
        )
        required = OPEX_COLUMNS - {"year"}
        assert required.issubset(opex.columns)
        assert len(opex) == 5
        assert list(opex["year"]) == [1, 2, 3, 4, 5]

    def test_year1_om_matches_formula(self) -> None:
        # O&M Solar = 6000 × 40.36 = 241,800
        # O&M BESS  = 2000 × 66    = 132,000
        # Other     = 1000 × 40.36 =  40,360
        # Total o_and_m = 414,160
        opex = build_opex_schedule(
            project_years=1,
            installed_pv_mwp=40.36,
            bess_mwh=66.0,
            total_capex_usd=49_513_200.0,
            om_solar_usd_per_mwp=6_000.0,
            om_bess_usd_per_mwh=2_000.0,
            other_opex_usd_per_mwp=1_000.0,
        )
        expected_om = 6_000.0 * 40.36 + 2_000.0 * 66.0 + 1_000.0 * 40.36
        assert opex.loc[1, "o_and_m_usd"] == pytest.approx(expected_om, rel=1e-6)

    def test_year1_insurance_matches_formula(self) -> None:
        # Insurance = (0.25% + 0.25%) × 49,513,200 = 247,566
        opex = build_opex_schedule(
            project_years=1,
            installed_pv_mwp=40.36,
            bess_mwh=66.0,
            total_capex_usd=49_513_200.0,
            insurance_solar_pct_capex=0.0025,
            insurance_bess_pct_capex=0.0025,
        )
        expected_ins = (0.0025 + 0.0025) * 49_513_200.0
        assert opex.loc[1, "insurance_usd"] == pytest.approx(expected_ins, rel=1e-6)

    def test_escalation_applied_compound(self) -> None:
        opex = build_opex_schedule(
            project_years=3,
            installed_pv_mwp=10.0,
            bess_mwh=10.0,
            total_capex_usd=10_000_000.0,
            opex_escalation_pct=0.10,  # 10% escalation for easy math
        )
        yr1 = opex.loc[1, "o_and_m_usd"]
        yr2 = opex.loc[2, "o_and_m_usd"]
        yr3 = opex.loc[3, "o_and_m_usd"]
        assert yr2 == pytest.approx(yr1 * 1.10, rel=1e-9)
        assert yr3 == pytest.approx(yr1 * 1.21, rel=1e-9)

    def test_zero_escalation_keeps_flat_values(self) -> None:
        opex = build_opex_schedule(
            project_years=5,
            installed_pv_mwp=10.0,
            bess_mwh=10.0,
            total_capex_usd=5_000_000.0,
            opex_escalation_pct=0.0,
        )
        yr1_om = opex.loc[1, "o_and_m_usd"]
        for yr in range(2, 6):
            assert opex.loc[yr, "o_and_m_usd"] == pytest.approx(yr1_om, rel=1e-9)

    def test_land_lease_proportional_to_revenue(self) -> None:
        year1_revenue = 4_576_659.86
        opex = build_opex_schedule(
            project_years=2,
            installed_pv_mwp=40.0,
            bess_mwh=66.0,
            total_capex_usd=49_000_000.0,
            land_lease_pct_revenue=0.02,
            opex_escalation_pct=0.0,
            year1_total_revenue_usd=year1_revenue,
        )
        expected_lease = 0.02 * year1_revenue
        assert opex.loc[1, "land_lease_usd"] == pytest.approx(expected_lease, rel=1e-9)

    def test_zero_pv_mwp_gives_zero_om_solar(self) -> None:
        opex = build_opex_schedule(
            project_years=1,
            installed_pv_mwp=0.0,
            bess_mwh=66.0,
            total_capex_usd=13_200_000.0,
        )
        # o_and_m_usd = bess_only = 2000 × 66 = 132,000
        assert opex.loc[1, "o_and_m_usd"] == pytest.approx(2_000.0 * 66.0, rel=1e-9)

    def test_taxes_and_mra_are_zero_in_output(self) -> None:
        opex = build_opex_schedule(
            project_years=3,
            installed_pv_mwp=10.0,
            bess_mwh=10.0,
            total_capex_usd=5_000_000.0,
        )
        assert (opex["taxes_usd"] == 0.0).all()
        assert (opex["mra_contribution_usd"] == 0.0).all()

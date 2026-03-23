"""
Unit tests for financial.opex module.

Tests cover:
1. Basic OPEX computation from unit rates.
2. Compound CPI escalation logic.
3. Zero-value edge cases (no PV, no BESS, no capex).
4. Flat land lease and asset management fees.
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
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_513_200.0,
            project_years=5,
        )
        required = OPEX_COLUMNS - {"year"}
        assert required.issubset(opex.columns)
        assert len(opex) == 5
        assert list(opex["year"]) == [1, 2, 3, 4, 5]

    def test_year1_om_matches_formula(self) -> None:
        # O&M Solar = 8,000 × 40.0 = 320,000
        # O&M BESS  = 5,000 × 66.0 = 330,000
        # Total o_and_m = 650,000
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_513_200.0,
            project_years=1,
            om_solar_usd_per_mwp=8_000.0,
            om_bess_usd_per_mwh=5_000.0,
        )
        expected_om = 8_000.0 * 40.0 + 5_000.0 * 66.0
        assert opex.loc[1, "o_and_m_usd"] == pytest.approx(expected_om, rel=1e-6)

    def test_year1_insurance_matches_formula(self) -> None:
        # Insurance = 0.5% × 49,513,200 = 247,566
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_513_200.0,
            project_years=1,
            insurance_pct_capex=0.005,
        )
        expected_ins = 0.005 * 49_513_200.0
        assert opex.loc[1, "insurance_usd"] == pytest.approx(expected_ins, rel=1e-6)

    def test_year1_flat_asset_management(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_513_200.0,
            project_years=1,
            asset_management_usd=15_000.0,
        )
        assert opex.loc[1, "management_fees_usd"] == pytest.approx(15_000.0, rel=1e-9)

    def test_year1_flat_land_lease(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_513_200.0,
            project_years=1,
            land_lease_usd=20_000.0,
        )
        assert opex.loc[1, "land_lease_usd"] == pytest.approx(20_000.0, rel=1e-9)

    def test_escalation_applied_compound(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=10.0,
            bess_capacity_mwh=10.0,
            total_capex_usd=10_000_000.0,
            project_years=3,
            cpi=0.10,  # 10% escalation for easy math
        )
        yr1 = opex.loc[1, "o_and_m_usd"]
        yr2 = opex.loc[2, "o_and_m_usd"]
        yr3 = opex.loc[3, "o_and_m_usd"]
        assert yr2 == pytest.approx(yr1 * 1.10, rel=1e-9)
        assert yr3 == pytest.approx(yr1 * 1.21, rel=1e-9)

    def test_zero_cpi_keeps_flat_values(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=10.0,
            bess_capacity_mwh=10.0,
            total_capex_usd=5_000_000.0,
            project_years=5,
            cpi=0.0,
        )
        yr1_om = opex.loc[1, "o_and_m_usd"]
        for yr in range(2, 6):
            assert opex.loc[yr, "o_and_m_usd"] == pytest.approx(yr1_om, rel=1e-9)

    def test_land_lease_escalates_with_cpi(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=49_000_000.0,
            project_years=3,
            cpi=0.04,
            land_lease_usd=20_000.0,
        )
        assert opex.loc[1, "land_lease_usd"] == pytest.approx(20_000.0, rel=1e-9)
        assert opex.loc[2, "land_lease_usd"] == pytest.approx(20_000.0 * 1.04, rel=1e-9)
        assert opex.loc[3, "land_lease_usd"] == pytest.approx(20_000.0 * 1.04**2, rel=1e-9)

    def test_zero_pv_mwp_gives_zero_om_solar(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=0.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=13_200_000.0,
        )
        # o_and_m_usd = bess_only = 5,000 × 66 = 330,000
        assert opex.loc[1, "o_and_m_usd"] == pytest.approx(5_000.0 * 66.0, rel=1e-9)

    def test_taxes_and_mra_are_zero_in_output(self) -> None:
        opex = build_opex_schedule(
            solar_capacity_mwp=10.0,
            bess_capacity_mwh=10.0,
            total_capex_usd=5_000_000.0,
            project_years=3,
        )
        assert (opex["taxes_usd"] == 0.0).all()
        assert (opex["mra_contribution_usd"] == 0.0).all()

    def test_default_values_ballpark(self) -> None:
        """Year 1 total OPEX with defaults should be in a reasonable range for a ~40 MWp project."""
        opex = build_opex_schedule(
            solar_capacity_mwp=40.0,
            bess_capacity_mwh=66.0,
            total_capex_usd=43_500_000.0,
            project_years=25,
        )
        # O&M Solar: 8,000×40 = 320,000
        # O&M BESS:  5,000×66 = 330,000
        # Insurance: 0.5%×43.5M = 217,500
        # Asset Mgmt: 15,000
        # Land Lease: 20,000
        # Total ≈ 902,500
        year1_total = (
            opex.loc[1, "o_and_m_usd"]
            + opex.loc[1, "insurance_usd"]
            + opex.loc[1, "management_fees_usd"]
            + opex.loc[1, "land_lease_usd"]
        )
        assert 800_000 < year1_total < 1_200_000
        assert len(opex) == 25

    def test_other_opex_asset_management_and_revenue_land_lease_inputs(self) -> None:
        annual_revenue = {1: 1_000_000.0, 2: 1_100_000.0}

        opex = build_opex_schedule(
            solar_capacity_mwp=3.0,
            bess_capacity_mwh=2.0,
            total_capex_usd=1_000_000.0,
            project_years=2,
            cpi=0.0,
            om_solar_usd_per_mwp=6_000.0,
            om_bess_usd_per_mwh=2_000.0,
            other_opex_usd_per_mwp=1_000.0,
            asset_management_usd_per_mwp=3_000.0,
            land_lease_pct_revenue=0.005,
            annual_revenue_usd=annual_revenue,
            asset_management_usd=0.0,
            land_lease_usd=0.0,
        )

        assert opex.loc[1, "o_and_m_usd"] == pytest.approx(25_000.0)
        assert opex.loc[1, "management_fees_usd"] == pytest.approx(9_000.0)
        assert opex.loc[1, "land_lease_usd"] == pytest.approx(5_000.0)
        assert opex.loc[2, "land_lease_usd"] == pytest.approx(5_500.0)

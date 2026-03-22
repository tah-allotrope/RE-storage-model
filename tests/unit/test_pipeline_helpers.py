"""Unit tests for workbook-alignment helpers in pipeline.py."""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.pipeline import (
    _build_dppa_net_generation,
    _normalize_hourly_price_columns_to_usd,
    _run_financial,
)


def test_build_dppa_net_generation_includes_discharge() -> None:
    """DPPA net generation should follow the workbook's Calc!AB signal."""
    hourly = pd.DataFrame(
        {
            "solar_gen_kw": [10.0, 0.0],
            "pv_charged_kw": [3.0, 0.0],
            "discharged_kw": [2.0, 4.0],
        }
    )

    result = _build_dppa_net_generation(hourly)

    assert result.tolist() == pytest.approx([9.0, 4.0])


def test_normalize_hourly_price_columns_to_usd_converts_vnd_scale() -> None:
    """Workbook hourly prices in VND should be converted to USD/kWh."""
    hourly = pd.DataFrame(
        {
            "fmp_usd_per_kwh": [1300.0, 2600.0],
            "cfmp_usd_per_kwh": [1500.0, 2800.0],
        }
    )

    result = _normalize_hourly_price_columns_to_usd(hourly, exchange_rate_usd_vnd=26000.0)

    assert result["fmp_usd_per_kwh"].tolist() == pytest.approx([0.05, 0.1])
    assert result["cfmp_usd_per_kwh"].tolist() == pytest.approx(
        [1500.0 / 26000.0, 2800.0 / 26000.0]
    )


def test_normalize_hourly_price_columns_to_usd_leaves_usd_scale_unchanged() -> None:
    """Already-normalized hourly prices should not be divided again."""
    hourly = pd.DataFrame(
        {
            "fmp_usd_per_kwh": [0.05, 0.1],
            "cfmp_usd_per_kwh": [0.055, 0.11],
        }
    )

    result = _normalize_hourly_price_columns_to_usd(hourly, exchange_rate_usd_vnd=26000.0)

    assert result.equals(hourly)


def test_run_financial_aligns_year_indexed_lifetime_and_opex() -> None:
    """Financial stage should align year-indexed annual schedules without length mismatches."""
    lifetime = pd.DataFrame(
        {
            "year": [1, 2],
            "generation_mwh": [1000.0, 980.0],
            "battery_capacity_kwh": [500.0, 490.0],
            "dppa_revenue_usd": [1000.0, 950.0],
            "grid_savings_usd": [300.0, 280.0],
        }
    ).set_index("year", drop=False)

    result = _run_financial(
        lifetime=lifetime,
        project_years=2,
        interest_rate_pct=6.0,
        tenor_years=1,
        target_dscr=1.3,
        initial_capex_usd=500.0,
        discount_rate_pct=8.0,
        cod_date="2027-01-01",
        solar_capacity_mwp=0.0,
        bess_capacity_mwh=0.0,
        om_solar_usd_per_mwp=0.0,
        om_bess_usd_per_mwh=0.0,
        insurance_pct_capex=0.0,
        asset_management_usd=0.0,
        land_lease_usd=0.0,
        cpi=0.0,
        tax_rate=0.0,
        tax_holiday_years=2,
        first_discount_years=0,
        first_discount_rate=0.0,
        second_discount_years=0,
        second_discount_rate=0.0,
        pv_depreciation_tenor_years=2,
        bess_depreciation_tenor_years=2,
        bess_capex_usd=0.0,
        pv_capex_usd=0.0,
        bess_mra_pct=0.0,
        pv_mra_pct=0.0,
        demand_charge_savings_usd_yr1=0.0,
    )

    assert result["year1_ebitda_usd"] == pytest.approx(1300.0)
    assert result["year1_opex_usd"] == pytest.approx(0.0)

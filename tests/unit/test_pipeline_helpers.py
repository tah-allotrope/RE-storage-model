"""Unit tests for workbook-alignment helpers in pipeline.py."""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.types import TimePeriod
from re_storage.inputs.loaders import load_tariff_schedule
from re_storage.pipeline import (
    _build_battery_config,
    _run_physics,
    _build_dppa_net_generation,
    _normalize_hourly_price_columns_to_usd,
    _run_financial,
)
from re_storage.inputs.schemas import SystemAssumptions


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


def test_load_tariff_schedule_can_select_alternate_sheet(tmp_path) -> None:
    """Excel tariff loading should support explicit TOU2026 sheet selection."""
    workbook = tmp_path / "tariffs.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "hour": list(range(24)),
                "period": ["off_peak"] * 6 + ["standard"] * 12 + ["peak"] * 6,
            }
        ).to_excel(writer, sheet_name="Tariff Schedule", index=False)
        pd.DataFrame(
            {
                "hour": list(range(24)),
                "period": ["off_peak"] * 6 + ["standard"] * 12 + ["peak"] * 5 + ["standard"],
            }
        ).to_excel(writer, sheet_name="Tariff Schedule 2026", index=False)

    default_schedule = load_tariff_schedule(workbook)
    tou2026_schedule = load_tariff_schedule(workbook, sheet_name="Tariff Schedule 2026")

    assert default_schedule[TimePeriod.PEAK] == [18, 19, 20, 21, 22, 23]
    assert tou2026_schedule[TimePeriod.PEAK] == [18, 19, 20, 21, 22]
    assert tou2026_schedule[TimePeriod.STANDARD][-1] == 23


def test_build_battery_config_uses_dispatch_flags() -> None:
    """Pipeline battery config should preserve dispatch flags from assumptions."""
    assumptions = SystemAssumptions(
        simulation_capacity_kwp=100.0,
        actual_capacity_kwp=100.0,
        usable_bess_capacity_kwh=500.0,
        bess_power_rating_kw=250.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=1,
        charging_mode=1,
        charge_start_hour=0,
        charge_end_hour=5,
        precharge_target_hour=18,
        precharge_target_soc_kwh=500.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_reduction_target=0.0,
        strike_price_usd_per_kwh=0.05,
        k_factor=1.0,
        kpp=1.0,
        bess_enabled=True,
        dppa_enabled=True,
        when_needed=False,
        after_sunset=True,
        optimize_mode=True,
        peak_mode=False,
        max_cycles_per_day=1,
    )

    config = _build_battery_config(assumptions)

    assert config.when_needed is False
    assert config.after_sunset is True
    assert config.optimize_mode is True
    assert config.peak_mode is False
    assert config.max_cycles_per_day == 1


def test_run_physics_honors_cycle_cap() -> None:
    """A max_cycles_per_day override should suppress a second discharge start."""
    hourly = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01", periods=24, freq="h"),
            "simulation_profile_kw": [
                8.0 if h in {0, 1, 2, 12, 13, 14} else 0.0 for h in range(24)
            ],
            "irradiation_wh_m2": [0.0] * 24,
            "load_kw": [2.0] * 24,
            "fmp_usd_per_kwh": [0.05] * 24,
            "cfmp_usd_per_kwh": [0.05] * 24,
        }
    )
    assumptions = SystemAssumptions(
        simulation_capacity_kwp=1.0,
        actual_capacity_kwp=100.0,
        usable_bess_capacity_kwh=500.0,
        bess_power_rating_kw=250.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=1,
        charging_mode=1,
        charge_start_hour=0,
        charge_end_hour=23,
        precharge_target_hour=18,
        precharge_target_soc_kwh=500.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_reduction_target=0.0,
        strike_price_usd_per_kwh=0.05,
        k_factor=1.0,
        kpp=1.0,
        bess_enabled=True,
        dppa_enabled=True,
        when_needed=False,
        after_sunset=False,
        optimize_mode=False,
        peak_mode=True,
        max_cycles_per_day=1,
    )
    schedule = {
        TimePeriod.OFF_PEAK: [0, 1, 2, 3, 4, 5],
        TimePeriod.STANDARD: [6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 21, 22, 23],
        TimePeriod.PEAK: [10, 11, 18, 19, 20],
    }

    result = _run_physics(hourly, assumptions, schedule)
    discharge_hours = result.index[result["discharged_kw"] > 0].tolist()

    assert discharge_hours == [10, 11]

"""
Integration tests for end-to-end pipeline scenarios.

These tests stitch together physics, settlement, and aggregation logic using
small synthetic datasets to validate module interoperability.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from re_storage.aggregation import aggregate_hourly_to_monthly, build_lifetime_projection
from re_storage.aggregation.annual import calculate_year1_totals
from re_storage.core.types import TimePeriod
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.physics.solar import (
    calculate_direct_pv_consumption_vectorized,
    calculate_surplus_generation_vectorized,
    scale_generation,
)
from re_storage.settlement.dppa import calculate_dppa_revenue
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_grid_savings,
    calculate_re_expense,
)


def _assumptions(dppa_enabled: bool = True) -> SystemAssumptions:
    return SystemAssumptions(
        simulation_capacity_kwp=100.0,
        actual_capacity_kwp=100.0,
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


def _tariff_rates() -> dict[TimePeriod, float]:
    return {
        TimePeriod.OFF_PEAK: 0.05,
        TimePeriod.STANDARD: 0.1,
        TimePeriod.PEAK: 0.2,
    }


def _time_periods(datetimes: pd.Series) -> pd.Series:
    def _classify(hour: int) -> TimePeriod:
        if hour < 7:
            return TimePeriod.OFF_PEAK
        if hour < 17:
            return TimePeriod.STANDARD
        return TimePeriod.PEAK

    return pd.Series([_classify(ts.hour) for ts in datetimes], index=datetimes.index)


def _build_hourly_results(hours: int = 48) -> pd.DataFrame:
    datetimes = pd.date_range("2025-01-31", periods=hours, freq="h")
    simulation_profile_kw = pd.Series(50.0, index=datetimes)
    load_kw = pd.Series(40.0, index=datetimes)

    solar_gen_kw = scale_generation(simulation_profile_kw.to_numpy(), scale_factor=1.0)
    pv_to_bess_kw = pd.Series(0.0, index=datetimes)
    direct_consumption_kw = calculate_direct_pv_consumption_vectorized(
        solar_gen_kw, load_kw.to_numpy(), pv_to_bess_kw.to_numpy()
    )
    surplus_kw = calculate_surplus_generation_vectorized(
        solar_gen_kw, direct_consumption_kw, pv_to_bess_kw.to_numpy()
    )

    grid_load_after_solar_kw = (load_kw.to_numpy() - direct_consumption_kw).clip(min=0.0)
    grid_load_after_re_kw = grid_load_after_solar_kw

    hourly = pd.DataFrame(
        {
            "datetime": datetimes,
            "simulation_profile_kw": simulation_profile_kw.values,
            "solar_gen_kw": solar_gen_kw,
            "load_kw": load_kw.values,
            "load_kwh": load_kw.values,
            "net_gen_for_dppa_kwh": surplus_kw,
            "fmp_usd_per_kwh": 0.02,
            "grid_load_after_solar_kw": grid_load_after_solar_kw,
            "grid_load_after_re_kw": grid_load_after_re_kw,
        }
    )
    return hourly


class TestFullPipeline:
    def test_end_to_end_small_dataset(self) -> None:
        hourly = _build_hourly_results()
        assumptions = _assumptions()

        time_period = _time_periods(hourly["datetime"])
        bau_expense = calculate_bau_expense(hourly["load_kwh"], time_period, _tariff_rates())
        re_expense = calculate_re_expense(
            hourly["grid_load_after_re_kw"], time_period, _tariff_rates()
        )
        hourly = hourly.assign(
            bau_expense_usd=bau_expense,
            re_expense_usd=re_expense,
        )
        hourly["grid_savings_usd"] = calculate_grid_savings(bau_expense, re_expense)

        dppa_hourly = calculate_dppa_revenue(hourly, assumptions)
        monthly = aggregate_hourly_to_monthly(
            hourly,
            demand_reduction_target_ratio=assumptions.demand_reduction_target,
        )
        year1 = calculate_year1_totals(
            monthly,
            hourly,
            dppa_hourly,
            scale_factor=assumptions.scale_factor,
            solar_gen_column="solar_gen_kw",
        )

        degradation_table = pd.DataFrame(
            {
                "year": [1, 2],
                "pv_factor": [1.0, 0.98],
                "battery_factor_with_replacement": [1.0, 0.97],
            }
        )
        lifetime = build_lifetime_projection(
            year1,
            degradation_table,
            initial_capacity_kwh=assumptions.usable_bess_capacity_kwh,
            project_years=2,
        )

        assert list(monthly.index) == [1, 2]
        assert "total_dppa_revenue_usd" in year1.columns
        assert lifetime.index.tolist() == [1, 2]
        assert lifetime["dppa_revenue_usd"].sum() > 0

    def test_dppa_disabled_zeroes_revenue(self) -> None:
        hourly = _build_hourly_results()
        assumptions = _assumptions(dppa_enabled=False)

        dppa_hourly = calculate_dppa_revenue(hourly, assumptions)
        assert (dppa_hourly["total_dppa_revenue_usd"] == 0).all()

    def test_leap_year_monthly_aggregation(self) -> None:
        datetimes = pd.date_range("2024-01-01", periods=8784, freq="h")
        hourly = pd.DataFrame(
            {
                "datetime": datetimes,
                "load_kw": 10.0,
                "bau_expense_usd": 1.0,
                "re_expense_usd": 0.0,
                "grid_load_after_solar_kw": 5.0,
                "grid_load_after_re_kw": 5.0,
            }
        )

        monthly = aggregate_hourly_to_monthly(hourly, demand_reduction_target_ratio=0.0)
        assert len(monthly) == 12
        assert monthly["bau_grid_expense_usd"].sum() == pytest.approx(8784.0)
        assert monthly["re_grid_expense_usd"].sum() == pytest.approx(0.0)

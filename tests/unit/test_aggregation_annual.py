"""
Unit tests for aggregation.annual module.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.aggregation.annual import (
    calculate_total_dppa_revenue_usd,
    calculate_total_solar_generation_mwh,
    calculate_year1_totals,
)
from re_storage.core.exceptions import InputValidationError


def _hourly_data() -> pd.DataFrame:
    return pd.DataFrame({"solar_gen_kw": [100.0, 100.0, 100.0, 100.0]})


def _dppa_hourly() -> pd.DataFrame:
    return pd.DataFrame({"total_dppa_revenue_usd": [10.0, 20.0, 30.0, 40.0]})


def _monthly_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "baseline_peak_kw": [120.0, 90.0],
            "demand_target_kw": [108.0, 81.0],
            "bau_grid_expense_usd": [22.0, 17.0],
            "re_grid_expense_usd": [13.0, 11.0],
            "grid_savings_usd": [9.0, 6.0],
            "peak_demand_after_solar_kw": [80.0, 65.0],
            "peak_demand_after_re_kw": [60.0, 45.0],
        },
        index=[1, 2],
    )


class TestAnnualTotals:
    def test_total_solar_generation_mwh(self) -> None:
        hourly = _hourly_data()
        result = calculate_total_solar_generation_mwh(hourly, scale_factor=1.1)
        assert result == pytest.approx(0.44)

    def test_total_dppa_revenue_usd(self) -> None:
        dppa = _dppa_hourly()
        result = calculate_total_dppa_revenue_usd(dppa)
        assert result == pytest.approx(100.0)

    def test_calculate_year1_totals(self) -> None:
        monthly = _monthly_data()
        hourly = _hourly_data()
        dppa = _dppa_hourly()
        result = calculate_year1_totals(monthly, hourly, dppa, scale_factor=1.0)

        assert result.loc[1, "total_solar_generation_mwh"] == pytest.approx(0.4)
        assert result.loc[1, "total_dppa_revenue_usd"] == pytest.approx(100.0)
        assert result.loc[1, "total_grid_savings_usd"] == pytest.approx(15.0)
        assert result.loc[1, "baseline_peak_kw"] == pytest.approx(120.0)
        assert result.loc[1, "demand_target_kw"] == pytest.approx(108.0)
        assert result.loc[1, "peak_demand_after_solar_kw"] == pytest.approx(80.0)
        assert result.loc[1, "peak_demand_after_re_kw"] == pytest.approx(60.0)

    def test_missing_monthly_column_raises(self) -> None:
        monthly = _monthly_data().drop(columns=["grid_savings_usd"])
        with pytest.raises(InputValidationError, match="Missing required columns"):
            calculate_year1_totals(monthly, _hourly_data(), _dppa_hourly(), scale_factor=1.0)

"""
Unit tests for aggregation.monthly module.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.aggregation.monthly import aggregate_hourly_to_monthly
from re_storage.core.exceptions import InputValidationError


def _sample_hourly() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2025-01-01 00:00",
                    "2025-01-15 12:00",
                    "2025-02-01 00:00",
                    "2025-02-15 12:00",
                ]
            ),
            "load_kw": [100.0, 120.0, 80.0, 90.0],
            "bau_expense_usd": [10.0, 12.0, 8.0, 9.0],
            "re_expense_usd": [6.0, 7.0, 5.0, 6.0],
            "grid_load_after_solar_kw": [70.0, 80.0, 60.0, 65.0],
            "grid_load_after_re_kw": [50.0, 60.0, 40.0, 45.0],
        }
    )


class TestAggregateHourlyToMonthly:
    def test_monthly_rollup_columns_and_values(self) -> None:
        hourly = _sample_hourly()
        result = aggregate_hourly_to_monthly(hourly, demand_reduction_target_ratio=0.1)

        assert list(result.index) == [1, 2]
        assert result.loc[1, "baseline_peak_kw"] == pytest.approx(120.0)
        assert result.loc[2, "baseline_peak_kw"] == pytest.approx(90.0)
        assert result.loc[1, "demand_target_kw"] == pytest.approx(108.0)
        assert result.loc[2, "demand_target_kw"] == pytest.approx(81.0)
        assert result.loc[1, "bau_grid_expense_usd"] == pytest.approx(22.0)
        assert result.loc[2, "bau_grid_expense_usd"] == pytest.approx(17.0)
        assert result.loc[1, "re_grid_expense_usd"] == pytest.approx(13.0)
        assert result.loc[2, "re_grid_expense_usd"] == pytest.approx(11.0)
        assert result.loc[1, "peak_demand_after_solar_kw"] == pytest.approx(80.0)
        assert result.loc[2, "peak_demand_after_solar_kw"] == pytest.approx(65.0)
        assert result.loc[1, "peak_demand_after_re_kw"] == pytest.approx(60.0)
        assert result.loc[2, "peak_demand_after_re_kw"] == pytest.approx(45.0)
        assert result.loc[1, "grid_savings_usd"] == pytest.approx(9.0)
        assert result.loc[2, "grid_savings_usd"] == pytest.approx(6.0)

    def test_missing_required_columns_raises(self) -> None:
        hourly = _sample_hourly().drop(columns=["bau_expense_usd"])
        with pytest.raises(InputValidationError, match="Missing required columns"):
            aggregate_hourly_to_monthly(hourly, demand_reduction_target_ratio=0.1)

    def test_invalid_demand_reduction_ratio_raises(self) -> None:
        hourly = _sample_hourly()
        with pytest.raises(InputValidationError, match="demand_reduction_target_ratio"):
            aggregate_hourly_to_monthly(hourly, demand_reduction_target_ratio=1.5)

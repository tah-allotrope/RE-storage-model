"""
Unit tests for aggregation.lifetime module.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.aggregation.lifetime import (
    build_lifetime_projection,
    project_battery_capacity_kwh,
    project_lifetime_generation_mwh,
)
from re_storage.core.exceptions import DegradationTableError, InputValidationError


def _degradation_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [1, 2, 3],
            "pv_factor": [1.0, 0.9, 0.8],
            "battery_factor_with_replacement": [1.0, 0.95, 0.9],
        }
    )


def _year1_totals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [1],
            "total_solar_generation_mwh": [100.0],
            "total_dppa_revenue_usd": [50.0],
            "total_grid_savings_usd": [20.0],
        }
    ).set_index("year")


class TestLifetimeProjection:
    def test_project_lifetime_generation(self) -> None:
        result = project_lifetime_generation_mwh(100.0, _degradation_table(), project_years=3)
        assert result.tolist() == pytest.approx([100.0, 90.0, 80.0])
        assert list(result.index) == [1, 2, 3]

    def test_project_battery_capacity(self) -> None:
        result = project_battery_capacity_kwh(200.0, _degradation_table(), project_years=3)
        assert result.tolist() == pytest.approx([200.0, 190.0, 180.0])
        assert list(result.index) == [1, 2, 3]

    def test_build_lifetime_projection(self) -> None:
        result = build_lifetime_projection(
            _year1_totals(),
            _degradation_table(),
            initial_capacity_kwh=200.0,
            project_years=3,
        )
        assert result.loc[1, "generation_mwh"] == pytest.approx(100.0)
        assert result.loc[2, "generation_mwh"] == pytest.approx(90.0)
        assert result.loc[3, "generation_mwh"] == pytest.approx(80.0)
        assert result.loc[1, "battery_capacity_kwh"] == pytest.approx(200.0)
        assert result.loc[2, "battery_capacity_kwh"] == pytest.approx(190.0)
        assert result.loc[3, "battery_capacity_kwh"] == pytest.approx(180.0)
        assert result.loc[1, "dppa_revenue_usd"] == pytest.approx(50.0)
        assert result.loc[2, "dppa_revenue_usd"] == pytest.approx(45.0)
        assert result.loc[3, "dppa_revenue_usd"] == pytest.approx(40.0)
        assert result.loc[1, "grid_savings_usd"] == pytest.approx(20.0)
        assert result.loc[2, "grid_savings_usd"] == pytest.approx(18.0)
        assert result.loc[3, "grid_savings_usd"] == pytest.approx(16.0)

    def test_missing_years_raise(self) -> None:
        table = _degradation_table().iloc[:2].copy()
        with pytest.raises(DegradationTableError, match="covers"):
            project_lifetime_generation_mwh(100.0, table, project_years=3)

    def test_invalid_factors_raise(self) -> None:
        table = _degradation_table().copy()
        table.loc[1, "pv_factor"] = 1.2
        with pytest.raises(InputValidationError, match="pv_factor"):
            project_lifetime_generation_mwh(100.0, table, project_years=3)

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

    def test_dppa_escalation_applied_5pct(self) -> None:
        """DPPA revenue should grow at 5%/yr from year 1 (before degradation)."""
        result = build_lifetime_projection(
            _year1_totals(),
            _degradation_table(),
            initial_capacity_kwh=200.0,
            project_years=3,
            revenue_escalation_pct=0.05,
            fmp_descent_pct=0.0,
        )
        # year 1: 50 × 1.0 (pv) × 1.05^0 = 50
        # year 2: 50 × 0.9 (pv) × 1.05^1 = 47.25
        # year 3: 50 × 0.8 (pv) × 1.05^2 = 44.1
        assert result.loc[1, "dppa_revenue_usd"] == pytest.approx(50.0)
        assert result.loc[2, "dppa_revenue_usd"] == pytest.approx(50.0 * 0.9 * 1.05, rel=1e-6)
        assert result.loc[3, "dppa_revenue_usd"] == pytest.approx(50.0 * 0.8 * 1.05**2, rel=1e-6)

    def test_fmp_descent_applied_minus_5pct(self) -> None:
        """Grid savings should decline at 5%/yr when fmp_descent_pct=-0.05."""
        result = build_lifetime_projection(
            _year1_totals(),
            _degradation_table(),
            initial_capacity_kwh=200.0,
            project_years=3,
            revenue_escalation_pct=0.0,
            fmp_descent_pct=-0.05,
        )
        # grid factor = (1 + 0.0 + (-0.05))^(y-1) × pv_factor
        # year 1: 20 × 1.0 × 0.95^0 = 20
        # year 2: 20 × 0.9 × 0.95^1 = 17.1
        # year 3: 20 × 0.8 × 0.95^2 = 14.42
        assert result.loc[1, "grid_savings_usd"] == pytest.approx(20.0)
        assert result.loc[2, "grid_savings_usd"] == pytest.approx(20.0 * 0.9 * 0.95, rel=1e-6)
        assert result.loc[3, "grid_savings_usd"] == pytest.approx(20.0 * 0.8 * 0.95**2, rel=1e-6)

    def test_dppa_and_fmp_escalation_independent(self) -> None:
        """With dppa=5% and fmp=-5%, DPPA grows while grid savings are flat (net 0%)."""
        result = build_lifetime_projection(
            _year1_totals(),
            _degradation_table(),
            initial_capacity_kwh=200.0,
            project_years=3,
            revenue_escalation_pct=0.05,
            fmp_descent_pct=-0.05,
        )
        # DPPA grows at 5% per year (× pv_factor)
        assert result.loc[2, "dppa_revenue_usd"] == pytest.approx(50.0 * 0.9 * 1.05, rel=1e-6)
        # grid_savings net escalation = 5% + (-5%) = 0%; only pv degradation applies
        assert result.loc[2, "grid_savings_usd"] == pytest.approx(20.0 * 0.9 * 1.0, rel=1e-6)
        assert result.loc[3, "grid_savings_usd"] == pytest.approx(20.0 * 0.8 * 1.0, rel=1e-6)

    def test_missing_years_raise(self) -> None:
        table = _degradation_table().iloc[:2].copy()
        with pytest.raises(DegradationTableError, match="does not cover"):
            project_lifetime_generation_mwh(100.0, table, project_years=3)

    def test_invalid_factors_raise(self) -> None:
        table = _degradation_table().copy()
        table.loc[1, "pv_factor"] = 1.2
        with pytest.raises(InputValidationError, match="pv_factor"):
            project_lifetime_generation_mwh(100.0, table, project_years=3)

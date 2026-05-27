"""Unit tests for the reporting chart generator."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from re_storage.reporting.charts import (
    generate_average_day_dispatch,
    generate_dscr_line_chart,
    generate_monthly_generation_bar,
)


def _sample_hourly_df() -> pd.DataFrame:
    """Create a small synthetic hourly DataFrame (48 hours = 2 days)."""
    hours = list(range(48))
    return pd.DataFrame(
        {
            "solar_gen_kw": [max(0, 500 * ((h % 24) - 6) / 6) if 6 <= (h % 24) <= 12 else 0 for h in hours],
            "load_kw": [800 + 200 * ((h % 24) > 17) for h in hours],
            "soc_kwh": [3000 + 1000 * ((h % 24) / 24) for h in hours],
            "discharged_kw": [100 if 18 <= (h % 24) <= 22 else 0 for h in hours],
            "pv_charged_kw": [200 if 6 <= (h % 24) <= 12 else 0 for h in hours],
            "grid_load_after_re_kw": [400 if 18 <= (h % 24) <= 22 else 100 for h in hours],
        }
    )


def _sample_annual_df() -> pd.DataFrame:
    """Create a small synthetic annual DataFrame (5 years)."""
    return pd.DataFrame(
        {
            "year": list(range(1, 6)),
            "dppa_revenue_usd": [200_000, 210_000, 220_000, 230_000, 240_000],
            "grid_savings_usd": [250_000, 245_000, 240_000, 235_000, 230_000],
            "demand_charge_savings_usd": [50_000, 48_000, 46_000, 44_000, 42_000],
            "dscr": [1.5, 1.48, 1.46, 1.44, 1.42],
        }
    )


class TestAverageDayDispatch:
    def test_average_day_dispatch_creates_png(self):
        df = _sample_hourly_df()
        path = generate_average_day_dispatch(df, title="Test Dispatch")
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0

    def test_average_day_dispatch_with_datetime_index(self):
        df = _sample_hourly_df()
        df.index = pd.date_range("2024-01-01", periods=len(df), freq="h")
        path = generate_average_day_dispatch(df, title="Test Dispatch Datetime")
        assert path.exists()
        assert path.stat().st_size > 0


class TestDscrChart:
    def test_dscr_chart_creates_png(self):
        df = _sample_annual_df()
        path = generate_dscr_line_chart(df, covenant=1.3, title="Test DSCR")
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0

    def test_dscr_chart_missing_column_raises(self):
        df = pd.DataFrame({"year": [1, 2, 3], "revenue": [100, 200, 300]})
        with pytest.raises(ValueError, match="dscr"):
            generate_dscr_line_chart(df)


class TestRevenueBarChart:
    def test_revenue_bar_creates_png(self):
        df = _sample_annual_df()
        path = generate_monthly_generation_bar(df, title="Test Revenue")
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0

    def test_revenue_bar_with_partial_columns(self):
        df = pd.DataFrame(
            {
                "year": [1, 2, 3],
                "dppa_revenue_usd": [100_000, 110_000, 120_000],
            }
        )
        path = generate_monthly_generation_bar(df, title="Partial Revenue")
        assert path.exists()
        assert path.stat().st_size > 0

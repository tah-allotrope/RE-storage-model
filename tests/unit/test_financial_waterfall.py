"""
Unit tests for financial.waterfall module.

Tests cover:
1. Waterfall calculations for revenue, opex, and cash flow.
2. Capex handling for year 0 and augmentation years.
3. Validation for missing required columns.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.exceptions import InputValidationError
from re_storage.financial.waterfall import build_cash_flow_waterfall


def _lifetime_revenue() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [1, 2],
            "dppa_revenue_usd": [1000.0, 900.0],
            "grid_savings_usd": [200.0, 180.0],
            "demand_charge_savings_usd": [100.0, 90.0],
        }
    ).set_index("year", drop=False)


def _lifetime_opex() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [1, 2],
            "o_and_m_usd": [100.0, 100.0],
            "insurance_usd": [20.0, 20.0],
            "land_lease_usd": [10.0, 10.0],
            "management_fees_usd": [30.0, 30.0],
            "grid_connection_usd": [40.0, 40.0],
            "taxes_usd": [90.0, 80.0],
            "mra_contribution_usd": [10.0, 10.0],
        }
    ).set_index("year", drop=False)


def _debt_schedule() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [1, 2],
            "interest_usd": [50.0, 40.0],
            "principal_usd": [150.0, 160.0],
            "total_debt_service_usd": [200.0, 200.0],
        }
    ).set_index("year", drop=False)


class TestCashFlowWaterfall:
    """Tests for build_cash_flow_waterfall."""

    def test_waterfall_calculation(self) -> None:
        revenue = _lifetime_revenue()
        opex = _lifetime_opex()
        debt = _debt_schedule()
        capex = {
            "initial_capex_usd": 1000.0,
            "augmentation_capex_usd": pd.Series({2: 200.0}),
        }

        result = build_cash_flow_waterfall(revenue, opex, debt, capex)

        assert 0 in result.index
        assert result.loc[0, "capex_usd"] == pytest.approx(1000.0)
        assert result.loc[2, "capex_usd"] == pytest.approx(200.0)
        assert result.loc[1, "total_revenue_usd"] == pytest.approx(1300.0)
        assert result.loc[1, "total_opex_usd"] == pytest.approx(200.0)
        assert result.loc[1, "ebitda_usd"] == pytest.approx(1100.0)
        assert result.loc[1, "cfads_usd"] == pytest.approx(900.0)
        assert result.loc[1, "free_cash_flow_to_equity_usd"] == pytest.approx(800.0)

    def test_missing_columns_raise(self) -> None:
        revenue = _lifetime_revenue().drop(columns=["grid_savings_usd"])
        opex = _lifetime_opex()
        debt = _debt_schedule()
        capex = {"initial_capex_usd": 1000.0}

        with pytest.raises(InputValidationError, match="Missing required columns"):
            build_cash_flow_waterfall(revenue, opex, debt, capex)

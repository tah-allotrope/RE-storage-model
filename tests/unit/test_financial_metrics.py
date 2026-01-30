"""
Unit tests for financial.metrics module.

Tests cover:
1. XNPV calculation for dated cashflows.
2. XIRR calculations for project and equity cashflows.
3. DSCR series calculation and validation.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.exceptions import InputValidationError
from re_storage.financial.metrics import (
    calculate_dscr_series,
    calculate_equity_irr,
    calculate_npv,
    calculate_project_irr,
)


def _dates() -> pd.Series:
    return pd.to_datetime(["2025-01-01", "2026-01-01", "2027-01-01"])


class TestFinancialMetrics:
    """Tests for IRR/NPV and DSCR calculations."""

    def test_calculate_npv(self) -> None:
        cashflows = pd.Series([-1000.0, 600.0, 600.0])
        dates = _dates()
        expected = -1000.0 + 600.0 / 1.1 + 600.0 / (1.1**2)

        result = calculate_npv(cashflows, dates, discount_rate_pct=10.0)

        assert result == pytest.approx(expected)

    def test_calculate_project_irr(self) -> None:
        cashflows = pd.Series([-1000.0, 600.0, 600.0])
        dates = _dates()

        result = calculate_project_irr(cashflows, dates)

        assert result == pytest.approx(0.130662, rel=1e-4)

    def test_calculate_equity_irr(self) -> None:
        cashflows = pd.Series([-1000.0, 600.0, 600.0])
        dates = _dates()

        result = calculate_equity_irr(cashflows, dates)

        assert result == pytest.approx(0.130662, rel=1e-4)

    def test_calculate_dscr_series(self) -> None:
        ebitda = pd.Series([100.0, 120.0], index=[1, 2])
        debt_service = pd.Series([50.0, 60.0], index=[1, 2])

        result = calculate_dscr_series(ebitda, debt_service)

        assert result.loc[1] == pytest.approx(2.0)
        assert result.loc[2] == pytest.approx(2.0)

    def test_invalid_debt_service_raises(self) -> None:
        ebitda = pd.Series([100.0], index=[1])
        debt_service = pd.Series([0.0], index=[1])

        with pytest.raises(InputValidationError, match="debt_service"):
            calculate_dscr_series(ebitda, debt_service)
